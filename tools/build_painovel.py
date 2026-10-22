#!/usr/bin/env python3
"""Build or verify deterministic PaiNovel pages without touching legacy apps."""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "apps" / "painovel"
SITE = ROOT / "dist" / "painovel"

CSS = """:root{color-scheme:dark;--bg:#0f131d;--panel:#171b26;--text:#f2e7d7;--muted:#b8afa4;--accent:#ffc174;--line:#2b303d}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.75 Inter,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}header,main,footer{width:min(860px,calc(100% - 32px));margin:auto}header{padding:28px 0 18px;display:flex;gap:18px;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line)}.brand{font-size:20px;font-weight:800;color:var(--accent);text-decoration:none}.nav{display:flex;gap:14px;flex-wrap:wrap}.nav a{color:var(--muted)}main{padding:44px 0 64px}h1{font-size:clamp(32px,6vw,50px);line-height:1.12;margin:0 0 10px}.meta,.lead{color:var(--muted)}.lead{font-size:18px;margin:24px 0 38px}section{padding:20px 0;border-top:1px solid var(--line)}h2{font-size:22px}a{color:var(--accent)}footer{padding:22px 0 40px;color:var(--muted);border-top:1px solid var(--line)}@media(max-width:620px){header{align-items:flex-start;flex-direction:column}main{padding-top:30px}}"""

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def expand(value: str, common: dict) -> str:
    for key in ("app_name", "operator", "contact_email", "effective_date"):
        value = value.replace("{{" + key + "}}", str(common[key]))
    return value

def page(common: dict, locale: str, data: dict, kind: str) -> str:
    doc = data[kind]
    zh = locale == "zh-CN"
    effective = "生效日期" if zh else "Effective date"
    language = "语言" if zh else "Language"
    other = "en" if zh else "zh-CN"
    other_label = "English" if zh else "简体中文"
    privacy = "隐私政策" if zh else "Privacy"
    terms = "用户协议" if zh else "Terms"
    sections = "\n".join(
        f'<section><h2>{html.escape(expand(s["heading"], common))}</h2>'
        + "".join(f'<p>{html.escape(expand(p, common))}</p>' for p in s["paragraphs"])
        + "</section>" for s in doc["sections"]
    )
    return f'''<!doctype html>
<html lang="{locale}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(doc["title"])}</title><meta name="description" content="{html.escape(doc["intro"])}"><link rel="stylesheet" href="../assets/legal.css"></head>
<body><header><a class="brand" href="../index.html">{html.escape(common["app_name"])}</a><nav class="nav"><a href="privacy.html">{privacy}</a><a href="terms.html">{terms}</a><a hreflang="{other}" href="../{other}/{kind}.html">{other_label}</a></nav></header><main><h1>{html.escape(doc["title"])}</h1><div class="meta">{effective}: <time datetime="{common["effective_date"]}">{common["effective_date"]}</time> · {language}: {html.escape(data["language_name"])}</div><p class="lead">{html.escape(expand(doc["intro"], common))}</p>{sections}</main><footer>© {common["effective_date"][:4]} {html.escape(common["operator"])} · <a href="mailto:{html.escape(common["contact_email"])}">{html.escape(common["contact_email"])}</a></footer></body></html>
'''

def index(common: dict) -> str:
    links = "".join(f'<section><h2>{loc}</h2><p><a href="{loc}/privacy.html">Privacy / 隐私政策</a> · <a href="{loc}/terms.html">Terms / 用户协议</a></p></section>' for loc in common["languages"])
    return f'''<!doctype html><html lang="{common["default_language"]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(common["app_name"])} Legal</title><link rel="stylesheet" href="assets/legal.css"></head><body><header><span class="brand">{html.escape(common["app_name"])}</span></header><main><h1>Legal / 法律文件</h1><p class="lead">Effective / 生效日期: <time datetime="{common["effective_date"]}">{common["effective_date"]}</time></p>{links}</main></body></html>\n'''

def expected_files() -> dict[Path, str]:
    common = load_json(CONTENT / "legal.json")
    if not common.get("effective_date"):
        raise ValueError("content/legal.json: effective_date is required")
    outputs = {SITE / "assets/legal.css": CSS + "\n", SITE / "index.html": index(common)}
    for locale in common["languages"]:
        source = CONTENT / "legal" / f"{locale}.json"
        if not source.is_file():
            raise ValueError(f"missing language source: {source}")
        data = load_json(source)
        for kind in common["documents"]:
            if kind not in data:
                raise ValueError(f"{source}: missing {kind}")
            outputs[SITE / locale / f"{kind}.html"] = page(common, locale, data, kind)
    return outputs

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated output differs from sources")
    parser.add_argument("--ready", action="store_true", help="fail if publication metadata is incomplete")
    args = parser.parse_args()
    try:
        outputs = expected_files()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"legal build error: {exc}", file=sys.stderr)
        return 1
    common = load_json(CONTENT / "legal.json")
    if args.ready and ("待确认" in common["operator"] or "待确认" in common["contact_email"] or ".example" in common["contact_email"]):
        print("PaiNovel publication metadata is incomplete", file=sys.stderr)
        return 2
    if args.check:
        mismatches = [str(path.relative_to(ROOT)) for path, body in outputs.items() if not path.is_file() or path.read_text(encoding="utf-8") != body]
        extras = [str(path.relative_to(ROOT)) for path in SITE.rglob("*.html") if path not in outputs] if SITE.exists() else []
        if mismatches or extras:
            print("generated legal site is stale or incomplete:", *(f"- {p}" for p in mismatches + extras), sep="\n", file=sys.stderr)
            return 1
        print(f"legal site is current ({len(outputs)} files)")
        return 0
    for path, body in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    print(f"generated {len(outputs)} files in {SITE}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
