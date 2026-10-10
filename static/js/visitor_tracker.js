/**
 * Visitor Tracking & Geolocation Permission Handler
 * 
 * Captures visitor timestamp, device type, OS, browser, screen resolution,
 * and requests GPS location permission. If allowed, logs coordinates and address;
 * if not allowed/denied, logs visit without GPS location.
 */
(function () {
  "use strict";

  // Do not track admin panel or internal pages
  var path = window.location.pathname;
  if (path.indexOf("/admin-panel") === 0 || path.indexOf("/django-admin") === 0) {
    return;
  }

  var currentVisitId = null;
  var hasLoggedInitial = false;
  var promptTimer = null;

  var bannerEl = document.getElementById("locationPromptBanner");
  var btnAllow = document.getElementById("btnAllowLocation");
  var btnDeny = document.getElementById("btnDenyLocation");
  var btnDismiss = document.getElementById("btnDismissLocationPrompt");
  var btnAllowText = document.getElementById("btnAllowLocationText");
  var btnAllowSpinner = document.getElementById("btnAllowLocationSpinner");
  var toastEl = document.getElementById("locationSuccessToast");

  /**
   * Base payload containing device information and navigation data.
   */
  function getBasePayload() {
    return {
      visit_id: currentVisitId,
      page_url: window.location.pathname + window.location.search,
      referrer: document.referrer || "",
      screen_resolution: (window.screen.width || 0) + "x" + (window.screen.height || 0),
      language: navigator.language || navigator.userLanguage || "",
    };
  }

  /**
   * Send tracking request to backend.
   */
  function sendTracking(payload, onSuccess) {
    var data = Object.assign(getBasePayload(), payload);
    fetch("/api/track-visit/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
      keepalive: true,
    })
      .then(function (res) {
        return res.json();
      })
      .then(function (resp) {
        if (resp && resp.visit_id) {
          currentVisitId = resp.visit_id;
        }
        hasLoggedInitial = true;
        if (typeof onSuccess === "function") {
          onSuccess(resp);
        }
      })
      .catch(function (err) {
        console.warn("Visitor tracking ping error:", err);
      });
  }

  /**
   * Reverse-geocode coordinates using OpenStreetMap Nominatim.
   */
  function reverseGeocode(lat, lon, callback) {
    var url = "https://nominatim.openstreetmap.org/reverse?format=json&lat=" +
              encodeURIComponent(lat) + "&lon=" + encodeURIComponent(lon) +
              "&zoom=14&addressdetails=1";

    var controller = typeof AbortController !== "undefined" ? new AbortController() : null;
    var signal = controller ? controller.signal : null;
    var timeoutId = null;

    if (controller) {
      timeoutId = setTimeout(function () {
        controller.abort();
      }, 2500);
    }

    fetch(url, { signal: signal, headers: { Accept: "application/json" } })
      .then(function (res) {
        if (timeoutId) clearTimeout(timeoutId);
        return res.json();
      })
      .then(function (data) {
        var addr = data.address || {};
        var city = addr.city || addr.town || addr.village || addr.municipality || addr.suburb || "";
        var state = addr.state || addr.region || "";
        var country = addr.country || "";
        var postalCode = addr.postcode || "";
        var address = data.display_name || "";
        callback({
          city: city,
          state: state,
          country: country,
          postal_code: postalCode,
          address: address,
        });
      })
      .catch(function () {
        // Fallback: callback with empty address; server will attempt backend reverse geocode
        callback({});
      });
  }

  function showBanner() {
    if (bannerEl) {
      bannerEl.style.display = "block";
    }
  }

  function hideBanner() {
    if (bannerEl) {
      bannerEl.style.display = "none";
    }
    if (promptTimer) {
      clearTimeout(promptTimer);
      promptTimer = null;
    }
  }

  function showSuccessToast(city, country) {
    if (!toastEl || !window.bootstrap) return;
    var msgEl = document.getElementById("locationSuccessMessage");
    if (msgEl) {
      if (city) {
        msgEl.textContent = "Location detected (" + city + (country ? ", " + country : "") + "). Showing local vehicles!";
      } else {
        msgEl.textContent = "Location enabled! Showing local vehicles.";
      }
    }
    try {
      var toast = new bootstrap.Toast(toastEl, { delay: 4000 });
      toast.show();
    } catch (e) {
      /* ignore */
    }
  }

  /**
   * Request GPS position via HTML5 Geolocation API.
   */
  function requestPosition(onSuccess, onError) {
    if (!navigator.geolocation) {
      if (onError) onError({ code: 0, message: "Geolocation not supported" });
      return;
    }
    navigator.geolocation.getCurrentPosition(
      function (position) {
        if (onSuccess) onSuccess(position);
      },
      function (err) {
        if (onError) onError(err);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000,
      }
    );
  }

  /**
   * Handle user granting location permission.
   */
  function handleLocationGranted(position) {
    var coords = position.coords;
    var lat = coords.latitude;
    var lon = coords.longitude;
    var accuracy = coords.accuracy;

    reverseGeocode(lat, lon, function (geo) {
      var payload = {
        location_enabled: true,
        location_status: "granted",
        latitude: lat,
        longitude: lon,
        accuracy: accuracy,
        city: geo.city || "",
        state: geo.state || "",
        country: geo.country || "",
        postal_code: geo.postal_code || "",
        address: geo.address || "",
      };

      sendTracking(payload, function () {
        showSuccessToast(geo.city, geo.country);
      });
    });
  }

  /**
   * Handle user denying location or timeout.
   */
  function handleLocationDenied(status) {
    var payload = {
      location_enabled: false,
      location_status: status || "denied",
    };
    sendTracking(payload);
  }

  // --- Attach Event Listeners ---
  if (btnAllow) {
    btnAllow.addEventListener("click", function () {
      if (btnAllowSpinner && btnAllowText) {
        btnAllowSpinner.classList.remove("d-none");
        btnAllowText.classList.add("d-none");
        btnAllow.disabled = true;
      }

      requestPosition(
        function (pos) {
          hideBanner();
          handleLocationGranted(pos);
        },
        function (err) {
          hideBanner();
          handleLocationDenied("denied");
        }
      );
    });
  }

  if (btnDeny) {
    btnDeny.addEventListener("click", function () {
      hideBanner();
      try {
        sessionStorage.setItem("loc_prompt_dismissed", "1");
      } catch (e) {}
      handleLocationDenied("denied");
    });
  }

  if (btnDismiss) {
    btnDismiss.addEventListener("click", function () {
      hideBanner();
      try {
        sessionStorage.setItem("loc_prompt_dismissed", "1");
      } catch (e) {}
      handleLocationDenied("denied");
    });
  }

  // --- Main Initialization Flow ---
  function initTracker() {
    if (!navigator.geolocation) {
      // Browser does not support geolocation
      sendTracking({ location_enabled: false, location_status: "unsupported" });
      return;
    }

    var dismissed = false;
    try {
      dismissed = sessionStorage.getItem("loc_prompt_dismissed") === "1";
    } catch (e) {}

    // Check Permissions API if available
    if (navigator.permissions && navigator.permissions.query) {
      navigator.permissions
        .query({ name: "geolocation" })
        .then(function (permissionStatus) {
          if (permissionStatus.state === "granted") {
            // Already allowed - fetch position silently without annoying banner
            requestPosition(
              function (pos) {
                handleLocationGranted(pos);
              },
              function () {
                handleLocationDenied("error");
              }
            );
          } else if (permissionStatus.state === "denied") {
            // User previously blocked location
            handleLocationDenied("denied");
          } else {
            // 'prompt' state
            if (dismissed) {
              handleLocationDenied("denied");
            } else {
              // Show prompt banner after slight delay
              setTimeout(showBanner, 800);

              // Fallback timer: if user ignores the banner for 6 seconds, save visit without GPS
              promptTimer = setTimeout(function () {
                if (!hasLoggedInitial) {
                  sendTracking({ location_enabled: false, location_status: "prompt_ignored" });
                }
              }, 6000);
            }
          }

          // Listen for permission change (if user changes settings in URL bar)
          permissionStatus.onchange = function () {
            if (permissionStatus.state === "granted") {
              hideBanner();
              requestPosition(handleLocationGranted);
            }
          };
        })
        .catch(function () {
          // Fallback if query failed
          fallbackPromptFlow(dismissed);
        });
    } else {
      fallbackPromptFlow(dismissed);
    }
  }

  function fallbackPromptFlow(dismissed) {
    if (dismissed) {
      handleLocationDenied("denied");
    } else {
      setTimeout(showBanner, 800);
      promptTimer = setTimeout(function () {
        if (!hasLoggedInitial) {
          sendTracking({ location_enabled: false, location_status: "prompt_ignored" });
        }
      }, 6000);
    }
  }

  // Run when DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTracker);
  } else {
    initTracker();
  }
})();
