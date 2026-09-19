"use strict";

// Apply the preference before the body paints. Only the visual layer changes;
// routes, loaded records and pending form inputs stay in place.
(() => {
  const storageKey = "career-copilot-design";
  const valid = (value) => value === "v1" || value === "v2" || value === "v3";
  const stylesheetV2 = document.getElementById("design-v2");
  const stylesheetV3 = document.getElementById("design-v3");
  const designOnly = () => document.querySelectorAll("[data-design-only]");
  let saved;
  try { saved = localStorage.getItem(storageKey); } catch (_) { /* Storage is optional. */ }
  const requested = new URL(location.href).searchParams.get("design");
  let version = valid(requested) ? requested : valid(saved) ? saved : "v3";

  function apply(value) {
    version = valid(value) ? value : "v3";
    stylesheetV2.disabled = version === "v1";
    stylesheetV3.disabled = version !== "v3";
    document.documentElement.dataset.design = version;
    designOnly().forEach((node) => { node.hidden = node.dataset.designOnly !== version; });
    try { localStorage.setItem(storageKey, version); } catch (_) { /* Keep the current-page choice. */ }
  }
  apply(version);

  document.addEventListener("DOMContentLoaded", () => {
    const select = document.getElementById("design-version");
    select.value = version;
    select.addEventListener("change", () => {
      apply(select.value);
      // Replace a deep link's old override too, so reloading keeps this choice.
      const url = new URL(location.href);
      url.searchParams.set("design", version);
      history.replaceState(history.state, "", url);
    });
  });
})();
