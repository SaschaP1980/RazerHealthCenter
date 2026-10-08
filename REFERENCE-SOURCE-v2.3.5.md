# Reference Source v2.3.5

Canonical source baseline for Razer Synapse + Chroma Health Monitor v2.3.5.

The performance change replaces the production live PowerShell probe with native Windows SetupAPI enumeration in `device_monitor.go`. The active `setup/` runtime directory contains only the full Setup Scanner 1.0.6; the previous live PowerShell probe is retained solely as historical documentation under `docs/setup-history`.

Known-connection live refresh remains PID-free in semantics: observed PIDs are runtime data, and a current PID is accepted only when the present physical USB root reports a BusReportedDeviceDesc whose normalized productKey matches the stored product. Guided learning uses the same native target-product probe and preserves exact-delta/fail-closed semantics.
