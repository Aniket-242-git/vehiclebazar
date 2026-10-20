/* =============================================================
   Shared front-end behaviour:
   1. Offer modal – auto-show once per session per offer id.
   2. Filter form – auto-submit on select change (listing page).
   ============================================================= */
(function () {
  "use strict";

  /* ---------- 1. Offer modal ---------- */
  var modalEl = document.getElementById("offerModal");
  if (modalEl && window.bootstrap) {
    var offerId = modalEl.getAttribute("data-offer-id") || "default";
    var storageKey = "seenOffer_" + offerId;
    var shown = false;
    try { shown = sessionStorage.getItem(storageKey) === "1"; } catch (e) { /* private mode */ }

    if (!shown) {
      // slight delay so the page paints first
      setTimeout(function () {
        var modal = new bootstrap.Modal(modalEl);
        modal.show();
        try { sessionStorage.setItem(storageKey, "1"); } catch (e) { /* ignore */ }
      }, 800);
    }
  }

  /* ---------- 2. Auto-submit filter selects ---------- */
  var filterForm = document.getElementById("filterForm");
  if (filterForm) {
    var cleanFormBeforeSubmit = function () {
      filterForm.querySelectorAll("input, select").forEach(function (el) {
        if (!el.name) return;
        var val = (el.value || "").trim();
        if (val === "" || val.toLowerCase() === "none" || val.toLowerCase() === "null") {
          el.disabled = true;
        }
      });
      setTimeout(function () {
        filterForm.querySelectorAll("input, select").forEach(function (el) {
          el.disabled = false;
        });
      }, 100);
    };

    filterForm.addEventListener("submit", function () {
      cleanFormBeforeSubmit();
    });

    filterForm.querySelectorAll("select").forEach(function (sel) {
      sel.addEventListener("change", function () {
        if (typeof filterForm.requestSubmit === "function") {
          filterForm.requestSubmit();
        } else {
          cleanFormBeforeSubmit();
          filterForm.submit();
        }
      });
    });

    window.addEventListener("pageshow", function () {
      filterForm.querySelectorAll("input, select").forEach(function (el) {
        el.disabled = false;
      });
    });
  }
})();
