# Release v2.2.0

v2.2.0 introduces the persistent read-only Setup & Device Inventory architecture.
The Setup view is inserted above Status. A valid inventory is mandatory before a
health run; first health requests automatically route through Setup and continue
only after a valid profile is created.

The Setup scanner inventories Razer VID_1532 PnP endpoints, historical alternate
connection paths, DriverStore INF associations, RzDev/RzCommon service names and
observed logical product IDs without changing Windows/Razer state. The profile is
stored as `Setup/RazerDeviceInventory-v1.json` and exported with diagnostics.

Health Engine 1.4.0 removes the old hardcoded BlackWidow PID 02C9/PID 02CC,
RzDev_02c9/RzDev_02cc and logical product 716 requirements from active health
logic. Gates 2-6 and Gate 12 now consume the setup inventory. Gate 4 is renamed
to `Razer Geräte Live-PnP` and validates at least one active known connection
path for each required inventoried product.

INFO presentation is now cyan and explicitly informational; the normal detail
view no longer implies a Soll requirement for INFO findings.

Repair Engine 1.0.0 and the narrow Gate-8 UAC repair policy are unchanged.
Synapse/Chroma version monitor semantics from v2.1.2 are unchanged.
