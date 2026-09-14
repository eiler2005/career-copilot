import json
from pathlib import Path

import httpx
import pytest

from job_search_agent import backup, privacy, sources, workflow
from job_search_agent.cli import seed_demo, verify
from job_search_agent.core import (
    Store,
    atomic_write,
    canonical_url,
    encode,
    import_legacy,
    init_home,
    public_root,
)


@pytest.fixture
def store(tmp_path):
    home = init_home(tmp_path / "private", demo=True)
    with Store(home) as db:
        seed_demo(db)
        yield db


def test_workspace_cannot_be_public_or_implicit(tmp_path):
    for value in (public_root() / "private", Path("relative"), Path("/"), Path.home()):
        with pytest.raises(ValueError):
            init_home(value)
    home = init_home(tmp_path / "good")
    with pytest.raises(ValueError):
        init_home(home)


def test_artifacts_immutable_and_path_safe(store):
    store.artifact("evidence/sample.txt", "one")
    store.artifact("evidence/sample.txt", "one")
    with pytest.raises(ValueError):
        store.artifact("evidence/sample.txt", "two")
    with pytest.raises(ValueError):
        store.artifact("../escaped.txt", "secret")


def test_dedup_canonical_url_and_preserve_decision(store):
    original = store.get("vacancies", "demo-platform-lead")
    original["decision"] = "user decision"
    store.put("vacancies", original)
    copy = {**original, "id": "other-source-id", "urls": [original["urls"][0] + "?utm_source=test"]}
    assert store.observe_vacancy(copy, "other", "snapshot") == original["id"]
    assert len(store.all("vacancies")) == 1
    assert store.get("vacancies", original["id"])["decision"] == "user decision"


@pytest.mark.parametrize(
    "raw,evidence,expected",
    [("L5", True, "pass"), ("L4", True, "fail"), ("L5", False, "flag"), ("Other", True, "flag")],
)
def test_bigtech_exception_is_company_specific(raw, evidence, expected):
    policy = {
        "russia_director_only": True,
        "bigtech_company_ids": ["example"],
        "company_levels": {
            "example": {
                "accepted": ["L5", "L6"],
                "below": ["L4"],
                "source": "synthetic employer rubric",
            }
        },
    }
    vacancy = {
        "title": "Product Manager",
        "market": "ru",
        "level": {"raw": raw, "source": "synthetic posting" if evidence else None},
    }
    assert workflow.seniority(vacancy, {"id": "example"}, policy)["verdict"] == expected
    assert workflow.seniority(vacancy, {"id": "other"}, policy)["verdict"] == "fail"


def test_tag_match_does_not_prove_competence(store):
    result = workflow.evaluate(store, "demo-platform-lead")[0]
    assert result["requirements"][0]["suggested_facts"] == ["sample-book"]
    assert result["requirements"][0]["covered"] is False
    workflow.evaluate(store, "demo-platform-lead")
    assert len(store.all("assessments")) == 1


def test_years_and_targets_not_certified_by_keyword(store):
    vacancy = store.get("vacancies", "demo-platform-lead")
    vacancy["requirements"][0]["minimum_years"] = 5
    store.put("vacancies", vacancy)
    plan = workflow.learning_plan(store, vacancy["id"], "product")
    assert plan["gaps"][0]["gap_type"] == "structural"
    assert len(plan["weeks"]) == 6
    assert plan["hours_per_week"] == 6


def test_baseline_not_falsely_extracted_from_job(store):
    vacancy = store.get("vacancies", "demo-platform-lead")
    vacancy["requirements"] = []
    store.put("vacancies", vacancy)
    plan = workflow.learning_plan(store, vacancy["id"], "technical-leadership")
    assert plan["baseline_only"] is True
    assert "system design" in plan["weeks"][0]["focus"]


@pytest.mark.parametrize(
    "provider,payload",
    [
        (
            "greenhouse",
            {
                "jobs": [
                    {
                        "id": 1,
                        "title": "Lead",
                        "content": "<p>Build platforms</p>",
                        "absolute_url": "https://example.invalid/1",
                    }
                ]
            },
        ),
        (
            "lever",
            [
                {
                    "id": "one",
                    "text": "Lead",
                    "hostedUrl": "https://example.invalid/1",
                    "descriptionPlain": "Build platforms",
                }
            ],
        ),
        (
            "ashby",
            {
                "jobs": [
                    {
                        "id": "one",
                        "title": "Lead",
                        "jobUrl": "https://example.invalid/1",
                        "descriptionHtml": "<p>Build platforms</p>",
                    }
                ]
            },
        ),
        (
            "hh",
            {
                "items": [
                    {
                        "id": "1",
                        "name": "Lead",
                        "alternate_url": "https://example.invalid/1",
                        "snippet": {"requirement": "Build platforms"},
                    }
                ]
            },
        ),
    ],
)
def test_api_adapters(provider, payload):
    jobs = sources.parse_jobs(
        provider, json.dumps(payload), {"company_id": "example", "url": "https://example.invalid"}
    )
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Lead"
    assert jobs[0]["availability"] == "open"
    assert jobs[0]["requirements"] == []


def test_corporate_jsonld_and_schema_failure():
    source = {"company_id": "example", "url": "https://example.invalid/job"}
    body = (
        '<script type="application/ld+json">'
        + json.dumps({"@type": "JobPosting", "title": "Lead", "description": "Build"})
        + "</script>"
    )
    assert sources.parse_jobs("corporate", body, source)[0]["availability"] == "unknown"
    with pytest.raises(ValueError):
        sources.parse_jobs("corporate", "No JSON-LD", source)


def configure_source(store):
    settings = store.settings
    settings["sources"] = [
        {
            "id": "example-board",
            "provider": "greenhouse",
            "board": "example",
            "company_id": "example-systems",
            "interval_seconds": 4,
        }
    ]
    atomic_write(store.home / "settings.json", encode(settings))


@pytest.mark.parametrize(
    "code,body,status",
    [
        (200, '{"jobs":[]}', "success_empty"),
        (200, "<html>verify you are human</html>", "blocked"),
        (403, "denied", "blocked"),
        (401, "login", "auth_required"),
        (429, "slow", "rate_limited"),
        (200, '{"changed":[]}', "parse_changed"),
        (500, "error", "http_error"),
    ],
)
def test_source_health_not_empty_success(store, code, body, status):
    configure_source(store)
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(code, text=body, headers={"retry-after": "60"})
        )
    ) as client:
        result = sources.discover(store, client=client)
        assert result[0]["status"] == status
        assert sources.discover(store, client=client)[0]["status"] == "cooldown"


def test_timeout_is_observed(store):
    configure_source(store)

    def fail(request):
        raise httpx.ReadTimeout("synthetic timeout")

    with httpx.Client(transport=httpx.MockTransport(fail)) as client:
        assert sources.discover(store, client=client)[0]["status"] == "timeout"


def test_replay_is_offline_idempotent(store):
    configure_source(store)
    body = json.dumps(
        {"jobs": [{"id": 1, "title": "Lead", "absolute_url": "https://example.invalid/new"}]}
    )
    path = store.artifact("snapshots/demo.txt", body)
    sources.discover(store, replay=path)
    sources.discover(store, replay=path)
    assert len(store.all("vacancies")) == 2
    assert len(store.all("observations")) == 2
    historical = next(v for v in store.all("vacancies") if v["id"] != "demo-platform-lead")
    assert historical["availability"] == "unknown"
    assert historical["status_checked_on"] is None
    assert store.all("source_health") == []
    historical.update(availability="archived", status_checked_on="2026-01-01")
    store.put("vacancies", historical)
    sources.discover(store, replay=path)
    assert store.get("vacancies", historical["id"])["availability"] == "archived"


def test_archive_privacy_and_traversal(tmp_path):
    import zipfile

    path = tmp_path / "example.whl"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("package/metadata.txt", "SyntheticPrivate" + "Marker")
    dictionary = tmp_path / "dict.json"
    atomic_write(dictionary, encode({"terms": ["SyntheticPrivate" + "Marker"]}))
    assert privacy.check_artifact(path, dictionary)["passed"] is False
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("../escape.txt", "safe")
    assert privacy.check_artifact(path)["passed"] is False


def test_proxy_without_permission_rejected(store):
    configure_source(store)
    settings = store.settings
    settings["sources"][0]["proxy_env"] = "SYNTHETIC_PROXY"
    atomic_write(store.home / "settings.json", encode(settings))
    with pytest.raises(ValueError):
        sources.discover(store)


def test_only_safe_urls():
    for url in (
        "file:///tmp/example",
        "javascript:alert(1)",
        "http://" + "user:pass" + "@example.invalid/",
    ):
        with pytest.raises(ValueError):
            canonical_url(url)
    with pytest.raises(ValueError):
        sources.checked_url("https://127.0.0.1/test", {"127.0.0.1"})


def test_backup_restore_checksum_before_mutation(store, tmp_path):
    store.artifact("evidence/one.txt", "synthetic")
    snapshot = tmp_path / "backup"
    backup.backup(store, snapshot)
    restored = tmp_path / "restored"
    assert backup.restore(snapshot, restored)["verified"] is True
    with Store(restored) as recovered:
        assert verify(recovered)["passed"] is True
        assert recovered.get("companies", "example-systems") == store.get(
            "companies", "example-systems"
        )
    atomic_write(snapshot / "evidence/one.txt", "changed")
    with pytest.raises(ValueError):
        backup.restore(snapshot, tmp_path / "must-not-exist")
    assert not (tmp_path / "must-not-exist").exists()


def test_privacy_redacts_matches_and_detects_private_files(tmp_path):
    term = "SyntheticPrivate" + "CandidateMarker"
    assert "private-dictionary-match" in privacy.scan_blob("docs/test.md", term.encode(), [term])
    assert "path-not-allowlisted" in privacy.scan_blob("private/facts.json", b"{}", [])
    assert "uninspectable-content" in privacy.scan_blob("docs/image.png", b"\0abc", [])
    key = ("sk-" + "a" * 30).encode()
    assert "api-key" in privacy.scan_blob("docs/key.txt", key, [])
    assert privacy.scan_blob("docs/safe.md", b"contact: alex@example.invalid", []) == []


def test_exact_git_index_and_history(tmp_path):
    import subprocess

    root = tmp_path / "public"
    root.mkdir()

    def git(*args):
        return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)

    git("init")
    secret = "SyntheticPrivate" + "CandidateMarker"
    atomic_write(root / "README.md", secret)
    git("add", "README.md")
    atomic_write(root / "README.md", "safe worktree")
    dictionary = tmp_path / "dictionary.json"
    atomic_write(dictionary, encode({"terms": [secret]}))
    assert privacy.check(root, "index", dictionary)["passed"] is False
    assert privacy.check(root, "worktree", dictionary)["passed"] is True
    git(
        "-c",
        "user.name=Example",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-m",
        "Synthetic fixture",
    )
    git("add", "README.md")
    git(
        "-c",
        "user.name=Example",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-m",
        "Clean latest",
    )
    assert privacy.check(root, "history", dictionary)["passed"] is False


def test_symlink_cannot_publish(tmp_path):
    root = tmp_path / "public"
    root.mkdir()
    (root / "README.md").symlink_to(tmp_path / "outside.txt")
    result = privacy.check(root, "worktree")
    assert result["findings"][0]["rules"] == ["symlink-forbidden"]


def test_legacy_dry_run_repeat_and_conflict(store, tmp_path):
    registry = tmp_path / "legacy" / "journal" / "registry.json"
    data = {
        "schema_version": 2,
        "companies": [{"id": "legacy-example", "name": "Legacy synthetic"}],
        "vacancies": [],
        "packages": [],
        "events": [],
    }
    atomic_write(registry, encode(data))
    before = len(store.all("companies"))
    assert import_legacy(store, registry, dry_run=True)["counts"]["companies"] == 1
    assert len(store.all("companies")) == before
    import_legacy(store, registry)
    import_legacy(store, registry)
    assert len(store.all("companies")) == before + 1
    store.put("companies", {"id": "legacy-example", "name": "Newer decision"})
    with pytest.raises(ValueError):
        import_legacy(store, registry)


def test_master_pdf_and_hash_bound_independent_reviews(store, tmp_path):
    text, coverage = workflow.markdown_draft(store.facts, "product")
    cv = tmp_path / "draft.md"
    atomic_write(cv, text)
    matrix = tmp_path / "coverage.json"
    atomic_write(matrix, encode(coverage))
    package = workflow.prepare(
        store,
        "master",
        "product",
        cv=cv,
        author_model="gpt-6-astra",
        author_session="author",
        coverage_file=matrix,
    )
    same = workflow.prepare(
        store,
        "master",
        "product",
        cv=cv,
        author_model="gpt-6-astra",
        author_session="author",
        coverage_file=matrix,
    )
    assert len(same["versions"]) == 1
    version = package["versions"][0]
    assert version["review_status"] == "pending"
    report = tmp_path / "review.json"
    review = {
        "kind": "content",
        "version_id": version["id"],
        "sha256": version["sha256"],
        "model": "gpt-6-astra",
        "session": "author",
        "passed": True,
        "coverage_complete": True,
        "findings": ["Synthetic assertions inspected"],
    }
    atomic_write(report, encode(review))
    with pytest.raises(ValueError):
        workflow.record_review(store, package["id"], report)
    review["session"] = "independent"
    atomic_write(report, encode(review))
    assert workflow.record_review(store, package["id"], report)["status"] == "pending"
    review.update(kind="visual", checked_pages=[1], extracted_text_checked=True)
    atomic_write(report, encode(review))
    assert workflow.record_review(store, package["id"], report)["status"] == "passed"
    atomic_write(store.path(version["files"]["cv_source"]), "changed source")
    assert verify(store)["passed"] is False
    with pytest.raises(ValueError):
        workflow.record_review(store, package["id"], report)
