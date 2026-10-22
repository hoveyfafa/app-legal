# App legal sites

`content/legal.json` is the single source for the app name, shared effective date, publisher, public contact, and enabled languages. Per-language documents are in `content/legal/<language>.json`. Generated files in `dist/` are version-controlled deployment artifacts.

```sh
python3 tools/build_site.py
python3 tools/build_site.py --check
python3 tools/build_site.py --ready --check
```

`--check` only verifies that generated HTML matches the JSON sources. `--ready` additionally prevents publication while the source has draft contact details. Before publication, replace the draft publisher/contact, set `draft` to `false`, rebuild, and commit both `content/` and `dist/`.

The generated paths are `/zh-CN/privacy/`, `/zh-CN/terms/`, `/en/privacy/`, and `/en/terms/`. Configure GitHub Pages to publish the `dist/` directory with GitHub Actions, or deploy the contents of `dist/` to the Pages publishing branch.

The repository also publishes PaiNovel without changing those existing 2048Pai URLs. PaiNovel source lives in `content/apps/painovel/`; its committed output and stable paths are:

- `/painovel/zh-CN/privacy.html`
- `/painovel/zh-CN/terms.html`
- `/painovel/en/privacy.html`
- `/painovel/en/terms.html`

Build and verify PaiNovel with:

```sh
python3 tools/build_painovel.py --ready
python3 tools/build_painovel.py --ready --check
```

## Preview and GitHub Pages

Preview locally after a build with `python3 -m http.server 8000 --directory dist`, then open `http://localhost:8000/zh-CN/privacy/`.

The included workflow at `.github/workflows/pages.yml` builds only after the site passes `--ready` and `--check`. To enable it, push this directory as the `app-legal` repository, then in GitHub choose **Settings → Pages → Build and deployment → Source: GitHub Actions**. Its deployed base URL will normally be `https://<account>.github.io/<repository>/`; use that exact base in the App link configuration described in the Flutter repository's `LEGAL.md`.
