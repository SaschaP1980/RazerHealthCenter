# Canonical Source Reference v2.1.2

v2.1.2 supersedes v2.1.1 as the active source/development baseline.

Local Synapse/Chroma public-version derivation is now based only on local,
product-specific evidence. For the exact top-level dashboard metadata, Razer's
observed raw `0.0.<product>` version is combined with the leading major of the
active local RazerAppEngine `app-X.Y.Z` package and the dashboard's own
`buildVersion`. Example: AppEngine `4.0.699` + Synapse `0.0.86` +
`2608311115` -> `4.0.86.2608311115`. The same rule yields Chroma
`4.0.63.2608271424` from raw `0.0.63` + `2608271424`.

The online Razer release is never used to synthesize the local value; it is an
independent informational comparison only. Generic uninstall DisplayVersion
values, AppEngine FileVersion and module metadata remain excluded from the
public product-version comparison. Invalid or incomplete local evidence yields
`UNKLAR`.

`VersionStatus` schema 3 records the raw product version, buildVersion and
derivation method in addition to the derived public release and source path.

Health Engine 1.3.6, Repair Engine 1.0.0, the 13-gate health model, the v2.1.1
Info footer layout, de-DE-only i18n policy and the delivery contract remain
unchanged.

This complete Source ZIP is the canonical reference for all future development.
