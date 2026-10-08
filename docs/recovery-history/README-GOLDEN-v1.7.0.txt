Razer Synapse + Chroma Health Monitor v1.7.0
=============================================

Windows x64 diagnostic application.

BASELINE
--------
v1.7.0 is based on the stable v1.6.8 behavior and Health Engine 1.3.5.

CHANGES IN v1.7.0
-----------------
- Internationalization (i18n) preparation introduced.
- A stable UI key catalog has been defined for the complete presentation layer.
- German remains the default/active language in v1.7.0.
- German (de-DE) and English (en-US) catalogs are included in locales\.
- Dynamic texts use named placeholders; plural-ready strings use .one/.other keys.
- Technical/machine-readable values such as PASS, WARN, FAIL, UNKNOWN and INFO,
  JSON field names and progress protocol records remain language-neutral.
- Product/technical identifiers remain unchanged.
- This release intentionally does not expose the language selector yet; the
  translation catalogs are prepared first so terminology can be validated.
- Existing diagnostics, historical measurement handling, severity logic,
  popovers, export behavior, icon resources and UI-thread fixes are retained.

I18N
----
See README-I18N.txt and i18n-manifest.json.
Catalogs:
- locales\de-DE.json
- locales\en-US.json
