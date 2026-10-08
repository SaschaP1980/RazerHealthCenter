# Release v2.3.10

- App: 2.3.10
- Health Engine: 1.4.5 (unchanged)
- Setup Scanner: 1.0.6 (unchanged)
- Fast Setup Live Probe: 1.1.0 native SetupAPI (unchanged)
- Repair Engine: 1.0.0 (unchanged)
- Device Inventory schema: 2
- Connection History schema: 2
- VersionStatus schema: 3
- ExportManifest schema: 4
- Runtime locale: de-DE, 348 UI keys

## Guided Connection Learning UX

The guided learning flow is now explicitly staged per connection type:

1. **Start** – neutral explanation and explicit detector-start button. No physical
   cable/switch instruction is shown before the baseline is armed.
2. **Action / wait** – after a successful native target-product baseline, the wizard
   tells the user what to do physically and shows a separate waiting status.
3. **Success** – a uniquely learned role is persisted and shown as a clear success
   result, including the concrete `Typ · PID`. The wizard does not advance yet.
4. **Acknowledge** – only `Weiter` advances from USB to Wireless or from Wireless to
   the next product / completion.

USB starts as `1. USB-Verbindung erkennen` with `USB-Erkennung starten`. After the
baseline is ready, the action copy asks the user to connect USB and, if present, set
the device to wired mode. Success shows `USB-Verbindung erfolgreich erkannt.` plus
`USB-Kabel · PID`.

Wireless mirrors the same model. Mouse profiles retain the event-driven transition
where cable removal itself may establish Wireless. Non-mouse profiles retain the
explicit `Wireless prüfen` path so a permanently present dongle is not treated as
proof of peripheral mode. Both paths stop at `Wireless-Verbindung erfolgreich
erkannt.` plus `Wireless-Dongle · PID` and wait for `Weiter`.

Existing step-skip and device-skip semantics are retained. Device skip is available
from success states and does not roll back a role already committed in the session.

## Regression contract

`tools/validate_guided_ux_v2310.py` is part of `build.sh`. Against the exact
canonical v2.3.9 source it is RED (2/20); against v2.3.10 it is GREEN (20/20).
The contract covers neutral pre-baseline prompts, separate action/wait copy, explicit
success stages, retained concrete success result, acknowledgement-only advancement,
and preservation of the mouse/non-mouse Wireless semantics.
