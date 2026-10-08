# v1.8.1

Runtime layout maintenance release.

- Restores a structured ephemeral `Runtime` tree.
- Health Engine remains directly in `Runtime/`.
- Extracted icon assets now preserve the source hierarchy under `Runtime/assets/`, including `status/` and `ui/`.
- UI icon loading, startup hash diagnostics and packaging were updated to the structured paths.
- No Health Engine, gate logic, i18n behavior or read-only semantics changed.
