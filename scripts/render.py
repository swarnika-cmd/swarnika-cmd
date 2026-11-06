#!/usr/bin/env python3
"""Render the SVG cards for my GitHub profile README.

Three cards, all built from real data:

  assets/terminal.svg  an animated terminal replaying a real `curl -i` against my
                       HTTP/1.1 server (CI compiles and starts the server first)
  assets/bench.svg     benchmark numbers read from the committed results in each
                       project repo (bench/results/)
  assets/oss.svg       my merged pull requests, from the GitHub search API

Standard library only, so the workflow needs no pip install.

    python scripts/render.py --response response.txt --out assets
"""
import argparse
import csv
import io
import json
import os
import statistics
import urllib.request
from datetime import datetime, timezone
from html import escape

USER = "swarnika-cmd"
RAW = "https://raw.githubusercontent.com/" + USER

# Merged PRs in these repos are left off the open-source card: they are small
# content additions, not code.
EXCLUDE_REPOS = {"lingdojo/kana-dojo"}

FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

# GitHub dark palette
BG, PANEL, BORDER = "#0d1117", "#161b22", "#30363d"
TEXT, DIM = "#e6edf3", "#7d8590"
GREEN, BLUE, PURPLE, ORANGE, TEAL, RED = "#7ee787", "#79c0ff", "#d2a8ff", "#ffa657", "#56d4dd", "#ff7b72"


# ---------------------------------------------------------------- helpers

def fetch(url, token=None):
    req = urllib.request.Request(url, headers={"User-Agent": USER + "-profile-renderer"})
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def fetch_json(url, token=None):
    return json.loads(fetch(url, token))


def write(path, svg):
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", path)


def fmt_int(n):
    return "{:,}".format(int(round(n)))


def fmt_k(n):
    return "{:.0f}K".format(n / 1000) if n >= 10000 else fmt_int(n)


# ---------------------------------------------------------------- terminal

def json_spans(text):
    """Colour a pretty-printed JSON line: keys, strings, numbers, punctuation."""
    out, i = [], 0
    while i < len(text):
        ch = text[i]
        if ch == '"':
            j = text.index('"', i + 1)
            token = text[i:j + 1]
            is_key = text[j + 1:j + 2] == ":"
            out.append((token, BLUE if is_key else "#a5d6ff"))
            i = j + 1
        elif ch.isdigit() or ch == "-":
            j = i
            while j < len(text) and (text[j].isdigit() or text[j] in ".-"):
                j += 1
            out.append((text[i:j], ORANGE))
            i = j
        else:
            out.append((ch, TEXT if ch.strip() else TEXT))
            i += 1
    return out


def terminal_lines(response, command):
    head, _, body = response.replace("\r\n", "\n").partition("\n\n")
    lines = [[("swarnika@bengaluru", GREEN), (":", TEXT), ("~", BLUE), ("$ ", TEXT), (command, TEXT)]]
    for n, line in enumerate(head.split("\n")):
        if n == 0:
            lines.append([(line, GREEN if " 2" in line[:13] else RED)])
        elif line.lower().startswith("date:"):
            continue  # the date changes every run; keep the card stable
        else:
            name, _, value = line.partition(":")
            lines.append([(name, PURPLE), (":", DIM), (value, TEXT)])
    lines.append([])
    body = body.strip()
    try:
        pretty = json.dumps(json.loads(body), indent=2, ensure_ascii=False)
    except ValueError:
        pretty = body
    for line in pretty.split("\n"):
        lines.append(json_spans(line))
    lines.append([("swarnika@bengaluru", GREEN), (":", TEXT), ("~", BLUE), ("$ ", TEXT)])
    return lines


def render_terminal(response, command):
    lines = terminal_lines(response, command)
    width, line_h, top, left = 860, 21, 64, 24
    height = top + line_h * (len(lines) - 1) + 28
    cmd_chars = len(command)
    type_dur = round(cmd_chars * 0.045, 2)
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
        'aria-label="Terminal: curl -i against my HTTP/1.1 server">'.format(w=width, h=height),
        "<style>text{{font-family:{f};font-size:14px;white-space:pre}}"
        ".t{{font-family:{s};font-size:12px}}</style>".format(f=FONT, s=SANS),
        '<rect x="0.5" y="0.5" width="{}" height="{}" rx="12" fill="{}" stroke="{}"/>'.format(width - 1, height - 1, BG, BORDER),
        '<path d="M0.5 36 H{} M12.5 0.5" stroke="{}"/>'.format(width - 0.5, BORDER),
        '<rect x="0.5" y="0.5" width="{}" height="35" rx="12" fill="{}"/>'.format(width - 1, PANEL),
        '<rect x="0.5" y="24" width="{}" height="12" fill="{}"/>'.format(width - 1, PANEL),
    ]
    for k, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        out.append('<circle cx="{}" cy="18" r="6" fill="{}"/>'.format(22 + k * 20, c))
    out.append('<text class="t" x="{}" y="22" fill="{}" text-anchor="middle">'
               "live response from HTTP-1.1-Server · rebuilt by CI</text>".format(width // 2, DIM))

    # line 0: prompt, then the command typed out with a clip that grows
    y0 = top
    prompt = lines[0][:-1]
    out.append('<text x="{}" y="{}">{}</text>'.format(
        left, y0, "".join('<tspan fill="{}">{}</tspan>'.format(c, escape(t)) for t, c in prompt)))
    prompt_w = sum(len(t) for t, _ in prompt) * 8.43
    out.append('<clipPath id="type"><rect x="{}" y="{}" width="0" height="{}">'
               '<animate attributeName="width" from="0" to="{}" dur="{}s" begin="0.4s" fill="freeze" '
               'calcMode="discrete" values="{}"/></rect></clipPath>'.format(
                   left + prompt_w, y0 - 15, line_h,
                   cmd_chars * 8.43 + 2, type_dur,
                   ";".join("{:.1f}".format(i * 8.43) for i in range(cmd_chars + 1))))
    out.append('<text x="{}" y="{}" fill="{}" clip-path="url(#type)">{}</text>'.format(
        left + prompt_w, y0, TEXT, escape(command)))

    # remaining lines appear one after another, like a streamed response
    start = 0.4 + type_dur + 0.35
    for n, spans in enumerate(lines[1:], start=1):
        y = top + n * line_h
        begin = start + (n - 1) * 0.07
        inner = "".join('<tspan fill="{}">{}</tspan>'.format(c, escape(t)) for t, c in spans)
        out.append('<text x="{}" y="{}" opacity="0">{}<animate attributeName="opacity" from="0" to="1" '
                   'begin="{:.2f}s" dur="0.15s" fill="freeze"/></text>'.format(left, y, inner, begin))
    # blinking cursor after the final prompt
    last_y = top + (len(lines) - 1) * line_h
    cur_x = left + sum(len(t) for t, _ in lines[-1]) * 8.43
    end = start + (len(lines) - 2) * 0.07 + 0.2
    out.append('<rect x="{:.1f}" y="{}" width="8.5" height="16" fill="{}" opacity="0">'
               '<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.01;0.5;0.51" dur="1.1s" '
               'begin="{:.2f}s" repeatCount="indefinite"/></rect>'.format(cur_x, last_y - 13, TEXT, end))
    out.append("</svg>")
    return "\n".join(out)


# ---------------------------------------------------------------- benchmarks

def load_bench():
    http_rows = list(csv.DictReader(io.StringIO(fetch(RAW + "/HTTP-1.1-Server/master/bench/results/results.csv"))))

    def med(mode, field):
        vals = [float(r[field]) for r in http_rows
                if r["mode"] == mode and r["keepalive"] == "on" and r["connections"] == "100"]
        return statistics.median(vals)

    trie = fetch_json(RAW + "/SearchTypeahead/master/bench/results/trie-bench-full.json")
    load = fetch_json(RAW + "/SearchTypeahead/master/bench/results/load-full.json")
    big = max(trie["results"], key=lambda r: r["terms"])
    sw_rows = []
    for sweep in ("sweep-50-200", "sweep-100-150"):
        data = fetch_json(RAW + "/ShieldWall-Gateway/main/bench/results/{}/k6-summary.json".format(sweep))
        sw_rows += [r for r in data["rows"] if r["gateway_error_rate"] == 0]
    sw_rows.sort(key=lambda r: r["rate_rps"])
    return {
        "http": {
            "platform_rps": med("platform", "req_per_sec"), "platform_p99": med("platform", "p99_ms"),
            "virtual_rps": med("virtual", "req_per_sec"), "virtual_p99": med("virtual", "p99_ms"),
        },
        "trie": {"terms": big["terms"], "p99_us": big["latencyUs"]["p99"], "heap_mb": big["heapMB"],
                 "rps": load["requestsPerSec"], "api_p99": load["latencyMs"]["p99"]},
        "gateway": [(r["rate_rps"], r["overhead_p50_ms"], r["overhead_p99_ms"]) for r in sw_rows],
    }


def card(x, y, w, h, title, sub, link_hint):
    return [
        '<rect x="{}" y="{}" width="{}" height="{}" rx="10" fill="{}" stroke="{}"/>'.format(x, y, w, h, PANEL, BORDER),
        '<text x="{}" y="{}" fill="{}" class="h">{}</text>'.format(x + 18, y + 30, TEXT, escape(title)),
        '<text x="{}" y="{}" fill="{}" class="s">{}</text>'.format(x + 18, y + 48, DIM, escape(sub)),
        '<text x="{}" y="{}" fill="{}" class="s">{}</text>'.format(x + 18, y + h - 14, DIM, escape(link_hint)),
    ]


def bar(x, y, max_w, value, max_value, color, label, value_text, delay):
    w = max(3.0, max_w * value / max_value)
    return [
        '<text x="{}" y="{}" fill="{}" class="s">{}</text>'.format(x, y - 6, DIM, escape(label)),
        '<rect x="{}" y="{}" width="0" height="12" rx="3" fill="{}">'
        '<animate attributeName="width" from="0" to="{:.1f}" dur="0.9s" begin="{}s" fill="freeze"/></rect>'.format(
            x, y, color, w, delay),
        '<text x="{:.1f}" y="{}" fill="{}" class="v">{}</text>'.format(x + w + 8, y + 11, TEXT, escape(value_text)),
    ]


def render_bench(b):
    width, height = 860, 250
    cw, gap, top = 270, 15, 10
    xs = [10, 10 + cw + gap, 10 + 2 * (cw + gap)]
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
        'aria-label="Benchmark results from my projects">'.format(w=width, h=height),
        "<style>.h{{font:600 15px {s}}}.s{{font:12px {s}}}.v{{font:600 12px {f}}}.big{{font:700 26px {s}}}</style>".format(
            s=SANS, f=FONT),
    ]
    ch = height - 20

    # HTTP server: p99 bars, platform pool vs virtual threads
    h = b["http"]
    out += card(xs[0], top, cw, ch, "HTTP/1.1 Server", "Java 21 · wrk · 100 conns",
                "results.csv · median of 3 runs")
    out.append('<text x="{}" y="{}" fill="{}" class="big">{}</text>'.format(xs[0] + 18, top + 88, TEAL, fmt_k(h["platform_rps"]) + " req/s"))
    out.append('<text x="{}" y="{}" fill="{}" class="s">peak, 64-thread pool</text>'.format(xs[0] + 18, top + 106, DIM))
    mx = max(h["platform_p99"], h["virtual_p99"])
    out += bar(xs[0] + 18, top + 136, 150, h["platform_p99"], mx, ORANGE, "p99 · platform pool", "{:.1f} ms".format(h["platform_p99"]), 0.3)
    out += bar(xs[0] + 18, top + 176, 150, h["virtual_p99"], mx, GREEN, "p99 · virtual threads", "{:.1f} ms".format(h["virtual_p99"]), 0.5)

    # Typeahead
    t = b["trie"]
    out += card(xs[1], top, cw, ch, "Search Typeahead", "TypeScript · trie + top-K",
                "trie-bench + load-full.json")
    out.append('<text x="{}" y="{}" fill="{}" class="big">{} µs</text>'.format(xs[1] + 18, top + 88, TEAL, ("%g" % round(t["p99_us"], 1))))
    out.append('<text x="{}" y="{}" fill="{}" class="s">p99 lookup · {}M terms</text>'.format(xs[1] + 18, top + 106, DIM, t["terms"] // 1000000))
    out.append('<text x="{}" y="{}" fill="{}" class="big">{} req/s</text>'.format(xs[1] + 18, top + 152, BLUE, fmt_k(t["rps"])))
    out.append('<text x="{}" y="{}" fill="{}" class="s">API under k6 · p99 {:.1f} ms</text>'.format(xs[1] + 18, top + 170, DIM, t["api_p99"]))
    out.append('<text x="{}" y="{}" fill="{}" class="s">cost: {:.1f} GB heap at 1M</text>'.format(xs[1] + 18, top + 192, ORANGE, t["heap_mb"] / 1000))

    # Gateway: overhead p99 per request rate
    g = b["gateway"]
    out += card(xs[2], top, cw, ch, "ShieldWall Gateway", "FastAPI · added latency (k6)",
                "sweep-*/k6-summary.json")
    best = max(g, key=lambda r: r[0])
    out.append('<text x="{}" y="{}" fill="{}" class="big">+{:.1f} ms</text>'.format(xs[2] + 18, top + 88, TEAL, best[1]))
    out.append('<text x="{}" y="{}" fill="{}" class="s">p50 at {} req/s, 1 worker</text>'.format(xs[2] + 18, top + 106, DIM, best[0]))
    mx = max(r[2] for r in g)
    for k, (rate, _p50, p99) in enumerate(g[-3:]):
        y = top + 128 + k * 24
        out.append('<text x="{}" y="{}" fill="{}" class="s">{} rps</text>'.format(xs[2] + 18, y + 10, DIM, rate))
        out.append('<rect x="{}" y="{}" width="0" height="11" rx="3" fill="{}">'
                   '<animate attributeName="width" from="0" to="{:.1f}" dur="0.9s" begin="{}s" fill="freeze"/></rect>'.format(
                       xs[2] + 78, y, PURPLE, max(3.0, 90 * p99 / mx), 0.3 + 0.2 * k))
        out.append('<text x="{}" y="{}" fill="{}" class="v">p99 +{:.1f} ms</text>'.format(xs[2] + 176, y + 10, TEXT, p99))
    out.append("</svg>")
    return "\n".join(out)


# ---------------------------------------------------------------- open source

def load_prs(token=None):
    q = "is:pr+author:{}+is:merged".format(USER)
    data = fetch_json("https://api.github.com/search/issues?q={}&per_page=100&sort=updated".format(q), token)
    prs = []
    for item in data.get("items", []):
        repo = item["repository_url"].split("/repos/")[1]
        if repo in EXCLUDE_REPOS:
            continue
        merged = item.get("pull_request", {}).get("merged_at") or item["closed_at"]
        prs.append({"repo": repo, "number": item["number"], "title": item["title"], "merged": merged[:10]})
    prs.sort(key=lambda p: p["merged"], reverse=True)
    return prs


def render_oss(prs):
    width, row_h, top = 860, 30, 78
    height = top + row_h * len(prs) + 34
    repos = sorted({p["repo"] for p in prs})
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
        'aria-label="My merged pull requests">'.format(w=width, h=height),
        "<style>.h{{font:600 16px {s}}}.s{{font:12px {s}}}.r{{font:12px {f}}}.n{{font:600 12px {f}}}</style>".format(s=SANS, f=FONT),
        '<rect x="0.5" y="0.5" width="{}" height="{}" rx="12" fill="{}" stroke="{}"/>'.format(width - 1, height - 1, PANEL, BORDER),
        '<text x="24" y="34" fill="{}" class="h">git log --merged</text>'.format(TEXT),
        '<text x="24" y="54" fill="{}" class="s">{} merged pull requests across {} repositories · refreshed by CI from the GitHub API</text>'.format(
            DIM, len(prs), len(repos)),
    ]
    for k, p in enumerate(prs):
        y = top + k * row_h
        owner, name = p["repo"].split("/")
        title = p["title"] if len(p["title"]) <= 40 else p["title"][:38] + "…"
        out.append('<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{:.2f}s" dur="0.3s" fill="freeze"/>'.format(0.2 + k * 0.08))
        out.append('<circle cx="30" cy="{}" r="5" fill="#8957e5"/>'.format(y + 8))
        if k < len(prs) - 1:
            out.append('<path d="M30 {} V{}" stroke="{}" stroke-width="2"/>'.format(y + 14, y + row_h + 2, BORDER))
        out.append('<text x="48" y="{}" fill="{}" class="r">{}</text>'.format(y + 13, ORANGE, p["merged"]))
        out.append('<text x="140" y="{}" class="r"><tspan fill="{}">{}/</tspan><tspan fill="{}">{}</tspan>'
                   '<tspan fill="{}" class="n"> #{}</tspan></text>'.format(y + 13, DIM, escape(owner), BLUE, escape(name), GREEN, p["number"]))
        out.append('<text x="545" y="{}" fill="{}" class="r">{}</text>'.format(y + 13, TEXT, escape(title)))
        out.append("</g>")
    out.append("</svg>")
    return "\n".join(out)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--response", help="raw `curl -i` output from the HTTP server")
    ap.add_argument("--command", default="curl -i localhost:8080/swarnika.txt")
    ap.add_argument("--out", default="assets")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    token = os.environ.get("GITHUB_TOKEN")

    if args.response:
        with open(args.response, encoding="utf-8") as f:
            write(os.path.join(args.out, "terminal.svg"), render_terminal(f.read(), args.command))
    write(os.path.join(args.out, "bench.svg"), render_bench(load_bench()))
    write(os.path.join(args.out, "oss.svg"), render_oss(load_prs(token)))
    print("rendered at", datetime.now(timezone.utc).isoformat(timespec="seconds"))


if __name__ == "__main__":
    main()
