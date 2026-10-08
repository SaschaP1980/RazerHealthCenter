//go:build windows

package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"
)

const (
	razerDiscoveryURL    = "https://discovery3.razerapi.com/api/v1/endpoints"
	razerManifestBaseURL = "https://manifest3.razerapi.com/api/v1/releases/"
	razerManifestChannel = "prod"
)

const (
	versionStateChecking        = "CHECKING"
	versionStateCurrent         = "CURRENT"
	versionStateUpdateAvailable = "UPDATE_AVAILABLE"
	versionStateAhead           = "AHEAD"
	versionStateUnknown         = "UNKNOWN"

	registrationStateNotEvaluated = "NOT_EVALUATED"
	registrationStatePresent      = "PRESENT"
	registrationStateUnreadable   = "UNREADABLE"
)

// VersionStatus schema 4 switches the online authority from public release-note
// scraping to Razer's own system-specific prod manifest. The offered module
// version is compared only with the registry value whose key/value pair is
// supplied by that same manifest. This is deliberately informational: an older
// installed version yields UPDATE_AVAILABLE, never a Health Engine warning.
type VersionStatus struct {
	SchemaVersion            int       `json:"schemaVersion"`
	ToolVersion              string    `json:"toolVersion"`
	CheckedAt                time.Time `json:"checkedAt"`
	SourceURL                string    `json:"sourceUrl"`
	DiscoveryURL             string    `json:"discoveryUrl"`
	ManifestChannel          string    `json:"manifestChannel"`
	ManifestProdHash         string    `json:"manifestProdHash,omitempty"`
	ManifestURL              string    `json:"manifestUrl,omitempty"`
	InstalledSynapse         string    `json:"installedSynapse"`
	InstalledSynapseSource   string    `json:"installedSynapseSource,omitempty"`
	InstalledChroma          string    `json:"installedChroma,omitempty"`
	InstalledChromaSource    string    `json:"installedChromaSource,omitempty"`
	AppEnginePackage         string    `json:"appEnginePackage"`
	AppEngineFileVersion     string    `json:"appEngineFileVersion"`
	AppEnginePath            string    `json:"appEnginePath,omitempty"`
	LatestSynapse            string    `json:"latestSynapse"`
	LatestChroma             string    `json:"latestChroma"`
	SynapseProductVersion    string    `json:"synapseProductVersion,omitempty"`
	SynapseDisplayVersion    string    `json:"synapseDisplayVersion,omitempty"`
	ChromaProductVersion     string    `json:"chromaProductVersion,omitempty"`
	ChromaDisplayVersion     string    `json:"chromaDisplayVersion,omitempty"`
	SynapseRegistryKey       string    `json:"synapseRegistryKey,omitempty"`
	SynapseRegistryValue     string    `json:"synapseRegistryValue,omitempty"`
	ChromaRegistryKey        string    `json:"chromaRegistryKey,omitempty"`
	ChromaRegistryValue      string    `json:"chromaRegistryValue,omitempty"`
	SynapseRegistrationState string    `json:"synapseRegistrationState,omitempty"`
	SynapseRegistrationError string    `json:"synapseRegistrationError,omitempty"`
	SynapseRegistryView      string    `json:"synapseRegistryView,omitempty"`
	ChromaRegistrationState  string    `json:"chromaRegistrationState,omitempty"`
	ChromaRegistrationError  string    `json:"chromaRegistrationError,omitempty"`
	ChromaRegistryView       string    `json:"chromaRegistryView,omitempty"`
	SynapseStatus            string    `json:"synapseStatus"`
	ChromaStatus             string    `json:"chromaStatus"`
	LocalError               string    `json:"localError,omitempty"`
	OnlineError              string    `json:"onlineError,omitempty"`
}

type localVersionProbe struct {
	AppPackage     string `json:"appPackage"`
	AppFileVersion string `json:"appFileVersion"`
	AppPath        string `json:"appPath"`
}

type manifestMachineContext struct {
	OS     string `json:"os"`
	OSVer  string `json:"osver"`
	Arch   string `json:"arch"`
	Mfr    string `json:"mfr"`
	Model  string `json:"model"`
	SKU    string `json:"sku"`
	Locale string `json:"locale"`
}

type razerDiscoveryResponse struct {
	Data struct {
		Items []struct {
			Hash string `json:"hash"`
			Name string `json:"name"`
		} `json:"items"`
	} `json:"data"`
}

type razerManifestResponse struct {
	Data struct {
		Items []razerManifestProduct `json:"items"`
	} `json:"data"`
}

type razerManifestProduct struct {
	Endpoint       string `json:"endpoint"`
	Name           string `json:"name"`
	Version        string `json:"version"`
	DisplayVersion string `json:"display_version"`
	Metadata       struct {
		DisplayName string   `json:"display_name"`
		Alias       []string `json:"alias"`
	} `json:"metadata"`
	Modules []razerManifestModule `json:"modules"`
}

type razerManifestModule struct {
	Name                        string `json:"name"`
	Version                     string `json:"version"`
	CurrentVersionRegistryKey   string `json:"current_version_registry_key"`
	CurrentVersionRegistryValue string `json:"current_version_registry_value"`
	IsPrimaryModule             bool   `json:"is_primary_module"`
}

type manifestModuleReference struct {
	ProductName     string
	ProductVersion  string
	DisplayVersion  string
	ModuleName      string
	OfferedVersion  string
	RegistryKey     string
	RegistryValue   string
	IsPrimaryModule bool
}

type razerProdManifest struct {
	ProdHash string
	URL      string
	Synapse  manifestModuleReference
	Chroma   manifestModuleReference
}

func (a *App) refreshVersionStatusAsync() {
	a.mu.Lock()
	if a.versionChecking {
		a.mu.Unlock()
		return
	}
	a.versionChecking = true
	// Keep previously resolved values visible during a refresh. Only the first
	// probe starts in CHECKING.
	if a.versionStatus.CheckedAt.IsZero() {
		a.versionStatus = VersionStatus{
			SchemaVersion:   4,
			ToolVersion:     appVersion,
			SourceURL:       razerDiscoveryURL,
			DiscoveryURL:    razerDiscoveryURL,
			ManifestChannel: razerManifestChannel,
			SynapseStatus:   versionStateChecking,
			ChromaStatus:    versionStateChecking,
		}
	}
	a.mu.Unlock()
	procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)

	go func() {
		st := collectVersionStatus()
		a.mu.Lock()
		a.versionStatus = st
		a.versionChecking = false
		a.mu.Unlock()
		a.persistVersionStatus(st)
		a.debugf("VERSION manifest channel=%s prodHash=%q manifest=%q installedSynapse=%q offeredSynapse=%q synapseStatus=%s synapseRegistration=%s synapseRegistryView=%s installedChroma=%q offeredChroma=%q chromaStatus=%s chromaRegistration=%s chromaRegistryView=%s appPackage=%q appFile=%q localErr=%q onlineErr=%q",
			st.ManifestChannel, st.ManifestProdHash, st.ManifestURL, st.InstalledSynapse, st.LatestSynapse, st.SynapseStatus, st.SynapseRegistrationState, st.SynapseRegistryView, st.InstalledChroma, st.LatestChroma, st.ChromaStatus, st.ChromaRegistrationState, st.ChromaRegistryView, st.AppEnginePackage, st.AppEngineFileVersion, st.LocalError, st.OnlineError)
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
	}()
}

func collectVersionStatus() VersionStatus {
	st := VersionStatus{
		SchemaVersion:            4,
		ToolVersion:              appVersion,
		CheckedAt:                time.Now(),
		SourceURL:                razerDiscoveryURL,
		DiscoveryURL:             razerDiscoveryURL,
		ManifestChannel:          razerManifestChannel,
		SynapseStatus:            versionStateUnknown,
		ChromaStatus:             versionStateUnknown,
		SynapseRegistrationState: registrationStateNotEvaluated,
		ChromaRegistrationState:  registrationStateNotEvaluated,
	}

	local, appErr := probeLocalAppEngineIdentity()
	st.AppEnginePackage = strings.TrimSpace(local.AppPackage)
	st.AppEngineFileVersion = strings.TrimSpace(local.AppFileVersion)
	st.AppEnginePath = strings.TrimSpace(local.AppPath)

	ctx, ctxErr := probeManifestMachineContext()
	if ctxErr != nil {
		st.LocalError = joinVersionErrors(st.LocalError, "Systemkontext: "+ctxErr.Error())
		st.OnlineError = "Razer prod-Manifest kann ohne Systemkontext nicht systemspezifisch abgefragt werden."
		if appErr != nil {
			st.LocalError = joinVersionErrors(st.LocalError, "AppEngine: "+appErr.Error())
		}
		return st
	}

	manifest, err := fetchRazerProdManifest(ctx)
	if err != nil {
		st.OnlineError = err.Error()
		if appErr != nil {
			st.LocalError = joinVersionErrors(st.LocalError, "AppEngine: "+appErr.Error())
		}
		return st
	}
	st.ManifestProdHash = manifest.ProdHash
	st.ManifestURL = manifest.URL
	st.SourceURL = manifest.URL

	st.LatestSynapse = strings.TrimSpace(manifest.Synapse.OfferedVersion)
	st.LatestChroma = strings.TrimSpace(manifest.Chroma.OfferedVersion)
	st.SynapseProductVersion = strings.TrimSpace(manifest.Synapse.ProductVersion)
	st.SynapseDisplayVersion = strings.TrimSpace(manifest.Synapse.DisplayVersion)
	st.ChromaProductVersion = strings.TrimSpace(manifest.Chroma.ProductVersion)
	st.ChromaDisplayVersion = strings.TrimSpace(manifest.Chroma.DisplayVersion)
	st.SynapseRegistryKey = strings.TrimSpace(manifest.Synapse.RegistryKey)
	st.SynapseRegistryValue = strings.TrimSpace(manifest.Synapse.RegistryValue)
	st.ChromaRegistryKey = strings.TrimSpace(manifest.Chroma.RegistryKey)
	st.ChromaRegistryValue = strings.TrimSpace(manifest.Chroma.RegistryValue)

	if st.SynapseRegistryKey != "" && st.SynapseRegistryValue != "" {
		probe, readErr := probeManifestRegistryValue(st.SynapseRegistryKey, st.SynapseRegistryValue)
		if readErr != nil {
			st.SynapseRegistrationState = registrationStateUnreadable
			st.SynapseRegistrationError = readErr.Error()
			st.LocalError = joinVersionErrors(st.LocalError, "Synapse-Version: "+readErr.Error())
		} else {
			st.InstalledSynapse = strings.TrimSpace(probe.Value)
			st.SynapseRegistryView = strings.TrimSpace(probe.View)
			st.InstalledSynapseSource = "Razer manifest registry mapping (" + st.SynapseRegistryView + "): " + st.SynapseRegistryKey + " [" + st.SynapseRegistryValue + "]"
			st.SynapseRegistrationState = registrationStatePresent
		}
	}
	if st.ChromaRegistryKey != "" && st.ChromaRegistryValue != "" {
		probe, readErr := probeManifestRegistryValue(st.ChromaRegistryKey, st.ChromaRegistryValue)
		if readErr != nil {
			st.ChromaRegistrationState = registrationStateUnreadable
			st.ChromaRegistrationError = readErr.Error()
			st.LocalError = joinVersionErrors(st.LocalError, "Chroma-Version: "+readErr.Error())
		} else {
			st.InstalledChroma = strings.TrimSpace(probe.Value)
			st.ChromaRegistryView = strings.TrimSpace(probe.View)
			st.InstalledChromaSource = "Razer manifest registry mapping (" + st.ChromaRegistryView + "): " + st.ChromaRegistryKey + " [" + st.ChromaRegistryValue + "]"
			st.ChromaRegistrationState = registrationStatePresent
		}
	}
	if appErr != nil {
		st.LocalError = joinVersionErrors(st.LocalError, "AppEngine: "+appErr.Error())
	}

	st.SynapseStatus = compareInstalledToOffered(st.InstalledSynapse, st.LatestSynapse)
	st.ChromaStatus = compareInstalledToOffered(st.InstalledChroma, st.LatestChroma)
	return st
}

func joinVersionErrors(existing, next string) string {
	existing = strings.TrimSpace(existing)
	next = strings.TrimSpace(next)
	if existing == "" {
		return next
	}
	if next == "" {
		return existing
	}
	return existing + " | " + next
}

func probeLocalAppEngineIdentity() (localVersionProbe, error) {
	script := `$ErrorActionPreference='SilentlyContinue';
$procs=@(Get-CimInstance Win32_Process -Filter "Name='RazerAppEngine.exe'" -Property ExecutablePath,CommandLine,CreationDate -ErrorAction SilentlyContinue);
$main=$procs | Where-Object {$_.CommandLine -notmatch '--type='} | Sort-Object CreationDate | Select-Object -Last 1; if(-not $main){$main=$procs|Select-Object -First 1};
$appPath=''; if($main){$appPath=[string]$main.ExecutablePath};
if((-not $appPath) -or (-not (Test-Path -LiteralPath $appPath))){$base=Join-Path $env:ProgramFiles 'Razer\RazerAppEngine'; if(Test-Path -LiteralPath $base){$d=Get-ChildItem -LiteralPath $base -Directory -Filter 'app-*' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1; if($d){$candidate=Join-Path $d.FullName 'RazerAppEngine.exe'; if(Test-Path -LiteralPath $candidate){$appPath=$candidate}}}};
$pkg='';$fv=''; if($appPath -and (Test-Path -LiteralPath $appPath)){try{$leaf=Split-Path -Leaf (Split-Path -Parent $appPath);if($leaf -match '^app-(.+)$'){$pkg=[string]$Matches[1]}}catch{};try{$fv=[string](Get-Item -LiteralPath $appPath).VersionInfo.FileVersion}catch{}};
[ordered]@{appPackage=$pkg;appFileVersion=$fv;appPath=$appPath} | ConvertTo-Json -Compress`
	var out localVersionProbe
	if err := runVersionPowerShellJSON(script, &out); err != nil {
		return localVersionProbe{}, err
	}
	return out, nil
}

func probeManifestMachineContext() (manifestMachineContext, error) {
	// Razer's own installer requests the prod manifest with this system context.
	// No serial number or other unique device identifier is sent by this code.
	script := `$ErrorActionPreference='Stop';
$os=Get-CimInstance Win32_OperatingSystem -ErrorAction Stop;
$cs=Get-CimInstance Win32_ComputerSystem -ErrorAction Stop;
$build=0; [void][int]::TryParse([string]$os.BuildNumber,[ref]$build);
$osver=if($build -ge 22000){'11'}else{'10'};
$arch=if([Environment]::Is64BitOperatingSystem){'64'}else{'32'};
$locale=[Globalization.CultureInfo]::CurrentUICulture.Name; if(-not $locale){$locale='en-US'};
[ordered]@{os='WINDOWS';osver=$osver;arch=$arch;mfr=[string]$cs.Manufacturer;model=[string]$cs.Model;sku=[string]$cs.SystemSKUNumber;locale=$locale} | ConvertTo-Json -Compress`
	var out manifestMachineContext
	if err := runVersionPowerShellJSON(script, &out); err != nil {
		return manifestMachineContext{}, err
	}
	if strings.TrimSpace(out.OS) == "" {
		out.OS = "WINDOWS"
	}
	if strings.TrimSpace(out.Arch) == "" {
		out.Arch = "64"
	}
	if strings.TrimSpace(out.Locale) == "" {
		out.Locale = "en-US"
	}
	return out, nil
}

func runVersionPowerShellJSON(script string, out any) error {
	ps := "$enc = New-Object System.Text.UTF8Encoding($false); [Console]::OutputEncoding=$enc; $OutputEncoding=$enc; " + script
	cmd := exec.Command("powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		msg := strings.TrimSpace(stderr.String())
		if msg == "" {
			msg = err.Error()
		}
		return errors.New(msg)
	}
	if err := json.Unmarshal(bytes.TrimSpace(stdout.Bytes()), out); err != nil {
		return fmt.Errorf("PowerShell-Probe JSON: %w", err)
	}
	return nil
}

func fetchRazerProdManifest(ctx manifestMachineContext) (razerProdManifest, error) {
	client := &http.Client{Timeout: 8 * time.Second}
	var discovery razerDiscoveryResponse
	if err := fetchRazerJSON(client, razerDiscoveryURL, &discovery); err != nil {
		return razerProdManifest{}, fmt.Errorf("Razer Discovery: %w", err)
	}

	prodHash := ""
	for _, item := range discovery.Data.Items {
		name := strings.ToLower(strings.TrimSpace(item.Name))
		if name == "prod" {
			prodHash = strings.TrimSpace(item.Hash)
			break
		}
	}
	if !isSafeManifestHash(prodHash) {
		return razerProdManifest{}, errors.New("Razer Discovery lieferte keinen gültigen prod-Hash")
	}

	q := url.Values{}
	q.Set("os", strings.TrimSpace(ctx.OS))
	q.Set("osver", strings.TrimSpace(ctx.OSVer))
	q.Set("arch", strings.TrimSpace(ctx.Arch))
	q.Set("mfr", strings.TrimSpace(ctx.Mfr))
	q.Set("model", strings.TrimSpace(ctx.Model))
	q.Set("sku", strings.TrimSpace(ctx.SKU))
	q.Set("l", strings.TrimSpace(ctx.Locale))
	manifestURL := razerManifestBaseURL + url.PathEscape(prodHash) + "/tags/" + razerManifestChannel + "/products?" + q.Encode()

	var manifest razerManifestResponse
	if err := fetchRazerJSON(client, manifestURL, &manifest); err != nil {
		return razerProdManifest{}, fmt.Errorf("Razer prod-Manifest: %w", err)
	}

	syn, synOK := findManifestModule(manifest.Data.Items, "Razer Synapse")
	chr, chrOK := findManifestModule(manifest.Data.Items, "Razer Chroma")
	if !synOK && !chrOK {
		return razerProdManifest{}, errors.New("Razer prod-Manifest enthält weder Razer Synapse noch Razer Chroma")
	}
	return razerProdManifest{ProdHash: prodHash, URL: manifestURL, Synapse: syn, Chroma: chr}, nil
}

func fetchRazerJSON(client *http.Client, sourceURL string, out any) error {
	req, err := http.NewRequest(http.MethodGet, sourceURL, nil)
	if err != nil {
		return err
	}
	req.Header.Set("User-Agent", "Razer-Synapse-Chroma-Health-Center/"+appVersion+" version-manifest-check")
	req.Header.Set("Accept", "application/json")
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("HTTP %d", resp.StatusCode)
	}
	body, err := io.ReadAll(io.LimitReader(resp.Body, 8<<20))
	if err != nil {
		return err
	}
	if err := json.Unmarshal(body, out); err != nil {
		return fmt.Errorf("ungültiges JSON: %w", err)
	}
	return nil
}

func isSafeManifestHash(v string) bool {
	v = strings.TrimSpace(v)
	if v == "" || len(v) > 128 {
		return false
	}
	for _, r := range v {
		if (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') || (r >= '0' && r <= '9') || r == '_' || r == '-' {
			continue
		}
		return false
	}
	return true
}

func findManifestModule(products []razerManifestProduct, moduleName string) (manifestModuleReference, bool) {
	var fallback manifestModuleReference
	fallbackOK := false
	for _, product := range products {
		for _, module := range product.Modules {
			if !strings.EqualFold(strings.TrimSpace(module.Name), moduleName) {
				continue
			}
			ref := manifestModuleReference{
				ProductName:     firstNonEmpty(strings.TrimSpace(product.Metadata.DisplayName), strings.TrimSpace(product.Name)),
				ProductVersion:  strings.TrimSpace(product.Version),
				DisplayVersion:  strings.TrimSpace(product.DisplayVersion),
				ModuleName:      strings.TrimSpace(module.Name),
				OfferedVersion:  strings.TrimSpace(module.Version),
				RegistryKey:     strings.TrimSpace(module.CurrentVersionRegistryKey),
				RegistryValue:   strings.TrimSpace(module.CurrentVersionRegistryValue),
				IsPrimaryModule: module.IsPrimaryModule,
			}
			if module.IsPrimaryModule {
				return ref, true
			}
			if !fallbackOK {
				fallback, fallbackOK = ref, true
			}
		}
	}
	return fallback, fallbackOK
}

type registryValueProbe struct {
	Value string `json:"value"`
	View  string `json:"view"`
}

func probeManifestRegistryValue(key, valueName string) (registryValueProbe, error) {
	key = strings.TrimSpace(key)
	valueName = strings.TrimSpace(valueName)
	if key == "" || valueName == "" {
		return registryValueProbe{}, errors.New("Razer-Manifest enthält keine Registry-Zuordnung")
	}
	// The official manifest supplies one logical registry path. On 64-bit
	// Windows, Razer products may register it in either the 64-bit or 32-bit
	// view. Query both views explicitly instead of rewriting WOW6432Node into
	// the manifest path. The first readable non-empty value wins.
	ps := `$ErrorActionPreference='Stop'; $key=` + quotePowerShellLiteral(key) + `; $valueName=` + quotePowerShellLiteral(valueName) + `; ` +
		`$k=$key -replace '^Registry::',''; $hive=''; $sub=''; ` +
		`if($k -match '(?i)^HKEY_LOCAL_MACHINE\\(.+)$'){$hive='LocalMachine';$sub=$Matches[1]}elseif($k -match '(?i)^HKLM:\\(.+)$'){$hive='LocalMachine';$sub=$Matches[1]}elseif($k -match '(?i)^HKEY_CURRENT_USER\\(.+)$'){$hive='CurrentUser';$sub=$Matches[1]}elseif($k -match '(?i)^HKCU:\\(.+)$'){$hive='CurrentUser';$sub=$Matches[1]}else{throw 'Nicht unterstützter Registry-Hive im Razer-Manifest'}; ` +
		`$views=@([Microsoft.Win32.RegistryView]::Registry64,[Microsoft.Win32.RegistryView]::Registry32); $errs=@(); foreach($view in $views){$base=$null;$rk=$null;try{$hk=if($hive -eq 'LocalMachine'){[Microsoft.Win32.RegistryHive]::LocalMachine}else{[Microsoft.Win32.RegistryHive]::CurrentUser};$base=[Microsoft.Win32.RegistryKey]::OpenBaseKey($hk,$view);$rk=$base.OpenSubKey($sub,$false);if($null -eq $rk){throw 'Registry-Schlüssel fehlt'};$v=$rk.GetValue($valueName,$null,[Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames);if($null -eq $v -or [string]::IsNullOrWhiteSpace([string]$v)){throw 'Registry-Wert fehlt oder ist leer'};$vn=if($view -eq [Microsoft.Win32.RegistryView]::Registry64){'Registry64'}else{'Registry32'};[ordered]@{value=[string]$v;view=$vn}|ConvertTo-Json -Compress;exit 0}catch{$errs+=($view.ToString()+': '+$_.Exception.Message)}finally{if($rk){$rk.Dispose()};if($base){$base.Dispose()}}};[Console]::Error.Write(($errs -join ' | '));exit 3`
	var out registryValueProbe
	if err := runVersionPowerShellJSON(ps, &out); err != nil {
		return registryValueProbe{}, err
	}
	out.Value = strings.TrimSpace(out.Value)
	out.View = strings.TrimSpace(out.View)
	if out.Value == "" || (out.View != "Registry64" && out.View != "Registry32") {
		return registryValueProbe{}, errors.New("Registry-Wert ist leer oder Registry-View unbekannt")
	}
	return out, nil
}

func compareInstalledToOffered(installed, offered string) string {
	if !isComparableManifestVersion(installed) || !isComparableManifestVersion(offered) {
		return versionStateUnknown
	}
	switch c := compareVersionNumbers(installed, offered); {
	case c < 0:
		return versionStateUpdateAvailable
	case c > 0:
		return versionStateAhead
	default:
		return versionStateCurrent
	}
}

func isComparableManifestVersion(v string) bool {
	v = strings.TrimSpace(strings.TrimPrefix(strings.TrimSpace(v), "V"))
	parts := strings.Split(v, ".")
	if len(parts) < 2 {
		return false
	}
	for _, p := range parts {
		if p == "" {
			return false
		}
		for _, r := range p {
			if r < '0' || r > '9' {
				return false
			}
		}
	}
	return true
}

func compareVersionNumbers(a, b string) int {
	aa, bb := strings.Split(strings.TrimSpace(strings.TrimPrefix(a, "V")), "."), strings.Split(strings.TrimSpace(strings.TrimPrefix(b, "V")), ".")
	n := len(aa)
	if len(bb) > n {
		n = len(bb)
	}
	for i := 0; i < n; i++ {
		var av, bv uint64
		if i < len(aa) {
			av, _ = strconv.ParseUint(leadingDigits(aa[i]), 10, 64)
		}
		if i < len(bb) {
			bv, _ = strconv.ParseUint(leadingDigits(bb[i]), 10, 64)
		}
		if av < bv {
			return -1
		}
		if av > bv {
			return 1
		}
	}
	return 0
}

func leadingDigits(s string) string {
	var b strings.Builder
	for _, r := range s {
		if r < '0' || r > '9' {
			break
		}
		b.WriteRune(r)
	}
	if b.Len() == 0 {
		return "0"
	}
	return b.String()
}

func (a *App) persistVersionStatus(st VersionStatus) {
	if a.diagDir == "" || a.session == "" {
		return
	}
	path := filepath.Join(a.diagDir, "VersionStatus-"+a.session+".json")
	b, err := json.MarshalIndent(st, "", "  ")
	if err != nil {
		return
	}
	b = append(b, '\n')
	if err := os.WriteFile(path, b, 0644); err == nil {
		a.mu.Lock()
		a.versionStatusPath = path
		a.mu.Unlock()
	}
}

func versionStatusTextKey(state string) string {
	switch state {
	case versionStateCurrent:
		return "version.status.current"
	case versionStateUpdateAvailable:
		return "version.status.update"
	case versionStateAhead:
		return "version.status.ahead"
	case versionStateChecking:
		return "version.status.checking"
	default:
		return "version.status.unknown"
	}
}
