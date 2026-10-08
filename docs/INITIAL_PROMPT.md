# RHC — Initial Prompt: verbindlicher vollständiger Projekteintritt

> Einstieg nach jedem Chat-/Agentenwechsel: [`docs/INITIAL_PROMPT.md` auf GitHub `main`](https://github.com/SaschaP1980/RazerHealthCenter/blob/main/docs/INITIAL_PROMPT.md). Dieser Einstieg **verpflichtet zum Lesen der gesamten aktuellen Dokumentation**; er ersetzt weder die Dokumente noch GitHub-Live-Evidenz. Keine Entwicklungsänderung vor der nachfolgenden Bestandsaufnahme. Keine Produktveröffentlichung ohne separate Freigabe.

## 1. GitHub-Autorität zuerst rekonstruieren

Repository: [`SaschaP1980/RazerHealthCenter`](https://github.com/SaschaP1980/RazerHealthCenter); kanonischer Source-Branch: `main`. Benutze den verbundenen GitHub-Connector. Ermittele den **aktuellen vollständigen `main`-Commit-SHA**, den rekursiven Git-Tree (nicht abgeschnitten), alle existierenden Branches und ihre SHAs, offene **und relevante abgeschlossene** Issues, sämtliche offenen PRs samt Draft-/Merge-Status, die jeweils zugehörigen Rolling Comments, aktuelle CI-Runs/Statuses auf **exakten** SHAs sowie die wirksamen Repository-Rulesets/Permissions soweit zugänglich.

Frühere Chatprotokolle, alte SHA-Angaben in Dokumenten oder Issue-Headern, lokale ZIPs und historische Golden-Dateien sind **keine eigenständige gegenwärtige Autorität**. Vor **jeder** schreibenden GitHub-Aktion `main` und den Ziel-Branch bzw. PR-Head erneut prüfen; SHA-/Blob-Leases und verifizierte Diff-Grenzen verwenden. Bei nicht zugänglichen API-Endpunkten die Sichtbarkeitslücke nennen, niemals fehlende CI/Branch-Schutz-Evidenz erfinden.

## 2. Pflichtlektüre: alle Markdown-Dateien unter `docs/`

Inventarisiere `docs/` bei **jedem** Neueinstieg zunächst vollständig und **rekursiv** direkt aus dem aktuellen `main`-Git-Tree, einschließlich neuer Dateien und Unterordner. Lies und verstehe **jede** dort vorhandene `.md`-Datei, bevor du Entwicklungs- oder Release-Entscheidungen triffst. Die folgende konkrete Aufstellung ist die überprüfte Struktur vom 8. Oktober 2026, **keine statische Erlaubnis, später hinzugekommene Dateien zu übergehen**.

### Neun operative Hauptdokumente direkt unter `docs/` (alle verpflichtend)

| Dokument | Wozu es gelesen werden muss |
| --- | --- |
| [`INITIAL_PROMPT.md`](INITIAL_PROMPT.md) | Eintritt, verbindliche Lesereihenfolge und Pflicht zur aktuellen Bestandsaufnahme |
| [`DEVELOPMENT_GUIDELINES.md`](DEVELOPMENT_GUIDELINES.md) | Fast-/Work-Path, Test-first, Rolling Heartbeats, Checkpoints, autonome Merges und Cleanup |
| [`GITHUB_HOWTO.md`](GITHUB_HOWTO.md) | Issue-Identität, GitHub-Eigenheiten, Branchschutz, Actions, Berechtigungen und Reporting |
| [`MIGRATION_STATUS.md`](MIGRATION_STATUS.md) | M0–M6-Gates, Quellenmigration, SHA-/CI-Nachweise, Entscheidungen und überholte Phasen |
| [`RELEASE_PROCESS.md`](RELEASE_PROCESS.md) | **Aktuelle** Distribution `repo-downloads`, Release-Gates, atomare Aktivierung, Nachprüfung |
| [`RHC_CICD_ARCHITECTURE.md`](RHC_CICD_ARCHITECTURE.md) | Candidate-/Work-Path-Architektur, genaue Hosted-Gates, implementierte vs. fehlende Stufen |
| [`RHC_RELEASE_DRY_RUN_PLAN.md`](RHC_RELEASE_DRY_RUN_PLAN.md) | Fail-closed-/Recovery-Simulation und **historische**, durch RHC-12 überholte GitHub-Releases-Architektur |
| [`MIGRATION_LESSONS.md`](MIGRATION_LESSONS.md) | Beobachtete Fehler mit Ursachen, Korrekturen und Präventionsregeln; auch bei neuem Fehler fortschreiben |
| [`SOURCE_IMPORT_PLAYBOOK.md`](SOURCE_IMPORT_PLAYBOOK.md) | Nachvollziehbare **abgeschlossene** Migration der originalen 321 Quelldateien; nicht erneut ausführen |

### Zwei verbindliche Templates unter `docs/templates/`

- [`PROJECT_MIGRATION_TEMPLATE.md`](templates/PROJECT_MIGRATION_TEMPLATE.md): vollständige projektneutrale Migrationsphasen, GitHub-/Actions-Besonderheiten, Label-Provisionierung, Source-Byte-Schutz, Fehler- und Evidenzregeln. Als **Prozessregel und Muster** lesen, nicht blind fremde Produktpfade übernehmen.
- [`WORK_PATH_ROLLING_COMMENT.md`](templates/WORK_PATH_ROLLING_COMMENT.md): **normative** Struktur, BOOTSTRAP-Bedingungen, ein einziger fortgeschriebener Issue-Kommentar, Heartbeat-/Checkpoint-Vorgaben, Messungen, Zwischenstände und Abschlussprüfung.

### Weitere Markdown-Dateien in Unterordnern

Der geprüfte Tree enthält außerdem **zehn** Dateien in [`docs/recovery-history/`](recovery-history/). Sie sind **historische** Dokumentation der v1.7.0-Source-/UI-Recovery, nicht die aktuelle Release- oder Versionsautorität. Trotzdem beim rekursiven Lesen erfassen; historische technische Erkenntnisse von heutigen Vorgaben trennen. Für künftig hinzugefügte `docs/**`-Markdown-Dateien gilt dieselbe Lesepflicht. Beim Bericht getrennt ausweisen: **9 Hauptdokumente + 2 Templates + 10 Recovery-Historien = 21 rekursiv** (Stand der vorgenannten Inventur).

## 3. Technischen Projektstand und Quellcode verstehen

Lies auf dem **aktuellen** `main` mindestens `README.md`, `go.mod`, `build.sh`, `model.go`, `SAFETY-MODEL.txt`, `SOURCE-DELIVERY-CONTRACT.md`, `config/rhc-release-policy.json`, die für den nächsten Schritt relevanten `tools/` und `tests/` sowie alle einschlägigen `.github/workflows/`. Wenn Quellcode oder Build-Eingaben fehlen, **BLOCKED** statt erfolgreichem Bootstrap melden.

- Produkt: Go-1.23.2-Windows-amd64-GUI mit eingebetteten PowerShell-Diagnose- und Repair-Payloads, PE-Ressourcen, Health-/Setup-/Diagnostic-/Repair-System. Source of truth für **App- und Referenzversion** sind `appVersion` und `referenceVersion` in `model.go`.
- **RHC-16:** Versionierung ausschließlich für **aktuelle App/Candidate/Release** als `MAJOR.MINOR.PATCH.HOTFIX`, zuerst `3.0.8.0`; ein Hotfix wäre `3.0.8.1` (`Release-Profile: hotfix`), neuer Patch `3.0.9.0`. Versionen der Engines, Razer-Schnittstellen und alte History-Werte sind eigene Domänen und dürfen nicht pauschal umformatiert werden. Werte vor Änderung **live nachlesen**.
- Die **historische** v3.0.8-Golden-Basis (321 Quelldateien, SHA-geprüfte EXE, Source Intake) ist auf den ursprünglichen Import-Commit/PR #2 gepinnt. Der aktuelle vierteilige Build muss **unabhängig** auf aktuellem SHA reproduzierbar sein; ihn nicht irrtümlich gegen den alten v3.0.8-EXE-Hash vergleichen.
- Der separat unter [`downloads/qa/`](../downloads/qa/README.md) archivierte v3.0.8-Portable-Build ist ausdrücklich **TEST / UNSIGNED**, nicht offiziell released. Historische QA-Dateinamen, SHA/Bytes und Metadaten nicht für `3.0.8.0` umetikettieren.

**Unverhandelbare Sicherheitsregeln:** Health/Setup/Diagnostics read-only gegenüber Razer/Windows. Reparatur nur nach expliziter In-App-Benutzerbestätigung, exakter Problem-/Recipe-/Payload-/SHA-/Allowlist-Prüfung, bedarfsgesteuertem UAC (nicht als Bestätigungsersatz), kleinstem Eingriffsbereich und erfolgreicher **read-only Post-Repair-Verifikation**. Unknown/mehrdeutige PID-/Geräte-/Runtime-Zustände dürfen nicht als HEALTHY oder reparierbar geraten werden. Hosted CI führt **keine** reale Razer-Reparatur aus; Linux-Crossbuild, native Windows-PS5.1-Tests und physische Razer-Hardwareabnahme sind drei **verschiedene** Evidenzklassen.

## 4. GitHub-Arbeitsmodell und Entwicklungszyklus

1. Aktuellen `main`-SHA, Version, Issue-/PR-/Rolling-Comment-Status und exakten zulässigen Diff rekonstruieren. Issue #N hat Kennung `[RHC-N]` (keinen eigenen Issue-Zähler, kein `LBS-N`); vorhandenen Issue-Work-Path fortführen statt duplizieren. Aktive und bereits gemergte PRs/Branches anhand **live** GitHub-Refs prüfen.
2. **Dokumentations-Fast-Path:** auf frischem geprüftem `main` eine einzelne atomare, überprüfte Doku-Änderung; keine künstliche Produktversion, kein Candidate/Release und kein neues Work-Path-Rolling-Protokoll.
3. **Kleiner Patch/Hotfix:** nach `DEVELOPMENT_GUIDELINES.md` standardmäßig branchless Fast-Path; bestätigte Fehler möglichst RED auf unverändertem Basis-SHA, dann fokussiertes GREEN, ein vollständig geprüfter atomarer Candidate, auf exaktem SHA Linux+Windows-Preflight. Fast-Path nicht nur für zusätzliche Checkpoint-Commits in einen Work-Path umwandeln.
4. **Große/riskante Arbeit:** begründeter `work/RHC-N`; **vor Branch-Erstellung** einen einzigen Rolling Comment in `BOOTSTRAP` anlegen, frisch zeitstempeln und **durch GitHub zurücklesen**; danach Branch-SHA verifizieren, denselben Kommentar aktualisieren und erneut zurücklesen, **erst dann** Code committen. Bestehender Work-Path: Originalkommentar und bisherigen Work-/Main-/CI-Checkpoint zuerst rekonstruieren.
5. **Während ACTIVE Work-Path:** denselben Rolling Comment ungefähr **alle 3 Minuten** mit verifiziertem, frischem ISO-8601-UTC-Millisekunden-Zeitstempel aktualisieren und nach jedem Write lesen; auch ohne neuen Commit. Nach ~5 Minuten altem ACTIVE-Status ohne live verifizierten Workflow als gestoppt betrachten und alle Referenzen rekonstruieren. Nur wahrheitsgemäß belegte `WAITING_FOR_GITHUB` (exakte laufende/queued Run-ID), `BLOCKED_EXTERNAL`, tatsächliches `IDLE/STOPPED` oder `COMPLETED` unterbrechen die aktive Heartbeat-Pflicht. **Unabhängig** davon spätestens nach ungefähr **10–15 Minuten** substanzieller Arbeit einen kohärenten dauerhaften Work-Code-Checkpoint persistieren. Versäumte Intervalle im Audit benennen, niemals rückdatieren.
6. In jedem neuen aktiven Work-Chat einen **tatsächlich nutzerseitig sichtbaren** Marker `RHC<N>CHAT<12 zufällige Großbuchstaben-Hex-Zeichen>` ausgeben und im **bestehenden** Rolling Comment ergänzen; keine private Chat-ID oder Zeit erfinden. Alle Prüfergebnisse und Fehlschläge mit echtem SHA, Run-/Job-ID, Testzahl und Quelle festhalten. Temporäre, fehlgeschlagene oder `SKIPPED`-Runs niemals als grün werten.
7. Work-Path: exakter eingefrorener Work-SHA → überprüftes **Development Completion** (Commit-Trailer `Development-Completion: requested`, genauer SHA/Hosted-Status) → Candidate Entry → Candidate-Gates. Vor dem nächsten Schritt GitHub-Status/Ancestry neu lesen. Routine-Commits, geprüfte PR-Merges und verifizierte Branch-Bereinigung **innerhalb bereits genehmigten Umfangs** autonom ausführen; keine erneute Zustimmung für Routinearbeit, **aber** keine stillschweigende Produkt-/Release-/Signing-Freigabe.
8. Auto-Cleanup nach Merge erfolgt ausschließlich über den geprüften `rhc-branch-cleanup`-Mechanismus: gemergten PR, exakten alten Work-Head, Hauptbranch-Ancestry, unveränderten Ref und bestätigte Löschung prüfen. Aktive oder unverheiratete fremde Branches bewahren; nicht über `--force` unkontrolliert löschen. Terminaler Rolling Comment muss reale PR-/Main-/CI-/Cleanup-Ergebnisse und `Agent-State: COMPLETED` konsistent nachführen.

**GitHub-Spezifika:** Die verifizierte Stage-1-`main`-Ruleset [#24701145](https://github.com/SaschaP1980/RazerHealthCenter/rules/24701145) blockiert Löschen und Force-Push, **nicht** alle direkten Fast-Forward-Pushes. Required PR/status checks sind getrennte, noch nicht allgemein aktivierte Stufen. Ein Legacy-Branch-Protection-API-403 widerlegt die lesbare Ruleset-Evidenz nicht. GitHub-`GITHUB_TOKEN`-Pushes starten PR-Workflows nicht automatisch; bei berechtigtem Staging gezielt neu qualifizieren. YAML-Fehler mit **null Jobs** sind keine fehlgeschlagenen Produkt-Tests; `SKIPPED` und `cancelled` nicht zu PASS hochstufen. Issue-Labels/Katalog nur nach tatsächlicher API-Prüfung und verifiziertem Provisioning annehmen. Temporäre Write-Workflows vor finalem Merge entfernen. Nie unerklärte Statuskontexte, erfundene PR-/Actions-Runs oder implizite Repository-Rechte annehmen.

## 5. CI und Release: implementiert, geplant oder gesperrt?

Die vorhandenen Workflow-Dateien unter `.github/workflows/` und ihre aktuellen Berechtigungen **tatsächlich lesen**, insbesondere:

- `rhc-source-intake.yml`: **historische** 321-Dateien-/v3.0.8-Golden-Prüfung gegen eingefrorene Quelle.
- `rhc-infrastructure-ci.yml`: aktuelle Build-/Vertragsprüfungen mit unabhängigen Windows-GUI-Builds, Linux und nativen Windows/PowerShell-5.1-Gates.
- `rhc-development-completion.yml`: exakter eingefrorener Work-SHA und qualifizierte Hosted-Evidenz.
- `rhc-candidate-preflight.yml`: Candidate Linux/Windows; **Promotion ist absichtlich fail-closed**, kein Nachweis einer betriebsbereiten Release-Orchestrierung.
- `rhc-release-rehearsal.yml` und `rhc-release-dry-run.yml`: nur nichtpublizierende Simulations-/Sicherheitsprüfungen.
- `rhc-downloads-verify.yml`: **read-only** Downloads-/QA-/Katalogintegrität.
- `rhc-branch-cleanup.yml`: eng begrenzte, unabhängig verifizierte Branch-Löschung nach Merge.

**Geltendes Distributionsmodell seit RHC-12:** `config/rhc-release-policy.json.distribution = repo-downloads`; [`RELEASE_PROCESS.md`](RELEASE_PROCESS.md) ist maßgeblich. Künftige autorisierte Versionen werden als unveränderliche schlanke `main/downloads/RazerHealthCenter-Portable-vX.Y.Z.H.zip` plus `downloads/releases.json`, `downloads/latest.json` und `downloads/README.md` über **einen** überprüften Release-PR-Merge aktiviert. Original Source liegt in GitHub, kein verschachteltes Source-ZIP oder zweiter GitHub-Releases-Publisher. Vor dem ersten Produkt-Release muss `releases.json` leer und `latest.json` abwesend sein. Historische GitHub Release/Draft-Pläne in RHC-5 und einigen Migrationsabschnitten sind **überholt**, nicht erneut als aktuelle Architektur übernehmen.

**Release-Gates noch nicht erfüllt:** `productionEnabled=false`, `signingDecision=unknown`, `rollbackVerified=false` (jeweils live verifizieren). Signierter Publisher **oder** ausdrückliche versions-/Quell-SHA-/ZIP-Hash-spezifische Genehmigung eines unsignierten Windows-Release samt SmartScreen-Hinweis erforderlich; außerdem Candidate/Release-Orchestrator, unabhängige reproduzierbare Lean-ZIP-/Quelltag-Prüfung, Pre-Activation, geprüfter Single-PR-Merge, unveränderliches Release-Verzeichnis, Post-Release Verification, branch policies/permissions und erforderliche Native-/Hardware-Abnahmen. **Kein** Tag, Release, neuester Pointer, Produktions-ZIP oder Freischalten von Write-Berechtigungen durch einen Chat-Neustart.

**Offene Vertragsabweichungen aktiv kennzeichnen:** `SOURCE-DELIVERY-CONTRACT.md` fordert historisch pro Version ein zusätzliches Source-ZIP; die aktuell gewählte `repo-downloads`-Veröffentlichung definiert Source über GitHub. GPL-3.0-or-later-Draft PR #7 sieht eine `LICENSE` in künftigen Archiven vor (andere Dateizahl als derzeitiger Lean-Vertrag), ist **nicht gemergt** und braucht technische/legale Revalidierung gegen aktuelles `main`. Eine genehmigte zukünftige Produktbezeichnung `Peripheral Health Center` (RHC-8) bedeutet weder abgeschlossene Rechteprüfung noch autorisierten Rename, Build oder Release. Widersprüche berichten, nicht per Annahme auflösen.

## 6. Resume-Audit und kompakter Status **vor jeder neuen Entwicklung**

Lies mindestens die Live-Issues [RHC-1](https://github.com/SaschaP1980/RazerHealthCenter/issues/1) (Migration), [RHC-3](https://github.com/SaschaP1980/RazerHealthCenter/issues/3) (offener CI/CD-Work-Branch), [RHC-5](https://github.com/SaschaP1980/RazerHealthCenter/issues/5) (historische Dry-Run-Planung), [RHC-6](https://github.com/SaschaP1980/RazerHealthCenter/issues/6) / [PR #7](https://github.com/SaschaP1980/RazerHealthCenter/pull/7) (GPL, Rechte/Trademark), [RHC-8](https://github.com/SaschaP1980/RazerHealthCenter/issues/8) (vorgemerkte Branding-Umsetzung) sowie die neueren/aktuellen Issues, PRs **einschließlich ihrer Kommentare**. Relevante abgeschlossene Issues [RHC-12](https://github.com/SaschaP1980/RazerHealthCenter/issues/12), [RHC-14](https://github.com/SaschaP1980/RazerHealthCenter/issues/14), [RHC-16](https://github.com/SaschaP1980/RazerHealthCenter/issues/16) liefern neuere Entscheidungen und feste historische Nachweise. Laufende Work-Branch-SHAs und Rolling-Comments können inzwischen hinter `main` liegen; nie blind darauf weitercommitten oder sie als `ACTIVE` deuten.

**Antwort an den Nutzer vor Arbeitsbeginn:** aktuelle Version aus `model.go`, vollständiger `main`-SHA, aktive Branches/offene PRs, genau identifizierter Work- und Rolling-Checkpoint, aktuelle CI-Nachweise nach SHA/OS, M0–M6-Status, echte Blocker, QA-/Produktionsstatus, **explizite widersprüchliche oder überholte Dokumentationsangaben**, nächster begründeter Arbeitsschritt. Unterschied zwischen lokal, GitHub-hosted, native Windows und realem Razer-Hardwaretest ist Pflicht. Danach nur bei eindeutigem erlaubten Umfang mutieren; nach Änderung exakten Scope, Commit, Prüfungen und erforderliches Cleanup verifizieren.