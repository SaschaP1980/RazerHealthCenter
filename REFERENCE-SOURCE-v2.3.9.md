# Reference Source v2.3.9

Canonical source baseline for Razer Synapse + Chroma Health Monitor v2.3.9.

v2.3.9 is based on v2.3.8 and changes only the SETUP connection presentation plus
version/release/validation metadata. When a connection has a learned medium/high
confidence role, the SETUP table renders `Typ · PID` instead of `PID · Typ`.
Connections inside a product row are sorted as wired USB, wireless dongle, then
unknown/generic, with a deterministic PID tie-break.

The complete currently present typed entry keeps the existing Acid-Green live
presence color. Unknown/untyped connections remain PID-only and are never assigned
a guessed role. No product/PID-specific production rules are introduced.

Health Engine 1.4.5, Setup Scanner 1.0.6, native SetupAPI Live Probe 1.1.0, Repair
Engine 1.0.0, inventory/history schemas, guided-learning semantics and Healthcheck
selection semantics are unchanged from v2.3.8.

A dedicated connection-presentation validator is included in `build.sh`; it is
RED on the exact canonical v2.3.8 source and GREEN on v2.3.9.
