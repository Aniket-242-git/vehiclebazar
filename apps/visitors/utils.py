"""Utilities for visitor analytics: IP extraction, User-Agent parsing, reverse geocoding."""
from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)


def get_client_ip(request) -> str:
    """Extract client IP address from request, taking proxy/CDN headers into account."""
    header_keys = [
        "HTTP_CF_CONNECTING_IP",  # Cloudflare
        "HTTP_X_FORWARDED_FOR",   # Standard reverse proxy
        "HTTP_X_REAL_IP",         # Nginx
        "REMOTE_ADDR",            # Standard socket
    ]
    for key in header_keys:
        val = request.META.get(key)
        if val:
            # X-Forwarded-For can be a comma-separated list of IPs; first one is client
            ip = val.split(",")[0].strip()
            if ip:
                return ip
    return "127.0.0.1"


def parse_user_agent(ua_string: str) -> dict[str, str]:
    """Parse User-Agent string to extract device type, operating system, and browser."""
    if not ua_string:
        return {
            "device_type": "desktop",
            "os": "Unknown",
            "browser": "Unknown",
            "browser_version": "",
        }

    ua = ua_string
    device_type = "desktop"
    os_name = "Unknown"
    browser = "Unknown"
    browser_version = ""

    # Check for bots/crawlers
    if re.search(r"bot|crawler|spider|slurp|facebookexternalhit|bingbot|googlebot", ua, re.I):
        device_type = "bot"
        browser = "Bot / Crawler"

    # Device type detection
    if re.search(r"tablet|ipad|playbook|silk|(android(?!.*mobi))", ua, re.I):
        device_type = "tablet"
    elif re.search(r"mobile|iphone|ipod|android.*mobile|blackberry|iemobile|opera mini", ua, re.I):
        device_type = "mobile"
    else:
        if device_type != "bot":
            device_type = "desktop"

    # OS Detection
    if "Windows NT 10.0" in ua:
        os_name = "Windows 10 / 11"
    elif "Windows NT 6.3" in ua:
        os_name = "Windows 8.1"
    elif "Windows NT 6.2" in ua:
        os_name = "Windows 8"
    elif "Windows NT 6.1" in ua:
        os_name = "Windows 7"
    elif "Windows NT" in ua:
        os_name = "Windows"
    elif "iPhone" in ua:
        m = re.search(r"OS (\d+[_.]\d+)", ua)
        ver = m.group(1).replace("_", ".") if m else ""
        os_name = f"iOS {ver}".strip()
    elif "iPad" in ua:
        m = re.search(r"OS (\d+[_.]\d+)", ua)
        ver = m.group(1).replace("_", ".") if m else ""
        os_name = f"iPadOS {ver}".strip()
    elif "Mac OS X" in ua:
        m = re.search(r"Mac OS X (\d+[_.]\d+)", ua)
        ver = m.group(1).replace("_", ".") if m else ""
        os_name = f"macOS {ver}".strip()
    elif "Android" in ua:
        m = re.search(r"Android (\d+(?:\.\d+)?)", ua)
        ver = m.group(1) if m else ""
        os_name = f"Android {ver}".strip()
    elif "Linux" in ua:
        os_name = "Linux"
    elif "CrOS" in ua:
        os_name = "Chrome OS"

    # Browser Detection (order matters because Chrome UA contains Safari, Edge contains Chrome)
    if "Edg/" in ua or "Edge/" in ua:
        browser = "Microsoft Edge"
        m = re.search(r"(?:Edg|Edge)/(\d+(?:\.\d+)?)", ua)
        browser_version = m.group(1) if m else ""
    elif "SamsungBrowser/" in ua:
        browser = "Samsung Internet"
        m = re.search(r"SamsungBrowser/(\d+(?:\.\d+)?)", ua)
        browser_version = m.group(1) if m else ""
    elif "OPR/" in ua or "Opera" in ua:
        browser = "Opera"
        m = re.search(r"(?:OPR|Opera)/(\d+(?:\.\d+)?)", ua)
        browser_version = m.group(1) if m else ""
    elif "Firefox/" in ua:
        browser = "Firefox"
        m = re.search(r"Firefox/(\d+(?:\.\d+)?)", ua)
        browser_version = m.group(1) if m else ""
    elif "Chrome/" in ua and "Chromium" not in ua:
        browser = "Chrome"
        m = re.search(r"Chrome/(\d+(?:\.\d+)?)", ua)
        browser_version = m.group(1) if m else ""
    elif "Safari/" in ua and "Chrome" not in ua:
        browser = "Safari"
        m = re.search(r"Version/(\d+(?:\.\d+)?)", ua)
        browser_version = m.group(1) if m else ""
    elif "MSIE" in ua or "Trident/" in ua:
        browser = "Internet Explorer"
    elif device_type != "bot":
        browser = "Browser"

    return {
        "device_type": device_type,
        "os": os_name,
        "browser": browser,
        "browser_version": browser_version,
    }


def reverse_geocode(latitude: float, longitude: float) -> dict[str, str]:
    """Reverse-geocode latitude and longitude into address components using OSM Nominatim."""
    result: dict[str, str] = {
        "city": "",
        "state_region": "",
        "country": "",
        "postal_code": "",
        "address": "",
    }
    if not latitude or not longitude:
        return result

    try:
        url = (
            f"https://nominatim.openstreetmap.org/reverse?format=json"
            f"&lat={latitude}&lon={longitude}&zoom=14&addressdetails=1"
        )
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "VehicleMarketplace-VisitorAnalytics/1.0",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                addr = data.get("address", {})
                result["city"] = (
                    addr.get("city")
                    or addr.get("town")
                    or addr.get("village")
                    or addr.get("municipality")
                    or addr.get("suburb")
                    or ""
                )
                result["state_region"] = addr.get("state") or addr.get("region") or ""
                result["country"] = addr.get("country") or ""
                result["postal_code"] = addr.get("postcode") or ""
                result["address"] = data.get("display_name") or ""
    except Exception as exc:
        logger.debug("Reverse geocoding error: %s", exc)

    return result
