# Egyptian Language Platform — source-expanded lexicon releases

**Status (2026-10-24): Source ingestion, canonical SQLite compilation, signed-by-SHA256 browser release installation and two-app deployment are implemented and tested. The selected available source editions have been fully processed; historically exhaustive coverage and advanced morphological/contextual prediction are NOT certified.**

## Current independently audited source builds

| Pack | Native prediction surfaces | SQLite records | Lexical evidence |
| --- | ---: | ---: | --- |
| Late Egyptian hieroglyphic | **40,265 distinct native-script surfaces** | **41,330** SQLite spelling records; **3,129 verified lemma identities**; **34,144 newly imported, unlinked Ramses word forms** | 3,606 intact TLA sentences, seven curated AES Late Egyptian documents, and 37,984 Unicode-convertible sign sequences from the CC BY 4.0 Ramses training model |
| Coptic | **20,652** native-script word forms | 11,283 TEI entries plus 20,652 unlinked corpus-index identities; 38,194 spelling records with per-form provenance | 32,229 TEI form records from the full published KELLIA Comprehensive Coptic Lexicon v1.2 (2020), reconciled against existing Scriptorium Sahidic/Bohairic forms and KELLIA supplements |

Unique prediction surfaces are **not** the number of meanings, lemmas, textual occurrences, or the total vocabulary used in all periods.

The Coptic prediction masks retain Sahidic-only (12,246), Bohairic-only (3,358), both (4,041), and no verified Sahidic/Bohairic attribution (1,007) forms. Unverified dialect attribution is never guessed.

All provided datasets were acquired from their explicit public release and checked against pinned SHA-256 source hashes. The Late Egyptian vocabulary does **not** silently include Earlier Egyptian material. AES supplies **1,036 additional** exact lemma–spelling records; the pinned University of Helsinki/Ramses model supplies **34,144 additional unique written surfaces** after excluding 3,840 that were already present. These Ramses surfaces are **corpus-level evidence**, without individual manuscript references or verified lemma identities. Their unlinked identity is explicit in the SQLite records and keyboard; 10,930 additional model rows were rejected as not fully Unicode-convertible. ORAEC remains an uncounted supplement candidate. Access-restricted Ramsès materials beyond this explicitly CC BY-licensed model, Lesko and the full TLA online corpus are excluded.

## Binary authority and app behavior

- **One canonical SQLite master per language:** `src/compile_lexica.py` produces immutable `lexicon.sqlite3` with lemma, spelling and evidence tables.
- The compact Unicode prediction JSON is an **export of that master build**, not another independently edited dictionary.
- Renpet bundles and installs both validated releases; MdwNfr bundles and installs only the Late Egyptian release. Renpet no longer ships raw Scriptorium/KELLIA word source tables as its editable prediction authority.
- A dedicated IndexedDB installation area checks SHA-256 and structural integrity on every startup. Valid saved copies start offline. Missing or corrupt copies are installed, repaired from a verified previous release or fetched from the bundled PWA cache/network. Failed updates cannot delete personal appointments, documents or learning.
- MdwNfr's Python runtime spelling catalog is replaced at build time with the **same 41,330-record release** shipped in Renpet; MdwNfr's advanced layout and Renpet's simple inline Unicode layout remain separate.

## How to regenerate the verified release

Download these specific open files into a private build directory, checking the exact SHA-256 digest:

- TLA Late Egyptian v19 premium `train.jsonl`: `dfded75c7d34bc1f2f12e18af6936394dc0c5cadacd1229dc28d46751d6389df`
- AED-TEI `dictionary.xml` at commit `462c722e0323e05641aea2eee8cdf1e27303d939`: `faaca47fc4e3c89899a764e56321ca2dc051e58ef6462acedaa6205ea666b730`
- AES literary text collection `_aes_sawlit.json` at commit `35276d2527cca1a055e31ed5f6683e777717170f`: `b3d5eb695584be976b9981392eb4e149d13f447f677cf445b5a954898bc82ef4`. Only IDs in `sources/aes_late_documents.json` qualify.
- Ramses word-model `Models/RamsesTrainingSetModel.json` from University of Helsinki MaReTE commit `c612a91407bddf8d546beedaf46edd5190a67eef`: `b399acfef9462c76f4df97794a97369c24f33dc6d87269f315e41a5d16103691` (CC BY 4.0; credit Heidi and Tommi Jauhiainen, Serge Rosmorduc and original Ramsès contributors).
- KELLIA Comprehensive Coptic Lexicon v1.2 (2020) XML at commit `f365e2d239bd12b6897f3a761487e40d384b2b24`: `ace84fce11b76386a6adb9888b2cb947056954fc9fe9c04aa0676b1f595fd43d`

```bash
python shared-language/src/compile_lexica.py egyptian \
  --tla /private/tla.jsonl --aed /private/aed.xml \
  --aes /private/aes_sawlit.json \
  --aes-whitelist shared-language/sources/aes_late_documents.json \
  --ramses /private/RamsesTrainingSetModel.json \
  --out /private/build/egy
python shared-language/src/publish_release.py \
  --catalog /private/build/egy/lexicon.json --out /private/build/egy
python shared-language/src/compile_lexica.py coptic \
  --tei /private/coptic.xml \
  --forms renpet/web/assets/dictionaries/coptic.json \
  --popular renpet/web/assets/dictionaries/coptic-popular.json \
  --out /private/build/cop
python shared-language/src/publish_compiled_coptic.py --out /private/build/cop
```

The compiler prints coverage reports and writes `coverage.json`, `manifest.json`, `lexicon.json`, and `lexicon.sqlite3` per language. The automated source-build workflow also uploads both master databases as a downloadable artifact.

## Verification

- `validate-corpora.yml`: checks all source imports, manifests, SQLite integrity, reproducible coverage counts, native-script exclusion filters and licensed source fingerprints.
- `test-shared-language.yml`: verifies missing/corrupt/offline/rollback first-run scenarios and dictionary-pack contracts.
- `deploy-renpet-pages.yml` and `deploy-mdwnfr.yml`: reconstruct and verify the same source editions, then check deployed release counts via HTTPS smoke tests.
- `renpet-mobile-qa.yml`: exercises iPhone-size WebKit/Chromium calendar input, save/reopen and offline behavior against the source-expanded packs.

## Coverage-measurement milestone (2026-10-24)

The **pre-Ramses** source-pinned leave-one-AES-document-out benchmark ships as
`src/benchmark_late_egyptian.py` and `heldout_coverage.json` in the canonical
SQLite artifact. Evaluating **13,112 complete, lemma-linked Unicode tokens** in
seven scorable curated works (one selected text contains no usable Unicode
tokens) produced **90.18% token coverage** and **66.67% distinct
lemma-spelling coverage**. The TLA-only baseline was **76.78% token coverage**
and **56.63% type coverage**. These are cross-document internal scores, NOT
generalization to unseen literature as a whole or to unencoded texts.
The 95%/90% acceptance targets are **not met**.

An explicit Unicode spatial-control grammar now recognizes balanced,
undamaged Egyptian format controls rather than silently rejecting them.
Full sign-code sequences from AES can be decoded using official Unicode
Gardiner names only when each sign resolves uniquely and an explicitly
present Unicode spelling is not damaged. All conversion methods are recorded
in the attestation reference. Mixed markup, uncertain editorial glyphs,
incomplete Gardiner codes, and reconstruction from transliteration are
rejected. All of these rules have unit tests.

We audited nine additional Ramesside poetry and scribal selections. In the
pinned openly licensed AES release they yielded **zero** complete,
lemma-linked Unicode spellings. The documents remain candidate-only, and
neither the **41,330** Late Egyptian spelling-record count nor the **20,652** Coptic forms count includes those unconvertible sources. Further increases require additional genuine sign-encoded evidence,
source-by-source philological stage checks, or independently reviewed
transcriptions of manuscript material. ORAEC's continuous Unicode text lines
cannot be blindly segmented into attested *words*.

## Source evidence tiers and deployment

- **TLA/AES (primary):** exact Unicode spelling and a TLA/AED lemma ID backed by source-level references.
- **Ramses model (secondary, labeled RTC):** fully decoded MdC-to-Unicode *sign sequences* from an openly licensed Late Egyptian word model. No per-witness IDs and no verified lemma equivalence; one unlinked placeholder per new spelling is used to keep SQLite referential integrity. Duplicates of primary spellings are stored independently as `corpus_form` evidence rather than reattributed to an unrelated homographic lemma.
- The **authoritative SQLite** (~32 MiB) remains a verified artifact of `validate-corpora.yml`. To respect Cloudflare's **25-MiB individual static asset limit**, neither browser PWA publishes that non-runtime master file. Both ship the exact **41,330-record, SHA-256-verified JSON projection** (~8.5 MB). The installer preserves offline, rollback and corruption repair.
- The earlier pre-Ramses 90.18%/66.67% held-out AES scores are historical baselines only. A new cross-corpus evaluation needs independent documents outside the Ramses model; we do not claim unmeasured post-expansion coverage.

## What is still NOT 100% linguistically complete

The downloadable TLA v19 premium dataset contains a *filtered portion* of known Late Egyptian materials; curated AES literary evidence substantially improves coverage but does not supply the entire historical stage, not the entire TLA corpus. Some attested words use non-Unicode or unencoded signs (1,034 word occurrences in this import), which cannot become valid native-sign suggestions without independent source verification. AED additionally contains many broader-stage transliteration-only entries; those are **not** automatically converted into Late Egyptian written words.

The Coptic sources are substantial, not all historic dialects or inflected word forms ever attested. TEI lexical descriptions do not automatically constitute a contextual predictive language model. A future comprehensive orthographic coverage audit and trained next-word/morphology evaluation are separate requirements.

This distinction prevents a falsely '100% complete' badge even though the **implemented database pipeline, bootstrap and deployment** are production-operational for the imported material.

Attribution: Thesaurus Linguae Aegyptiae, Simon D. Schweitzer and contributors (AED), KELLIA Comprehensive Coptic Lexicon (BBAW/DDGLC), Coptic SCRIPTORIUM. Reuse follows the respective published CC BY-SA permissions and acknowledgments.
