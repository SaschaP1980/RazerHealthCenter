# Canonical Source Reference v2.1.0

v2.1.0 supersedes v2.0.1 as the active source/development baseline.

New diagnostic/version semantics:

- Health Engine: 1.3.6, still 13 gates and read-only.
- AppEngine package version and FileVersion are collected as separate INFO
  values; no cross-domain baseline warning.
- Installed Synapse/Chroma public versions are read from Windows uninstall
  DisplayVersion metadata when available.
- Latest stable Synapse/Chroma versions are read asynchronously over HTTPS from
  official Razer Insider release pages.
- Online version availability does not participate in overall health status.
- Version status is exported as a session diagnostic artifact.

Repair Engine 1.0.0 and its narrow Gate-8 safety model are unchanged.

This complete Source ZIP is the canonical reference for all future development.
