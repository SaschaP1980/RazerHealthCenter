# Reference Source v2.3.6

Canonical source baseline for Razer Synapse + Chroma Health Monitor v2.3.6.

This release corrects Guided Connection Learning while preserving the native v2.3.5 SetupAPI live-presence architecture. Wireless learning is now interaction-aware without product/PID hardcoding: generic mouse profiles remain event-driven because cable removal can be the complete intended transition, while keyboard and unknown profiles require explicit user confirmation before a permanently present receiver may be committed as the Wireless connection.

The explicit confirmation path performs a fresh native target-product probe, requires current verified product identity, rejects a still-present learned wired path, and persists the distinct source `user-guided-wireless-confirmation`. The Windows device-change event itself remains only a trigger and cannot auto-complete the confirmation state.

Guided completion no longer launches the full PowerShell Setup scanner. Learned roles are written directly to Connection History and existing inventory entries; newly discovered PIDs that still require full driver/topology/capability materialization are reported as an advisory for a later manual Setup scan.
