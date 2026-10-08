# RHC-6 — Product name, application icon and brand-color review

**Review status (2026-10-08):** Evidence-based technical/visual first-pass **COMPLETE**. Trademark/legal clearance **NOT CLAIMED**. Scope is the frozen source baseline RHC **v3.0.8**, GitHub draft [PR #7](https://github.com/SaschaP1980/RazerHealthCenter/pull/7), head `d8a3275c0c70783553ef155fff3627e83211e9f5` at review entry. No installed Windows application was used in this review.

## Executive result

| Element | Observed evidence | Risk judgement (not legal conclusion) | Proposed action |
| --- | --- | --- | --- |
| Green/black visual palette | Maintainer expressly requested a Razer-inspired color scheme; visible icons use green on dark background | Low to moderate on colors **alone**; overall trade dress still needs holistic review | **Retain** the current palette pending actual product branding decision |
| Main RHC app icon | `assets/app-heart.ico` renders as a luminous **heart** with green highlights, **not** the Razer triple-headed snake emblem or Razer wordmark | Low for direct logo copying within inspected icon; residual similarity questions cannot be categorically excluded | **Retain** existing heart icon for now, no replacement generated or published |
| Embedded EXE Windows icon | `resources/app_rsrc.bin` contains ten PNG image payloads, all **byte-identical** to the ten frames of `assets/app-heart.ico` | No hidden alternative snake logo in the embedded icon frames | Retain resource bytes unchanged |
| Status icons | `assets/idle.ico` monochrome heart, `assets/passed.ico` neon-green heart; visual first-pass sample | No Razer snake/wordmark in these inspected icons | Retain; no icon mutation |
| Generic UI icons | Inspected the green representative from 16 `assets/ui/` families: Chroma services, DriverStore, filters, game manager, kernel, keyboard, lamp array, nav info/logs/setup/status, power, registry, rzcom, Synapse services, virtual | Generic symbols (monitor, keyboard, chip, lamp, heartbeat, etc.); no clear triple-headed-snake graphic visible | Retain for now. Red/muted/warning color variations and full trade-dress similarity have **not** been individually legally cleared |
| Product naming/primary branded text | Current product and repository prominently use `Razer`; `RAZER SYNAPSE + CHROMA` is used as the primary in-app branding text | **Higher potential confusion / trademark risk** than colors or heart icon | **Change to an independent primary brand before first public signed/unsigned release**, subject to owner naming approval and conflict check |
| Descriptive compatibility references | Diagnostic strings refer to Razer Synapse, Chroma, devices and services, and a disclaimer already says unofficial | Can be necessary to explain what is being diagnosed; placement/presentation matters | **Keep accurate descriptive names**, separated from the app's own brand/title; retain/improve the existing non-affiliation notice |

## Exact reviewed file identities and icon extraction method

All files were fetched from the exact RHC-6 Draft PR head noted above; no original files were edited during review.

- [`assets/app-heart.ico`](../assets/app-heart.ico), Git blob `43ce2d216736bc2fdc77de0327fc991be20074dc`: actual ICO frame sizes `16,20,24,32,40,48,64,96,128,256` pixels, 10 PNG payloads. Extracted and visually inspected the 256px embedded PNG.
- [`resources/app_rsrc.bin`](../resources/app_rsrc.bin), Git blob `a53ebecc76ca7a6b3a99ee8a7b71bd778f8830d4`: independently parsed PNG chunk framing and confirmed **10/10 embedded PNG payloads exactly match the source ICO frames byte-for-byte**, including 256px.
- [`assets/idle.ico`](../assets/idle.ico), Git blob `115c6c2f1c812a5b38c0511b37f370ac3f19d445`, and [`assets/passed.ico`](../assets/passed.ico), Git blob `36e6fd94d2a142c4983e072c4e4b5035c1754ee2`: 256px icon frames visually inspected.
- Reviewed one 128px green frame each from the following 16 named UI icon families: `chroma-services`, `driverstore`, `filters`, `game-manager`, `kernel`, `keyboard`, `lamparray`, `nav-info`, `nav-logs`, `nav-setup`, `nav-status`, `power`, `registry`, `rzcom`, `synapse-services`, `virtual`. This is **16/16 green-family representatives**, **not** a declaration about every color variant or any uninspected artwork.

## Existing name/branding usage confirmed in source

| Surface | File and observed source | Why it matters |
| --- | --- | --- |
| Windows title / app name | [`locales/de-DE.json`](../locales/de-DE.json): `app.title = "Razer Synapse + Chroma Health Center"`; `model.go` uses `tr("app.title")`; `ui.go` builds the window title | Appears as the actual product/app identity |
| Uppercase primary wordmark-like header | `locales/de-DE.json`: `app.brand.primary = "RAZER SYNAPSE + CHROMA"`, secondary `"HEALTH CENTER"` | Large, front-facing prominent Razer branding — not merely a compatibility notice |
| Other UI headings | `app.header`, `info.app_title`, and descriptive support text mention Synapse and Chroma | Distinguish neutral app label from accurate target-software references |
| Windows tray tips | `locales/de-DE.json` keys `tray.tip.checking`, `failed`, `healthy`, `incomplete`, `unchecked` all use `Razer Health Center` | User-visible product identity outside the main window |
| Windows downloadable filename | `tools/rhc_release_contracts.py` and `build.sh` produce/refer to `RazerHealthCenter.exe`; future Source/Portable ZIPs include this name | Product identity on downloaded binaries and in release notes |
| Repository slug and documentation | `SaschaP1980/RazerHealthCenter` and root README use Razer as part of app/project name | Can suggest an official product to GitHub visitors |
| Win32 internals | `win32.go` classes prefixed `RazerHealthMonitor`; single-instance mutex `Local\RazerSynapseChromaHealthMonitor.SingleInstance` | Internal identity/stability; **do not rename mechanically** without native Windows regression and migration plan |
| Existing non-affiliation notice | `locales/de-DE.json` has `info.disclaimer`, `info.disclaimer.independent`, `info.disclaimer.trademarks` | Positive and should remain, but placed in Information and does not turn a prominent Razer-like primary brand into an authorized one |

## Trademark and brand comparison

Razer describes its corporate symbol as the **triple-headed snake**; its [official trademark-use guidelines](https://www.razer.com/sg-en/legal/trademark-use-guidelines) permit referring to Razer products/services but limit independent use of Razer marks and warn against misleading affiliation. The [Razer API Terms](https://www.razer.com/de-de/legal/razer-api-terms-of-use) additionally restrict use of Razer marks as a developer's own logo or product/service name in the context of that API agreement; **do not assume these specific API terms govern RHC unless RHC actually uses that licensed API**.

This first-pass icon review found **a heart, not Razer's triple-headed-snake logo**. The stronger issue is **prominent use of the Razer word mark as the app's own brand**. This is a risk-based recommendation rather than a judicial determination of infringement or assurance of noninfringement. The existing Razer-inspired color palette is not automatically forbidden, but the entire presentation may require a more specific trade-dress review.

## Recommended naming decision before any product version changes

Select a genuinely independent primary name **without** `Razer`, `Synapse` or `Chroma` as the product-brand token. **Working candidate, not trademark-cleared:** `Peripheral Health Center`. A generic alternative is `Peripheral Runtime Health Center`. Neither candidate has been independently searched for conflicts/availability; **owner selection and name search are still required**.

Describe compatibility **separately**, e.g. `Unoffizielles Diagnosewerkzeug für Razer Synapse und Razer Chroma`, alongside an always-accessible non-affiliation/trademark notice.

Only in an **explicitly approved future product-brand migration issue**:
1. Confirm independent primary project/product name and repository slug after name conflict review.
2. Change `app.title`, `app.brand.primary/secondary`, tray tooltips, about text, README, ZIP/EXE names and relevant build/release checks **together**.
3. Evaluate Win32 class names/mutex and local persisted user data for backward compatibility; no blind global replacement and no hidden data loss.
4. Build/test hosted Linux and real Windows PowerShell 5.1 and native UI/single-instance/upgrade paths; update asset/manifest contracts and product version only by a separately authorized version change.
5. Review project branding again as a **whole visual presentation**; preserve green/black colors and heart icon unless new evidence requires revisiting them.

**Current outcome:** naming decision remains **BLOCKED waiting for owner**, icon and palette **provisionally retained**, GPL Draft PR **remains DRAFT**, and `config/rhc-release-policy.json.productionEnabled=false`. No public release or SignPath application was created.

## Review limitations

This is a technical/visual review of repository assets and source identifiers, not a live Windows GUI screenshot/installer test, trademark-registration search, complete third-party copyright audit, actual Razer endorsement check or legal opinion. All conclusions are bounded to the inspected Git blobs/strings. No assumption that all historical or bundled icons were individually inspected.

