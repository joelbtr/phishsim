#!/usr/bin/env python3
"""
phishsim.py — Ethical Phishing Simulation Tool
For authorized security awareness testing ONLY.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

BANNER = """
╔══════════════════════════════════════════════════════╗
║           PhishSim — Awareness Testing Tool          ║
║  FOR AUTHORIZED USE ONLY. Misuse is illegal.         ║
╚══════════════════════════════════════════════════════╝
"""

def check_deps():
    """Ensure required packages are installed."""
    missing = []
    for pkg in ["flask", "requests", "bs4"]:
        try:
            __import__(pkg if pkg != "bs4" else "bs4")
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[!] Missing packages: {', '.join(missing)}")
        print(f"    Run: pip install {' '.join(missing)}")
        sys.exit(1)

def confirm_authorization():
    """Require explicit confirmation before proceeding."""
    print("\n[LEGAL CHECK] You must confirm before continuing:")
    print("  1. You have written authorization from the target org/individual.")
    print("  2. This test is being conducted in a controlled environment.")
    print("  3. No real credentials will be transmitted outside localhost/LAN.\n")
    answer = input("Type 'I CONFIRM' to proceed: ").strip()
    if answer != "I CONFIRM":
        print("[-] Aborted. Authorization not confirmed.")
        sys.exit(0)

def cmd_clone(args):
    """Clone a login page for simulation."""
    from cloner import clone_page
    print(f"[*] Cloning: {args.url}")
    output = args.output or "cloned_page.html"
    clone_page(args.url, output, redirect_url=args.redirect)
    print(f"[+] Saved to: {output}")

def cmd_serve(args):
    """Start the capture server."""
    from server import run_server
    page = args.page or "cloned_page.html"
    if not Path(page).exists():
        print(f"[!] Page not found: {page}")
        sys.exit(1)
    print(f"[*] Serving '{page}' on http://0.0.0.0:{args.port}")
    print(f"[*] Captures logged to: captures.log")
    print(f"[*] Press Ctrl+C to stop.\n")
    run_server(page, port=args.port, log_file=args.log)

def cmd_report(args):
    """Generate an HTML awareness report from the capture log."""
    from reporter import generate_report
    if not Path(args.log).exists():
        print(f"[!] Log file not found: {args.log}")
        sys.exit(1)
    output = args.output or "report.html"
    count = generate_report(args.log, output, campaign=args.campaign)
    print(f"[+] Report generated: {output}")
    print(f"[+] Total captures logged: {count}")

def main():
    print(BANNER)
    check_deps()

    parser = argparse.ArgumentParser(
        description="PhishSim — Ethical phishing simulation for awareness testing"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # clone subcommand
    p_clone = sub.add_parser("clone", help="Clone a login page")
    p_clone.add_argument("url", help="Target URL to clone")
    p_clone.add_argument("-o", "--output", help="Output HTML file (default: cloned_page.html)")
    p_clone.add_argument("-r", "--redirect", default="https://example.com/awareness",
                         help="URL to redirect victim to after capture")

    # serve subcommand
    p_serve = sub.add_parser("serve", help="Start the phishing capture server")
    p_serve.add_argument("-p", "--page", help="HTML page to serve (default: cloned_page.html)")
    p_serve.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    p_serve.add_argument("--log", default="captures.log", help="Log file path")

    # report subcommand
    p_report = sub.add_parser("report", help="Generate awareness report from captures")
    p_report.add_argument("--log", default="captures.log", help="Capture log file")
    p_report.add_argument("-o", "--output", help="Output HTML report (default: report.html)")
    p_report.add_argument("--campaign", default="Phishing Awareness Test",
                          help="Campaign name for the report")

    args = parser.parse_args()

    # Always confirm authorization first
    confirm_authorization()

    dispatch = {
        "clone": cmd_clone,
        "serve": cmd_serve,
        "report": cmd_report,
    }
    dispatch[args.command](args)

if __name__ == "__main__":
    main()
