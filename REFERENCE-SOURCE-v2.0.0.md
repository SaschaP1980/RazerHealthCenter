# Canonical Reference Source — v2.0.0

Effective with v2.0.0, this complete source snapshot is the authoritative
reference for future development.

v1.8.1 and the Golden/recovered v1.7.0 line remain historical references only.

New canonical invariant: diagnostics and repairs are separate execution modes.
Health Engine 1.3.5 remains read-only; system mutation is only possible through
an explicitly confirmed, elevated, gate-specific repair allowlist.

Initial repair capability:

- Gate 8: Chroma Dienste
- Repair Engine: repair-chroma-services-v1.0.0.ps1
- Allowed mutation: Start-Service only for Razer Chroma SDK Service and
  Razer Chroma SDK Server, and only under the documented eligibility pattern.
- Repair audit: Diagnostics/Repairs/*.json + *.log
- Diagnostic exports include current app-session repair artifacts.

All presentation text remains owned exclusively by locales/de-DE.json. No
language switching is implemented.
