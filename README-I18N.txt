Razer Synapse + Chroma Health Center v3.0.1 - i18n contract

Runtime locale
--------------
The application intentionally has NO language switch in v3.0.1.
The only active runtime locale is de-DE.

Single source of truth
----------------------
Every presentation-owned visible UI string, including diagnostic/problem/repair
and version-check presentation, is maintained in:
  locales/de-DE.json

Go rendering, tray, modal and user-facing error code must reference i18n keys.
New visible presentation text must never be added as a Go string literal.
The v3.0.1 catalog contains 371 presentation keys.

Technical boundary
------------------
Machine-readable JSON field names, protocol values, technical status codes, URLs,
service/product identifiers, problem IDs, repair IDs, audit field names and
diagnostic evidence remain technically stable and are not presentation
localization strings.

Future languages
----------------
A future language implementation must add a new catalog with the same key and
placeholder contract. It must not move presentation text back into Go code.
