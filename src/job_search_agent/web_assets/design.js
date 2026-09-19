"use strict";

// Apply the preference before the body paints. Only the visual layer changes;
// routes, loaded records and pending form inputs stay in place.
(() => {
  const storageKey = "career-copilot-design";
  const valid = (value) => value === "v1" || value === "v2";
  const stylesheet = document.getElementById("design-v2");
  let saved;
  try { saved = localStorage.getItem(storageKey); } catch (_) { /* Storage is optional. */ }
  const requested = new URL(location.href).searchParams.get("design");
  let version = valid(requested) ? requested : valid(saved) ? saved : "v2";

  function apply(value) {
    version = valid(value) ? value : "v2";
    stylesheet.disabled = version === "v1";
    document.documentElement.dataset.design = version;
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
