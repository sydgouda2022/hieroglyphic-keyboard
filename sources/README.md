# Late Egyptian — approved open-data-only research inputs

**Active source list:** `late_egyptian_registry.json`.

The source list is intentionally limited to the datasets that do **not** require
individual copyright permission, a negotiated research license or a paid bulk
export. Ingestion is performed once at build time, after verifying actual file
terms, revisions and SHA-256 hashes. The applications only use a canonical
`lexicon.sqlite3` release and derived indexes, with no source-server requests.

## Approved editions

1. **TLA Late Egyptian v19 premium extract:** openly published CC BY-SA 4.0,
   3,606 filtered sentences. This is a limited subset, not all of TLA.
   https://huggingface.co/datasets/thesaurus-linguae-aegyptiae/tla-late_egyptian-v19-premium
2. **AED v1.0:** open CC BY-SA 4.0 dataset. https://zenodo.org/records/3581069
3. **AES:** GitHub corpus under CC BY-SA 4.0. https://github.com/simondschweitzer/aes
4. **ORAEC:** only files with explicitly published CC BY-SA 4.0 or CC0
   terms; file-level verification is mandatory.
   https://github.com/oraec/corpus_raw_data

## Excluded from all active builds

- **Projet Ramsès:** no verified open bulk-data reuse permission.
- **Lesko's Dictionary of Late Egyptian:** copyrighted specialist dictionary,
  without an openly redistributable bulk dataset.
- **Full TLA Corpus 20:** its web interface is not an automatically reusable
  bulk data release. A separately published open-data extract would require a
  new explicit registry change after confirming its public license.

These are exclusions, not lower-ranked fallback sources. Reintroducing them
requires a separately approved policy change and tests.

## Open licensing is still licensing

CC BY-SA 4.0 requires appropriate attribution and compliance with ShareAlike
for adaptations; CC0 does not impose those license obligations. Keep source and
selected-file attribution/provenance with the master and distribute required
license information with applicable releases. Merely using sources at build
rather than runtime does not automatically remove obligations for derived data.

## Process

1. Download the specific public release and pin version/hash.
2. Verify exact source or per-file open license and attribution.
3. Normalize native hieroglyphic spellings and Late Egyptian stage evidence.
4. Reconcile shared 2018 lineage across AED, AES and ORAEC; preserve distinct
   lemmas and historical spelling variants.
5. Use `verified_source_manifest()` to pass only approved source files into
   `build_master.py`; unapproved IDs are blocked even by the production builder.
6. Generate the versioned runtime indexes for Renpet and MdwNfr from the same
   canonical database and verify reproducibility, offline use and credits.

**Registered does not mean acquired or imported.** The comprehensive dictionary
has not yet been compiled from these editions.
