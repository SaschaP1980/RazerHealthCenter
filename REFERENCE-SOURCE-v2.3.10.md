# Reference Source v2.3.10

Canonical source baseline for Razer Synapse + Chroma Health Monitor v2.3.10.

v2.3.10 is based on v2.3.9 and restructures only Guided Connection Learning plus
version/release/validation metadata. Each connection type now follows the explicit
state sequence Start -> Action/Wait -> Success -> Acknowledge. Physical instructions
are withheld until the native target-product baseline has been armed, preventing a
user from performing the transition before the detector is ready.

Successful USB and Wireless learning no longer advances immediately. The committed
role and PID are retained in the wizard and displayed as a success result until the
user presses `Weiter`. USB then enters the Wireless prompt; Wireless then advances to
the next product or normal completion. Existing `Gerät überspringen` and per-step
`Überspringen` semantics remain available where appropriate.

The generic device-class Wireless distinction from v2.3.6 is preserved: mouse
profiles remain event-driven, while non-mouse profiles use explicit user confirmation
when needed. There are no product-name or endpoint-PID rules.

Health Engine 1.4.5, Setup Scanner 1.0.6, native SetupAPI Live Probe 1.1.0, Repair
Engine 1.0.0, inventory/history schemas, Healthcheck selection, live connection
presentation and Gate semantics are unchanged from v2.3.9.

A dedicated `validate_guided_ux_v2310.py` contract is included in `build.sh`; it is
RED on exact canonical v2.3.9 and GREEN on v2.3.10.
