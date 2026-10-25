# Hieroglyphic Keyboard + Lexicon

Owns the Late Egyptian source-pinned, native Unicode prediction engine,
hieroglyphic sign catalog, and canonical SQLite/JSON spelling database.
Renpet and MdwNfr consume versioned copies of these assets, never
write to the source lexicon. Input remains separate from application
text-composition and page-layout systems.

The initial migrated release is verified against the original
`aaa` source and its SHA-256 manifest. See SOURCE_PROVENANCE.json.
