# Integration guide — Hieroglyphic Keyboard API v1

The **hieroglyphic-keyboard** repository has one authoritative Egyptian Unicode
keyboard library and an *optional* standalone PWA. Renpet, MdwNfr, and any
future browser application can use the library without importing the demo app.

## Runtime boundaries

- **Core (headless):** `keyboard_api.mjs`. No DOM, editor, service worker, user accounts, or third-party network service.
- **UI (optional):** `keyboard_ui.mjs`. Registers one Web Component only when `defineHieroglyphicKeyboardElement()` is called. The UI never mutates the host's text/document model.
- **Verified installer:** `lexicon_install.mjs`, used by `createHieroglyphicKeyboard()`. HTTPS/localhost, WebCrypto and IndexedDB (or supplied storage adapter) are required for verified installation.
- **Data:** `lexicon/manifest.json`, `lexicon/lexicon.json`, `signs.json`. The library's sign catalog is embedded in `keyboard_catalog.js`.
- **Bundled font:** `font.ttf`, `hiero-font.css`, `OFL-NotoEgyptian.txt` in the built portable library. Install the font CSS in the host's document if native Egyptian font support is absent.

No Coptic lexicon, transliteration, Renpet calendar state, MdwNfr editor model,
or Cloudflare service is required. No runtime connection to a third-party API.

## Produce a portable browser bundle

From the repository root:

```sh
python tools/build_library.py --out dist-library
```

This generates one static folder containing the API, UI, release data, font and
license. The font is fetched **at build time from a pinned Google Fonts revision**,
not Renpet. To build offline with the same pinned font:

```sh
python tools/build_library.py --font /path/to/NotoSansEgyptianHieroglyphs-Regular.ttf --out dist-library
```

Copy the **entire** `dist-library/` folder into the consuming app under
`public/vendor/hieroglyphic/` (or any equivalent local static directory),
pinning an immutable Git commit and release manifest SHA-256. Keep its
`lexicon/` subdirectory in place. Do not reference the standalone app's
`app.mjs`, `sw.js`, `editor-core.mjs`, or `index.html`.

The `package.json` also offers named ESM export entry points for source or
Git-based JavaScript builds. The package is **not published to npm** and marked
private until code/data redistribution licensing is reviewed.

## Headless usage (no keyboard interface)

```js
import {createHieroglyphicKeyboard} from
  '/vendor/hieroglyphic/keyboard_api.mjs';

const keyboard = await createHieroglyphicKeyboard({
  manifestUrl: '/vendor/hieroglyphic/lexicon/manifest.json',
  lexiconUrl: '/vendor/hieroglyphic/lexicon/lexicon.json',
  storageNamespace: 'renpet-egyptian-v1'
});

const uniliterals = keyboard.getSigns('uni');
const sign = keyboard.searchSigns('M17A')[0]; // {code, glyph, name, group}
const words = keyboard.predict('𓄿',{limit:6}); // raw first; never silently correct
const valid = keyboard.validate('𓄿𓈖');
const releaseInfo = keyboard.info; // {spellingRecords, sha256, complete, status}
```

If a trusted, already-loaded JSON catalog is available and no installer is
needed, use `createKeyboardFromData({lexicon:catalog})`. This in-memory
constructor intentionally **does not perform SHA-256 verification**. With
`createKeyboardFromData()` (no catalog), the sign keyboard still works and
predictions return only the typed text.

### API v1

| Method | Behavior |
| --- | --- |
| `getSigns(group='all')` | Snapshot array of immutable `{code,glyph,name,group}`; `uni/bi/tri/all`, plus full group names |
| `searchSigns(query,{group='all',limit=100})` | Case-insensitive Gardiner-code and English-description lookup |
| `predict(nativeText,{limit=4,learned={},previous=''})` | Native Unicode suggestions with provenance and raw-text option first |
| `validate(nativeText)` | Boolean structural check on native Egyptian Unicode signs/quadrat operators |
| `info` | Frozen, per-instance dictionary status and version metadata |

The library does not store learned words automatically, monitor keystrokes or
alter source lexicon evidence. Personal `learned` weights must be supplied by
the consumer; such results are marked personal, not Egyptian attestations.

## Embed the supplied keyboard UI

In an app that uses native browser modules:

```html
<link rel="stylesheet" href="/vendor/hieroglyphic/hiero-font.css">
<hieroglyphic-keyboard id="hieroglyphic-input"></hieroglyphic-keyboard>
```

```js
import {createHieroglyphicKeyboard,createKeyboardFromData} from
  '/vendor/hieroglyphic/keyboard_api.mjs';
import {defineHieroglyphicKeyboardElement} from
  '/vendor/hieroglyphic/keyboard_ui.mjs';

defineHieroglyphicKeyboardElement(); // idempotent; no automatic global setup
const component = document.getElementById('hieroglyphic-input');
// Let signs work before the dictionary finishes loading.
component.keyboard = createKeyboardFromData();
component.keyboard = await createHieroglyphicKeyboard({
  manifestUrl:'/vendor/hieroglyphic/lexicon/manifest.json',
  lexiconUrl:'/vendor/hieroglyphic/lexicon/lexicon.json',
  storageNamespace:'mdwnfr-egyptian-v1'
});
component.query = '𓄿'; // Host supplies the current word; UI does NOT read inputs.

// Each event bubbles across Shadow DOM. The host is authoritative:
component.addEventListener('hiero-insert', event => {
  hostEditor.insert(event.detail.text); // {text,code?,kind:'sign'|'control'}
});
component.addEventListener('hiero-delete', () => {
  hostEditor.deletePreviousGrapheme();
});
component.addEventListener('hiero-replace', event => {
  // {text,raw,candidate}. Check the active word still matches detail.raw.
  hostEditor.replaceCurrentWord(event.detail.raw,event.detail.text);
});
```

The `hostEditor` variable is intentionally pseudocode: Renpet and MdwNfr supply their own
editing operations. No textarea is created, selected, or changed by this UI.

For **Renpet**, insert the Unicode signs in the appointment input while Renpet
manages appointment persistence. For **MdwNfr**, send the requested Unicode signs
or quadrat operators to its composition/selection engine; do not let the
keyboard claim to own the document geometry, text direction or page layout.

On dictionary failure, leave `component.keyboard=createKeyboardFromData()`
so all sign keys remain available and a retry can happen independently.

## Per-consumer isolation

Each app chooses its own `storageNamespace`. The default verified store is
IndexedDB `hieroglyphic-keyboard-v1:<namespace>`. Distinct browser origins
are already isolated by the platform. A consumer may instead pass its own
`store`, `fetcher`, `online` and `timeoutMs` to support dependency injection
and offline tests. Asset URLs must be explicit and may point to version-pinned
same-origin static assets; these are **not** a hosted prediction service.

An app should avoid sharing the same storage namespace across incompatible
lexicon editions unless it intentionally wants them to migrate in place.
All installations verify byte hashes before accepting data and retain the
previous verified slot as a rollback source. Integrity checking does not
authenticate the hosting publisher.

## Release compatibility contract

`API_VERSION = '1.0.0'`; API v1 is a documented interface, not a published npm
registry release or GitHub tag. Pin the exact source commit and
`release/manifest.json` hash until intentional updates.

- Adding optional result fields or new signs: minor-compatible changes.
- Renaming methods, events, object properties, or changing native sign semantics:
  major version.
- Rebuilding the lexicon: a separate data-version/release operation.
- Editor behavior and UI colors: application responsibility; no API break.

The actual current release is **incomplete**. Unlinked model word forms are
identified as `RAMSES-CORPUS`, not verified lemma records. The keyboard returns
raw typed text even when no suggestion is historically supported.
