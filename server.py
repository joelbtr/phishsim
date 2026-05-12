"""
server.py — Flask server that serves the cloned page and captures
            form submissions to a local log file.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template_string

# Suppress Flask's default request logging (we do our own)
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

AWARENESS_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Security Awareness Notice</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f5f5f5; display: flex; align-items: center;
    justify-content: center; min-height: 100vh; padding: 20px;
  }
  .card {
    background: #fff; border-radius: 12px; padding: 40px 48px;
    max-width: 560px; width: 100%; border-left: 6px solid #e53e3e;
    box-shadow: 0 2px 16px rgba(0,0,0,0.08);
  }
  .icon { font-size: 40px; margin-bottom: 16px; }
  h1 { font-size: 22px; color: #1a1a1a; margin-bottom: 12px; }
  p { font-size: 15px; color: #444; line-height: 1.7; margin-bottom: 12px; }
  .tips { background: #fff8f0; border-radius: 8px; padding: 16px 20px; margin-top: 20px; }
  .tips h2 { font-size: 14px; color: #b45309; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; }
  .tips ul { list-style: none; padding: 0; }
  .tips li { font-size: 13px; color: #555; padding: 4px 0; padding-left: 18px; position: relative; }
  .tips li::before { content: "→"; position: absolute; left: 0; color: #b45309; }
  .badge { display: inline-block; background: #e53e3e; color: #fff; font-size: 11px;
    font-weight: 600; padding: 3px 10px; border-radius: 20px; margin-bottom: 16px; }
</style>
</head>
<body>
<div class="card">
  <div class="icon">⚠️</div>
  <span class="badge">SECURITY SIMULATION</span>
  <h1>You clicked a simulated phishing link</h1>
  <p>This was part of a <strong>controlled security awareness exercise</strong>
     authorized by your organization. No real credentials were captured or
     transmitted outside this network.</p>
  <p>The purpose of this exercise is to help you recognize phishing attempts
     before they happen in the real world.</p>
  <div class="tips">
    <h2>What to watch for next time</h2>
    <ul>
      <li>Check the URL bar — does it match the real domain exactly?</li>
      <li>Look for HTTPS and a valid certificate</li>
      <li>Hover over links before clicking to preview the destination</li>
      <li>Unexpected login prompts are a red flag — verify via another channel</li>
      <li>When in doubt, report to your security team</li>
    </ul>
  </div>
</div>
</body>
</html>
"""


def run_server(page_path: str, port: int = 8080, log_file: str = "captures.log"):
    app = Flask(__name__)

    # ------------------------------------------------------------------ #
    #  Routes                                                              #
    # ------------------------------------------------------------------ #

    @app.route("/")
    def index():
        return send_file(page_path)

    @app.route("/capture", methods=["POST"])
    def capture():
        """
        Receives form data (JSON) from the injected JS interceptor.
        Logs timestamp + IP + submitted fields to captures.log.
        Returns a redirect URL to the awareness page.
        """
        data = request.get_json(silent=True) or request.form.to_dict()

        # Sanitize: strip empty fields and very long values (anti-garbage)
        cleaned = {
            k: v[:200]
            for k, v in data.items()
            if v and k not in ("", "_")
        }

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", ""),
            "fields": cleaned,
        }

        # Append to log (one JSON object per line = easy to parse)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        # Print to console for the operator
        print(f"  [CAPTURE] {entry['timestamp']}  IP={entry['ip']}")
        for k, v in cleaned.items():
            print(f"            {k}: {v}")
        print()

        return jsonify({"status": "ok", "redirect": "/awareness"})

    @app.route("/awareness")
    def awareness():
        return render_template_string(AWARENESS_PAGE)

    # ------------------------------------------------------------------ #
    #  Run                                                                 #
    # ------------------------------------------------------------------ #
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
