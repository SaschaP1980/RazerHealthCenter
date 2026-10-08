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
