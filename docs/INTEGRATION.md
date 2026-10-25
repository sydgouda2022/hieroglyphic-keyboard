# Hieroglyphic Keyboard API v2.0.1 — Integration Contract

This package is **headless only**. There is no PWA, embedded keyboard component,
visual styling layer, browser service worker, HTTP server or standalone editor.
Renpet, MdwNfr and other applications control all document editing and UI.

## Install or copy assets

Pin the source repository to a tested commit. Build an API-only static export:

```sh
python tools/export_api.py --out dist-api
```

Copy `dist-api/` into your web application's static folder as
`/vendor/hieroglyphic/` and keep `lexicon/` under that folder.
The `keyboard_api.mjs` import is valid in native browser ESM, Node and modern
JavaScript bundlers. A source checkout can also import package exports
`@sydgouda/hieroglyphic-keyboard`, `./search`, `./installer`, `./catalog`.

Package registry publication is intentionally disabled; deploy a pinned
copy rather than auto-updating `main` in production.

## Minimal, no-dictionary usage

```js
import {createKeyboardFromData} from '/vendor/hieroglyphic/keyboard_api.mjs';
const keyboard = createKeyboardFromData();
const uni = keyboard.getSigns('uni');
const all = keyboard.getSigns('all');
const sign = keyboard.searchSigns('M17A')[0]; // {code,glyph,name,group}
const isWellFormed = keyboard.validate('𓄿𓈖');
```

## Fully verified local lexicon usage

```js
import {createHieroglyphicKeyboard} from
  '/vendor/hieroglyphic/keyboard_api.mjs';
const keyboard = await createHieroglyphicKeyboard({
  manifestUrl:'/vendor/hieroglyphic/lexicon/manifest.json',
  lexiconUrl:'/vendor/hieroglyphic/lexicon/lexicon.json',
  expectedSha256:'48f7769c20b1560f76b0080e8ac5155b5e42c2b9fe2c1fe696f765e803dd5a39',
  storageNamespace:'mdwnfr-hieroglyphic',
  timeoutMs:30000
});
const predictions=keyboard.predict('𓄿',{limit:6});
const identity=keyboard.info; // {apiVersion,sha256,spellingRecords,...}
```

The pinned fingerprint belongs to the currently committed lexicon release.
Change it only after reviewing and approving a new dataset. SHA-256 checks
**byte integrity, not the origin's identity or authenticity**.

An app can supply `store` and `fetcher` implementations for custom
persistence and testing. The default uses IndexedDB and browser WebCrypto.
If the browser already has the correct verified release, it is reused
**without a network request**; `refresh:true` explicitly rechecks the remote
manifest. `expectedSha256` applies to cached, restored and remote releases.
By default a dictionary fetch can take up to 30 seconds; callers may override
`timeoutMs` (milliseconds). The default IndexedDB store is scoped by
`storageNamespace` **and** a provided `expectedSha256`, so different pinned
dictionary releases never overwrite one another. Migrating from the prior
storage layout may involve one new download; consumers supplying their own
store manage isolation themselves. Distinct injected fetchers are never
mistakenly coalesced into one request. Personal learned suggestions must be
well-formed native Egyptian Unicode; typed raw text itself is always retained.

## Public return shape

`getSigns(group='all')`: immutable-data snapshot; `uni`, `bi`, `tri`,
`all` or equivalent full names.

`searchSigns(query,{group='all',limit=100})`: case-insensitive Gardiner code
and English description lookup; numeric-aware Gardiner sort.

`predict(word,{limit=4,learned={},previous=''})`: typed Unicode is always
the first result. Other results include:

```js
{
  text: '𓄿𓈖',
  raw: false,
  personal: false,
  attested: true,                // actual TLA/AES textual occurrence
  lexicalIdentityVerified: true,
  source: 'LATE',                 // or RAMSES-CORPUS / PERSONAL
  sourceId: 'TLA-LE19',
  lexicon_ref: 'tla19:...',
  lexicon_refs: ['tla19:...'],
  lemma: 'tla19:...',
  frequency: 12                 // source-specific, NOT cross-source probability
}
```

An entry from `RAMSES-CORPUS` has `attested:false` and
`lexicalIdentityVerified:false`. A textual occurrence with unresolved lemma
has `attested:true`, `lexicalIdentityVerified:false`. A personal/learned
suggestion is never historical evidence. Source classes are ranked by
evidence tier before their noncomparable frequency values.

`validate(nativeText)`: structural Unicode sign/layout validator.
It is **not** a historical-spelling validator.

`info`: frozen API/data metadata, including `complete:false` for the
current historical dataset.

`createKeyboardFromData({lexicon})` is a synchronous option for a trusted,
already loaded object catalog; it does **not** verify its checksum. Legacy
array-based lexicon records are deliberately rejected in v2.

## Host editing contract

The keyboard does not take ownership of selections, cursors or documents.
The host decides how to use a sign or prediction:

```js
const selected = keyboard.searchSigns('G17')[0];
renpetAppointmentEditor.insertUnicode(selected.glyph); // application-defined

const options = keyboard.predict(currentEgyptianWord,{limit:6});
// The app chooses whether to show suggestions and how to replace selected text.
```

A Renpet appointment input and MdwNfr's quadrat layout engine can both use
the same API; no shared UI component is required. Unicode fonts, script
direction, touch targets, Coptic/Arabic translations and application-level
document persistence belong to the consumer.

## Scope and compatibility

API v2 removes the Web Component and the application, replacing the prior
v1 UI/event contract with a headless-only surface. This is an intentional
breaking change. Neither Renpet nor MdwNfr is automatically migrated.
Install/update consumers after testing their own application behaviors.

The shipped corpus remains source-filtered, incomplete and not a full
dictionary of Ancient Egyptian. See `docs/THIRD_PARTY_NOTICES.md`.
