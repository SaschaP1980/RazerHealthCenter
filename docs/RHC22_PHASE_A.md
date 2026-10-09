# RHC-29: autonome Phase-A-QA (Phase B bleibt gesperrt)

**Owner-Auftrag 2026-10-08:** „Wir setzen Phase A um, Phase B bleibt deaktiviert, bis wir etwas anderes vereinbaren.“

Dies ist ein **technischer, nichtpublizierender QA-Pfad**, ausdrücklich kein erster Produktrelease. Die unverändert bindenden externen Freigaben stehen in [RHC-22](https://github.com/SaschaP1980/RazerHealthCenter/issues/22). Eine automatisierte Linux-/Windows-Prüfung und ein QA-Artefakt ersetzen **keine** echte Razer-Geräteabnahme, echten Rollback oder ausdrücklich vom Owner erteilte Windows-Signing-/Unsigned-/Produktionszustimmung.

## Autonomer Durchlauf

Die [Phase-A-Workflowdatei](../.github/workflows/rhc-phase-a-qa.yml) wird bei relevanten Pull Requests, jedem neuen Push auf `main` sowie dem genehmigten `work/RHC-29` automatisch gestartet; nach Aufnahme der Datei auf `main` ist zusätzlich ein manueller `workflow_dispatch` möglich. Der Betrieb erfordert keine Aktion des Owners.

1. **Linux:** Checkout der exakten Quell-SHA, isolierte Regressionstests und aktuelle Download-Katalogprüfung; nur `productionEnabled=false`, `signingDecision=unknown` und `rollbackVerified=false` werden akzeptiert. Zwei unabhängige Go/PE-Builds mit `build.sh` werden byteidentisch verglichen. `tools/rhc_phase_a_qa.py stage` erstellt außerhalb des Quellverzeichnisses ein sieben Dateien enthaltendes Lean-ZIP und ein eigenes `qa-evidence.json`. Ein unabhängiges `verify` prüft Quelle, Version, ZIP-Bytes, interne Checksums und das unveränderlich gesperrte Phase-B-Ergebnis. Der historische `downloads/qa`-Stand bleibt byteidentisch.
2. **Temporäre Übergabe:** Ein nur eintägiges GitHub-Actions-Zwischenartefakt trägt bereits im Namen `INTERNAL-NOT-RELEASE`; dies ist technische Runner-Übergabe und **noch kein abschließend bestandenes Windows-Gate**. Es ist trotz dieser Kennzeichnung im Actions-UI für Berechtigte möglicherweise sichtbar; niemals als freigegebenen Build weitergeben.
3. **Native Windows 2025:** Der zweite Job prüft die exakt gleichen QA-ZIP-Bytes und die manifestgebundene SHA, verlangt Windows PowerShell **5.1**, parst Razer-PS-Skripte, führt `go test`, `go vet`, Diagnose-, Recovery- und Repair-Safety-Validatoren aus und prüft die **tatsächliche im Linux-Build erzeugte EXE** mit `Get-AuthenticodeSignature`. Für das als Test/Unsigned gekennzeichnete ZIP ist der Status `NotSigned` erforderlich; dies ist eine **technische Statusmessung**, keine SmartScreen-Risikoakzeptanz.
4. **Abschluss nur bei 2/2 GREEN:** Ein nachgeschalteter Linux-Job prüft Archiv/Manifest und gesperrte Release-Policy erneut. Erst danach erstellt er ein sieben Tage aufbewahrtes Actions-Artefakt `RHC29-TEST-UNSIGNED-NOT-RELEASE-<sourceSHA>`. Dessen Nutzinhalt sind ausschließlich das schlanke sieben-Dateien-Portable-Test-ZIP und die separate maschinenlesbare `qa-evidence.json`. Das Artefakt ist **kein GitHub Release**; es wird nicht dauerhaft unter `main/downloads/` eingetragen.

## Maschinenlesbare Evidence-Semantik

Die Manifestdaten binden `version`, exakte `sourceSha`, ZIP-Namen, ZIP-SHA-256, ZIP-Bytegröße, exakt sieben Payload-Namen sowie EXE-SHA-256. Die Paket-Checksummen werden unabhängig durch `tools/rhc_downloads.py` geprüft. Der Code verlangt einen checkout-verifizierten exakten Git-Commit, eine gesperrte Produktionspolicy, zwei identische externe PE-Builds und einen externen **noch nicht existierenden** Stagingordner (kein blindes Überschreiben nach unsicherem Runnerzustand).

Die folgenden Phase-B-Werte sind fest verdrahtet und werden beim unabhängigen Nachlesen **exakt** verlangt:

| Phase-B-Evidenz | Einzig erlaubter Manifestwert |
| --- | --- |
| `status` | `DISABLED` |
| `hardwareAcceptance` | `NOT_VERIFIED` |
| `rollback` | `NOT_VERIFIED` |
| `ownerTrustApproval` | `NOT_AUTHORIZED` |
| `productionRelease` | `BLOCKED` |
| `githubRulesetAdministration` | `NOT_MODIFIED` |

`nativeWindowsEvidence=SEE_EXACT_SHA_ACTIONS_RUN_NOT_HARDWARE` verweist bewusst auf den **wirklichen GitHub Actions-Lauf** statt einen fiktiven Hardwaretest einzutragen. Die Windows-Prüfung muss über die zugehörigen Job-Ergebnisse/Logs unabhängig nachvollzogen werden. Die Manifestdaten dürfen weder externe Owner-Entscheidungen treffen noch einen späteren RHC-22-Release automatisch freischalten.

## Explizit deaktivierte Phase B

Bis der Owner etwas anderes beauftragt, sind die folgenden Tätigkeiten **nicht Teil des Arbeitsauftrags**:

- Kein Zugriff auf physische Razer-Geräte oder auf das Windows-System des Owners; keine Geräte-/Repair-Mutation.
- Keine Behauptung nativer Hardwareabnahme oder eines dort ausgeführten Restore-/Rollback-Tests.
- Keine Authenticode-Zertifikatsbeschaffung, keine stellvertretende Unsigned-/SmartScreen-Einwilligung und keine Owner-Signoff-Kommentare auf RHC-22.
- Keine Änderung von `config/rhc-release-policy.json` oder Verwandlung fehlender Gate-Evidenz in PASS. Das produktive Stage-/Finalize-Hard-Gate bleibt vollständig aktiv.
- Keine administrativen GitHub-Main-Ruleset-Writes; erforderliche Owner-Admin-Aktivierung bleibt in RHC-22 OPEN.
- Kein `candidate/v*`- oder `release/v*`-Ref, kein Tag, kein GitHub Release, kein offizielles ZIP unter `main/downloads/`, keine Änderung des Katalogs und kein `downloads/latest.json`.

Die Phase-B-*Arbeit* ist deaktiviert; die **Produktionsschutzmechanismen werden nicht abgeschaltet**. Das Phase-A-Issue darf technisch abgeschlossen werden, während RHC-22 mit allen externen Checkboxen offen bleibt.

## Prüf- und Troubleshooting-Vertrag

Auf dem betreffenden SHA sind getrennt nachzuweisen: fokussierte `test_rhc_phase_a_qa_contracts.py`, native Windows-5.1- und Linux-Go-Buildresultate, zweifacher PE-/ZIP-Vergleich, realer Test-Artifact-Upload/Download, Rücklesen des SHA-256-Manifests, unveränderte historische QA- und Produkt-Downloads, und GitHub-hosted Pull-Request-Checks nach einem eigenständigen Work-Completion. Die Exit-Status `RED`, `SKIPPED`, `PENDING` oder ein Upload aus einer nur halbfertigen Matrix dürfen niemals als bestandene End-to-End-QA-Abnahme gelten.

**Testpaket abrufen:** Das jeweilige Actions-Run-Artefakt `RHC29-TEST-UNSIGNED-NOT-RELEASE-<SHA>` trägt im GitHub UI den Download. Die ZIP wird **einmalig** extrahiert. Vor lokalem Gebrauch sind SHA-256 und Quelle zu vergleichen. Keine SmartScreen-/Windows-Schutzmechanismen deaktivieren. Manuelle Tests auf Razer-Hardware zählen erst nach eigener kontrollierter Phase-B-Freigabe.

## Live-Qualifikation vor finaler PR-Übernahme (2026-10-08)

Auf dem vorläufigen vollständigen Work-Commit `951277e98a2965776ccf3ada9b4a507bb21ec127` wurde der **echte GitHub-Actions-Dreischritt** erstmals erfolgreich durchgeführt: [Phase-A #37851248540](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37851248540) mit Linux-Build/Test, nativer Windows-2025-/PS5.1-/Authenticode-Prüfung und finalem Actions-Artefakt jeweils SUCCESS. Die separate [Infrastruktur #37851248589](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37851248589) hatte Linux und natives Windows SUCCESS. Die fokussierten Phase-A-Vertragstests bestanden mit 6/6 auf Linux.

Die ausführlich manifestierte ZIP `RazerHealthCenter-Portable-v3.0.8.0-TEST-UNSIGNED-951277e98a29.zip` enthielt sieben erlaubte Dateien mit SHA-256 `f762e4427e95c092b659cb4470f420ba0ca2650676ff9de0c68aece1882e5a08` und EXE-SHA-256 `da141d5992625b19962973dd0a8cf829856edbe993cbb35e8bbbd8abf8c33872`. Das finale Testartefakt ist [GitHub Actions Artifact #11582256172](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37851248540/artifacts/11582256172), 8.621.437 Bytes, Ablauf 2026-10-15. Seine technische Prüfung ist **kein** RHC-22-Hardware-, Rollback- oder Windows-Owner-Vertrauensnachweis. Die vorherige RED-Testkontrakt-Verwechslung (`GITHUB_SHA` statt `SOURCE_SHA/github.sha`) wurde korrigiert; RED wurde nicht als Produktfehler ausgegeben.

**Wichtig:** Diese Messung gilt nur für den genannten exakt überprüften alten Work-SHA. Der nachfolgende final eingefrorene Work-Commit und der spätere PR-/Main-Merge müssen unabhängig ihre eigene GitHub-Evidenz erhalten; andere SHAs dürfen dieses Ergebnis nicht erben. Auch nach dem technischen QA-PR-Merge bleibt Phase B ausgesetzt und jedes produktive Release-Gate unverändert aktiv.

## RHC-31 — echtes v3.0.8.1-Candidate-Testpaket (Ergänzung Phase A)

**Problem:** Der RHC-29-Auto-`main`-QA-Workflow ist korrekt implementiert, baut aber die unveränderte Produktversion `3.0.8.0` aus `main`. Ein solcher Testbuild darf **nicht** in `3.0.8.1` umetikettiert werden. Der bereits unabhängig geprüfte Candidate `candidate/v3.0.8.1` hat den festen Quell-SHA `1b78ca928979e9507863a53ce2e4b25491544d5e` und enthält wirklich `appVersion=referenceVersion=3.0.8.1`. Da dieser Candidate von einem älteren Main abstammt, darf sein alter Preflight-Verlauf **nicht** als aktuelle Main-/Release-Ancestry-Freigabe gelten.

**Nichtpublizierende Lösung:** Die gesonderte [RHC-31-Workflowdatei](../.github/workflows/rhc-candidate-qa-v3081.yml) führt eine vollständig eigenständige Candidate-QA mit **zwei separaten Checkouts** aus. Checkout A ist das aktuelle, commitgebundene und getestete technische QA-Tooling aus der PR- beziehungsweise Main-SHA. Checkout B ist exakt der unveränderte Candidate-SHA, **aus dessen Quelle** die beiden Windows-PEs und sieben-Dateien-ZIPs tatsächlich gebaut werden. Die QA-Skripte laufen außerhalb des Candidate-Buildverzeichnisses; weder der produktive Source-Code noch die Candidate-Branch-Daten werden verändert.

Das neue [Gate-Skript](../tools/rhc_candidate_qa_gate.py) verlangt vor und nach dem Build: existierenden unveränderten Remote-Ref `candidate/v3.0.8.1`, SHA-identischen Candidate-Checkout, genau einen Version-only-Commit mit ausschließlich `model.go` und `CHANGELOG.md`, korrekte alte/neue Model-Versionen und `CHANGELOG.md`-Eintrag, sowie die drei echten, vom GitHub-Actions-Bot erfolgreichen Candidate-Statuskontexte `rhc/preflight/linux`, `rhc/preflight/windows` und `rhc/preflight/candidate`. Die ursprüngliche Candidate-Promotion blieb wegen fehlender Produktfreigabe absichtlich blockiert. Fehlende, später fehlgeschlagene oder gefälschte Statuskontexte blockieren auch die rein technische QA.

Der neue Workflow wird durch das erste qualifizierte Merge seiner eigenen Workflowdatei auf `main` automatisch **einmalig** gestartet (Push-Pfadfilter); wiederholbare Ausführung per `workflow_dispatch` bleibt möglich. Er muss auf Linux zwei unabhängige reale Candidate-Go-Windows-Builds/ZIPs byteweise vergleichen, den SHA-/ZIP-/Source-Testmanifestvertrag erfüllen, und auf gehostetem **nativem Windows 2025 / PowerShell 5.1** den übertragenen ZIP und die Authenticode-Statusanzeige `NotSigned` prüfen. Erst nach beiden erfolgreichen Jobs erfolgt der abschließende unabhängige QA-Artefakt-Upload `RHC31-TEST-UNSIGNED-NOT-RELEASE-v3.0.8.1-1b78ca928979` (GitHub Actions, sieben Tage). Bis zu dessen tatsächlichem Run-`success` und externem Manifest-Readback ist das Paket **nicht als fertig abgenommen** zu melden.

**Phase-B-Sperre unverändert:** Dieser Build bleibt ein `TEST / UNSIGNED / NOT AN OFFICIAL RELEASE`-Paket. Die aktuelle App-Version auf `main` darf bei dieser historischen Candidate-QA 3.0.8.0 bleiben; erst eine spätere getrennt qualifizierte Produkt-Promotion kann das ändern. Keine tatsächliche Windows/Razer-Zielhardwareabnahme, kein echter Rollback, keine Owner-Signing-/Unsigned-/SmartScreen-Zustimmung, keine produktive GitHub-Ruleset-Admin-Änderung, keine Änderung von `productionEnabled=false`/`signingDecision=unknown`/`rollbackVerified=false`. Keine offiziellen `main/downloads`-ZIPs, keine Release-Tags oder `latest.json`.
