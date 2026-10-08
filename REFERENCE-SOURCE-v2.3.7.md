# Reference Source v2.3.7

Canonical source baseline for Razer Synapse + Chroma Health Monitor v2.3.7.

This release adds persistent per-product Healthcheck participation while
preserving the v2.3.6 Guided Learning correction and the v2.3.5 native SetupAPI
connection-refresh architecture.

The SETUP product rows are explicit Healthcheck selectors. `required=true`
means the product participates in the next Healthcheck; `required=false` excludes
its product-specific requirements. The preference is app-owned, persisted in
`Setup/RazerDeviceInventory-v2.json`, restored at restart, and merged across later
full Setup scans for recognized products. New products retain scanner default
`required=true`. Live PID/role presence remains independent from selection.

Health Engine 1.4.4 consumes only required products and their relevant
connections. Because schema 2 stores `logicalProductIds` globally rather than per
product, Gate 12 treats that field as informational during partial product
selection rather than allowing an excluded product to affect the assessment.

Changing product selection immediately invalidates the current dashboard result
to UNGEPRÜFT without deleting historical measurements. If no product is active,
Setup scan and Healthcheck start are blocked and the app shows an in-window
notice. The setup rows expose a hover state and active/inactive icon/status
colors, while live connection coloring stays independent.

Guided Learning additionally exposes `Gerät überspringen`, distinct from the
existing per-step `Überspringen`: it advances to the next product and leaves any
already learned role intact. The Setup action-card subtitles are shortened to fit
the existing card geometry.
