#!/usr/bin/env python3
"""Build (or verify) the static 2048Pai legal site from JSON sources."""
from __future__ import annotations

import argparse
import html
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
DIST = ROOT / "dist"


def load(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def page(common, local, doc_key: str) -> str:
    doc = local["documents"][doc_key]
    title = f'{doc["title"]} | {common["appName"]}'
    language_links = " ".join(
        f'<a href="../../{code}/{doc_key}/">{esc(code)}</a>'
        for code in common["locales"]
    )
    doc_links = " ".join(
        f'<a href="../{kind}/">{esc(local["documents"][kind]["title"])}</a>'
        for kind in common["documents"]
    )
    warning = ""
    if common.get("draft"):
        warning = '<p class="notice">DRAFT — publication is blocked until the publisher and public contact are completed.</p>'
    sections = "".join(
        "<section><h2>{}</h2>{}</section>".format(
            esc(section["heading"]),
            "".join(f'<p>{esc(paragraph)}</p>' for paragraph in section["paragraphs"]),
        )
        for section in doc["sections"]
    )
    return f"""<!doctype html>
<html lang="{esc(local['locale'])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(doc['summary'])}">
  <title>{esc(title)}</title>
  <style>
    :root {{ color-scheme: light; --ink:#28231f; --accent:#b65a31; --paper:#fffaf3; --line:#ead8c7; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--paper); color:var(--ink); font:16px/1.65 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    header,main,footer {{ max-width:820px; margin:auto; padding-inline:24px; }} header {{ padding-top:42px; border-bottom:1px solid var(--line); }}
    .brand {{ color:var(--accent); font-weight:800; letter-spacing:.02em; }} nav {{ display:flex; flex-wrap:wrap; gap:12px; padding:18px 0; }} a {{ color:var(--accent); }}
    main {{ padding-block:38px 24px; }} h1 {{ font-size:clamp(2rem,5vw,3rem); line-height:1.12; margin:0 0 12px; }} h2 {{ margin:32px 0 8px; font-size:1.35rem; }}
    p {{ margin:8px 0; }} .summary {{ color:#5d5148; font-size:1.08rem; }} .notice {{ background:#fff0d9; border-left:4px solid #c77714; padding:10px 14px; }}
    .meta {{ border-top:1px solid var(--line); margin-top:36px; padding-top:18px; }} footer {{ color:#6f6258; font-size:.9rem; padding-bottom:34px; }}
  </style>
</head>
<body>
  <header>
    <div class="brand">{esc(common['appName'])}</div>
    <nav aria-label="Document navigation">{doc_links}</nav>
    <nav aria-label="Language navigation">{language_links}</nav>
  </header>
  <main>
    {warning}
    <h1>{esc(doc['title'])}</h1>
    <p class="summary">{esc(doc['summary'])}</p>
    {sections}
    <div class="meta"><p><strong>Effective date:</strong> {esc(common['effectiveDate'])}</p><p><strong>Publisher:</strong> {esc(common['publisherName'])}</p><p><strong>Public contact:</strong> {esc(common['publicContact'])}</p></div>
  </main>
  <footer>{esc(common['appName'])} · {esc(local['languageName'])}</footer>
</body>
</html>
"""


def build(target: Path) -> None:
    common = load(CONTENT / "legal.json")
    for code in common["locales"]:
        local = load(CONTENT / "legal" / f"{code}.json")
        for doc_key in common["documents"]:
            output = target / code / doc_key / "index.html"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(page(common, local, doc_key), encoding="utf-8")


def compare(expected: Path, actual: Path) -> bool:
    expected_files = {p.relative_to(expected) for p in expected.rglob("*") if p.is_file()}
    actual_files = {p.relative_to(actual) for p in actual.rglob("*") if p.is_file()} if actual.exists() else set()
    if expected_files != actual_files:
        print("Generated file set differs.", file=sys.stderr)
        print("Missing:", sorted(map(str, expected_files - actual_files)), file=sys.stderr)
        print("Unexpected:", sorted(map(str, actual_files - expected_files)), file=sys.stderr)
        return False
    stale = [str(path) for path in sorted(expected_files) if (expected / path).read_bytes() != (actual / path).read_bytes()]
    if stale:
        print("Generated files are stale:", *stale, sep="\n", file=sys.stderr)
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify dist matches JSON sources without writing")
    parser.add_argument("--ready", action="store_true", help="fail if the site is still a publication draft")
    args = parser.parse_args()
    common = load(CONTENT / "legal.json")
    if args.ready and (common.get("draft") or "须填写" in common["publisherName"] or "须填写" in common["publicContact"]):
        print("Publication is blocked: set publisherName, publicContact, and draft=false in content/legal.json.", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory() as temp:
        generated = Path(temp)
        build(generated)
        if args.check:
            return 0 if compare(generated, DIST) else 1
        if DIST.exists():
            shutil.rmtree(DIST)
        shutil.copytree(generated, DIST)
    print(f"Built {DIST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
