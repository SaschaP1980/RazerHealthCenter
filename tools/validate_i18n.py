#!/usr/bin/env python3
from pathlib import Path
import json, re, subprocess, sys

root=Path(__file__).resolve().parents[1]
locale_path=root/'locales/de-DE.json'
manifest_path=root/'i18n-manifest.json'
errors=[]

def fail(msg): errors.append(msg)

try:
    doc=json.loads(locale_path.read_text(encoding='utf-8'))
    strings=doc['strings']
except Exception as e:
    raise SystemExit(f'cannot load de-DE catalog: {e}')

manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
if doc.get('_meta',{}).get('locale')!='de-DE': fail('catalog locale must be de-DE')
if doc.get('_meta',{}).get('version')!='3.0.8.0': fail('catalog version must be 3.0.8.0')
if manifest.get('catalogVersion')!='3.0.8.0': fail('manifest catalogVersion must be 3.0.8.0')
if manifest.get('runtimeLocale')!='de-DE': fail('runtimeLocale must be de-DE')
if manifest.get('availableLocales')!=['de-DE']: fail('only de-DE may be active in v3.0.8.0')
if manifest.get('languageSwitchingImplemented') is not False: fail('language switch must remain disabled')
if manifest.get('sourceOfTruth')!='locales/de-DE.json': fail('de-DE must be declared source of truth')
if manifest.get('uiKeyCount')!=len(strings): fail('uiKeyCount mismatch')
if (root/'locales/en-US.json').exists(): fail('en-US runtime catalog must not be present in v3.0.8.0')

ph=re.compile(r'\{([A-Za-z0-9_.-]+)\}')
for k,v in strings.items():
    if not isinstance(v,str): fail(f'{k}: value is not a string'); continue
    # unmatched braces are almost always an i18n defect.
    stripped=ph.sub('',v)
    if '{' in stripped or '}' in stripped: fail(f'{k}: malformed placeholder syntax')

# Static key usage in Go source.
used=set(); plural=set()
for path in root.glob('*.go'):
    text=path.read_text(encoding='utf-8')
    used.update(re.findall(r'\btr\("([^"]+)"\)',text))
    used.update(re.findall(r'\btrf\("([^"]+)"',text))
    plural.update(re.findall(r'\btrn\("([^"]+)"',text))
for k in sorted(used):
    if k not in strings: fail(f'missing key used by Go: {k}')
for base in sorted(plural):
    for suffix in ('.one','.other'):
        if base+suffix not in strings: fail(f'missing plural key: {base+suffix}')

# Dynamic gate key families.
for family in ('appengine','driverstore','kernel','devices','virtual','filters','chroma_registry','chroma_services','synapse_services','game_manager','rzcom','power','lamparray'):
    for suffix in ('name','detail','summary'):
        k=f'gate.{family}.{suffix}'
        if k not in strings: fail(f'missing dynamic gate key: {k}')

# Important v3.0.8.0 keys that may not be caught through literal call parsing.
required={
 'app.title','app.window_title','app.brand.primary','app.brand.secondary','app.tagline','app.version',
 'measurement.result.healthy','measurement.result.hint','measurement.result.unclear','measurement.result.failed',
 'tray.menu.result','modal.export.success.title','popover.raw.expected','popover.raw.detail','popover.raw.section',
 'error.single_instance','error.runtime_prepare','error.window_create','error.export','error.clipboard',
 'action.repair','action.repair.start','action.repair.recheck','repair.confirm.title','repair.running.title',
 'repair.result.success.title','repair.result.failed.title','repair.error.uac',
 'info.versioncheck.title','info.versioncheck.synapse.installed','info.versioncheck.synapse.latest',
 'info.versioncheck.chroma.installed','info.versioncheck.chroma.latest','info.versioncheck.appengine.package',
 'info.versioncheck.appengine.file','info.versioncheck.source','info.versioncheck.source.offline',
 'version.status.current','version.status.update','version.status.ahead','version.status.unknown','version.status.checking',
 'nav.setup','page.setup.title','action.setup_scan','setup.state.required','setup.state.ready','popover.finding.info','popover.raw.info_expected',
 'action.skip_device','setup.table.state','setup.product.required','setup.product.optional',
 'setup.healthcheck.none.title','setup.healthcheck.none.detail','setup.healthcheck.persist_error.title','setup.healthcheck.persist_error.detail',
 'diagnostic.running','problem.gate.repair_available','problem.gate.unclassified','problem.unclassified.title','problem.chroma.stopped_auto.title',
 'repair.confirm.problem_id','repair.confirm.recipe_id','repair.result.verification'
}
for k in sorted(required):
    if k not in strings: fail(f'missing required key: {k}')

# Prevent duplicate presentation ownership: no exact catalog translation may be
# reintroduced as a Go literal in presentation files. Technical status tokens,
# diagnostic payloads and product identifiers are outside this check.
presentation_files=['ui.go','main.go']
technical_compat={'GESUND','BESTANDEN','HINWEIS','UNKLAR','FEHLER','WARTET','PRÜFUNG','PRÜFUNG …','NICHT GEPRÜFT','INFO'}
static_values={v for v in strings.values() if '{' not in v and len(v)>=4 and re.search(r'[A-Za-zÄÖÜäöüß]',v)}
for fn in presentation_files:
    text=(root/fn).read_text(encoding='utf-8')
    literals=[]
    for m in re.finditer(r'"((?:\\.|[^"\\])*)"',text):
        try:
            v=bytes(m.group(1),'utf-8').decode('unicode_escape')
        except Exception:
            v=m.group(1)
        literals.append((text.count('\n',0,m.start())+1,v))
    for line,v in literals:
        if v in static_values and v not in technical_compat:
            fail(f'{fn}:{line}: catalog text duplicated as Go literal: {v!r}')

if errors:
    for e in errors: print('FAIL:',e)
    print(f'i18n validation: FAIL ({len(errors)} issue(s))')
    sys.exit(1)
print(f'i18n catalog keys: {len(strings)}')
print(f'i18n static Go keys: {len(used)}; plural bases: {len(plural)}')
print('i18n validation: PASS')
