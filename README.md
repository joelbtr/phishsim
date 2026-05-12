# PhishSim

A local phishing simulation toolkit for **authorized security awareness testing**.

> ⚠️ **Authorized use only.** Running this tool against any system or individual
> without explicit written authorization is illegal under the Computer Fraud and
> Abuse Act (CFAA), the UK Computer Misuse Act, and equivalent laws in most
> jurisdictions. This tool is designed for internal awareness training and CTF
> environments.

---

## Features

- **Page cloner** — fetches a target login page and rewrites forms to capture locally
- **Capture server** — Flask server that logs submitted credentials to a local file
- **Awareness redirect** — victim is immediately shown an educational notice after submitting
- **HTML report** — campaign report showing capture count, unique IPs, timeline
- **Simulation watermark** — always visible "SIMULATION ONLY" badge on cloned pages

---

## Installation

```bash
git clone https://github.com/joelbtr/phishsim
cd phishsim
pip install flask requests beautifulsoup4
```

---

## Usage

### 1. Clone a page

```bash
# If using the docker image vulnerables/web-dvwa
python phishsim.py clone http://localhost/login.php --output test.html
```

### 2. Serve it

```bash
python phishsim.py serve --page my_page.html --port 8080
```

Capture log is written to `captures.log` (one JSON entry per line).

### 3. Generate the report

```bash
python phishsim.py report --log captures.log --campaign "Q1 Awareness Test" -o report.html
```

Open `report.html` in a browser.

---

## How it works

```
Target URL
    │
    ▼ clone
cloned_page.html  (forms rewritten, JS intercept injected)
    │
    ▼ serve
Flask server  :8080
    │
    ├─ GET /          → serves cloned page
    ├─ POST /capture  → logs data to captures.log
    └─ GET /awareness → shows educational notice
```

The JS intercept in the cloned page catches form submissions before they reach
the server, POSTs them as JSON to `/capture`, then redirects the user to the
awareness page. No data leaves `localhost` / LAN.

---

## Detection guide

This section documents how a defender or SOC analyst would detect a simulation
(or a real phish) like this one. Understanding detection is as important as
understanding the attack.

### 1. URL / domain indicators

| Indicator                                   | How to detect                                  |
| ------------------------------------------- | ---------------------------------------------- |
| Domain doesn't match the legitimate service | Hover before clicking; check URL bar           |
| Recently registered domain                  | `whois` lookup; WHOIS age check                |
| HTTP instead of HTTPS                       | Browser warning; padlock missing               |
| Mismatched TLS certificate (wrong CN/SAN)   | Browser certificate viewer; `openssl s_client` |
| Lookalike domain (paypa1.com vs paypal.com) | Punycode rendering; IDN homograph check        |

### 2. Network-level detection

```bash
# See all HTTP traffic to/from the simulation server
tcpdump -i lo port 8080 -A

# Check for unexpected POST requests to non-standard ports
wireshark # filter: http.request.method == "POST"

# Suricata rule to detect credential POST to non-HTTPS endpoint
alert http any any -> any any (
    msg:"Possible credential capture - plaintext POST";
    http.method; content:"POST";
    http.request_body; content:"password";
    nocase; sid:9000001; rev:1;
)
```

### 3. Email-level detection (if sim includes phish email)

- SPF/DKIM/DMARC failures — check `Received` headers
- Mismatched `Reply-To` and `From`
- Generic greeting ("Dear User") + urgency language
- Link preview mismatch (`href` vs displayed text)

Tools: `mxtoolbox.com`, `mail-tester.com`, `spamassassin`

### 4. Endpoint / browser indicators

- Unexpected `fetch()` / XHR to `localhost` or non-standard ports
- Hidden `<div>` with "SIMULATION" text (visible in DevTools)
- Form `action` attribute pointing to `/capture` instead of a real endpoint
- `document.addEventListener('submit')` override in page source

```javascript
// In browser console, detect if form has been hijacked:
document.querySelectorAll("form").forEach(
  (f) => console.log(f.action, getEventListeners(f)), // Chrome DevTools only
);
```

### 5. Log analysis patterns

If you were defending the server being cloned, you'd see:

```
# Unusual GET spike on login page from same IP (recon/cloning)
grep "GET /login" access.log | awk '{print $1}' | sort | uniq -c | sort -rn

# User-agent used during clone step
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ...
```

---

## Project structure

```
phishsim/
├── phishsim.py     # CLI entry point
├── cloner.py       # Page fetching and rewriting
├── server.py       # Flask capture server
├── reporter.py     # HTML report generator
├── captures.log    # Runtime: capture log (gitignored)
└── README.md
```

---

## Ethics & responsible use

This tool was built as a portfolio project demonstrating social engineering
simulation techniques. Key design decisions that make it responsible:

1. **No external exfiltration** — all captures stay on `localhost`/LAN
2. **Mandatory authorization check** — CLI refuses to proceed without explicit confirmation
3. **Immediate awareness redirect** — victim is educated, not left confused
4. **Simulation watermark** — cloned pages are always visually marked
5. **No evasion** — no anti-sandbox, no email delivery, no URL shorteners

For production awareness testing, consider dedicated platforms (GoPhish, KnowBe4,
Proofpoint Security Awareness) which include consent management, metrics, and legal
scaffolding out of the box.

---

## License

MIT. Use responsibly.
