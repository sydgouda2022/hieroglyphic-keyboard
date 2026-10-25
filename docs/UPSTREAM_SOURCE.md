# Late Egyptian keyboard: pinned evidence and release architecture

Status: October 25, 2026. This repository owns one standalone PWA and one Late Egyptian lexicon compiler. Renpet and MdwNfr are consumers, not dependencies.

## Current source-pinned release

- **41,330** SQLite spelling records.
- **40,265** distinct Unicode written surfaces.
- **3,129** reported linked lemma identities, with unresolved alignment excluded from future verified-identity counts.
- **34,144** extra unlinked Ramses MaReTE word-model Unicode sign sequences. These are not verified lemma identities or manuscript witness references.
- TLA v19: 3,606 filtered sentences (not the entire historical TLA corpus).
- AES: eight individually approved literary documents; seven supply complete Unicode word signs, adding 1,036 lemma–form pairs.
- 10,930 model encodings could not be converted without guessing and were excluded.
- `metadata.complete=false` is authoritative. Nothing here certifies total coverage of Late Egyptian.

The exact hashes, licenses and source roles are in `sources/late_egyptian_registry.json`. Unlike access-restricted Ramsès bulk manuscript material, the particular University of Helsinki MaReTE training model used here is published under CC BY 4.0 with distinct conditions and limitations. ORAEC is a candidate only, not counted as an imported corpus.

## Authoritative flow

```
pinned open source files → src/compile_lexica.py
                           → release/lexicon.sqlite3 (canonical master)
                           → release/lexicon.json (browser projection)
                           → src/publish_release.py → release/manifest.json
                           → tools/build_app.py → standalone static PWA
```

Only `compile_lexica.py` defines the canonical SQLite schema used in this release. Alternative historic builders and pack contracts are retired. The source compiler verifies registered TLA, AED, AES and MaReTE SHA-256 files by default; synthetic tests explicitly opt out. The separate AES document approval list is `sources/aes_late_documents.json`. The Ramses model encoder does not reconstruct uncertain or damaged signs.

The browser checks the manifest size/hash and the payload's native-sign structure; it falls back to a previously verified local copy if an update fails. Hash matching authenticates neither a compromised hosting account nor a simultaneously replaced manifest and payload. No digital-signature claim is made.

`src/keyboard_catalog.js` is the sole curated sign group source. `release/signs.json` is generated from it with `python tools/build_keyboard_signs.py` (or checked with `--check`). The groups are for keyboard convenience and do not imply a unique historic phonetic reading for every sign.

## Rebuild sources

Download the exact pinned files listed in the registry and compile:

```sh
PYTHONPATH=src python src/compile_lexica.py --tla /private/train.jsonl \
  --aed /private/dictionary.xml --aes /private/aes_sawlit.json \
  --aes-whitelist sources/aes_late_documents.json \
  --ramses /private/RamsesTrainingSetModel.json --out /private/release-build
PYTHONPATH=src python src/publish_release.py \
  --catalog /private/release-build/lexicon.json --out /private/published
```

The compiler refuses source fingerprint mismatches. Output directories should be new/empty and must be kept distinct from the tracked release. To replace the tracked release, independently compare generated SQLite rows, evidence lineage, and JSON record identities, then update the authoritative release files together.

## Benchmark limitations

The historical held-out benchmark reported 90.18% token coverage and 66.67% distinct lemma–form coverage on 13,112 scorable, complete Unicode tokens from a restricted group of AES texts. These figures are *not* validation of the expanded Ramses model, unseen documents, all genres, damaged signs or complete Late Egyptian. Re-run `src/benchmark_late_egyptian.py` with original source material to reproduce or extend the evaluation.

## Distribution

A built static app includes `manifest.json`, `lexicon.json`, `coverage.json`, generated signs, the font and its license, without serving the 33.9MB canonical SQLite master. The source repository retains SQLite for audits and Python consumers; browsers do not fetch it. App PWA behavior and live mobile Safari interaction need device-level verification in addition to the automated checks.
