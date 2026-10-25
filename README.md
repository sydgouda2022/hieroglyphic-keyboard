# Hieroglyphic Keyboard API

**Headless Egyptian Unicode keyboard library.** This repository is an API
package, **not** a standalone application, PWA, hosted service or REST endpoint.

It provides Unicode sign lookup, Late Egyptian spelling prediction, explicit
evidence/source metadata, structural Unicode validation and optional verified
local-first dictionary installation. Renpet, MdwNfr and future applications own
their own interfaces, editors, storage for documents and deployment.

## Public API v2.0.0

```js
import {createKeyboardFromData,createHieroglyphicKeyboard} from
  '@sydgouda/hieroglyphic-keyboard';

// Sign-only core: synchronous, no browser globals, downloads or storage.
const signs = createKeyboardFromData();
signs.getSigns('uni');
signs.searchSigns('M17A');
signs.validate('𓄿𓈖');

// Dictionary-assisted core: trusted, explicit, app-hosted static assets.
// The expected SHA-256 pin prevents accidental lexicon release drift.
const keyboard = await createHieroglyphicKeyboard({
  manifestUrl: '/vendor/hieroglyphic/lexicon/manifest.json',
  lexiconUrl: '/vendor/hieroglyphic/lexicon/lexicon.json',
  expectedSha256: '48f7769c20b1560f76b0080e8ac5155b5e42c2b9fe2c1fe696f765e803dd5a39',
  storageNamespace: 'renpet'
});
keyboard.predict('𓄿',{limit:6});
console.log(keyboard.info); // release metadata, incomplete coverage flag
```

The API never changes a host document. Prediction is always initiated by the
consumer, never by a background keyboard service. It does not require an
internet connection after a verified dictionary has been installed. A
`createKeyboardFromData({lexicon})` constructor is available for already trusted
local data, but does **not** itself verify the dictionary's SHA-256.

The corpus contains **41,330 spelling records** (40,265 distinct Unicode
surfaces). Its historical coverage is explicitly **incomplete**. The 34,144
unlinked Ramses/MaReTE model-only forms are not verified lemmata or individual
manuscript witnesses. Prediction data distinguishes textual attestations
from model-only forms. Legacy array records are rejected because they discard
that distinction.

## Browser integration without a hosted service

The package is currently **unpublished** and marked private because
redistribution rights must be reviewed. Consumers can pin a Git commit or
copy an exact static API export from CI:

```sh
python tools/export_api.py --out dist-api
```

`dist-api/` contains JavaScript modules, `lexicon/manifest.json`,
`lexicon/lexicon.json`, coverage metadata and data-source notices.
There are no HTML, CSS, images, fonts, service workers, editors, or PWA assets.

Copy these files to your application's static assets and import
`/vendor/hieroglyphic/keyboard_api.mjs`. The dictionary's signed-looking
hash is **an integrity check, not publisher authentication**; serve it from a
trusted origin and set `expectedSha256`.

Detailed interfaces, error handling and examples:
**[docs/INTEGRATION.md](docs/INTEGRATION.md)**.

## Source/maintenance layout

| Path | Purpose |
| --- | --- |
| `src/keyboard_api.mjs` | Public headless v2 facade |
| `src/keyboard_search.mjs` | Sole provenance-aware predictor |
| `src/keyboard_catalog.js` | Curated Gardiner-code sign catalog |
| `src/lexicon_install.mjs` | Verified local lexicon storage and updates |
| `src/compile_lexica.py` | Authoritative historical source compilation |
| `src/publish_release.py` | Immutable validated JSON/manifest release |
| `sources/` | Fixed source edition registry and document approvals |
| `release/` | Auditable SQLite master, JSON lexicon, coverage and manifest |
| `tools/export_api.py` | Consumer asset package, no application layer |
| `tests/` | JavaScript API, integrity, provenance and Python pipeline regression tests |

## Tests

```sh
node --test tests/*.test.mjs
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
python -m compileall -q src tools
python tools/export_api.py --out dist-api
```

CI verifies the committed JSON and SQLite data row-by-row and builds the
headless distribution artifact. API v2 is a breaking upgrade from the earlier
experimental v1 Web Component interface; consumers must migrate deliberately.

## Evidence and rights

The four fixed data lineages are TLA Late Egyptian v19, AED, approved AES
(CC BY-SA 4.0) and the MaReTE Ramses model (CC BY 4.0). See
[third-party notices](docs/THIRD_PARTY_NOTICES.md),
[upstream evidence notes](docs/UPSTREAM_SOURCE.md) and
[sources/README.md](sources/README.md). The repository is not an unrestricted
license grant for its upstream corpora. No font is redistributed by this API.
