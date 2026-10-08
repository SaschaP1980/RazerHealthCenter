# Reference Source v3.0.5

Canonical base: Razer Synapse + Chroma Health Center v3.0.4.

v3.0.5 adds the Health Center application-registration guard without modifying Health Engine 1.4.6. The final app-level result now composes official Razer prod-manifest registration evidence with the base engine result. Unreadable manifest-defined Synapse/Chroma product registration turns a base PASS AppEngine gate into UNKNOWN and the final overall result into UNCLEAR. Version differences remain INFO-only and manifest/network unavailability has no Health impact.

New source: `health_application_guard.go`.
New measurement artifact: `ApplicationHealthAssessment-<stamp>.json`.
New build gate: `tools/validate_v305_false_green_guard.py`.
