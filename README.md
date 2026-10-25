# Hieroglyphic Keyboard

**Reusable Egyptian Unicode keyboard library** with an optional embeddable Web
Component and standalone test/writing PWA.

The independent source repository supplies **one** core for Renpet, MdwNfr and
future applications. There is no required network prediction API and no dependency
on any consuming application. The UI never owns the host's cursor/document model.

## Modules and purpose

| Source | Role |
| --- | --- |
| `src/keyboard_api.mjs` | Stable v1 headless API: `createKeyboardFromData`, `createHieroglyphicKeyboard` |
| `src/keyboard_ui.mjs` | Optional `<hieroglyphic-keyboard>` Web Component and edit-request events |
| `src/keyboard_search.mjs`, `src/_generic_search.mjs` | Canonical Unicode prefix predictor |
| `src/keyboard_catalog.js` | Single curated sign catalog (27 uniliterals, 151 biliterals, 89 triliterals) |
| `src/lexicon_install.mjs` | Configurable URL, namespace and verified local-first installer |
| `release/` | Canonical source-aware data; SQLite master, browser lexicon, matching SHA-256 manifest |
| `web/` | Optional standalone writing/demo app; consumes the same public API and component |
| `tools/build_library.py` | Build portable library folder for any project |
| `tools/build_app.py` | Build optional PWA using the exact portable library |

The API provides `getSigns`, `searchSigns`, `predict`, `validate` and
`info`. It is DOM-free. The UI emits `hiero-insert`, `hiero-delete` and
`hiero-replace` events; the host chooses how to apply each requested operation.

**Start with [docs/INTEGRATION.md](docs/INTEGRATION.md)** for real browser
integration, offline operation, API examples and release pinning.

## Build the portable reusable library

Python 3.12+:

```sh
python tools/build_keyboard_signs.py --check
python tools/build_library.py --out dist-library
```

`dist-library/` contains only the library's modules, font, license, signs,
manifest and lexicon. Copy that folder into the consuming app under its own
static asset path. The font is fetched from a pinned **Google Fonts** revision
at build time; it does not come from Renpet. Supply `--font /path/to/font.ttf`
for a fully offline build.

## Build the optional standalone PWA

```sh
python tools/build_app.py --out dist
cd dist
python -m http.server 8000
```

Open `http://localhost:8000/`; publish `dist/` as an HTTPS static website to
make it installable. The PWA owns only its demo editor and optional service
worker. It reuses the exact library core and component—there is no second
keyboard. The browser stores its text locally; export important work before
clearing site storage.

## Tests

```sh
node --test tests/*.test.mjs
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
python -m compileall -q src tools
```

GitHub Actions checks source sign projection, SQLite/JSON row parity, checksum,
native Unicode semantics, consumer separation, UI event contract, both build
artifacts and published module imports. It uploads the portable library and
the optional standalone PWA as separate artifacts.

## Evidence and rights

The Late Egyptian release contains **41,330 spelling records** and **40,265
distinct written forms**. It explicitly does **not** claim complete vocabulary
coverage. Its 34,144 extra unlinked MaReTE/Ramses word-model forms must not be
presented as verified lemmas or individual text attestations. The engine
preserves raw input and the model-source distinction.

The four pinned input lineages are TLA Late Egyptian v19, AED, whitelisted AES
(CC BY-SA 4.0) and a specific MaReTE training model (CC BY 4.0). ORAEC remains
unimported. Redistribution must respect dataset rights and attribution.
The bundled Noto Sans Egyptian Hieroglyphs font is licensed under SIL OFL 1.1
(`web/OFL-NotoEgyptian.txt`). See
[docs/UPSTREAM_SOURCE.md](docs/UPSTREAM_SOURCE.md) and
[sources/README.md](sources/README.md).

The installer checks SHA-256 **integrity**, not publisher authentication.
The library package has a `1.0.0` interface version but is **not published
to npm**, and its package metadata prevents accidental publication pending
explicit redistribution/licensing review.

## Integration scope

Renpet and MdwNfr have **not been modified by this refactor**; they can migrate
separately to a pinned version of this new API. Existing release file paths and
`keyboard_search.mjs` exports are preserved for compatibility.
