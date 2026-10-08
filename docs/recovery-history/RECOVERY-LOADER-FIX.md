# Recovery loader fix — r2

The first recovered test executable was rejected by native Windows before the Go program started.

Root cause in the recovery build process: the first resource injector copied the golden `.rsrc` section at the original v1.7.0 RVA into the smaller reconstructed image. Although the resulting PE passed basic static parsing, that layout was not accepted on the native Windows test host.

Recovery revision r2 changes only the PE resource-placement mechanism:

- `.rsrc` is placed at the next section-aligned RVA after the reconstructed image.
- `IMAGE_RESOURCE_DATA_ENTRY.OffsetToData` fields are relocated by the exact RVA delta.
- All 11 resource payloads (manifest/icon resources) remain SHA-256-identical to Golden v1.7.0.
- A new PE/resource structural validator runs on every build.

This does not claim native Windows success until the r2 binary is actually tested on Windows.
