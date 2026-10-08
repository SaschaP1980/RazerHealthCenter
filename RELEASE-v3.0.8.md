# Razer Synapse + Chroma Health Center v3.0.8

## Scope
v3.0.8 fixes a false-positive AppEngine runtime health classification found in a real healthy post-recovery Windows session.

## AppEngine diagnostic 1.0.2
- `win-synapse` and `win-chroma-app` dashboard renderers are transient supporting evidence and are no longer required for HEALTHY.
- HEALTHY now requires the validated full Synapse+Chroma Run contract, one unambiguous versioned main runtime using that contract, systray, background manager, lighting engine and generic `win-usb_*_mw` device middleware.
- No PID/product identity is inferred from middleware names.
- Missing systray still prevents HEALTHY and keeps the previously observed real broken state detectable.
- PS5.1-safe native arrays from diagnostic 1.0.1 remain unchanged.
- Read-only semantics remain unchanged.

## Unchanged
Registry64/Registry32 product registration, repair catalog, explicit confirmation requirement, recipe-specific elevation, AppEngine recovery payload, Chroma repair and all historical/archive UI semantics are unchanged.
