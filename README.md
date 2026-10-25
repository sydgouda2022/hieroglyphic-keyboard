# Hieroglyphic Keyboard

Standalone, installable web app for composing Egyptian Unicode hieroglyphs and exploring attested Late Egyptian spellings. **No Renpet or MdwNfr installation is required.** Designed for mobile Safari and desktop browsers.

## Features

- Native Unicode sign keyboard with searchable Gardiner IDs, three phonogram groups, and explicit joining controls.
- On-device writing surface: cursor-aware insertion, copy, paste, selection, undo/redo, delete, and UTF-8 text export.
- Versioned 41,330-record Late Egyptian spelling catalog (40,265 distinct written surfaces) with locally ranked prefix suggestions; your typed text always remains available.
- Offline-first PWA, local workspace storage, self-repairing IndexedDB dictionary, previous-release fallback and SHA-256 integrity checks.
- Bundled Noto Sans Egyptian Hieroglyphs font in the built app, with its OFL license notice.
- No analytics, account, server-side document storage, or external runtime corpus lookups.

**Research scope:** The release is explicitly **incomplete**. 34,144 new Ramses/ MaReTE training-model sign sequences are **not independently verified lemma identities**; candidate badges mark these RTC rather than lemma-linked LE. A spelling-record count is not a vocabulary-size or historical-coverage claim. Model data is not individual manuscript evidence.

## Build the standalone app

Requires Python 3.12+. From the repository root:

```sh
python tools/build_keyboard_signs.py --check
python tools/build_app.py --out dist
cd dist
python -m http.server 8000
```

Open **http://localhost:8000/**. The builder downloads an exact, Git-blob-pinned SIL-OFL Egyptian font **at build time**, then copies the app, keyboard modules, and verified release into `dist/`. With a previously acquired pinned font you can build without network using `--font /path/to/NotoSansEgyptianHieroglyphs-Regular.ttf`. Builds never modify sources or overwrite an existing `dist/`; remove `dist/` before intentionally rebuilding.

The build output can be hosted on any HTTPS static host (including GitHub Pages or Cloudflare Pages). Install from the browser's Add to Home Screen / Install option. The document and dictionary are stored locally by the browser; clearing site data removes local work, so export important writing.

## Test

```sh
node --test tests/*.test.mjs
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
python -m compileall -q src tools
```

CI also checks SHA-256 of `release/lexicon.json`, SQLite integrity, sign-catalog projection and the packaged app. Each CI run attaches a standalone static site artifact.

## Repository authority

| Path | Role |
| --- | --- |
| `web/` | Standalone app source, document editor and offline service worker |
| `src/_generic_search.mjs` | Single Egyptian-only prediction implementation |
| `src/keyboard_search.mjs` | Stable exported prediction API |
| `src/lexicon_install.mjs` | Verified offline installer |
| `src/keyboard_catalog.js` | Authoritative grouped sign catalog |
| `release/` | Canonical SQLite master and matching published JSON projection |
| `src/compile_lexica.py` | Single canonical compiler for the current release schema |
| `sources/late_egyptian_registry.json` | Fixed source hashes, licensing and identity limits |
| `tools/build_keyboard_signs.py` | Derived sign pages, generated from one catalog |
| `tools/build_app.py` | Builds a self-contained PWA |

Renpet and MdwNfr can consume pinned copies of the library assets independently. This does not introduce dependencies from this app back to those products.

## Source rights and acknowledgments

Lexicon input sources are TLA Late Egyptian v19 (CC BY-SA 4.0), AED (CC BY-SA 4.0), document-whitelisted AES (CC BY-SA 4.0), and the specific MaReTE Ramses training word model (CC BY 4.0). ORAEC remains an unimported candidate. Rights compliance, attribution and dataset provenance must be carried into redistributions; source hashes alone are not licenses.

The Noto Sans Egyptian Hieroglyphs font is licensed under SIL OFL 1.1, with the complete notice in `web/OFL-NotoEgyptian.txt`. Consult `sources/README.md` and `docs/UPSTREAM_SOURCE.md` for exact source pins, limitations, and build details.

The installer verifies hash **integrity** but does not cryptographically sign or authenticate manifests. Host this app over trusted HTTPS.

### Safety and portability

Unicode hieroglyph rendering depends on font/engine support for quadrat controls. The writing surface is a plain-text Unicode editor, not MdwNfr's advanced page-layout engine. Imported/typed text is never treated as historically attested simply because it contains Egyptian characters.
