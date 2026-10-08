# RHC — Approved product branding

**Owner-approved branding decision:** 2026-10-08. **Status:** binding presentation contract; **not yet applied to the frozen 3.0.8 application**. Future implementation is tracked in [RHC-8](https://github.com/SaschaP1980/RazerHealthCenter/issues/8). The brand-name and trademark-conflict review remains an independent publication gate.

## Exact approved text (verbatim)

### Full heading

# Peripheral Health Center – for Razer Synapse & Chroma

### German descriptive subtitle

*Inoffizielles Diagnosewerkzeug für Razer Synapse und Razer Chroma*

### German independence notice

Unabhängiges Open-Source-Projekt. Nicht mit Razer Inc. verbunden, von Razer autorisiert oder unterstützt.

The spelling **Inoffizielles** is intentional and supersedes the previously proposed **Unoffizielles** wording.

## Brand hierarchy

- **Independent primary app/project brand:** `Peripheral Health Center`.
- **Compatibility descriptor shown with the approved full heading:** `for Razer Synapse & Chroma`. Razer, Synapse and Chroma identify supported third-party software and must not appear as the independent publisher or brand.
- **German subtitle:** show the approved German descriptive subtitle without substituting a variant.
- **Independence/trademark note:** display the exact approved German note in the Information/About surface and on public product description/download surfaces where applicable; retain appropriate notices for third-party marks. An independence notice is not itself a trademark license.
- **Visual identity:** retain the existing neon-green/black palette and the existing green heart icon (`assets/app-heart.ico`), including its 10 identical PNG frames embedded in the Windows PE resource. No new icons, source redesign or new color palette requested.
- **License intent:** `GPL-3.0-or-later`, subject to the focused GPL PR and remaining provenance/rights checks. This text is not authorization to sign or publish.

## Implementation mapping for a separately authorized future product version

| Surface | Future contract | Authority / caution |
| --- | --- | --- |
| Main window and About heading | `Peripheral Health Center – for Razer Synapse & Chroma`; main independent brand prominent, compatibility descriptor subordinate in visual hierarchy | `locales/de-DE.json`: `app.title`, `app.brand.primary`, `app.brand.secondary`, `app.header`, `info.app_title` |
| Description/subtitle | `Inoffizielles Diagnosewerkzeug für Razer Synapse und Razer Chroma` | User-facing localized text; don't broadly rewrite diagnostic component names |
| Non-affiliation | Exact owner-approved German sentence above, with informative trademark text | `info.disclaimer`, `info.disclaimer.independent`, `info.disclaimer.trademarks`; UI and distribution |
| Tray/status/window title | Neutral independent product identity; accurate Razer software references only as description | `app.title`, `app.window_title`, `tray.tip.*` |
| Executable/package/installer branding | Coordinate future naming with release packaging and reproducibility verification | Current `RazerHealthCenter.exe` is **historical v3.0.8 authority**, not yet renamed |
| README/GitHub display/repository slug | New brand, compatibility notice and official independence statement | The repository is currently `SaschaP1980/RazerHealthCenter`; **do not rename automatically** |
| Win32 class/mutex IDs, persisted app state, safety scripts | Explicit characterization / migration plan before any change | Current `RazerHealthMonitor*` classes and single-instance mutex are internal; blind replacement can break compatibility |
| App icon and colors | Preserve precisely | [BRAND_AND_ICON_REVIEW.md](BRAND_AND_ICON_REVIEW.md) records actual frame evidence |

**Release safety:** no modification to v3.0.8 `model.go`, source bytes, current Windows EXE, reference hashes, shipped ZIPs, app icon or embedded resources is implied by this contract. `productionEnabled=false`, `signingDecision=unknown`, `rollbackVerified=false` remain mandatory until separate, proven acceptance and per-version release authorization. An authorized future product-version migration must pass exact-SHA Linux/Windows CI, native UI/tray acceptance and release/rollback checks before publication.

## Trademark caveat

The owner selected this presentation and the descriptive word `for` to separate RHC from the third-party vendor. This selection **does not constitute a trademark clearance or guarantee of noninfringement**. Independently verify the selected name and overall presentation, including possible prior users of `Peripheral Health Center`, against relevant registers and Razer's [trademark guidelines](https://www.razer.com/sg-en/legal/trademark-use-guidelines). The use of `for Razer Synapse & Chroma` in the **full heading** should remain subordinate to the independent brand; inaccurate implied affiliation is unacceptable.

## Provenance

- [RHC-6](https://github.com/SaschaP1980/RazerHealthCenter/issues/6): GPL-3.0-or-later, open-source provenance, green heart / palette / trademark review
- [RHC-8](https://github.com/SaschaP1980/RazerHealthCenter/issues/8): eventual versioned product UI/runtime/packaging rename and native acceptance
- [Draft PR #7](https://github.com/SaschaP1980/RazerHealthCenter/pull/7): documentation of exact selected wording, without releasing or modifying v3.0.8 runtime
