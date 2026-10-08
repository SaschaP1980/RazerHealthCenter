[CmdletBinding()]
param(
    [string]$InventoryPath,
    [string]$OutputPath,
    [string]$JsonOutputPath,
    [string]$GateOutputPath,
    [string]$ProgressOutputPath,
    [switch]$ExitWithCode
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'SilentlyContinue'

$ScriptVersion = '1.4.1'
$BaselineDate  = '2026-09-10'
$VendorId      = '1532'

$Baseline = [ordered]@{
    RzDev            = '1.0.0.78'
    RzCommonKnown    = @('1.0.0.73','1.0.0.76')
    ChromaRoot       = '4.0.1.08260816'
    ChromaCore       = '4.0.1.08260816'
    ChromaDevices    = '4.0.1.07221608'
    ChromaStream     = '1.3.3'
    ChromaBroadcast  = '4.0.1'
    GameManager      = '3.14.0.1109'
    RzComDriver      = '23.0.6.0'
    LampArrayExeHash = 'CE2F7204D755E96E82887909288E0A6E3EB9566467C31994D3D393D946204700'
    LampArrayDllHash = '9D7A188C3F836C6CF20D35AC8DF7E988BA418EF47608C2A297E00FD21C333692'
    GameManagerHash  = '418747688ECABBCEB438EC1C18109C0F3640044A2F83AF2C6C0F74906A63F6A4'
    RzComDriverHash  = 'D17BBC15E025BCEE12948655ED5956BFE855019E626E497DD10ED40CB9A5E0DC'
}

# Device identities are supplied by the persistent read-only Setup inventory.
# The health engine contains no product-specific VID/PID allowlist.
if (-not $InventoryPath -or -not (Test-Path -LiteralPath $InventoryPath)) {
    throw 'Geräteinventar fehlt. Setup-Scan muss vor dem Health-Check ausgeführt werden.'
}
try { $DeviceInventory = Get-Content -LiteralPath $InventoryPath -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop }
catch { throw "Geräteinventar nicht lesbar: $($_.Exception.Message)" }
if ([int]$DeviceInventory.schemaVersion -lt 2 -or [string]$DeviceInventory.vendorId -ne $VendorId) { throw 'Geräteinventar ist inkompatibel. Setup-Scan muss mit dem aktuellen Scanner erneut ausgeführt werden.' }
$DeviceConnections = @($DeviceInventory.connections)
$DeviceProducts = @($DeviceInventory.products)
$RequiredProducts = @($DeviceProducts | Where-Object { $_.required })
# Only connection paths associated with currently required products become
# Health requirements. Unrelated historical Razer devices may remain in the
# Setup inventory for traceability without creating false DriverStore gates.
$DevicePids = @($RequiredProducts | ForEach-Object { @($_.connectionPids) } | ForEach-Object { ([string]$_).ToUpperInvariant() } | Where-Object { $_ -match '^[0-9A-F]{4}$' } | Sort-Object -Unique)
$RelevantConnections = @($DeviceConnections | Where-Object { $DevicePids -contains ([string]$_.pid).ToUpperInvariant() })
# Gate 2 must only validate Razer-owned DriverStore packages. Windows inbox
# INF files (keyboard.inf/input.inf/hidserv.inf/msmouse.inf/usb.inf, etc.) are
# valid for Windows-Inbox-HID devices and must not be searched in the
# Razer OEM package set. Scanner schema 2 persists the domains separately; the
# regex fallback is retained for forward/backward diagnostic resilience.
$InventoryInfNames = @(
    $RelevantConnections | ForEach-Object {
        if ($_.PSObject.Properties.Name -contains 'razerDriverInfNames') {
            @($_.razerDriverInfNames)
        } else {
            @($_.driverInfNames) | Where-Object { $_ -match '(?i)^(?:rzdevu_[0-9a-f]{4}_[a-z0-9]+|rzcommonu)\.inf$' }
        }
    } | ForEach-Object { ([string]$_).ToLowerInvariant() } |
        Where-Object { $_ -match '(?i)^(?:rzdevu_[0-9a-f]{4}_[a-z0-9]+|rzcommonu)\.inf$' } |
        Sort-Object -Unique
)
$InventoryServiceNames = @($RelevantConnections | ForEach-Object { @($_.serviceNames) } | ForEach-Object { [string]$_ } | Where-Object { $_ -match '^(?i)Rz(?:Dev_[0-9a-f]{4}|Common)$' } | Sort-Object -Unique)
$RequiresRzCommon = @($RelevantConnections | Where-Object {
    ($_.PSObject.Properties.Name -contains 'driverStack' -and [string]$_.driverStack -ieq 'razer-filter') -or
    ($_.PSObject.Properties.Name -contains 'capabilities' -and $_.capabilities -and [bool]$_.capabilities.requiresRzControl)
}).Count -gt 0
if ($RequiresRzCommon -and $InventoryServiceNames -notcontains 'RzCommon') { $InventoryServiceNames += 'RzCommon' }
$LogicalProductIds = @($DeviceInventory.logicalProductIds | ForEach-Object { [string]$_ } | Where-Object { $_ -match '^\d+$' } | Sort-Object -Unique)
if ($DevicePids.Count -eq 0 -or $RequiredProducts.Count -eq 0) { throw 'Geräteinventar enthält keine prüfbaren Razer-Produkte.' }

function Get-InventoryConnection {
    param([string]$DevicePid)
    return @($RelevantConnections | Where-Object { ([string]$_.pid).ToUpperInvariant() -eq ([string]$DevicePid).ToUpperInvariant() } | Select-Object -First 1)
}

function Get-ConnectionCapability {
    param([object]$Connection,[string]$Name,[bool]$Fallback=$false)
    if (-not $Connection) { return $Fallback }
    try {
        if ($Connection.PSObject.Properties.Name -contains 'capabilities' -and $Connection.capabilities) {
            $prop = $Connection.capabilities.PSObject.Properties[$Name]
            if ($prop) { return [bool]$prop.Value }
        }
    } catch {}
    return $Fallback
}

function Get-ConnectionType {
    param([object]$Connection)
    if (-not $Connection) { return 'unknown' }
    try {
        if ($Connection.PSObject.Properties.Name -contains 'connectionType' -and [string]$Connection.connectionType) {
            return [string]$Connection.connectionType
        }
    } catch {}
    return 'unknown'
}

function Test-ConnectionUsesRazerStack {
    param([object]$Connection)
    if (-not $Connection) { return $false }
    try {
        if ($Connection.PSObject.Properties.Name -contains 'driverStack') {
            return ([string]$Connection.driverStack -ieq 'razer-filter')
        }
    } catch {}
    $pid = ([string]$Connection.pid).ToLowerInvariant()
    $hasInf = @($Connection.driverInfNames | Where-Object { $_ -match "(?i)^rzdevu_${pid}_" }).Count -gt 0
    $hasSvc = @($Connection.serviceNames | Where-Object { $_ -ieq "RzDev_$pid" }).Count -gt 0
    return ($hasInf -or $hasSvc)
}

$Checks = New-Object System.Collections.Generic.List[object]
$Details = New-Object System.Collections.Generic.List[string]

# Permission-aware gate tracking. The default check runs unelevated. If a
# genuinely read-only data source is denied by Windows, the affected gate is
# marked ADMIN ERFORDERLICH instead of being misreported as FAILED.
$script:IsAdminGlobal = $false
$script:AdminGateReasons = @{}

function Test-IsAccessDenied {
    param([object]$ErrorRecord)
    if (-not $ErrorRecord) { return $false }
    $msg = ''
    try { $msg = [string]$ErrorRecord.Exception.Message } catch { $msg = [string]$ErrorRecord }
    return ($msg -match '(?i)access\s+is\s+denied|access\s+denied|unauthorized|zugriff\s+(wurde\s+)?verweigert|administrator|privilege|berechtigung')
}

function Mark-AdminGate {
    param([int]$Index,[string]$Reason)
    if ($script:IsAdminGlobal) { return }
    if ($Index -lt 1 -or $Index -gt 13) { return }
    if (-not $script:AdminGateReasons.ContainsKey($Index)) {
        $script:AdminGateReasons[$Index] = New-Object System.Collections.Generic.List[string]
    }
    if ($Reason) { $script:AdminGateReasons[$Index].Add($Reason) | Out-Null }
}

function Test-GateNeedsAdmin {
    param([int]$Index)
    return (-not $script:IsAdminGlobal -and $script:AdminGateReasons.ContainsKey($Index))
}

function Get-GateAdminDetail {
    param([int]$Index)
    if (-not (Test-GateNeedsAdmin $Index)) { return '' }
    $reasons = @($script:AdminGateReasons[$Index] | Select-Object -Unique)
    if ($reasons.Count -eq 0) { return 'Windows hat eine benötigte read-only Abfrage ohne Elevation nicht vollständig freigegeben.' }
    return (($reasons | Select-Object -First 3) -join ' | ')
}

function Add-Check {
    param(
        [string]$Section,
        [ValidateSet('PASS','WARN','FAIL','INFO','UNKNOWN')][string]$Status,
        [string]$Name,
        [string]$Actual,
        [string]$Expected,
        [string]$Detail = ''
    )
    $Checks.Add([pscustomobject]@{
        Section  = $Section
        Status   = $Status
        Check    = $Name
        Actual   = $Actual
        Expected = $Expected
        Detail   = $Detail
    }) | Out-Null
}

function Add-Detail {
    param([string]$Text)
    $Details.Add($Text) | Out-Null
}

function Get-FileVersionSafe {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return '' }
    try {
        $v = (Get-Item -LiteralPath $Path).VersionInfo.FileVersion
        if (-not $v) { $v = (Get-Item -LiteralPath $Path).VersionInfo.ProductVersion }
        return [string]$v
    } catch { return '' }
}

function Get-SignatureSummary {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try {
        $sig = Get-AuthenticodeSignature -FilePath $Path
        $subject = ''
        if ($sig.SignerCertificate) { $subject = $sig.SignerCertificate.Subject }
        return [pscustomobject]@{ Status=[string]$sig.Status; Subject=[string]$subject }
    } catch {
        return [pscustomobject]@{ Status='Unknown'; Subject='' }
    }
}

function Compare-BaselineVersion {
    param(
        [string]$Section,
        [string]$Name,
        [string]$Actual,
        [string]$KnownGood
    )
    if (-not $Actual) {
        Add-Check $Section 'UNKNOWN' $Name 'nicht ermittelbar' $KnownGood 'Version konnte nicht gelesen werden.'
    } elseif ($Actual -eq $KnownGood) {
        Add-Check $Section 'PASS' $Name $Actual $KnownGood 'Entspricht dem dokumentierten Known-Good-Stand.'
    } else {
        Add-Check $Section 'WARN' $Name $Actual $KnownGood 'Abweichung vom 2026-09-07-Baselinewert. Eine neuere/andere legitime Razer-Version ist nicht automatisch fehlerhaft.'
    }
}

$script:ServiceSnapshot = $null
$script:ServiceSnapshotQueryOK = $false

function Get-ServiceByDisplayOrName {
    param([string]$Name)
    if ($null -ne $script:ServiceSnapshot) {
        return $script:ServiceSnapshot | Where-Object { $_.Name -eq $Name -or $_.DisplayName -eq $Name } | Select-Object -First 1
    }
    try {
        return Get-CimInstance Win32_Service -ErrorAction Stop | Where-Object { $_.Name -eq $Name -or $_.DisplayName -eq $Name } | Select-Object -First 1
    } catch {
        if (Test-IsAccessDenied $_) {
            foreach ($i in @(8,9,10)) { Mark-AdminGate $i "Win32_Service nicht vollständig lesbar: $Name" }
        }
        return $null
    }
}

function Test-ServiceExpectation {
    param(
        [string]$DisplayOrName,
        [string]$ExpectedState,
        [string]$ExpectedStartMode,
        [bool]$Required = $true,
        [string]$Note = ''
    )
    $svc = Get-ServiceByDisplayOrName $DisplayOrName
    if (-not $svc) {
        $st = if ($Required) { 'FAIL' } else { 'INFO' }
        Add-Check 'Services' $st $DisplayOrName 'nicht gefunden' "$ExpectedState / $ExpectedStartMode" $Note
        return
    }
    $actual = "$($svc.State) / $($svc.StartMode)"
    $stateOK = ($ExpectedState -eq '*' -or [string]$svc.State -eq $ExpectedState)
    $modeOK  = ($ExpectedStartMode -eq '*' -or [string]$svc.StartMode -eq $ExpectedStartMode)
    if ($stateOK -and $modeOK) {
        Add-Check 'Services' 'PASS' $DisplayOrName $actual "$ExpectedState / $ExpectedStartMode" $Note
    } else {
        $status = if ($Required) { 'FAIL' } else { 'WARN' }
        Add-Check 'Services' $status $DisplayOrName $actual "$ExpectedState / $ExpectedStartMode" $Note
    }
}

function Get-RegistryValue32 {
    param([string]$SubKey,[string]$ValueName)
    try {
        $base = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
            [Microsoft.Win32.RegistryHive]::LocalMachine,
            [Microsoft.Win32.RegistryView]::Registry32
        )
        $key = $base.OpenSubKey($SubKey)
        if (-not $key) { $base.Close(); return $null }
        $value = $key.GetValue($ValueName, $null, [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
        $key.Close(); $base.Close()
        return $value
    } catch {
        if (Test-IsAccessDenied $_) { Mark-AdminGate 7 "HKLM Registry32 nicht vollständig lesbar: $SubKey" }
        return $null
    }
}

function Get-DeviceFilters {
    param([string]$InstanceId)
    $path = "Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Enum\$InstanceId"
    try {
        $p = Get-ItemProperty -LiteralPath $path -ErrorAction Stop
        $upper = @()
        $lower = @()
        if ($p.PSObject.Properties.Name -contains 'UpperFilters') { $upper = @($p.UpperFilters) }
        if ($p.PSObject.Properties.Name -contains 'LowerFilters') { $lower = @($p.LowerFilters) }
        return [pscustomobject]@{ Upper=$upper; Lower=$lower; Accessible=$true; AccessDenied=$false }
    } catch {
        $denied = Test-IsAccessDenied $_
        if ($denied) { Mark-AdminGate 6 "Gerätefilter-Registry nicht lesbar: $InstanceId" }
        return [pscustomobject]@{ Upper=@(); Lower=@(); Accessible=$false; AccessDenied=$denied }
    }
}

function Test-ContainsCI {
    param([object[]]$Values,[string]$Expected)
    foreach ($v in @($Values)) {
        if ([string]$v -ieq $Expected) { return $true }
    }
    return $false
}

function Get-LatestLogModuleState {
    param([string[]]$Lines,[string]$ModuleName)
    $escaped = [regex]::Escape($ModuleName)
    $candidates = @($Lines | Where-Object { $_ -match $escaped -and $_ -match 'isInstalled' })
    if (-not $candidates -or $candidates.Count -eq 0) { return $null }
    $line = [string]$candidates[-1]
    $normalized = $line -replace '\\"','"'
    $installed = $null
    $version = ''
    if ($normalized -match '"isInstalled"\s*:\s*(true|false)') { $installed = ($matches[1] -eq 'true') }
    if ($normalized -match '"version"\s*:\s*"([^"]*)"') { $version = $matches[1] }
    return [pscustomobject]@{ Installed=$installed; Version=$version; Line=$line }
}

function Add-ModuleLogCheck {
    param([string[]]$Lines,[string]$ModuleName,[string]$KnownGoodVersion,[string]$Kind='Module')
    $s = Get-LatestLogModuleState -Lines $Lines -ModuleName $ModuleName
    if (-not $s) {
        Add-Check 'AppEngine log' 'UNKNOWN' "$Kind $ModuleName" 'kein aktueller Treffer' "isInstalled=true; Baseline $KnownGoodVersion" 'Logbeleg fehlt; dies allein beweist keinen Defekt.'
        return
    }
    if ($null -eq $s.Installed) {
        Add-Check 'AppEngine log' 'UNKNOWN' "$Kind $ModuleName" 'Treffer nicht parsebar' "isInstalled=true; Baseline $KnownGoodVersion" $s.Line
        return
    }
    if (-not $s.Installed) {
        Add-Check 'AppEngine log' 'FAIL' "$Kind $ModuleName" "isInstalled=false; Version=$($s.Version)" "isInstalled=true; Baseline $KnownGoodVersion" $s.Line
        return
    }
    if ($s.Version -eq $KnownGoodVersion) {
        Add-Check 'AppEngine log' 'PASS' "$Kind $ModuleName" "isInstalled=true; Version=$($s.Version)" "isInstalled=true; Baseline $KnownGoodVersion" ''
    } else {
        Add-Check 'AppEngine log' 'WARN' "$Kind $ModuleName" "isInstalled=true; Version=$($s.Version)" "isInstalled=true; Baseline $KnownGoodVersion" 'Installiert, aber Version weicht vom dokumentierten Baselinewert ab.'
    }
}

function Get-LatestPowerForId {
    param([string[]]$Lines,[string]$ProductId)
    $escaped=[regex]::Escape($ProductId)
    $pattern = 'productId["\\]*\s*[:=]\s*' + $escaped + '|product_id["\\]*\s*[:=]\s*' + $escaped
    $hits = @($Lines | Where-Object { $_ -match $pattern -and $_ -match 'isPowerOn' })
    if (-not $hits -or $hits.Count -eq 0) { return $null }
    $line = ([string]$hits[-1]) -replace '\\"','"'
    $value = $null
    if ($line -match '"isPowerOn"\s*:\s*(true|false)') { $value = ($matches[1] -eq 'true') }
    return [pscustomobject]@{ Value=$value; Line=$line }
}

function Get-Sha256Shared {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return '' }
    $fs = $null
    $sha = $null
    try {
        # Maximum sharing: this read must not block Razer from reading, writing,
        # replacing or deleting its own runtime file while the check is active.
        $share = [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
        $fs = New-Object System.IO.FileStream($Path,[System.IO.FileMode]::Open,[System.IO.FileAccess]::Read,$share)
        $sha = [System.Security.Cryptography.SHA256]::Create()
        $bytes = $sha.ComputeHash($fs)
        return ([System.BitConverter]::ToString($bytes)).Replace('-','')
    } catch {
        return ''
    } finally {
        if ($sha) { $sha.Dispose() }
        if ($fs) { $fs.Dispose() }
    }
}

# -----------------------------------------------------------------------------
# Progressive 13-gate protocol for the tray UI
# -----------------------------------------------------------------------------
$GateNames = @(
    'Razer AppEngine',
    'Razer DriverStore',
    'Kernel-Treiber RzDev / RzCommon',
    'Razer Geräte Live-PnP',
    'RZVIRTUAL / RZCONTROL',
    'Upper-/LowerFilters',
    'Chroma Registry',
    'Chroma Dienste',
    'Synapse Dienste',
    'Razer Game Manager',
    'RzComDriver',
    'Produkt-/Power-State',
    'LampArray Runtime'
)

function Get-CheckExact {
    param([string]$Section,[string]$Name)
    return @($Checks | Where-Object { $_.Section -eq $Section -and $_.Check -eq $Name } | Select-Object -Last 1)
}

function Test-ExactChecksPass {
    param([string]$Section,[string[]]$Names)
    foreach ($n in $Names) {
        $c = @(Get-CheckExact $Section $n)
        if (-not $c -or $c.Count -eq 0 -or [string]$c[0].Status -ne 'PASS') { return $false }
    }
    return $true
}

function Write-ProgressLine {
    param([string]$Line)
    if (-not $ProgressOutputPath) { return }
    $fs = $null
    $sw = $null
    try {
        $parent = Split-Path -Parent $ProgressOutputPath
        if ($parent -and -not (Test-Path -LiteralPath $parent)) { [System.IO.Directory]::CreateDirectory($parent) | Out-Null }
        $share = [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
        $fs = New-Object System.IO.FileStream($ProgressOutputPath,[System.IO.FileMode]::Append,[System.IO.FileAccess]::Write,$share)
        $sw = New-Object System.IO.StreamWriter($fs,(New-Object System.Text.UTF8Encoding($false)))
        $sw.WriteLine($Line)
        $sw.Flush()
    } catch {
        # Progress is best-effort. It must never affect the health result.
    } finally {
        if ($sw) { $sw.Dispose() }
        elseif ($fs) { $fs.Dispose() }
    }
}

if ($ProgressOutputPath) {
    try {
        $parent = Split-Path -Parent $ProgressOutputPath
        if ($parent -and -not (Test-Path -LiteralPath $parent)) { [System.IO.Directory]::CreateDirectory($parent) | Out-Null }
        [System.IO.File]::WriteAllText($ProgressOutputPath, "RHM_PROGRESS_V2`r`n", (New-Object System.Text.UTF8Encoding($false)))
    } catch {}
}

function Start-GateProgress {
    param([int]$Index)
    if ($Index -lt 1 -or $Index -gt 13) { return }
    Write-ProgressLine "GATE|$Index|CHECKING||$($GateNames[$Index-1])"
}

function Get-GateEvaluation {
    param([int]$Index)
    $name = $GateNames[$Index-1]
    $passed = $false
    $detail = ''

    switch ($Index) {
        1 {
            $c = @(Get-CheckExact 'AppEngine' 'RazerAppEngine process')
            $passed = ($c.Count -gt 0 -and $c[0].Status -eq 'PASS')
            $detail = $(if($passed){'AppEngine ist aktiv.'}else{'RazerAppEngine.exe ist nicht aktiv oder konnte nicht sicher erkannt werden.'})
        }
        2 {
            $c = @($Checks | Where-Object { $_.Section -eq 'DriverStore' -and $_.Check -like 'Inventar Razer-INF *' })
            $driverStoreUnknown = @($Checks | Where-Object { $_.Section -eq 'DriverStore' -and $_.Status -eq 'UNKNOWN' })
            $passed = (@($c | Where-Object { $_.Status -eq 'FAIL' -or $_.Status -eq 'UNKNOWN' }).Count -eq 0 -and $driverStoreUnknown.Count -eq 0)
            $detail = $(if($c.Count -gt 0){"$($c.Count) inventarisierte Razer-Treiberpakete geprüft."}else{'Kein Razer-spezifisches DriverStore-Paket für die inventarisierten Verbindungswege erforderlich.'})
        }
        3 {
            $c = @($Checks | Where-Object { $_.Section -eq 'Kernel drivers' -and $_.Check -match ' (binary|service)$' })
            $passed = ($c.Count -gt 0 -and @($c | Where-Object { $_.Status -eq 'FAIL' -or $_.Status -eq 'UNKNOWN' }).Count -eq 0)
            $detail = "$($c.Count) inventarisierte RzDev/RzCommon-Prüfungen."
        }
        4 {
            $productChecks = @($Checks | Where-Object { $_.Section -eq 'Live PnP' -and $_.Check -like 'Produkt * Verbindung' })
            $problems = @($Checks | Where-Object { $_.Section -eq 'Live PnP' -and $_.Check -match '^PID [0-9A-F]{4} ProblemCode$' })
            $passed = ($productChecks.Count -eq $RequiredProducts.Count -and @($productChecks | Where-Object { $_.Status -ne 'PASS' }).Count -eq 0 -and @($problems | Where-Object { $_.Status -eq 'FAIL' }).Count -eq 0)
            $detail = "$($productChecks.Count)/$($RequiredProducts.Count) inventarisierte Produkte mit gültigem Live-Pfad."
        }
        5 {
            $c = @($Checks | Where-Object { $_.Section -eq 'Live PnP' -and $_.Check -match '(RZVIRTUAL|RZCONTROL|Razer-bound nodes|Razer binding stack)' })
            $passed = ($c.Count -gt 0 -and @($c | Where-Object { $_.Status -eq 'FAIL' -or $_.Status -eq 'UNKNOWN' }).Count -eq 0)
            $applicable = @($c | Where-Object { $_.Status -eq 'PASS' }).Count
            $na = @($c | Where-Object { $_.Status -eq 'INFO' }).Count
            $detail = "$applicable relevante Binding-Prüfungen bestanden; $na nicht anwendbar/informativ."
        }
        6 {
            $c = @($Checks | Where-Object { $_.Section -eq 'Device filters' })
            $passed = ($c.Count -gt 0 -and @($c | Where-Object { $_.Status -eq 'FAIL' -or $_.Status -eq 'UNKNOWN' }).Count -eq 0)
            $applicable = @($c | Where-Object { $_.Status -eq 'PASS' }).Count
            $na = @($c | Where-Object { $_.Status -eq 'INFO' }).Count
            $detail = "$applicable relevante Filterpfade bestanden; $na nicht anwendbar."
        }
        7 {
            $reg = @($Checks | Where-Object { $_.Section -eq 'Chroma registry (32-bit)' })
            $mods = @($Checks | Where-Object { $_.Section -eq 'AppEngine log' -and $_.Check -match '^Module Razer Chroma ' })
            $explicitFalse = (@($mods | Where-Object { $_.Status -eq 'FAIL' }).Count -gt 0)
            $passed = ($reg.Count -eq 4 -and @($reg | Where-Object { $_.Status -eq 'FAIL' -or $_.Status -eq 'UNKNOWN' }).Count -eq 0 -and -not $explicitFalse)
            $detail = $(if($explicitFalse){'Registry vorhanden, aber AppEngine meldet mindestens ein Chroma-Modul explizit als isInstalled=false.'}else{"$($reg.Count)/4 Registry-Komponenten gefunden."})
        }
        8 {
            $required = @('Razer Chroma SDK Diagnostic Service','Razer Chroma SDK Server','Razer Chroma SDK Service','Razer Chroma Stream Server')
            $passed = Test-ExactChecksPass 'Services' $required
            $detail = 'SDK Diagnostic/Server/Service plus Stream-Server-Zustand.'
        }
        9 {
            $required = @('RazerExperienceService','Razer Elevation Service')
            $passed = Test-ExactChecksPass 'Services' $required
            $detail = 'Experience- und Elevation-Service.'
        }
        10 {
            $svc = @(Get-CheckExact 'Services' 'Razer Game Manager Service 3')
            $log = @(Get-CheckExact 'AppEngine log' 'Module RazerGameManager')
            $explicitFalse = ($log.Count -gt 0 -and $log[0].Status -eq 'FAIL')
            $passed = ($svc.Count -gt 0 -and $svc[0].Status -eq 'PASS' -and -not $explicitFalse)
            $svcActual = $(if($svc.Count -gt 0){[string]$svc[0].Actual}else{'nicht gefunden'})
            $detail = $(if($log.Count -gt 0){"Service=$svcActual; AppEngine=$($log[0].Actual)"}else{"Service=$svcActual; kein aktueller AppEngine-Modultreffer."})
        }
        11 {
            $un = @(Get-CheckExact 'RzComDriver' 'RzCom uninstaller')
            $evidence = @(Get-CheckExact 'RzComDriver' 'RzCom driver evidence')
            $log = @(Get-CheckExact 'AppEngine log' 'Driver RzComDriver')
            $logPositive = ($log.Count -gt 0 -and ($log[0].Status -eq 'PASS' -or $log[0].Status -eq 'WARN'))
            $logFalse = ($log.Count -gt 0 -and $log[0].Status -eq 'FAIL')
            $directPositive = ($evidence.Count -gt 0 -and $evidence[0].Status -eq 'PASS')
            $unPositive = ($un.Count -gt 0 -and $un[0].Status -eq 'PASS')
            $passed = (($directPositive -or $logPositive) -and -not $logFalse)
            $detail = "DriverEvidence=$directPositive; AppEngineInstalled=$logPositive; UninstallRegistration=$unPositive"
        }
        12 {
            $power = @($Checks | Where-Object { $_.Section -eq 'Power state' -and $_.Check -like 'Logical product * isPowerOn' })
            $powerFalse = (@($power | Where-Object { $_.Status -eq 'WARN' }).Count -gt 0)
            $powerTrue = (@($power | Where-Object { $_.Status -eq 'PASS' }).Count -gt 0 -and -not $powerFalse)
            $passed = (-not $powerFalse)
            $detail = $(if($powerTrue){'Inventarisierte logische Produktzustände sind aktiv.'}elseif($powerFalse){'Mindestens ein inventarisierter logischer Produktzustand ist false.'}else{'Kein parsebarer inventarisierter Power-State; reine Zusatzdiagnose.'})
        }
        13 {
            $c = @(Get-CheckExact 'LampArray' 'LampArray runtime files')
            $passed = ($c.Count -gt 0 -and $c[0].Status -eq 'PASS')
            $detail = $(if($c.Count -gt 0){[string]$c[0].Actual}else{'Runtime nicht auswertbar.'})
        }
    }

    $status = 'FAILED'
    if ($passed) {
        $status = 'PASS'
    } elseif (Test-GateNeedsAdmin $Index) {
        $status = 'ADMIN ERFORDERLICH'
        $adminDetail = Get-GateAdminDetail $Index
        if ($adminDetail) { $detail = $adminDetail }
    }
    return [pscustomobject]@{ Name=$name; Status=$status; Detail=$detail }
}

function Get-GateChecks {
    param([int]$Index)
    switch ($Index) {
        1 { return @($Checks | Where-Object { $_.Section -eq 'AppEngine' }) }
        2 { return @($Checks | Where-Object { $_.Section -eq 'DriverStore' }) }
        3 { return @($Checks | Where-Object { $_.Section -eq 'Kernel drivers' }) }
        4 { return @($Checks | Where-Object { $_.Section -eq 'Live PnP' -and ($_.Check -like 'Produkt * Verbindung' -or $_.Check -match 'physical nodes|ProblemCode') }) }
        5 { return @($Checks | Where-Object { $_.Section -eq 'Live PnP' -and ($_.Check -match 'RZVIRTUAL' -or $_.Check -match 'RZCONTROL' -or $_.Check -match 'Razer-bound nodes') }) }
        6 { return @($Checks | Where-Object { $_.Section -eq 'Device filters' }) }
        7 { return @($Checks | Where-Object { $_.Section -eq 'Chroma registry (32-bit)' -or ($_.Section -eq 'AppEngine log' -and $_.Check -match '^Module Razer Chroma ') }) }
        8 { return @($Checks | Where-Object { $_.Section -eq 'Services' -and $_.Check -match 'Chroma' }) }
        9 { return @($Checks | Where-Object { $_.Section -eq 'Services' -and ($_.Check -eq 'RazerExperienceService' -or $_.Check -eq 'Razer Elevation Service') }) }
        10 { return @($Checks | Where-Object { ($_.Section -eq 'Services' -and $_.Check -match 'Game Manager') -or ($_.Section -eq 'AppEngine log' -and $_.Check -match 'RazerGameManager') }) }
        11 { return @($Checks | Where-Object { $_.Section -eq 'RzComDriver' -or ($_.Section -eq 'AppEngine log' -and $_.Check -match 'RzComDriver') }) }
        12 { return @($Checks | Where-Object { $_.Section -eq 'Power state' }) }
        13 { return @($Checks | Where-Object { $_.Section -eq 'LampArray' }) }
    }
    return @()
}

function Get-GateSeverity {
    param([int]$Index,[string]$EngineStatus)
    if ($EngineStatus -eq 'FAILED') { return 'FAILED' }
    if ($EngineStatus -eq 'ADMIN ERFORDERLICH') { return 'UNKLAR' }
    $gateChecks = @(Get-GateChecks $Index)
    if (@($gateChecks | Where-Object { $_.Status -eq 'FAIL' }).Count -gt 0) { return 'FAILED' }
    if (@($gateChecks | Where-Object { $_.Status -eq 'UNKNOWN' }).Count -gt 0) { return 'UNKLAR' }
    if (@($gateChecks | Where-Object { $_.Status -eq 'WARN' }).Count -gt 0) { return 'HINWEIS' }
    if ($EngineStatus -eq 'PASS') { return 'PASS' }
    return 'UNKLAR'
}

function Complete-GateProgress {
    param([int]$Index)
    $g = Get-GateEvaluation $Index
    $severity = Get-GateSeverity $Index $g.Status
    # V2 progress contract: engine lifecycle result and final user-facing severity
    # are emitted together. Once this line exists, the gate's visible state is
    # final for the remainder of this run.
    Write-ProgressLine "GATE|$Index|$($g.Status)|$severity|$($g.Name)"
}

# -----------------------------------------------------------------------------
# Parallel source snapshot collection (Windows PowerShell 5.1 compatible)
# -----------------------------------------------------------------------------
# Expensive independent read-only data sources are collected in a runspace pool
# with a hard cap of four workers. Gate evaluation itself remains deterministic
# and uses these snapshots; no Razer/Windows state is modified.
$ParallelWorkerLimit = 4
$script:ProbePool = [runspacefactory]::CreateRunspacePool(1, $ParallelWorkerLimit)
$script:ProbePool.Open()
$script:Probes = @{}

function Start-Probe {
    param([string]$Name,[scriptblock]$ScriptBlock,[object[]]$Arguments=@())
    $ps = [powershell]::Create()
    $ps.RunspacePool = $script:ProbePool
    [void]$ps.AddScript($ScriptBlock.ToString())
    foreach ($arg in @($Arguments)) { [void]$ps.AddArgument($arg) }
    $async = $ps.BeginInvoke()
    $script:Probes[$Name] = [pscustomobject]@{ Name=$Name; PS=$ps; Async=$async; Started=(Get-Date); Result=$null; Received=$false }
}

function Receive-Probe {
    param([string]$Name)
    $p = $script:Probes[$Name]
    if (-not $p) { return $null }
    if ($p.Received) { return $p.Result }
    try {
        $out = @($p.PS.EndInvoke($p.Async))
        if ($out.Count -gt 0) { $p.Result = $out[-1] }
    } catch {
        $p.Result = [pscustomobject]@{ ProbeError = [string]$_.Exception.Message }
    } finally {
        $p.Received = $true
        $observedMs = ((Get-Date) - $p.Started).TotalMilliseconds
        $hasExec = ($null -ne $p.Result -and $p.Result.PSObject.Properties.Name -contains 'ExecutionMs')
        $hasStart = ($null -ne $p.Result -and $p.Result.PSObject.Properties.Name -contains 'ProbeStarted')
        $hasMode = ($null -ne $p.Result -and $p.Result.PSObject.Properties.Name -contains 'QueryMode')
        if ($hasExec) {
            $queueMs = 0
            if ($hasStart) { $queueMs = ([datetime]$p.Result.ProbeStarted - [datetime]$p.Started).TotalMilliseconds }
            $mode = $(if($hasMode){[string]$p.Result.QueryMode}else{'default'})
            Add-Detail ("Parallel probe {0}: exec={1:N0} ms; queue={2:N0} ms; observed={3:N0} ms; mode={4}" -f $Name,[double]$p.Result.ExecutionMs,$queueMs,$observedMs,$mode)
        } else {
            Add-Detail ("Parallel probe {0}: observed={1:N0} ms" -f $Name,$observedMs)
        }
        try { $p.PS.Dispose() } catch {}
    }
    return $p.Result
}

function Close-Probes {
    foreach ($kv in @($script:Probes.GetEnumerator())) {
        $p = $kv.Value
        if (-not $p.Received) {
            try { [void](Receive-Probe $p.Name) } catch {}
        }
    }
    try { $script:ProbePool.Close() } catch {}
    try { $script:ProbePool.Dispose() } catch {}
}

# All gates have source work in flight from this point. The UI can therefore
# show genuine parallel activity instead of a simulated sequential animation.
for ($i=1; $i -le 13; $i++) { Start-GateProgress $i }
Write-ProgressLine "RUN|PARALLEL|$ParallelWorkerLimit"
Add-Detail "Parallel snapshot collection enabled; max workers=$ParallelWorkerLimit."

Start-Probe 'app' {
    $probeStarted=Get-Date; $sw=[Diagnostics.Stopwatch]::StartNew()
    $procErr=''; $osErr=''; $procs=@(); $os=$null; $wdl=@()
    try { $procs=@(Get-CimInstance Win32_Process -Filter "Name='RazerAppEngine.exe'" -Property Name,ProcessId,ExecutablePath,CommandLine,CreationDate,ParentProcessId -ErrorAction Stop) } catch { $procErr=[string]$_.Exception.Message }
    try { $wdl=@(Get-CimInstance Win32_Process -Filter "Name='razerwdl.exe'" -Property Name,ProcessId,ExecutablePath,CommandLine,CreationDate,ParentProcessId -ErrorAction Stop) } catch {}
    try { $os=Get-CimInstance Win32_OperatingSystem -Property Caption,Version,BuildNumber -ErrorAction Stop } catch { $osErr=[string]$_.Exception.Message }
    $sw.Stop()
    [pscustomobject]@{ Processes=$procs; WdlProcesses=$wdl; OS=$os; ProcessError=$procErr; OSError=$osErr; ProbeStarted=$probeStarted; ExecutionMs=$sw.Elapsed.TotalMilliseconds; QueryMode='filtered' }
}

Start-Probe 'driverstore' {
    param($systemRoot)
    $probeStarted=Get-Date; $sw=[Diagnostics.Stopwatch]::StartNew()
    $txt=''; $exit=$null; $err=''
    try {
        $txt = (& (Join-Path $systemRoot 'System32\pnputil.exe') /enum-drivers 2>&1 | Out-String -Width 4096)
        $exit=$LASTEXITCODE
    } catch { $err=[string]$_.Exception.Message }
    $sw.Stop()
    [pscustomobject]@{ Text=$txt; Exit=$exit; Error=$err; ProbeStarted=$probeStarted; ExecutionMs=$sw.Elapsed.TotalMilliseconds; QueryMode='pnputil' }
} @($env:SystemRoot)

Start-Probe 'kernel' {
    param($serviceCsv)
    $probeStarted=Get-Date; $sw=[Diagnostics.Stopwatch]::StartNew()
    $items=@(); $err=''; $mode='filtered'
    $names=@($serviceCsv -split '\|' | Where-Object {$_})
    $parts=@($names | ForEach-Object { $q=$_.Replace("'","''"); "Name='$q'" })
    $parts += "Name LIKE '%RzCom%'"; $parts += "DisplayName LIKE '%RzCom%'"
    $filter=($parts -join ' OR ')
    try { $items=@(Get-CimInstance Win32_SystemDriver -Filter $filter -Property Name,DisplayName,State,StartMode,PathName -ErrorAction Stop) }
    catch { $firstErr=[string]$_.Exception.Message; if($firstErr -match '(?i)access|denied|zugriff|berechtigung'){$err=$firstErr}else{$mode='fallback-full';try{$items=@(Get-CimInstance Win32_SystemDriver -ErrorAction Stop)}catch{$err="$firstErr | fallback: $([string]$_.Exception.Message)"}} }
    $sw.Stop(); [pscustomobject]@{Drivers=$items;Error=$err;ProbeStarted=$probeStarted;ExecutionMs=$sw.Elapsed.TotalMilliseconds;QueryMode=$mode;Returned=$items.Count}
} @(($InventoryServiceNames -join '|'))

Start-Probe 'pnp' {
    param($vendorId,$pidCsv)
    $probeStarted=Get-Date; $sw=[Diagnostics.Stopwatch]::StartNew()
    $pids=@($pidCsv -split '\|' | Where-Object {$_})
    $pnp=@();$signed=@();$pnpErr='';$signedErr='';$pnpMode='filtered';$signedMode='filtered'
    $pnpParts=@($pids | ForEach-Object { "PNPDeviceID LIKE '%VID_${vendorId}&PID_${_}%'" })
    $signedParts=@($pids | ForEach-Object { "DeviceID LIKE '%VID_${vendorId}&PID_${_}%'" })
    $pnpFilter=($pnpParts -join ' OR ')
    $signedFilter='('+($signedParts -join ' OR ')+") OR (DriverProviderName LIKE 'Razer%' AND (DeviceName LIKE '%RzCom%' OR DeviceName LIKE '%Communication%' OR DeviceName LIKE '%Control%' OR InfName LIKE '%RzCom%'))"
    try{$pnp=@(Get-CimInstance Win32_PnPEntity -Filter $pnpFilter -Property PNPDeviceID,ConfigManagerErrorCode,Name,Service -ErrorAction Stop)}catch{$firstErr=[string]$_.Exception.Message;if($firstErr -match '(?i)access|denied|zugriff|berechtigung'){$pnpErr=$firstErr}else{$pnpMode='fallback-full';try{$pnp=@(Get-CimInstance Win32_PnPEntity -ErrorAction Stop)}catch{$pnpErr="$firstErr | fallback: $([string]$_.Exception.Message)"}}}
    try{$signed=@(Get-CimInstance Win32_PnPSignedDriver -Filter $signedFilter -Property DeviceID,DriverProviderName,InfName,DeviceName,DriverVersion -ErrorAction Stop)}catch{$firstErr=[string]$_.Exception.Message;if($firstErr -match '(?i)access|denied|zugriff|berechtigung'){$signedErr=$firstErr}else{$signedMode='fallback-full';try{$signed=@(Get-CimInstance Win32_PnPSignedDriver -ErrorAction Stop)}catch{$signedErr="$firstErr | fallback: $([string]$_.Exception.Message)"}}}
    $sw.Stop();[pscustomobject]@{Pnp=$pnp;Signed=$signed;PnpError=$pnpErr;SignedError=$signedErr;ProbeStarted=$probeStarted;ExecutionMs=$sw.Elapsed.TotalMilliseconds;QueryMode=("pnp:{0};signed:{1}" -f $pnpMode,$signedMode);PnpReturned=$pnp.Count;SignedReturned=$signed.Count}
} @($VendorId,($DevicePids -join '|'))

Start-Probe 'services' {
    $probeStarted=Get-Date; $sw=[Diagnostics.Stopwatch]::StartNew()
    $items=@(); $err=''
    $serviceNames=@('Razer Chroma SDK Diagnostic Service','Razer Chroma SDK Server','Razer Chroma SDK Service','Razer Chroma Stream Server','RazerExperienceService','Razer Game Manager Service 3','Razer Elevation Service','RGS')
    $parts=@($serviceNames | ForEach-Object {
        $q=$_.Replace("'","''")
        "(Name='$q' OR DisplayName='$q')"
    })
    $filter=($parts -join ' OR ')
    try { $items=@(Get-CimInstance Win32_Service -Filter $filter -Property Name,DisplayName,State,StartMode,PathName -ErrorAction Stop) } catch { $err=[string]$_.Exception.Message }
    $sw.Stop()
    [pscustomobject]@{ Services=$items; Error=$err; ProbeStarted=$probeStarted; ExecutionMs=$sw.Elapsed.TotalMilliseconds; QueryMode='filtered'; Returned=$items.Count }
}

Start-Probe 'log' {
    param($localAppData)
    $probeStarted=Get-Date; $sw=[Diagnostics.Stopwatch]::StartNew()
    $path=Join-Path $localAppData 'Razer\RazerAppEngine\User Data\Logs\main.log'
    $lines=@(); $err=''; $exists=Test-Path -LiteralPath $path
    if ($exists) { try { $lines=@(Get-Content -LiteralPath $path -Tail 8000 -ErrorAction Stop) } catch { $err=[string]$_.Exception.Message } }
    $sw.Stop()
    [pscustomobject]@{ Path=$path; Exists=$exists; Lines=$lines; Error=$err; ProbeStarted=$probeStarted; ExecutionMs=$sw.Elapsed.TotalMilliseconds; QueryMode='tail-8000' }
} @($env:LOCALAPPDATA)

# Registry is quick, but collecting it concurrently avoids serial latency and
# gives the registry gate an independent snapshot timestamp.
Start-Probe 'registry' {
    $probeStarted=Get-Date; $sw=[Diagnostics.Stopwatch]::StartNew()
    $entries=@(
      @{Name='Chroma SDK Root ProductVersion';Key='SOFTWARE\Razer Chroma SDK';Value='ProductVersion'},
      @{Name='CoreComponents ProductVersion';Key='SOFTWARE\Razer Chroma SDK\CoreComponents';Value='ProductVersion'},
      @{Name='DeviceComponents ProductVersion';Key='SOFTWARE\Razer Chroma SDK\DeviceComponents';Value='ProductVersion'},
      @{Name='StreamingComponents ProductVersion';Key='SOFTWARE\Razer Chroma SDK\StreamingComponents';Value='ProductVersion'}
    )
    $vals=@(); $err=''
    try {
      $base=[Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::LocalMachine,[Microsoft.Win32.RegistryView]::Registry32)
      foreach($e in $entries){
        $key=$base.OpenSubKey($e.Key); $v=$null
        if($key){ $v=$key.GetValue($e.Value,$null,[Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames); $key.Close() }
        $vals += [pscustomobject]@{Name=$e.Name;Key=$e.Key;Value=$v}
      }
      $base.Close()
    } catch { $err=[string]$_.Exception.Message }
    $sw.Stop()
    [pscustomobject]@{ Values=$vals; Error=$err; ProbeStarted=$probeStarted; ExecutionMs=$sw.Elapsed.TotalMilliseconds; QueryMode='registry32' }
}

# -----------------------------------------------------------------------------
# Header / environment
# -----------------------------------------------------------------------------
$now = Get-Date
$isWindows = ($env:OS -eq 'Windows_NT')
if (-not $isWindows) {
    Write-Error 'Dieses Skript ist fuer Windows vorgesehen.'
    if ($ExitWithCode) { exit 2 }
    return
}

$isAdmin = $false
try {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($id)
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
} catch {}

$script:IsAdminGlobal = $isAdmin
Add-Check 'Environment' 'INFO' 'PowerShell elevated' ([string]$isAdmin) 'optional' 'Der Standardcheck ist bewusst unelevated. Nur tatsächlich verweigerte read-only Datenquellen führen zu ADMIN ERFORDERLICH.'
Add-Check 'Environment' 'INFO' 'HealthCheck version' $ScriptVersion $ScriptVersion "Baseline $BaselineDate"

$appProbe = Receive-Probe 'app'
$os = $appProbe.OS
if ($os) {
    Add-Check 'Environment' 'INFO' 'Windows' "$($os.Caption) | $($os.Version) | Build $($os.BuildNumber)" 'nur Information' ''
}

# -----------------------------------------------------------------------------
# AppEngine process / version
# -----------------------------------------------------------------------------
Start-GateProgress 1
$appProcs = @($appProbe.Processes)
if ($appProbe.ProcessError -and $appProbe.ProcessError -match '(?i)access|denied|zugriff|berechtigung') { Mark-AdminGate 1 'Win32_Process nicht vollständig lesbar.' }
if ($appProcs.Count -gt 0) {
    Add-Check 'AppEngine' 'PASS' 'RazerAppEngine process' "$($appProcs.Count) Prozess(e) aktiv" 'mindestens 1' ''
    $main = $appProcs | Where-Object { $_.CommandLine -notmatch '--type=' } | Sort-Object CreationDate | Select-Object -Last 1
    if (-not $main) { $main = $appProcs | Select-Object -First 1 }
    $appPath = [string]$main.ExecutablePath
    if ($appPath -and (Test-Path -LiteralPath $appPath)) {
        $appVer = Get-FileVersionSafe $appPath
        $appPackage = ''
        try {
            $parentName = Split-Path -Leaf (Split-Path -Parent $appPath)
            if ($parentName -match '^app-(.+)$') { $appPackage = [string]$Matches[1] }
        } catch {}
        if ($appPackage) {
            Add-Check 'AppEngine' 'INFO' 'RazerAppEngine package version' $appPackage 'nur Information' 'Paket-/AppEngine-Version der aktuell laufenden Installation.'
        } else {
            Add-Check 'AppEngine' 'INFO' 'RazerAppEngine package version' 'nicht ermittelbar' 'nur Information' 'Kein app-<Version>-Paketpfad aus dem laufenden Prozess ableitbar.'
        }
        Add-Check 'AppEngine' 'INFO' 'RazerAppEngine file version' $appVer 'nur Information' 'Windows FileVersion der aktuell laufenden RazerAppEngine.exe; nicht mit der Paketversion vergleichen.'
        Add-Detail "AppEngine main PID: $($main.ProcessId); Path: $appPath; PackageVersion=$appPackage; FileVersion=$appVer"
    } else {
        Add-Check 'AppEngine' 'UNKNOWN' 'RazerAppEngine executable path' 'nicht ermittelbar' 'vorhanden' ''
    }
} else {
    Add-Check 'AppEngine' 'WARN' 'RazerAppEngine process' 'nicht aktiv' 'mindestens 1' 'Synapse/Chroma koennen bei beendetem AppEngine nicht vollstaendig live validiert werden.'
}

# -----------------------------------------------------------------------------
Complete-GateProgress 1

# DriverStore packages via pnputil (language-independent filename matching)
# -----------------------------------------------------------------------------
Start-GateProgress 2
$pnputilText = ''
$pnputilBlocks = @()
$storeMap = @{}
$pnputilUsable = $false
$pnputilExit = $null
$driverProbe = Receive-Probe 'driverstore'
try {
    $pnputilText = [string]$driverProbe.Text
    $pnputilExit = $driverProbe.Exit
    $pnputilBlocks = @([regex]::Split($pnputilText, '(?:\r?\n){2,}') | Where-Object { $_.Trim() })
    $pnputilUsable = ($pnputilExit -eq 0 -and $pnputilText -and $pnputilText -notmatch '(?i)access\s+is\s+denied|zugriff\s+(wurde\s+)?verweigert|requires\s+administrator|administrator privileges')
    if ($driverProbe.Error -and $driverProbe.Error -match '(?i)access|denied|zugriff|berechtigung') { Mark-AdminGate 2 'PnPUtil DriverStore-Enumeration benötigt erhöhte Leserechte.'; Mark-AdminGate 6 'PnPUtil OEM-INF-Mapping benötigt erhöhte Leserechte.' }
} catch {}
if (-not $pnputilUsable -and -not $isAdmin) {
    Mark-AdminGate 2 "PnPUtil /enum-drivers nicht unelevated auswertbar (Exit=$pnputilExit)."
    Mark-AdminGate 6 "PnPUtil OEM-INF-Mapping nicht unelevated auswertbar (Exit=$pnputilExit)."
}

if (-not $pnputilUsable) {
    Add-Check 'DriverStore' 'UNKNOWN' 'pnputil /enum-drivers' ($(if($pnputilText){"nicht auswertbar; Exit=$pnputilExit"}else{'keine Ausgabe'})) 'auswertbare DriverStore-Liste' 'Keine fehlenden Treiber ableiten, solange die Enumeration selbst nicht verlässlich war.'
} else {
    if ($InventoryInfNames.Count -eq 0) {
        Add-Check 'DriverStore' 'INFO' 'Razer DriverStore requirement' 'nicht anwendbar' 'keine Razer-OEM-Pakete für die inventarisierten Verbindungswege erforderlich' 'Windows-Inbox-HID-Treiber sind gültige Gerätetreiber und werden nicht als fehlende Razer-Pakete gewertet.'
    }
    foreach ($inf in $InventoryInfNames) {
        $present = ($pnputilText -match [regex]::Escape($inf))
        Add-Check 'DriverStore' ($(if($present){'PASS'}else{'FAIL'})) "Inventar Razer-INF $inf" ($(if($present){'vorhanden'}else{'FEHLT'})) 'im beim Setup inventarisierten Razer-DriverStore vorhanden' 'Nur Razer-eigene rzdevu_*/rzcommonu-Pakete werden als DriverStore-Anforderung bewertet.'
    }
    foreach ($block in $pnputilBlocks) {
        $oem=[regex]::Match($block,'(?i)\boem\d+\.inf\b'); if(-not $oem.Success){continue}
        foreach($orig in $InventoryInfNames){if($block -match [regex]::Escape($orig)){$storeMap[$oem.Value.ToLowerInvariant()]=$orig.ToLowerInvariant()}}
    }
    Add-Detail ("DriverStore mapping: " + (($storeMap.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name)=$($_.Value)" }) -join '; '))
}

# -----------------------------------------------------------------------------
Complete-GateProgress 2

# Kernel driver binaries and services
# -----------------------------------------------------------------------------
Start-GateProgress 3
$driverItems = @($InventoryServiceNames | ForEach-Object { @{ Name=$_; File=(Join-Path $env:SystemRoot ("System32\drivers\{0}.sys" -f $_)); Known=$(if($_ -like 'RzDev_*'){$Baseline.RzDev}else{''}) } })
foreach ($d in $driverItems) {
    if (-not (Test-Path -LiteralPath $d.File)) { Add-Check 'Kernel drivers' 'FAIL' "$($d.Name) binary" 'FEHLT' $d.File ''; continue }
    $ver=Get-FileVersionSafe $d.File; Add-Check 'Kernel drivers' 'PASS' "$($d.Name) binary" "vorhanden; Version=$ver" $d.File ''
    if($d.Name -like 'RzDev_*' -and $d.Known -and $ver -ne $d.Known){Add-Check 'Kernel drivers' 'WARN' "$($d.Name) baseline version" $ver $d.Known 'Version weicht ab; das ist nicht automatisch ein Fehler.'}
    $sig=Get-SignatureSummary $d.File; if($sig){$sigStatus=if($sig.Status -eq 'Valid'){'PASS'}else{'WARN'};Add-Check 'Kernel drivers' $sigStatus "$($d.Name) Authenticode" "$($sig.Status) | $($sig.Subject)" 'gültige Razer/Microsoft-Treibersignatur' ''}
}
$kernelProbe=Receive-Probe 'kernel';$systemDrivers=@($kernelProbe.Drivers);$systemDriversQueryOK=(-not [string]$kernelProbe.Error)
if(-not $systemDriversQueryOK -and [string]$kernelProbe.Error -match '(?i)access|denied|zugriff|berechtigung'){Mark-AdminGate 3 'Win32_SystemDriver nicht vollständig lesbar.';Mark-AdminGate 11 'RzComDriver-Systemtreiber nicht unelevated auswertbar.'}
foreach($name in $InventoryServiceNames){$drv=$systemDrivers|Where-Object{$_.Name -ieq $name}|Select-Object -First 1;if(-not $drv){if(-not $systemDriversQueryOK){Add-Check 'Kernel drivers' 'UNKNOWN' "$name service" 'Systemtreiber-Abfrage nicht verfügbar' 'registriert (Demand/Manual)' ''}else{Add-Check 'Kernel drivers' 'FAIL' "$name service" 'nicht registriert' 'registriert (Demand/Manual)' ''}}else{$mode=[string]$drv.StartMode;$status=if($mode -eq 'Manual'){'PASS'}else{'WARN'};Add-Check 'Kernel drivers' $status "$name service" "$($drv.State) / $mode / $($drv.PathName)" 'vorhanden; StartMode Manual' ''}}

# -----------------------------------------------------------------------------
Complete-GateProgress 3

# Live PnP / binding / filters
# -----------------------------------------------------------------------------
Start-GateProgress 4
$pnpProbe = Receive-Probe 'pnp'
$pnp = @($pnpProbe.Pnp)
$signed = @($pnpProbe.Signed)
$pnpQueryOK = (-not [string]$pnpProbe.PnpError)
$signedQueryOK = (-not [string]$pnpProbe.SignedError)
if (-not $pnpQueryOK -and [string]$pnpProbe.PnpError -match '(?i)access|denied|zugriff|berechtigung') { foreach ($i in @(4,5,6,11,12)) { Mark-AdminGate $i 'Win32_PnPEntity nicht vollständig lesbar.' } }
if (-not $signedQueryOK -and [string]$pnpProbe.SignedError -match '(?i)access|denied|zugriff|berechtigung') { foreach ($i in @(5,6,11)) { Mark-AdminGate $i 'Win32_PnPSignedDriver nicht vollständig lesbar.' } }

$activePids = New-Object System.Collections.Generic.List[string]
foreach ($devicePid in $DevicePids) {
    $pattern="VID_$VendorId&PID_$devicePid"
    $physical=@($pnp|Where-Object{$_.PNPDeviceID -match "^(USB|HID)\\" -and $_.PNPDeviceID -like "*$pattern*"})
    if($physical.Count -gt 0){$activePids.Add($devicePid)|Out-Null}
    $conn=@(Get-InventoryConnection $devicePid)
    $label=if($conn.Count -gt 0){[string]$conn[0].modelName}else{"Razer Gerät PID $devicePid"}
    $connType=if($conn.Count -gt 0){Get-ConnectionType $conn[0]}else{'unknown'}
    $driverStack=if($conn.Count -gt 0 -and (Test-ConnectionUsesRazerStack $conn[0])){'razer-filter'}else{'windows-inbox'}
    Add-Check 'Live PnP' 'INFO' "PID $devicePid Verbindungsprofil" "$connType / $driverStack" 'aus Setup-Inventar; reine Einordnung' $label
    Add-Check 'Live PnP' ($(if($physical.Count -gt 0){'PASS'}else{'INFO'})) "PID $devicePid physical nodes" "$($physical.Count) present" 'mindestens bei physisch enumeriertem Verbindungsweg vorhanden' $label
    $bad=@($physical|Where-Object{$_.ConfigManagerErrorCode -ne 0})
    if($physical.Count -gt 0){Add-Check 'Live PnP' ($(if($bad.Count -eq 0){'PASS'}else{'FAIL'})) "PID $devicePid ProblemCode" ($(if($bad.Count -eq 0){'alle 0'}else{"$($bad.Count) Node(s) != 0"})) 'alle vorhandenen Nodes = 0' (($bad|Select-Object -First 8|ForEach-Object{"$($_.Name) [$($_.PNPDeviceID)] Code=$($_.ConfigManagerErrorCode)"}) -join ' | ')}
}
foreach($product in $RequiredProducts){
    $pp=@($product.connectionPids|ForEach-Object{([string]$_).ToUpperInvariant()})
    $live=@($activePids|Where-Object{$pp -contains $_})
    $name=[string]$product.name
    if($live.Count -gt 0){Add-Check 'Live PnP' 'PASS' "Produkt $name Verbindung" ($live -join ', ') 'mindestens ein inventarisierter Verbindungsweg aktiv' ''}
    else{Add-Check 'Live PnP' ($(if($pnpQueryOK){'FAIL'}else{'UNKNOWN'})) "Produkt $name Verbindung" 'kein inventarisierter Verbindungsweg aktiv' ($pp -join ' oder ') 'Setup-Profil definiert die gültigen Verbindungswege.'}
}

foreach ($devicePid in $activePids) {
    $pattern = "VID_$VendorId&PID_$devicePid"
    $connArr = @(Get-InventoryConnection $devicePid)
    $conn = if ($connArr.Count -gt 0) { $connArr[0] } else { $null }
    $usesRazerStack = Test-ConnectionUsesRazerStack $conn
    $requiresRzVirtual = Get-ConnectionCapability $conn 'requiresRzVirtual' $usesRazerStack
    $requiresRzControl = Get-ConnectionCapability $conn 'requiresRzControl' $usesRazerStack
    $requiresRazerBoundNodes = Get-ConnectionCapability $conn 'requiresRazerBoundNodes' $usesRazerStack
    $requiresDeviceFilters = Get-ConnectionCapability $conn 'requiresDeviceFilters' $usesRazerStack
    $connType = Get-ConnectionType $conn
    $model = if ($conn) { [string]$conn.modelName } else { "Razer Gerät PID $devicePid" }

    # A Windows-inbox HID path is a valid Razer device path. Do not require the
    # RzDev/RZVIRTUAL/RZCONTROL stack unless Setup evidence says that this
    # connection actually uses it.
    if (-not ($requiresRzVirtual -or $requiresRzControl -or $requiresRazerBoundNodes)) {
        Add-Check 'Live PnP' 'INFO' "PID $devicePid Razer binding stack" 'nicht anwendbar' 'kein Razer-Filterstack für diesen Verbindungsweg inventarisiert' "$model | $connType | Windows-Inbox-HID"
    } else {
        $rzv = @($pnp | Where-Object { $_.PNPDeviceID -like "RZVIRTUAL\*$pattern*" })
        $rzc = @($pnp | Where-Object { $_.PNPDeviceID -like "RZCONTROL\*$pattern*" })

        if ($requiresRzVirtual) {
            Add-Check 'Live PnP' ($(if($rzv.Count -gt 0){'PASS'}else{'FAIL'})) "PID $devicePid RZVIRTUAL" ($(if($rzv.Count -gt 0){"present ($($rzv.Count))"}else{'FEHLT'})) 'present; Service RzDev_PID' "$model | $connType"
            foreach ($node in $rzv) {
                $sd = $signed | Where-Object { $_.DeviceID -ieq $node.PNPDeviceID } | Select-Object -First 1
                $actual = if ($sd) { "$($sd.DriverProviderName) / $($sd.InfName) / $($node.Service)" } else { "Service=$($node.Service)" }
                $ok = ([string]$node.Service -ieq "RzDev_$($devicePid.ToLowerInvariant())")
                Add-Check 'Live PnP' ($(if($ok){'PASS'}else{'FAIL'})) "PID $devicePid RZVIRTUAL service" $actual "RzDev_$($devicePid.ToLowerInvariant())" ''
            }
        } else {
            Add-Check 'Live PnP' 'INFO' "PID $devicePid RZVIRTUAL" 'nicht erforderlich' 'laut Setup-Profil nicht erforderlich' "$model | $connType"
        }

        if ($requiresRzControl) {
            Add-Check 'Live PnP' ($(if($rzc.Count -gt 0){'PASS'}else{'FAIL'})) "PID $devicePid RZCONTROL" ($(if($rzc.Count -gt 0){"present ($($rzc.Count))"}else{'FEHLT'})) 'present; Service RzCommon' "$model | $connType"
            foreach ($node in $rzc) {
                $sd = $signed | Where-Object { $_.DeviceID -ieq $node.PNPDeviceID } | Select-Object -First 1
                $actual = if ($sd) { "$($sd.DriverProviderName) / $($sd.InfName) / $($node.Service)" } else { "Service=$($node.Service)" }
                $ok = ([string]$node.Service -ieq 'RzCommon')
                Add-Check 'Live PnP' ($(if($ok){'PASS'}else{'FAIL'})) "PID $devicePid RZCONTROL service" $actual 'RzCommon' ''
            }
        } else {
            Add-Check 'Live PnP' 'INFO' "PID $devicePid RZCONTROL" 'nicht erforderlich' 'laut Setup-Profil nicht erforderlich' "$model | $connType"
        }

        $relevantSigned = @($signed | Where-Object { $_.DeviceID -like "*$pattern*" -and $_.DriverProviderName -match '(?i)Razer' })
        if ($requiresRazerBoundNodes) {
            Add-Check 'Live PnP' ($(if($relevantSigned.Count -gt 0){'PASS'}else{'FAIL'})) "PID $devicePid Razer-bound nodes" "$($relevantSigned.Count)" '> 0' (($relevantSigned | Select-Object -First 12 | ForEach-Object { "$($_.DeviceName) [$($_.InfName)] $($_.DriverVersion)" }) -join ' | ')
        } else {
            Add-Check 'Live PnP' 'INFO' "PID $devicePid Razer-bound nodes" 'nicht erforderlich' 'Windows-Inbox-HID-Verbindungsweg' "$model | $connType"
        }
    }

    if (-not $requiresDeviceFilters) {
        Add-Check 'Device filters' 'INFO' "PID $devicePid Upper/LowerFilters" 'nicht anwendbar' 'kein Razer-Filterstack für diesen Verbindungsweg inventarisiert' "$model | $connType | Windows-Inbox-HID"
        continue
    }

    $relevantSignedForFilters = @($signed | Where-Object { $_.DeviceID -like "*$pattern*" -and $_.DriverProviderName -match '(?i)Razer' })
    $filterExpectedCount = 0
    $filterGoodCount = 0
    $filterUnknownCount = 0
    $filterFailures = New-Object System.Collections.Generic.List[string]

    foreach ($sd in $relevantSignedForFilters) {
        $published = ([string]$sd.InfName).ToLowerInvariant()
        if (-not $storeMap.ContainsKey($published)) { continue }
        $orig = [string]$storeMap[$published]
        $direction = ''
        if ($orig -match '_(dkm|mpos)\.inf$') { $direction = 'Lower' }
        elseif ($orig -match '_(kbd|kbd2|mou|mou2)\.inf$') { $direction = 'Upper' }
        else { continue }

        $filterExpectedCount++
        $f = Get-DeviceFilters -InstanceId ([string]$sd.DeviceID)
        if (-not $f.Accessible) {
            $filterUnknownCount++
            $filterFailures.Add("$orig [$($sd.DeviceID)] Registry nicht lesbar") | Out-Null
            continue
        }
        $expectedFilter = "RzDev_$($devicePid.ToLowerInvariant())"
        $ok = $false
        if ($direction -eq 'Upper') { $ok = Test-ContainsCI $f.Upper $expectedFilter }
        if ($direction -eq 'Lower') { $ok = Test-ContainsCI $f.Lower $expectedFilter }
        if ($ok) {
            $filterGoodCount++
        } else {
            $actualFilters = "Upper=[$(@($f.Upper) -join ',')]; Lower=[$(@($f.Lower) -join ',')]"
            $filterFailures.Add("$orig [$($sd.DeviceID)] erwartet $direction=$expectedFilter; $actualFilters") | Out-Null
        }
    }

    if ($filterExpectedCount -eq 0) {
        Add-Check 'Device filters' 'UNKNOWN' "PID $devicePid Upper/LowerFilters" 'Razer-Filterstack inventarisiert, aber keine mappbaren aktiven Razer-INF-Nodes' 'DKM/MPos LowerFilter; KBD/MOU UpperFilter = RzDev_PID' 'pnputil OEM->Original-INF-Mapping konnte für den aktiven Razer-Filterpfad nicht hergestellt werden.'
    } elseif ($filterGoodCount -eq $filterExpectedCount) {
        Add-Check 'Device filters' 'PASS' "PID $devicePid Upper/LowerFilters" "$filterGoodCount/$filterExpectedCount korrekt" 'alle mappbaren Filter korrekt' "$model | $connType"
    } elseif (($filterGoodCount + $filterUnknownCount) -eq $filterExpectedCount -and $filterUnknownCount -gt 0) {
        Add-Check 'Device filters' 'UNKNOWN' "PID $devicePid Upper/LowerFilters" "$filterGoodCount korrekt; $filterUnknownCount nicht lesbar" 'alle mappbaren Filter korrekt' ($filterFailures -join ' | ')
    } else {
        Add-Check 'Device filters' 'FAIL' "PID $devicePid Upper/LowerFilters" "$filterGoodCount/$filterExpectedCount korrekt" 'DKM/MPos LowerFilter; KBD/MOU UpperFilter = RzDev_PID' ($filterFailures -join ' | ')
    }
}

# -----------------------------------------------------------------------------
Complete-GateProgress 4
Start-GateProgress 5
Complete-GateProgress 5
Start-GateProgress 6
Complete-GateProgress 6

# Chroma SDK Registry 32-bit view
# -----------------------------------------------------------------------------
Start-GateProgress 7
$regChecks = @(
    @{ Name='Chroma SDK Root ProductVersion'; Key='SOFTWARE\Razer Chroma SDK';                    Value='ProductVersion'; Known=$Baseline.ChromaRoot },
    @{ Name='CoreComponents ProductVersion';   Key='SOFTWARE\Razer Chroma SDK\CoreComponents';    Value='ProductVersion'; Known=$Baseline.ChromaCore },
    @{ Name='DeviceComponents ProductVersion'; Key='SOFTWARE\Razer Chroma SDK\DeviceComponents';  Value='ProductVersion'; Known=$Baseline.ChromaDevices },
    @{ Name='StreamingComponents ProductVersion'; Key='SOFTWARE\Razer Chroma SDK\StreamingComponents'; Value='ProductVersion'; Known=$Baseline.ChromaStream }
)
$registryProbe = Receive-Probe 'registry'
if ($registryProbe.Error -and [string]$registryProbe.Error -match '(?i)access|denied|zugriff|berechtigung') { Mark-AdminGate 7 'HKLM Registry32 nicht vollständig lesbar.' }
foreach ($r in $regChecks) {
    $snap = @($registryProbe.Values | Where-Object { $_.Name -eq $r.Name } | Select-Object -First 1)
    $v = if ($snap.Count -gt 0) { $snap[0].Value } else { $null }
    if ($null -eq $v -or [string]$v -eq '') {
        Add-Check 'Chroma registry (32-bit)' 'FAIL' $r.Name 'FEHLT/nicht lesbar' $r.Known $r.Key
    } elseif ([string]$v -eq $r.Known) {
        Add-Check 'Chroma registry (32-bit)' 'PASS' $r.Name ([string]$v) $r.Known $r.Key
    } else {
        Add-Check 'Chroma registry (32-bit)' 'WARN' $r.Name ([string]$v) $r.Known 'Abweichende Version; nicht automatisch defekt, wenn Razer inzwischen aktualisiert wurde.'
    }
}

# -----------------------------------------------------------------------------
# Services: minimal documented successful state
# -----------------------------------------------------------------------------
Start-GateProgress 8
$serviceProbe = Receive-Probe 'services'
$script:ServiceSnapshot = @($serviceProbe.Services)
$script:ServiceSnapshotQueryOK = (-not [string]$serviceProbe.Error)
if (-not $script:ServiceSnapshotQueryOK -and [string]$serviceProbe.Error -match '(?i)access|denied|zugriff|berechtigung') { foreach ($i in @(8,9,10)) { Mark-AdminGate $i 'Win32_Service nicht vollständig lesbar.' } }
Test-ServiceExpectation 'Razer Chroma SDK Diagnostic Service' 'Running' 'Auto' $true
Test-ServiceExpectation 'Razer Chroma SDK Server'             'Running' 'Auto' $true
Test-ServiceExpectation 'Razer Chroma SDK Service'            'Running' 'Auto' $true
Test-ServiceExpectation 'Razer Chroma Stream Server'           'Stopped' 'Manual' $true 'Stopped/Manual ist der dokumentierte Sollzustand.'
Test-ServiceExpectation 'RazerExperienceService'               'Running' 'Auto' $true
Test-ServiceExpectation 'Razer Game Manager Service 3'         'Running' 'Auto' $true
Test-ServiceExpectation 'Razer Elevation Service'              '*'       'Manual' $true 'Kann je nach Nutzung Running oder Stopped sein.'
Test-ServiceExpectation 'RGS'                                  '*'       'Auto' $false 'War im Home-Zustand vorhanden, gehoert aber nicht zum minimalen erfolgreichen Sollzustand des Runbooks.'

# -----------------------------------------------------------------------------
Complete-GateProgress 8
Start-GateProgress 9
Complete-GateProgress 9

# RzComDriver independent evidence
# -----------------------------------------------------------------------------
Start-GateProgress 11
$rzComUninstaller = 'C:\ProgramData\Razer\Synapse3\Uninstall\RzComDriver\RzComDriverUninstaller.exe'
if (Test-Path -LiteralPath $rzComUninstaller) {
    $v = Get-FileVersionSafe $rzComUninstaller
    Add-Check 'RzComDriver' 'PASS' 'RzCom uninstaller' "vorhanden; Version=$v" $rzComUninstaller ''
} else {
    Add-Check 'RzComDriver' 'FAIL' 'RzCom uninstaller' 'FEHLT' $rzComUninstaller 'Der finale funktionierende Zustand enthielt diesen UninstallPath.'
}

$rzComSystem = @($systemDrivers | Where-Object { $_.Name -match '(?i)RzCom' -or $_.DisplayName -match '(?i)RzCom' })
$rzComPnp = @($signed | Where-Object { $_.DriverProviderName -match '(?i)Razer' -and ($_.DeviceName -match '(?i)RzCom|Communication|Control' -or $_.InfName -match '(?i)RzCom') })
if ($rzComSystem.Count -gt 0 -or $rzComPnp.Count -gt 0) {
    Add-Check 'RzComDriver' 'PASS' 'RzCom driver evidence' "SystemDriver=$($rzComSystem.Count); PnP=$($rzComPnp.Count)" '> 0 evidence' (($rzComSystem | ForEach-Object { "$($_.Name) $($_.State) $($_.StartMode)" }) -join ' | ')
} else {
    Add-Check 'RzComDriver' 'WARN' 'RzCom driver evidence' 'kein Win32_SystemDriver/PnP Treffer' 'Treiberbeleg vorhanden' 'AppEngine-Log und UninstallPath werden zusaetzlich ausgewertet; WMI kann je nach Treibertyp wenig liefern.'
}

# -----------------------------------------------------------------------------
# AppEngine log: module recognition + power state
# -----------------------------------------------------------------------------
Start-GateProgress 10
Start-GateProgress 12
$logProbe = Receive-Probe 'log'
$mainLog = [string]$logProbe.Path
$logLines = @($logProbe.Lines)
if ($logProbe.Exists) {
    Add-Check 'AppEngine log' 'PASS' 'main.log' "vorhanden; Tail=$($logLines.Count) Zeilen" $mainLog ''
} else {
    Add-Check 'AppEngine log' 'UNKNOWN' 'main.log' 'nicht gefunden' $mainLog 'Logbasierte Module-/Power-Pruefung nicht moeglich.'
}

if ($logLines.Count -gt 0) {
    Add-ModuleLogCheck $logLines 'RazerGameManager'          $Baseline.GameManager 'Module'
    Add-ModuleLogCheck $logLines 'RzComDriver'              $Baseline.RzComDriver 'Driver'
    Add-ModuleLogCheck $logLines 'Razer Chroma SDK Core'    $Baseline.ChromaCore 'Module'
    Add-ModuleLogCheck $logLines 'Razer Chroma SDK Devices' $Baseline.ChromaDevices 'Module'
    Add-ModuleLogCheck $logLines 'Razer Chroma Stream'      $Baseline.ChromaStream 'Module'
    Add-ModuleLogCheck $logLines 'Razer Chroma Broadcast SDK' $Baseline.ChromaBroadcast 'Module'

    if($LogicalProductIds.Count -eq 0){
        Add-Check 'Power state' 'INFO' 'Logical products inventory' 'keine IDs im Setup-Scan beobachtet' 'reine Zusatzdiagnose' 'Power-State beeinflusst den Treiber-/PnP-Health nicht.'
    } else {
        foreach($logicalId in $LogicalProductIds){
            $power=Get-LatestPowerForId $logLines $logicalId
            if(-not $power){Add-Check 'Power state' 'UNKNOWN' "Logical product $logicalId isPowerOn" 'kein parsebarer aktueller Treffer' 'true when product is active' 'Setup-inventarisierte logische Produkt-ID.'}
            elseif($null -eq $power.Value){Add-Check 'Power state' 'UNKNOWN' "Logical product $logicalId isPowerOn" 'Treffer nicht parsebar' 'true when product is active' $power.Line}
            elseif($power.Value){Add-Check 'Power state' 'PASS' "Logical product $logicalId isPowerOn" 'true' 'true when product is active' ''}
            else{Add-Check 'Power state' 'WARN' "Logical product $logicalId isPowerOn" 'false' 'true when product is active' 'Separater Idle-/Power-State-Pfad; kein automatischer Treiberfehler.'}
        }
    }

    $lastFFI = @($logLines | Where-Object { $_ -match 'missing ffi handler' } | Select-Object -Last 1)
    if ($lastFFI.Count -gt 0) {
        Add-Check 'AppEngine log' 'INFO' 'missing ffi handler evidence' 'im Log-Tail vorhanden' 'kein aktueller Blocker' [string]$lastFFI[0]
    } else {
        Add-Check 'AppEngine log' 'PASS' 'missing ffi handler evidence' 'nicht im Log-Tail gefunden' 'kein aktueller Blocker' ''
    }
} else {
    if($LogicalProductIds.Count -eq 0){
        Add-Check 'Power state' 'INFO' 'Logical products inventory' 'keine IDs im Setup-Scan beobachtet' 'reine Zusatzdiagnose' 'Power-State beeinflusst den Treiber-/PnP-Health nicht.'
    } else {
        foreach($logicalId in $LogicalProductIds){
            Add-Check 'Power state' 'UNKNOWN' "Logical product $logicalId isPowerOn" 'AppEngine-Log nicht verfügbar' 'true when product is active' 'Setup-inventarisierte logische Produkt-ID; ohne Log kein Zustand ableitbar.'
        }
    }
}

# -----------------------------------------------------------------------------
Complete-GateProgress 7
Complete-GateProgress 10
Complete-GateProgress 11
Complete-GateProgress 12

# LampArray known files / hashes (strictly passive shared-read)
# -----------------------------------------------------------------------------
Start-GateProgress 13
$lampBase = Join-Path $env:LOCALAPPDATA 'Razer\RazerAppEngine\User Data\Apps\Common\LampArray'
$lampExePath = Join-Path $lampBase 'razerwdl.exe'
$lampDllCandidates = @()
try { $lampDllCandidates = @(Get-ChildItem -LiteralPath $lampBase -Filter 'rz_lamp_array*.dll' -File -ErrorAction Stop) } catch {}
$lampRuntimeOK = ((Test-Path -LiteralPath $lampExePath) -and $lampDllCandidates.Count -gt 0)
Add-Check 'LampArray' ($(if($lampRuntimeOK){'PASS'}else{'FAIL'})) 'LampArray runtime files' ($(if($lampRuntimeOK){"razerwdl.exe + $($lampDllCandidates.Count) LampArray-DLL(s) vorhanden"}else{'Runtime-Datei(en) fehlen'})) 'razerwdl.exe + mindestens eine rz_lamp_array*.dll' 'Versions-/Hashabweichungen werden separat nur als Kontext bewertet.'
$lampItems = @(
    @{ Name='razerwdl.exe'; File=(Join-Path $lampBase 'razerwdl.exe'); Hash=$Baseline.LampArrayExeHash },
    @{ Name='rz_lamp_array_v1.0.46.0.dll'; File=(Join-Path $lampBase 'rz_lamp_array_v1.0.46.0.dll'); Hash=$Baseline.LampArrayDllHash }
)
foreach ($li in $lampItems) {
    if (-not (Test-Path -LiteralPath $li.File)) {
        Add-Check 'LampArray' 'WARN' $li.Name 'FEHLT' 'vorhanden im 2026-09-07 Common/LampArray baseline' 'Kann bei neuerer Razer-Version durch andere Dateiversion ersetzt worden sein.'
        continue
    }
    $hash = ''
    $hash = Get-Sha256Shared $li.File
    if ($hash -eq $li.Hash) {
        Add-Check 'LampArray' 'PASS' "$($li.Name) SHA256" $hash $li.Hash 'Known-good baseline hash.'
    } else {
        Add-Check 'LampArray' 'WARN' "$($li.Name) SHA256" $hash $li.Hash 'Hash weicht vom dokumentierten Baselinewert ab; bei Razer-Update moeglich. Nicht automatisch ersetzen/loeschen.'
    }
}

$wdlProc = @($appProbe.WdlProcesses)
Add-Check 'LampArray' 'INFO' 'razerwdl.exe process' "$($wdlProc.Count) aktiv" 'nur Information' (($wdlProc | ForEach-Object { "PID=$($_.ProcessId), Parent=$($_.ParentProcessId), $($_.CommandLine)" }) -join ' | ')

# -----------------------------------------------------------------------------
Complete-GateProgress 13

# Cached direct installers - verify only when present
# -----------------------------------------------------------------------------
$cacheBase = Join-Path $env:LOCALAPPDATA 'Razer\RazerAppEngine\User Data\Apps\Common\Drivers'
$cached = @(
    @{ Name='RazerGameManager installer'; File=(Join-Path $cacheBase 'RazerGameManager_3.14.0.1109.exe'); Hash=$Baseline.GameManagerHash },
    @{ Name='RzComDriver installer'; File=(Join-Path $cacheBase 'RzComDriver_v23.0.6.0.exe'); Hash=$Baseline.RzComDriverHash }
)
foreach ($ci in $cached) {
    if (-not (Test-Path -LiteralPath $ci.File)) {
        Add-Check 'Installer cache' 'INFO' $ci.Name 'nicht vorhanden' 'optional; Cache darf fehlen' 'Fehlender Installer-Cache ist nach erfolgreicher Installation kein Health-Fehler.'
        continue
    }
    $hash = ''
    $hash = Get-Sha256Shared $ci.File
    $sig = Get-SignatureSummary $ci.File
    $hashOK = ($hash -eq $ci.Hash)
    $sigOK = ($sig -and $sig.Status -eq 'Valid' -and $sig.Subject -match '(?i)Razer')
    if ($hashOK -and $sigOK) {
        Add-Check 'Installer cache' 'PASS' $ci.Name "Hash OK; Signatur Valid; $($sig.Subject)" 'Known-good hash + gueltige Razer-Signatur' ''
    } else {
        Add-Check 'Installer cache' 'WARN' $ci.Name "HashOK=$hashOK; Signatur=$($sig.Status); Signer=$($sig.Subject); SHA256=$hash" 'Known-good hash + gueltige Razer-Signatur' 'Nicht ausfuehren, falls Verifikation fehlschlaegt.'
    }
}

# -----------------------------------------------------------------------------
# All source probes have now been consumed. Release runspace resources before
# report serialization so the monitor leaves no background workers behind.
Close-Probes

# -----------------------------------------------------------------------------
# Final 13-gate snapshot. The same evaluator drives both progressive UI events
# and the final machine-readable/report result, preventing divergent logic.
# -----------------------------------------------------------------------------
$script:Gates = @()
for ($i = 1; $i -le 13; $i++) {
    $script:Gates += (Get-GateEvaluation $i)
}

for ($i = 0; $i -lt @($script:Gates).Count; $i++) {
    $g = $script:Gates[$i]
    $sev = Get-GateSeverity ($i + 1) $g.Status
    $label = switch ($sev) {
        'PASS'    { 'BESTANDEN' }
        'HINWEIS' { 'HINWEIS' }
        'UNKLAR'  { 'UNKLAR' }
        default   { 'FEHLER' }
    }
    $g | Add-Member -NotePropertyName DisplayStatus -NotePropertyValue $label -Force
}

$gateContractOK = (@($script:Gates).Count -eq 13)
if (-not $gateContractOK) { Add-Detail "INTERNAL: Gate contract invalid: $(@($script:Gates).Count)/13 generated." }
$functionalFailed = @($script:Gates | Where-Object { $_.Status -eq 'FAILED' }).Count
$functionalAdmin = @($script:Gates | Where-Object { $_.Status -eq 'ADMIN ERFORDERLICH' }).Count
if (-not $gateContractOK) { $functionalFailed = [Math]::Max(1,$functionalFailed) }
$functionalOverall = 'PASS'
$functionalExitCode = 0
if ($functionalFailed -gt 0) {
    $functionalOverall = 'FAILED'
    $functionalExitCode = 2
} elseif ($functionalAdmin -gt 0) {
    $functionalOverall = 'ADMIN ERFORDERLICH'
    $functionalExitCode = 4
}
$overallLabel = $(if($functionalFailed -gt 0){'FEHLER'}else{'GESUND'})
Write-ProgressLine "RUN|DONE|$functionalOverall"

$failCount    = @($Checks | Where-Object Status -eq 'FAIL').Count
$warnCount    = @($Checks | Where-Object Status -eq 'WARN').Count
$unknownCount = @($Checks | Where-Object Status -eq 'UNKNOWN').Count
$passCount    = @($Checks | Where-Object Status -eq 'PASS').Count
$infoCount    = @($Checks | Where-Object Status -eq 'INFO').Count

$rawOverall = 'PASS'
if ($failCount -gt 0) { $rawOverall = 'FAIL' }
elseif ($warnCount -gt 0 -or $unknownCount -gt 0) { $rawOverall = 'WARN' }

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine('=== RAZER SYNAPSE + CHROMA HEALTH CHECK ===')
[void]$sb.AppendLine("Script version : $ScriptVersion")
[void]$sb.AppendLine("Baseline       : $BaselineDate handover")
[void]$sb.AppendLine("Timestamp      : $($now.ToString('yyyy-MM-dd HH:mm:ss.fff'))")
[void]$sb.AppendLine("Computer       : $env:COMPUTERNAME")
[void]$sb.AppendLine("User           : $env:USERDOMAIN\$env:USERNAME")
[void]$sb.AppendLine("Elevated       : $isAdmin")
[void]$sb.AppendLine()
[void]$sb.AppendLine("SYSTEMSTATUS    : $overallLabel")
[void]$sb.AppendLine("ENGINE OVERALL  : $functionalOverall")
[void]$sb.AppendLine("RAW DIAGNOSTIC : $rawOverall")
[void]$sb.AppendLine("PASS=$passCount  WARN=$warnCount  FAIL=$failCount  UNKNOWN=$unknownCount  INFO=$infoCount")
[void]$sb.AppendLine()
[void]$sb.AppendLine('=== FUNKTIONS-CHECKLISTE ===')
foreach ($g in @($script:Gates)) {
    [void]$sb.AppendLine(("[{0,-9}] {1}" -f $g.DisplayStatus, $g.Name))
    if ($g.Detail) { [void]$sb.AppendLine("  Info: $($g.Detail)") }
}
[void]$sb.AppendLine('Legende: BESTANDEN = Gate ohne Befund; HINWEIS = bemerkenswerte Abweichung; UNKLAR = nicht eindeutig bewertbar; FEHLER = notwendiger Zustand fehlt.')
[void]$sb.AppendLine()

$sections = @($Checks | Select-Object -ExpandProperty Section -Unique)
foreach ($section in $sections) {
    [void]$sb.AppendLine("=== $section ===")
    foreach ($c in @($Checks | Where-Object Section -eq $section)) {
        [void]$sb.AppendLine(("[{0,-7}] {1}" -f $c.Status, $c.Check))
        [void]$sb.AppendLine("  Ist : $($c.Actual)")
        if ($c.Expected) { [void]$sb.AppendLine("  Soll: $($c.Expected)") }
        if ($c.Detail)   { [void]$sb.AppendLine("  Info: $($c.Detail)") }
    }
    [void]$sb.AppendLine()
}

if ($Details.Count -gt 0) {
    [void]$sb.AppendLine('=== TECHNISCHE DETAILS ===')
    foreach ($d in $Details) { [void]$sb.AppendLine($d) }
    [void]$sb.AppendLine()
}

if ($failCount -gt 0) {
    [void]$sb.AppendLine('=== FEHLER-KURZLISTE ===')
    foreach ($c in @($Checks | Where-Object Status -eq 'FAIL')) {
        [void]$sb.AppendLine("- [$($c.Section)] $($c.Check): $($c.Actual) (Soll: $($c.Expected))")
    }
    [void]$sb.AppendLine()
}

if ($warnCount -gt 0 -or $unknownCount -gt 0) {
    [void]$sb.AppendLine('=== WARNUNGEN / NICHT PRUEFBAR ===')
    foreach ($c in @($Checks | Where-Object { $_.Status -eq 'WARN' -or $_.Status -eq 'UNKNOWN' })) {
        [void]$sb.AppendLine("- [$($c.Status)] [$($c.Section)] $($c.Check): $($c.Actual)")
    }
    [void]$sb.AppendLine()
}

[void]$sb.AppendLine('Dieses Skript ist SYSTEM-READ-ONLY. Es veraendert keine Razer-/Windows-Treiber, Dienste, Registry-, PnP- oder Runtime-Zustaende; geschrieben werden nur eigene Diagnoseausgaben. Der Standardlauf benötigt bewusst keine Elevation.')
[void]$sb.AppendLine('Bei FAIL zuerst den betroffenen Layer aus der Fehler-Kurzliste untersuchen; keine generische Synapse-Komplettreinstallation.')

$report = $sb.ToString()

Write-Host ''
if ($overallLabel -eq 'GESUND') { Write-Host "RAZER HEALTH: GESUND" -ForegroundColor Green }
else { Write-Host "RAZER HEALTH: FEHLER" -ForegroundColor Red }
Write-Host "PASS=$passCount  WARN=$warnCount  FAIL=$failCount  UNKNOWN=$unknownCount  INFO=$infoCount"
Write-Host ''
Write-Output $report

if ($OutputPath) {
    try {
        $parent = Split-Path -Parent $OutputPath
        if ($parent -and -not (Test-Path -LiteralPath $parent)) { [System.IO.Directory]::CreateDirectory($parent) | Out-Null }
        [System.IO.File]::WriteAllText($OutputPath, $report, (New-Object System.Text.UTF8Encoding($true)))
        Write-Host "Report gespeichert: $OutputPath" -ForegroundColor Cyan
    } catch {
        Write-Warning "Report konnte nicht gespeichert werden: $($_.Exception.Message)"
    }
}

# Compact machine-readable result sidecar. This intentionally avoids JSON and
# provides the tray UI with a robust fallback if rich JSON serialization fails.
$machineOutputFailed = $false
if ($GateOutputPath) {
    try {
        $gateParent = Split-Path -Parent $GateOutputPath
        if ($gateParent -and -not (Test-Path -LiteralPath $gateParent)) { [System.IO.Directory]::CreateDirectory($gateParent) | Out-Null }
        $gb = New-Object System.Text.StringBuilder
        [void]$gb.AppendLine('RHM_GATE_RESULT_V1')
        [void]$gb.AppendLine("OVERALL|$functionalOverall")
        $gateIndex = 0
        foreach ($g in @($script:Gates)) {
            $gateIndex++
            [void]$gb.AppendLine("GATE|$gateIndex|$($g.Status)|$($g.Name)")
        }
        [System.IO.File]::WriteAllText($GateOutputPath, $gb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
        if (-not (Test-Path -LiteralPath $GateOutputPath) -or (Get-Item -LiteralPath $GateOutputPath).Length -le 0) { throw 'Gate result file was not created.' }
        Write-Host "Gate-Ergebnis gespeichert: $GateOutputPath" -ForegroundColor Cyan
    } catch {
        $machineOutputFailed = $true
        Write-Warning "Gate-Ergebnis konnte nicht gespeichert werden: $($_.Exception.Message)"
    }
}

if ($JsonOutputPath) {
    try {
        $jsonParent = Split-Path -Parent $JsonOutputPath
        if ($jsonParent -and -not (Test-Path -LiteralPath $jsonParent)) { [System.IO.Directory]::CreateDirectory($jsonParent) | Out-Null }
        # Convert generic lists to plain arrays/objects before serialization. This
        # avoids Windows PowerShell 5.1 collection edge cases seen in v1.1.0.
        $jsonGates = @($script:Gates | ForEach-Object { [pscustomobject]@{ Name=[string]$_.Name; Status=[string]$_.Status; Label=[string]$_.DisplayStatus; Detail=[string]$_.Detail } })
        $jsonChecks = @($Checks | ForEach-Object { [pscustomobject]@{ Section=[string]$_.Section; Status=[string]$_.Status; Check=[string]$_.Check; Actual=[string]$_.Actual; Expected=[string]$_.Expected; Detail=[string]$_.Detail } })
        $jsonDetails = @($Details | ForEach-Object { [string]$_ })
        $jsonObject = [ordered]@{
            schemaVersion    = 1
            toolVersion      = '1.3.0'
            engineVersion    = $ScriptVersion
            baselineDate     = $BaselineDate
            timestamp        = $now.ToString('o')
            computer         = $env:COMPUTERNAME
            user             = "$env:USERDOMAIN\$env:USERNAME"
            elevated         = $isAdmin
            overall          = $functionalOverall
            overallLabel     = $overallLabel
            rawDiagnostic    = $rawOverall
            counts           = [ordered]@{ pass=$passCount; warn=$warnCount; fail=$failCount; unknown=$unknownCount; info=$infoCount }
            gates            = $jsonGates
            checks           = $jsonChecks
            technicalDetails = $jsonDetails
        }
        $jsonText = $jsonObject | ConvertTo-Json -Depth 8
        [System.IO.File]::WriteAllText($JsonOutputPath, $jsonText, (New-Object System.Text.UTF8Encoding($false)))
        if (-not (Test-Path -LiteralPath $JsonOutputPath) -or (Get-Item -LiteralPath $JsonOutputPath).Length -le 2) { throw 'JSON result file was not created.' }
        Write-Host "JSON gespeichert: $JsonOutputPath" -ForegroundColor Cyan
    } catch {
        Write-Warning "JSON konnte nicht gespeichert werden: $($_.Exception.Message)"
    }
}

if ($ExitWithCode) {
    if ($GateOutputPath -and $machineOutputFailed) { exit 3 }
    exit $functionalExitCode
}
            