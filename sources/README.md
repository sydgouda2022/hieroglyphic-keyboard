# Late Egyptian source evidence

The only runtime lexicon is the pinned published JSON projection of the canonical SQLite master. External datasets are **build-time inputs**; the app never queries TLA/AED/AES/MaReTE while users type.

## Included with exact source hashes

- TLA Late Egyptian v19 premium extract: CC BY-SA 4.0; filtered sentence corpus, not all of TLA.
- AED v1.0 TEI: CC BY-SA 4.0; lexical metadata crosswalk.
- AES literary corpus: CC BY-SA 4.0; only document IDs in `aes_late_documents.json` and individually approved period scope.
- MaReTE Ramses training *word model*: CC BY 4.0. Sign sequences have no reliable source witness IDs or verified lemma links. This open model is not a license for restricted full Ramsès datasets.

Exact upstream URLs, license labels and SHA-256 fingerprints live in `late_egyptian_registry.json`. The compiler verifies all supplied source bytes by default before writing the database. Only tests with synthetic fixtures may explicitly bypass byte-pin verification.

## Not imported

ORAEC remains unimported: individual file permission/format and word segmentation must be vetted first. Lesko's dictionary, restricted Ramsès bulk sources and full TLA online Corpus 20 are not licensed imports here.

## Legal and historical caution

CC BY-SA 4.0 and CC BY 4.0 have attribution and redistribution obligations. Hash verification does not replace rights review; mixing source lineages does not create independent attestations. A shared Unicode spelling is not sufficient proof of shared lemma identity. Native sign sequences can have different meanings and variants across periods; this release is explicitly *not complete*.
