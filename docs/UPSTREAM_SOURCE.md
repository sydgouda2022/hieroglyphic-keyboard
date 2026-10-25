# Source-pinned Late Egyptian lexicon: evidence and build boundaries

This repository publishes a **headless keyboard API**, not a PWA or app.
It includes one auditable Late Egyptian source compiler and one immutable
on-device dictionary release. No runtime call to TLA, AES, AED or MaReTE
is required by the prediction API.

## Current committed data

- 41,330 spelling records; 40,265 distinct Unicode written surfaces.
- 3,129 reported resolved lemma identities according to the stored release.
- 34,144 additional *unlinked* Ramses/MaReTE model-only written forms.
- 3,606 TLA source sentences and 7 approved AES documents supplying complete
  encoded Unicode spellings; an eighth approved AES document contains no
  qualifying spellings in this particular extract.
- 10,930 source-model encodings excluded rather than completed by guessing.
- `complete:false` in the manifest and payload is authoritative.

The current record count is not a vocabulary-size or historical completeness
claim. MaReTE model frequency is **not** the same measurement as TLA/AES
textual occurrence frequency. The headless predictor distinguishes them.

## Canonical historical pipeline

```
pinned TLA/AED/AES/MaReTE inputs + pinned approved AES document whitelist
                         |
             src/compile_lexica.py
                  /          \
  release/lexicon.sqlite3   release/lexicon.json
                                    |
                        src/publish_release.py
                                    |
                         release/manifest.json
                                    |
                         tools/export_api.py
                                    |
                    API-only browser distribution
```

The compiler rejects unregistered upstream dataset bytes by SHA-256 and checks
the approved AES whitelist's pinned Git-blob identity. Failed compiler builds
must not replace an existing release. Publishing checks declared source
fingerprints and native text structure before generating the manifest.
Regeneration needs the original source datasets, not merely the compiled
browser JSON.

## Original-source reproduction

```sh
PYTHONPATH=src python src/compile_lexica.py \
  --tla /private/tla_late.jsonl --aed /private/aed.xml \
  --aes /private/aes_sawlit.json \
  --aes-whitelist sources/aes_late_documents.json \
  --ramses /private/RamsesTrainingSetModel.json \
  --out /private/compiled-release

PYTHONPATH=src python src/publish_release.py \
  --catalog /private/compiled-release/lexicon.json \
  --out /private/published-release
```

For actual releases, source byte verification stays enabled. Synthetic tests
may bypass pins explicitly, but **published releases cannot**.
The committed SQLite master and JSON projection are independently compared
in CI for all rows and frequency/reference correspondence.

## Limitations

The historical AES held-out benchmark applies only to its scoped documents,
complete Unicode tokens and lemma-linked forms. It is not a prediction
accuracy certification for unseen texts or model-only forms. A Unicode sequence
that the structural validator accepts is not necessarily a valid Egyptian word.

Upstream source IDs, checksums, licensing and approved scope are in
`sources/late_egyptian_registry.json`, `sources/README.md` and
`docs/THIRD_PARTY_NOTICES.md`. The API exporter carries source notices
alongside the dictionary. Reuse rights still require a separate compliance
review, especially for CC BY-SA attribution and redistribution conditions.

SHA-256 checks in the local installer detect mismatched bytes but do not
cryptographically authenticate the publisher's endpoint. Hosts should pin
`expectedSha256` and serve approved static assets from a trusted origin.
