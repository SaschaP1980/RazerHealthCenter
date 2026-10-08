# Source provenance

1. Canonical behavioral/build reference: RazerHealthMonitor v1.7.0.
2. Original source path recovered from DWARF: `/mnt/data/rhm165src/main.go`.
3. The original source file content was not present in the handover/Library.
4. Recovery inputs used:
   - v1.7.0 Portable ZIP supplied by the user;
   - Go PE symbol table and compressed DWARF sections;
   - Go `embed.FS` runtime layout and `main.embedded.files` data;
   - exact PE `.rsrc` section;
   - canonical handover/runbook rules;
   - v1.7.0 i18n catalogs.
5. Reconstructed Go source is explicitly marked recovered and must not be
   represented as the byte-for-byte original source.
