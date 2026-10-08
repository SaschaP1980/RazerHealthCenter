[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [string]$HistoryPath = '',
    [string]$ToolVersion = '2.3.0',
    [ValidateSet('none','wired','wireless')][string]$CalibrationMode = 'none',
    [string]$CalibrationProductKey = '',
    [string]$BaselinePath = ''
)

# Setup Scanner 1.0.6 for Razer Health Monitor v2.3.0.
# Read-only: queries PnP/CIM/registry/driver metadata only.
# It writes:
#   - the requested inventory JSON on success
#   - SetupScannerDebug-v1.0.6.json next to the inventory on every run
#   - SetupScannerDebug-v1.0.6.txt next to the inventory on every run
#   - RazerConnectionHistory-v2.json (when HistoryPath is provided)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$ScanVersion = '1.0.6'
$VendorId = '1532'

# No endpoint PID has a hard-coded product identity or connection role.
# Product identity is derived from current Windows/USB evidence. Connection
# roles are derived from explicit descriptor evidence where available and from
# explicit user-guided calibration/history otherwise.
$started = Get-Date
$parent = Split-Path -Parent $OutputPath
if (-not $parent) { $parent = (Get-Location).Path }
if (-not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
}

$DebugJsonPath = Join-Path $parent 'SetupScannerDebug-v1.0.6.json'
$DebugTextPath = Join-Path $parent 'SetupScannerDebug-v1.0.6.txt'
if (-not $HistoryPath) {
    $HistoryPath = Join-Path $parent 'RazerConnectionHistory-v2.json'
}


$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

# Last-resort diagnostic path: even an unexpected terminating error before the
# normal export stage should leave a machine-readable and human-readable trace.
trap {
    $fatal = $_
    try {
        $fallback = [ordered]@{
            schemaVersion = 1
            scannerVersion = $ScanVersion
            toolVersion = $ToolVersion
            fatal = $true
            occurredAt = (Get-Date).ToUniversalTime().ToString('o')
            outputPath = $OutputPath
            error = [ordered]@{
                type = if ($fatal.Exception) { $fatal.Exception.GetType().FullName } else { '' }
                hresult = if ($fatal.Exception) { ('0x{0:X8}' -f $fatal.Exception.HResult) } else { '' }
                message = if ($fatal.Exception) { $fatal.Exception.Message } else { [string]$fatal }
                scriptStackTrace = [string]$fatal.ScriptStackTrace
                positionMessage = if ($fatal.InvocationInfo) { [string]$fatal.InvocationInfo.PositionMessage } else { '' }
            }
        }

        [System.IO.File]::WriteAllText(
            $DebugJsonPath,
            ($fallback | ConvertTo-Json -Depth 8),
            $utf8NoBom
        )

        $fallbackText = @(
            "=== RAZER SETUP SCANNER FATAL $ScanVersion ==="
            "Zeit: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff'))"
            "Typ: $($fallback.error.type)"
            "HResult: $($fallback.error.hresult)"
            "Meldung: $($fallback.error.message)"
            ""
            "Position:"
            $fallback.error.positionMessage
            ""
            "Stack:"
            $fallback.error.scriptStackTrace
        ) -join [Environment]::NewLine

        [System.IO.File]::WriteAllText(
            $DebugTextPath,
            $fallbackText,
            $utf8NoBom
        )
    }
    catch {
        # No secondary failure should mask the original scanner error.
    }

    Write-Error $fatal
    exit 99
}

$errors = New-Object System.Collections.Generic.List[object]

function Add-ScanError {
    param([string]$Stage, [System.Exception]$Exception)
    $errors.Add([ordered]@{
        stage = $Stage
        type = if ($Exception) { $Exception.GetType().FullName } else { '' }
        hresult = if ($Exception) { ('0x{0:X8}' -f $Exception.HResult) } else { '' }
        message = if ($Exception) { $Exception.Message } else { '' }
    }) | Out-Null
}

function Get-OptionalPropertyString {
    param(
        [object]$InputObject,
        [string]$PropertyName
    )

    if ($null -eq $InputObject -or -not $PropertyName) {
        return ''
    }

    try {
        $prop = $InputObject.PSObject.Properties[$PropertyName]
        if ($null -ne $prop -and $null -ne $prop.Value) {
            return [string]$prop.Value
        }
    }
    catch {
        # Missing optional properties are normal in Enum\USB / Enum\HID.
    }

    return ''
}

function Get-PidFromId {
    param([string]$Id)
    if ($Id -and $Id -match '(?i)VID_1532&PID_([0-9A-F]{4})') {
        return $Matches[1].ToUpperInvariant()
    }
    return ''
}

function Clean-Name {
    param([string]$Value)
    if (-not $Value) { return '' }
    $s = [string]$Value
    $s = $s -replace '^@[^;]+;',''
    $s = $s -replace '^Razer Inc\.\s*','Razer '
    return $s.Trim()
}

function Best-Model {
    param([object[]]$Names, [string]$DevicePid)

    $clean = @(
        $Names |
        ForEach-Object { Clean-Name ([string]$_) } |
        Where-Object {
            $_ -and
            $_ -notmatch '(?i)^(USB Composite Device|USB Input Device|HID-compliant device|HID-compliant mouse|HID-compliant consumer control device|HID-compliant system controller|HID Keyboard Device|Razer Control Device|\(Standard .+\)|Microsoft)$'
        } |
        Select-Object -Unique
    )

    $razer = @(
        $clean |
        Where-Object {
            $_ -match '(?i)\bRazer\b' -and
            $_ -notmatch '(?i)Control Device|Virtual'
        }
    )

    if ($razer.Count -gt 0) { return [string]$razer[0] }
    if ($clean.Count -gt 0) { return [string]$clean[0] }
    return "Razer Gerät PID $DevicePid"
}

function Normalize-ProductIdentity {
    param([string]$Value)

    $s = Clean-Name $Value
    if (-not $s) { return '' }

    if ($s -match '(?i)^(USB Composite Device|USB Input Device|HID-compliant .+|HID Keyboard Device|Razer Control Device|\(Standard .+\)|Microsoft)$') {
        return ''
    }

    $s = $s.ToLowerInvariant()
    $s = $s -replace '\brazer\b',''
    # Strip only explicit transport-role words. Do not infer a role from
    # marketing tokens such as "HyperSpeed".
    $s = $s -replace '(?i)\b(?:wireless usb dongle|usb dongle|dongle|receiver|wired usb|wired|usb cable|cable)\b',''
    $s = $s -replace '[^a-z0-9]+',' '
    $s = ($s -replace '\s+',' ').Trim()
    return $s
}

function Product-Key {
    param([string]$Name, [string]$DevicePid)

    $s = Normalize-ProductIdentity $Name
    if (-not $s) {
        return "pid-$($DevicePid.ToLowerInvariant())"
    }
    return $s
}

function Get-ConnectionDeviceClass {
    param(
        [object[]]$PresentPnpRows,
        [string]$ModelName
    )

    # Device-class presentation is derived only from current generic PnP
    # evidence. No product name or endpoint PID is mapped to a class. The
    # primary HID interface (MI_00) is preferred because composite gaming
    # devices often expose both keyboard- and mouse-compatible side channels.
    $primary = @(
        $PresentPnpRows |
        Where-Object {
            [string]$_.instanceId -match '(?i)^HID\\VID_1532&PID_[0-9A-F]{4}&MI_00\\' -and
            [string]$_.class -match '(?i)^(Mouse|Keyboard)$'
        } |
        ForEach-Object { ([string]$_.class).ToLowerInvariant() } |
        Sort-Object -Unique
    )
    if ($primary.Count -eq 1) { return [string]$primary[0] }

    # A model-labelled class-specific node is also strong generic evidence.
    $modelClass = @(
        $PresentPnpRows |
        Where-Object {
            (Clean-Name ([string]$_.name)) -eq (Clean-Name $ModelName) -and
            [string]$_.class -match '(?i)^(Mouse|Keyboard)$'
        } |
        ForEach-Object { ([string]$_.class).ToLowerInvariant() } |
        Sort-Object -Unique
    )
    if ($modelClass.Count -eq 1) { return [string]$modelClass[0] }

    # Fall back only when exactly one functional class is exposed at all.
    $classes = @(
        $PresentPnpRows |
        Where-Object { [string]$_.class -match '(?i)^(Mouse|Keyboard)$' } |
        ForEach-Object { ([string]$_.class).ToLowerInvariant() } |
        Sort-Object -Unique
    )
    if ($classes.Count -eq 1) { return [string]$classes[0] }
    return 'device'
}

function Get-PnpPropertySnapshot {
    param([string]$InstanceId)

    $selected = [ordered]@{}
    if (-not $InstanceId) {
        return $selected
    }

    try {
        foreach ($prop in @(Get-PnpDeviceProperty -InstanceId $InstanceId -ErrorAction Stop)) {
            $key = [string]$prop.KeyName
            if ($key -notin @(
                'DEVPKEY_Device_BusReportedDeviceDesc',
                'DEVPKEY_Device_FriendlyName',
                'DEVPKEY_Device_DeviceDesc',
                'DEVPKEY_Device_ContainerId',
                'DEVPKEY_Device_Parent',
                'DEVPKEY_Device_LocationPaths',
                'DEVPKEY_Device_LastArrivalDate'
            )) {
                continue
            }

            $value = $prop.Data
            if ($null -eq $value) {
                $selected[$key] = $null
            }
            elseif ($value -is [System.Array]) {
                $selected[$key] = @($value | ForEach-Object { [string]$_ })
            }
            else {
                $selected[$key] = [string]$value
            }
        }
    }
    catch {
        Add-ScanError "Get-PnpDeviceProperty $InstanceId" $_.Exception
    }

    return $selected
}

function Get-RootIdentity {
    param(
        [string]$DevicePid,
        [object[]]$PresentRows
    )

    $rootId = @(
        $PresentRows |
        ForEach-Object { [string]$_.instanceId } |
        Where-Object { $_ -match "(?i)^USB\\VID_${VendorId}&PID_$DevicePid\\" } |
        Sort-Object -Unique |
        Select-Object -First 1
    )

    if (-not $rootId) {
        return [ordered]@{
            rootInstanceId = ''
            productName = ''
            productKey = ''
            identitySource = 'none'
            identityConfidence = 'none'
            containerId = ''
            parent = ''
            locationPaths = @()
            lastArrivalDate = ''
        }
    }

    $props = Get-PnpPropertySnapshot ([string]$rootId)
    $busName = ''
    if ($props.Contains('DEVPKEY_Device_BusReportedDeviceDesc')) {
        $busName = Clean-Name ([string]$props['DEVPKEY_Device_BusReportedDeviceDesc'])
    }

    $friendly = ''
    if ($props.Contains('DEVPKEY_Device_FriendlyName')) {
        $friendly = Clean-Name ([string]$props['DEVPKEY_Device_FriendlyName'])
    }

    $candidate = ''
    $source = 'none'
    $confidence = 'none'
    foreach ($pair in @(
        @($busName,'bus-reported-device-description','high'),
        @($friendly,'root-friendly-name','medium')
    )) {
        $normalized = Normalize-ProductIdentity ([string]$pair[0])
        if ($normalized) {
            $candidate = [string]$pair[0]
            $source = [string]$pair[1]
            $confidence = [string]$pair[2]
            break
        }
    }

    $key = ''
    if ($candidate) {
        $key = Product-Key $candidate $DevicePid
    }

    return [ordered]@{
        rootInstanceId = [string]$rootId
        productName = $candidate
        productKey = $key
        identitySource = $source
        identityConfidence = $confidence
        containerId = $(if($props.Contains('DEVPKEY_Device_ContainerId')){[string]$props['DEVPKEY_Device_ContainerId']}else{''})
        parent = $(if($props.Contains('DEVPKEY_Device_Parent')){[string]$props['DEVPKEY_Device_Parent']}else{''})
        locationPaths = $(if($props.Contains('DEVPKEY_Device_LocationPaths')){@($props['DEVPKEY_Device_LocationPaths'])}else{@()})
        lastArrivalDate = $(if($props.Contains('DEVPKEY_Device_LastArrivalDate')){[string]$props['DEVPKEY_Device_LastArrivalDate']}else{''})
    }
}

function Get-ExplicitConnectionRole {
    param([object[]]$EvidenceStrings)

    $joined = (@($EvidenceStrings | Where-Object { $_ }) -join ' | ')
    # "Wireless" alone is intentionally insufficient because many product
    # marketing names contain it for every transport. Receiver/dongle wording
    # is explicit transport evidence.
    if ($joined -match '(?i)\b(?:wireless usb dongle|usb dongle|dongle|receiver)\b') {
        return [ordered]@{
            type = 'wireless-dongle'
            confidence = 'high'
            source = 'explicit-device-role-text'
        }
    }
    if ($joined -match '(?i)\b(?:wired usb|usb cable|cable connection|wired connection)\b') {
        return [ordered]@{
            type = 'wired-usb'
            confidence = 'high'
            source = 'explicit-device-role-text'
        }
    }
    return [ordered]@{
        type = 'unknown'
        confidence = 'none'
        source = 'no-explicit-role-evidence'
    }
}

function Get-HistoryKey {
    param([string]$DevicePid)
    return "${VendorId}:$(([string]$DevicePid).ToUpperInvariant())"
}

function Get-HistoryConnectionMap {
    param([object]$History)

    $map = @{}
    if ($null -eq $History) { return $map }

    try {
        foreach ($entry in @($History.connections)) {
            $key = [string]$entry.key
            if ($key) { $map[$key] = $entry }
        }
    }
    catch {
        # Invalid/missing history fields are treated as empty.
    }
    return $map
}

function Read-ConnectionHistory {
    $candidatePath = $HistoryPath
    if (-not $candidatePath) { return $null }

    # v2.3.0 writes schema 2. If only the v2.2.4 schema-1 file exists, read it
    # as migration input. Passive topology roles from schema 1 are not trusted
    # as calibrated ground truth.
    if (-not (Test-Path -LiteralPath $candidatePath)) {
        $legacyPath = $candidatePath -replace 'RazerConnectionHistory-v2\.json$','RazerConnectionHistory-v1.json'
        if ($legacyPath -ne $candidatePath -and (Test-Path -LiteralPath $legacyPath)) {
            $candidatePath = $legacyPath
        } else {
            return $null
        }
    }

    try {
        $raw = Get-Content -LiteralPath $candidatePath -Raw -ErrorAction Stop
        $obj = $raw | ConvertFrom-Json -ErrorAction Stop
        $schema = [int]$obj.schemaVersion
        if ($schema -ne 1 -and $schema -ne 2) {
            throw "Unsupported connection history schema: $schema"
        }
        return $obj
    }
    catch {
        Add-ScanError 'Connection history read' $_.Exception
        return $null
    }
}

function Read-BaselineInventory {
    if ($CalibrationMode -eq 'none') { return $null }
    if (-not $BaselinePath -or -not (Test-Path -LiteralPath $BaselinePath)) {
        return $null
    }
    try {
        $raw = Get-Content -LiteralPath $BaselinePath -Raw -ErrorAction Stop
        $obj = $raw | ConvertFrom-Json -ErrorAction Stop
        if ([int]$obj.schemaVersion -ne 2) {
            throw "Unsupported baseline inventory schema: $($obj.schemaVersion)"
        }
        return $obj
    }
    catch {
        Add-ScanError 'Calibration baseline read' $_.Exception
        return $null
    }
}

function Confidence-Rank {
    param([string]$Value)
    switch (([string]$Value).ToLowerInvariant()) {
        'high' { return 3 }
        'medium' { return 2 }
        'low' { return 1 }
        default { return 0 }
    }
}

function Set-ConnectionRole {
    param(
        [object]$Connection,
        [string]$Type,
        [string]$Confidence,
        [string]$Source
    )

    if ($null -eq $Connection -or -not $Type -or $Type -eq 'unknown') { return }
    $newRank = Confidence-Rank $Confidence
    $oldRank = Confidence-Rank ([string]$Connection['connectionTypeConfidence'])
    if ($newRank -lt $oldRank) { return }
    if (
        $oldRank -gt 0 -and
        $newRank -eq $oldRank -and
        [string]$Connection['connectionType'] -ne 'unknown' -and
        [string]$Connection['connectionType'] -ne $Type
    ) {
        if ($Source -eq 'explicit-device-role-text') {
            # Current explicit transport wording outranks persisted heuristics.
        }
        elseif ([string]$Connection['connectionTypeSource'] -eq 'explicit-device-role-text') {
            return
        }
        else {
            $Connection['connectionType'] = 'usb-device'
            $Connection['connectionTypeConfidence'] = 'none'
            $Connection['connectionTypeSource'] = 'role-evidence-conflict'
            return
        }
    }

    $Connection['connectionType'] = $Type
    $Connection['connectionTypeConfidence'] = $Confidence
    $Connection['connectionTypeSource'] = $Source
}

# ---------------------------------------------------------------------------
# 1) Present PnP devices via PnpDevice cmdlet (primary present-device source)
# ---------------------------------------------------------------------------
$pnpCmdRows = @()
try {
    if (Get-Command Get-PnpDevice -ErrorAction SilentlyContinue) {
        $pnpCmdRows = @(
            Get-PnpDevice -PresentOnly -ErrorAction Stop |
            Where-Object {
                [string]$_.InstanceId -match '(?i)VID_1532&PID_[0-9A-F]{4}'
            } |
            ForEach-Object {
                [ordered]@{
                    instanceId = [string]$_.InstanceId
                    name       = [string]$_.FriendlyName
                    class      = [string]$_.Class
                    status     = [string]$_.Status
                    source     = 'Get-PnpDevice'
                }
            }
        )
    }
}
catch {
    Add-ScanError 'Get-PnpDevice' $_.Exception
}

# ---------------------------------------------------------------------------
# 2) Win32_PnPEntity via CIM (problem code + service)
#    Use a provider-side filter first; fall back to full enumeration.
# ---------------------------------------------------------------------------
$cimPnp = @()
try {
    $cimPnp = @(
        Get-CimInstance Win32_PnPEntity `
            -Filter "PNPDeviceID LIKE '%VID_1532&PID_%'" `
            -Property PNPDeviceID,ConfigManagerErrorCode,Name,Service `
            -ErrorAction Stop
    )
}
catch {
    Add-ScanError 'Win32_PnPEntity filtered' $_.Exception
    try {
        $cimPnp = @(
            Get-CimInstance Win32_PnPEntity -ErrorAction Stop |
            Where-Object {
                [string]$_.PNPDeviceID -match '(?i)VID_1532&PID_[0-9A-F]{4}'
            }
        )
    }
    catch {
        Add-ScanError 'Win32_PnPEntity fallback-full' $_.Exception
    }
}

# ---------------------------------------------------------------------------
# 3) Signed driver associations
# ---------------------------------------------------------------------------
$signed = @()
try {
    $signed = @(
        Get-CimInstance Win32_PnPSignedDriver `
            -Filter "DeviceID LIKE '%VID_1532&PID_%'" `
            -Property DeviceID,DriverProviderName,InfName,DeviceName,DriverVersion `
            -ErrorAction Stop
    )
}
catch {
    Add-ScanError 'Win32_PnPSignedDriver filtered' $_.Exception
    try {
        $signed = @(
            Get-CimInstance Win32_PnPSignedDriver -ErrorAction Stop |
            Where-Object {
                [string]$_.DeviceID -match '(?i)VID_1532&PID_[0-9A-F]{4}'
            }
        )
    }
    catch {
        Add-ScanError 'Win32_PnPSignedDriver fallback-full' $_.Exception
    }
}

# ---------------------------------------------------------------------------
# 4) Historical/alternate USB + HID enum paths
# ---------------------------------------------------------------------------
$registryRows = New-Object System.Collections.Generic.List[object]
foreach ($rootName in @('USB','HID')) {
    $root = "HKLM:\SYSTEM\CurrentControlSet\Enum\$rootName"
    try {
        if (-not (Test-Path -LiteralPath $root)) { continue }

        Get-ChildItem -LiteralPath $root -ErrorAction Stop |
        Where-Object {
            $_.PSChildName -match '(?i)^VID_1532&PID_[0-9A-F]{4}'
        } |
        ForEach-Object {
            $deviceKey = $_

            Get-ChildItem -LiteralPath $deviceKey.PSPath -ErrorAction SilentlyContinue |
            ForEach-Object {
                $v = Get-ItemProperty -LiteralPath $_.PSPath -ErrorAction SilentlyContinue

                $friendlyName = Get-OptionalPropertyString $v 'FriendlyName'
                $deviceDesc = Get-OptionalPropertyString $v 'DeviceDesc'
                $service = Get-OptionalPropertyString $v 'Service'
                $mfg = Get-OptionalPropertyString $v 'Mfg'

                $registryRows.Add([ordered]@{
                    instanceId   = "$rootName\$($deviceKey.PSChildName)\$($_.PSChildName)"
                    friendlyName = $friendlyName
                    deviceDesc   = $deviceDesc
                    service      = $service
                    manufacturer = $mfg
                    source       = "Registry-$rootName"
                }) | Out-Null
            }
        }
    }
    catch {
        Add-ScanError "Registry-$rootName" $_.Exception
    }
}

# ---------------------------------------------------------------------------
# 5) DriverStore mapping (read-only pnputil /enum-drivers)
# ---------------------------------------------------------------------------
$pnputilText = ''
try {
    $pnputilText = (& "$env:SystemRoot\System32\pnputil.exe" /enum-drivers 2>&1 | Out-String -Width 4096)
}
catch {
    Add-ScanError 'pnputil /enum-drivers' $_.Exception
}

$oemToOriginal = @{}
$allRazerInf = New-Object System.Collections.Generic.List[string]

foreach ($block in @(
    [regex]::Split([string]$pnputilText,'(?:\r?\n){2,}') |
    Where-Object { $_.Trim() }
)) {
    $oem = [regex]::Match($block,'(?i)\boem\d+\.inf\b')
    $origMatches = [regex]::Matches(
        $block,
        '(?i)\b(?:rzdevu_[0-9a-f]{4}_[a-z0-9]+|rzcommonu)\.inf\b'
    )

    if ($origMatches.Count -gt 0) {
        $name = $origMatches[0].Value.ToLowerInvariant()

        if (-not $allRazerInf.Contains($name)) {
            $allRazerInf.Add($name) | Out-Null
        }

        if ($oem.Success) {
            $oemToOriginal[$oem.Value.ToLowerInvariant()] = $name
        }
    }
}

# ---------------------------------------------------------------------------
# Merge all discovered PIDs
# ---------------------------------------------------------------------------
$pids = New-Object System.Collections.Generic.List[string]

foreach ($row in $pnpCmdRows) {
    $DevicePid = Get-PidFromId ([string]$row.instanceId)
    if ($DevicePid -and -not $pids.Contains($DevicePid)) { $pids.Add($DevicePid) | Out-Null }
}
foreach ($row in $cimPnp) {
    $DevicePid = Get-PidFromId ([string]$row.PNPDeviceID)
    if ($DevicePid -and -not $pids.Contains($DevicePid)) { $pids.Add($DevicePid) | Out-Null }
}
foreach ($row in $signed) {
    $DevicePid = Get-PidFromId ([string]$row.DeviceID)
    if ($DevicePid -and -not $pids.Contains($DevicePid)) { $pids.Add($DevicePid) | Out-Null }
}
foreach ($row in $registryRows) {
    $DevicePid = Get-PidFromId ([string]$row.instanceId)
    if ($DevicePid -and -not $pids.Contains($DevicePid)) { $pids.Add($DevicePid) | Out-Null }
}
foreach ($inf in $allRazerInf) {
    if ($inf -match '(?i)^rzdevu_([0-9a-f]{4})_') {
        $DevicePid = $Matches[1].ToUpperInvariant()
        if (-not $pids.Contains($DevicePid)) { $pids.Add($DevicePid) | Out-Null }
    }
}

# ---------------------------------------------------------------------------
# Load persistent role/product history. This history contains observed PIDs,
# but never assigns semantic meaning from a compile-time PID table.
# ---------------------------------------------------------------------------
$history = Read-ConnectionHistory
$historyMap = Get-HistoryConnectionMap $history
# Runtime-learned PIDs are app-owned observations, not compile-time semantics.
# Include them as discovery candidates so a newly calibrated connection is not
# lost if Windows has not yet materialized it into Registry/DriverStore history.
if ($null -ne $history) {
    foreach ($entry in @($history.connections)) {
        $historyPid = ([string]$entry.pid).ToUpperInvariant()
        if ($historyPid -match '^[0-9A-F]{4}$' -and -not $pids.Contains($historyPid)) {
            $pids.Add($historyPid) | Out-Null
        }
    }
}
$previousSnapshot = $null
if ($null -ne $history) {
    try { $previousSnapshot = $history.lastSnapshot } catch { $previousSnapshot = $null }
}
$baselineInventory = Read-BaselineInventory

# ---------------------------------------------------------------------------
# Build connections
# ---------------------------------------------------------------------------
$connections = New-Object System.Collections.Generic.List[object]

foreach ($DevicePid in @($pids | Sort-Object)) {
    $pattern = "VID_${VendorId}&PID_$DevicePid"

    $cmdNodes = @(
        $pnpCmdRows |
        Where-Object { [string]$_.instanceId -like "*$pattern*" }
    )

    $cimNodes = @(
        $cimPnp |
        Where-Object { [string]$_.PNPDeviceID -like "*$pattern*" }
    )

    $signedRows = @(
        $signed |
        Where-Object { [string]$_.DeviceID -like "*$pattern*" }
    )

    $regRows = @(
        $registryRows |
        Where-Object { [string]$_.instanceId -like "*$pattern*" }
    )

    # presentAtScan is deliberately a PHYSICAL USB/HID path state. RZVIRTUAL
    # and RZCONTROL are binding evidence, not proof that the physical
    # connection itself is active.
    $physicalCmdNodes = @(
        $cmdNodes | Where-Object { [string]$_.instanceId -match '^(?i)(USB|HID)\\' }
    )
    $physicalCimNodes = @(
        $cimNodes | Where-Object { [string]$_.PNPDeviceID -match '^(?i)(USB|HID)\\' }
    )
    $present = ($physicalCmdNodes.Count -gt 0 -or $physicalCimNodes.Count -gt 0)

    $names = @()
    $names += @($cmdNodes | ForEach-Object { $_.name })
    $names += @($cimNodes | ForEach-Object { $_.Name })
    $names += @($signedRows | ForEach-Object { $_.DeviceName })
    $names += @($regRows | ForEach-Object { $_.friendlyName })
    $names += @($regRows | ForEach-Object { $_.deviceDesc })

    # Fast identity path: one Get-PnpDeviceProperty call for the physical USB
    # root only. Deep per-interface property scans are intentionally avoided.
    $rootIdentity = Get-RootIdentity $DevicePid $physicalCmdNodes
    $historyKey = Get-HistoryKey $DevicePid
    $historyEntry = $null
    if ($historyMap.ContainsKey($historyKey)) {
        $historyEntry = $historyMap[$historyKey]
    }

    $model = [string]$rootIdentity['productName']
    $productKey = [string]$rootIdentity['productKey']
    $identitySource = [string]$rootIdentity['identitySource']
    $identityConfidence = [string]$rootIdentity['identityConfidence']

    if (-not $model -and $null -ne $historyEntry) {
        $histName = Get-OptionalPropertyString $historyEntry 'productName'
        $histKey = Get-OptionalPropertyString $historyEntry 'productKey'
        if ($histName -and $histKey) {
            $model = $histName
            $productKey = $histKey
            $identitySource = 'persistent-connection-history'
            $identityConfidence = 'high'
        }
    }

    if (-not $model) {
        $model = Best-Model $names $DevicePid
    }
    if (-not $productKey) {
        $productKey = Product-Key $model $DevicePid
    }
    if (-not $identitySource -or $identitySource -eq 'none') {
        $identitySource = 'pnp-name-fallback'
        $identityConfidence = 'medium'
    }

    $deviceClass = Get-ConnectionDeviceClass $physicalCmdNodes $model

    # Lightweight topology fingerprint from the already-enumerated present PnP
    # rows. This adds no per-interface property calls.
    $hidCollectionIds = @(
        $physicalCmdNodes |
        ForEach-Object { [string]$_.instanceId } |
        Where-Object { $_ -match '(?i)^HID\\' -and $_ -match '(?i)&COL[0-9A-F]{2}' } |
        Sort-Object -Unique
    )
    $hidInterfaceNumbers = @(
        $physicalCmdNodes |
        ForEach-Object {
            $id = [string]$_.instanceId
            if ($id -match '(?i)^HID\\' -and $id -match '(?i)&MI_([0-9A-F]{2})') {
                $Matches[1].ToUpperInvariant()
            }
        } |
        Where-Object { $_ } |
        Sort-Object -Unique
    )
    $usbInterfaceNumbers = @(
        $physicalCmdNodes |
        ForEach-Object {
            $id = [string]$_.instanceId
            if ($id -match '(?i)^USB\\' -and $id -match '(?i)&MI_([0-9A-F]{2})') {
                $Matches[1].ToUpperInvariant()
            }
        } |
        Where-Object { $_ } |
        Sort-Object -Unique
    )

    $infs = New-Object System.Collections.Generic.List[string]
    foreach ($row in $signedRows) {
        $name = ([string]$row.InfName).ToLowerInvariant()
        if ($oemToOriginal.ContainsKey($name)) {
            $name = [string]$oemToOriginal[$name]
        }
        if ($name -and -not $infs.Contains($name)) {
            $infs.Add($name) | Out-Null
        }
    }
    foreach ($name in $allRazerInf) {
        if (
            $name -match "(?i)^rzdevu_$($DevicePid.ToLowerInvariant())_" -and
            -not $infs.Contains($name)
        ) {
            $infs.Add($name) | Out-Null
        }
    }

    $services = New-Object System.Collections.Generic.List[string]
    foreach ($name in @($cimNodes | ForEach-Object { $_.Service })) {
        if (
            $name -and
            [string]$name -match '(?i)^Rz(?:Dev_[0-9a-f]{4}|Common)$' -and
            -not $services.Contains([string]$name)
        ) {
            $services.Add([string]$name) | Out-Null
        }
    }
    foreach ($name in @($regRows | ForEach-Object { $_.service })) {
        if (
            $name -and
            [string]$name -match '(?i)^Rz(?:Dev_[0-9a-f]{4}|Common)$' -and
            -not $services.Contains([string]$name)
        ) {
            $services.Add([string]$name) | Out-Null
        }
    }

    $expected = "RzDev_$($DevicePid.ToLowerInvariant())"
    $hasVcon = @(
        $infs |
        Where-Object { $_ -match '(?i)_vcon\.inf$' }
    ).Count -gt 0

    if ($hasVcon -and -not $services.Contains($expected)) {
        $services.Add($expected) | Out-Null
    }

    # Prefer CIM nodes because they include problem code + service.
    $nodeOut = @(
        $cimNodes |
        ForEach-Object {
            [ordered]@{
                instanceId = [string]$_.PNPDeviceID
                name = [string]$_.Name
                service = [string]$_.Service
                problemCode = [int]$_.ConfigManagerErrorCode
                present = $true
            }
        }
    )

    # If CIM did not expose the device, retain Get-PnpDevice evidence.
    if ($nodeOut.Count -eq 0) {
        $nodeOut = @(
            $cmdNodes |
            ForEach-Object {
                [ordered]@{
                    instanceId = [string]$_.instanceId
                    name = [string]$_.name
                    service = ''
                    problemCode = 0
                    present = $true
                }
            }
        )
    }

    $razerInfs = @(
        $infs | Where-Object { $_ -match '(?i)^(?:rzdevu_[0-9a-f]{4}_[a-z0-9]+|rzcommonu)\.inf$' }
    )
    $inboxInfs = @(
        $infs | Where-Object { $_ -notmatch '(?i)^(?:rzdevu_[0-9a-f]{4}_[a-z0-9]+|rzcommonu)\.inf$' }
    )
    $hasRzDevInf = @($razerInfs | Where-Object { $_ -match "(?i)^rzdevu_$($DevicePid.ToLowerInvariant())_" }).Count -gt 0
    $hasRzDevService = @($services | Where-Object { $_ -ieq "RzDev_$($DevicePid.ToLowerInvariant())" }).Count -gt 0
    $usesRazerFilterStack = ($hasRzDevInf -or $hasRzDevService)
    $hasVcon = @($razerInfs | Where-Object { $_ -match '(?i)_vcon\.inf$' }).Count -gt 0
    $hasDeviceFilterInf = @(
        $razerInfs | Where-Object { $_ -match '(?i)_(?:dkm|mpos|kbd|kbd2|mou|mou2)\.inf$' }
    ).Count -gt 0

    $role = Get-ExplicitConnectionRole @(
        @($rootIdentity['productName']) +
        @($names)
    )

    $connection = [ordered]@{
        deviceClass = $deviceClass
        pid = $DevicePid
        modelName = $model
        productKey = $productKey
        productIdentitySource = $identitySource
        productIdentityConfidence = $identityConfidence
        connectionFingerprint = $historyKey
        connectionType = 'usb-device'
        connectionTypeConfidence = 'none'
        connectionTypeSource = 'unclassified-connection'
        presentAtScan = $present
        driverStack = $(if($usesRazerFilterStack){'razer-filter'}else{'windows-inbox'})
        driverInfNames = @($infs)
        razerDriverInfNames = @($razerInfs)
        inboxDriverInfNames = @($inboxInfs)
        serviceNames = @($services)
        topology = [ordered]@{
            rootInstanceId = [string]$rootIdentity['rootInstanceId']
            containerId = [string]$rootIdentity['containerId']
            parent = [string]$rootIdentity['parent']
            locationPaths = @($rootIdentity['locationPaths'])
            lastArrivalDate = [string]$rootIdentity['lastArrivalDate']
            hidCollectionCount = $hidCollectionIds.Count
            hidInterfaceCount = $hidInterfaceNumbers.Count
            usbInterfaceCount = $usbInterfaceNumbers.Count
        }
        capabilities = [ordered]@{
            requiresRzVirtual = $hasVcon
            requiresRzControl = $hasVcon
            requiresRazerBoundNodes = $usesRazerFilterStack
            requiresDeviceFilters = $hasDeviceFilterInf
        }
        nodes = @($nodeOut)
    }

    # Reuse previously learned role evidence for this observed connection.
    if ($null -ne $historyEntry) {
        $histType = Get-OptionalPropertyString $historyEntry 'connectionType'
        $histConfidence = Get-OptionalPropertyString $historyEntry 'connectionTypeConfidence'
        $histSource = Get-OptionalPropertyString $historyEntry 'connectionTypeSource'
        $histProductKey = Get-OptionalPropertyString $historyEntry 'productKey'
        $histCalibrated = $false
        try { $histCalibrated = [bool]$historyEntry.calibrated } catch { $histCalibrated = $false }
        $trustedHistoryRole = (
            $histCalibrated -or
            $histSource -eq 'explicit-device-role-text' -or
            $histSource -like 'user-guided-*'
        )
        if (
            $trustedHistoryRole -and
            $histType -and
            $histType -ne 'usb-device' -and
            $histType -ne 'unknown' -and
            (-not $histProductKey -or $histProductKey -eq $productKey)
        ) {
            Set-ConnectionRole $connection $histType $histConfidence $(if($histSource){'history:' + $histSource}else{'persistent-connection-history'})
        }
    }

    # Explicit transport wording from current device evidence outranks history.
    Set-ConnectionRole $connection ([string]$role['type']) ([string]$role['confidence']) ([string]$role['source'])

    $connections.Add($connection) | Out-Null
}

# ---------------------------------------------------------------------------
# Guided connection-role calibration.
#
# v2.3.0 continues to avoid assigning semantic transport roles from random
# everyday one-path/two-path snapshots. A role becomes HIGH-confidence only
# from explicit current descriptor evidence or from a user-guided reference /
# transition for one selected product. HID topology remains diagnostic data.
# ---------------------------------------------------------------------------
$calibrationResult = [ordered]@{
    requested = ($CalibrationMode -ne 'none')
    mode = $CalibrationMode
    productKey = $CalibrationProductKey
    status = $(if($CalibrationMode -eq 'none'){'not-requested'}else{'pending'})
    role = ''
    assignedPids = @()
    source = ''
    detail = ''
}

if ($CalibrationMode -ne 'none') {
    if (-not $CalibrationProductKey) {
        $calibrationResult.status = 'target-not-specified'
        $calibrationResult.detail = 'No calibration productKey was provided.'
    }
    elseif ($null -eq $baselineInventory) {
        $calibrationResult.status = 'baseline-missing'
        $calibrationResult.detail = 'The guided calibration baseline inventory is unavailable.'
    }
    else {
        $targetGroup = @(
            $connections |
            Where-Object { [string]$_['productKey'] -eq $CalibrationProductKey }
        )
        $targetPresent = @(
            $targetGroup |
            Where-Object { [bool]$_['presentAtScan'] }
        )
        $baselinePresent = @(
            @($baselineInventory.connections) |
            Where-Object {
                [string]$_.productKey -eq $CalibrationProductKey -and
                [bool]$_.presentAtScan
            }
        )

        if ($targetGroup.Count -eq 0 -or $targetPresent.Count -eq 0) {
            $calibrationResult.status = 'target-not-found'
            $calibrationResult.detail = 'The selected product is not present in the current scan.'
        }
        else {
            $baselinePids = @(
                $baselinePresent |
                ForEach-Object { ([string]$_.pid).ToUpperInvariant() } |
                Sort-Object -Unique
            )
            $currentPids = @(
                $targetPresent |
                ForEach-Object { ([string]$_['pid']).ToUpperInvariant() } |
                Sort-Object -Unique
            )
            $newPids = @(
                $currentPids |
                Where-Object { $baselinePids -notcontains $_ }
            )

            $candidatePid = ''
            $targetRole = ''
            $source = ''

            if ($CalibrationMode -eq 'wired') {
                $targetRole = 'wired-usb'
                if ($newPids.Count -eq 1) {
                    $candidatePid = [string]$newPids[0]
                    $source = 'user-guided-wired-transition'
                }
                elseif ($currentPids.Count -eq 1) {
                    # The user explicitly declared this a wired reference state.
                    $candidatePid = [string]$currentPids[0]
                    $source = 'user-guided-wired-reference'
                }
            }
            elseif ($CalibrationMode -eq 'wireless') {
                $targetRole = 'wireless-dongle'
                $knownWiredPids = @(
                    $targetGroup |
                    Where-Object {
                        [string]$_['connectionType'] -eq 'wired-usb' -and
                        (Confidence-Rank ([string]$_['connectionTypeConfidence'])) -ge 3
                    } |
                    ForEach-Object { ([string]$_['pid']).ToUpperInvariant() } |
                    Sort-Object -Unique
                )
                $nonWiredCurrent = @(
                    $currentPids |
                    Where-Object { $knownWiredPids -notcontains $_ }
                )
                $wiredWasInBaseline = @($knownWiredPids | Where-Object { $baselinePids -contains $_ }).Count -gt 0
                $wiredNowAbsent = @($knownWiredPids | Where-Object { $currentPids -contains $_ }).Count -eq 0

                if ($knownWiredPids.Count -gt 0 -and $wiredWasInBaseline -and $wiredNowAbsent -and $nonWiredCurrent.Count -eq 1) {
                    $candidatePid = [string]$nonWiredCurrent[0]
                    $source = 'user-guided-wireless-transition'
                }
                elseif ($currentPids.Count -eq 1 -and $knownWiredPids -notcontains $currentPids[0]) {
                    # The user explicitly declared this a wireless reference state.
                    $candidatePid = [string]$currentPids[0]
                    $source = 'user-guided-wireless-reference'
                }
            }

            if (-not $candidatePid) {
                $calibrationResult.status = 'ambiguous'
                $calibrationResult.detail = "Guided $CalibrationMode calibration did not yield exactly one unambiguous connection."
            }
            else {
                $candidate = $targetGroup |
                    Where-Object { ([string]$_['pid']).ToUpperInvariant() -eq $candidatePid } |
                    Select-Object -First 1
                if (-not $candidate) {
                    $calibrationResult.status = 'ambiguous'
                    $calibrationResult.detail = 'The inferred connection was not found in the selected product group.'
                }
                elseif (
                    [string]$candidate['connectionTypeSource'] -eq 'explicit-device-role-text' -and
                    [string]$candidate['connectionType'] -ne $targetRole
                ) {
                    $calibrationResult.status = 'evidence-conflict'
                    $calibrationResult.detail = 'Explicit current descriptor evidence conflicts with the guided role.'
                }
                else {
                    # Guided calibration outranks stale/history topology evidence,
                    # but never overrides contradictory explicit descriptor text.
                    $candidate['connectionType'] = $targetRole
                    $candidate['connectionTypeConfidence'] = 'high'
                    $candidate['connectionTypeSource'] = $source
                    $calibrationResult.status = 'success'
                    $calibrationResult.role = $targetRole
                    $calibrationResult.assignedPids = @($candidatePid)
                    $calibrationResult.source = $source
                    $calibrationResult.detail = 'Guided connection role calibrated successfully.'
                }
            }
        }
    }
}

# ---------------------------------------------------------------------------
# Required products = products/connections actually present during setup.
# ---------------------------------------------------------------------------
$products = New-Object System.Collections.Generic.List[object]

# Connections are OrderedDictionary objects. In Windows PowerShell 5.1,
# "Group-Object productKey" does not reliably resolve dictionary keys and can
# collapse all devices into one empty group. Group explicitly through the
# dictionary indexer instead.
$groups = @(
    $connections |
    Group-Object -Property { [string]$_['productKey'] }
)

foreach ($group in $groups) {
    $presentConnections = @(
        $group.Group |
        Where-Object { [bool]$_['presentAtScan'] }
    )

    if ($presentConnections.Count -eq 0) { continue }

    $firstPresent = $presentConnections | Select-Object -First 1
    $name = [string]$firstPresent['modelName']

    $pidsFor = @(
        $group.Group |
        ForEach-Object { [string]$_['pid'] } |
        Where-Object { $_ } |
        Sort-Object -Unique
    )

    $key = [string]$group.Name
    if (-not $key) {
        # Never emit an invalid required product with an empty identity.
        $fallbackPid = [string]$firstPresent['pid']
        $key = Product-Key $name $fallbackPid
    }

    $deviceClasses = @(
        $presentConnections |
        ForEach-Object { [string]$_['deviceClass'] } |
        Where-Object { $_ -match '^(mouse|keyboard)$' } |
        Sort-Object -Unique
    )
    $productDeviceClass = 'device'
    if ($deviceClasses.Count -eq 1) { $productDeviceClass = [string]$deviceClasses[0] }

    $products.Add([ordered]@{
        deviceClass = $productDeviceClass
        key = $key
        name = $name
        required = $true
        connectionPids = $pidsFor
    }) | Out-Null
}

# ---------------------------------------------------------------------------
# Logical product IDs from local AppEngine evidence (read-only).
# ---------------------------------------------------------------------------
$logical = New-Object System.Collections.Generic.List[string]
$logicalLatest = @{}
$mainLog = Join-Path $env:LOCALAPPDATA 'Razer\RazerAppEngine\User Data\Logs\main.log'

if (Test-Path -LiteralPath $mainLog) {
    try {
        foreach ($line in @(
            Get-Content -LiteralPath $mainLog -Tail 12000 -ErrorAction Stop
        )) {
            $idMatch = [regex]::Match(
                [string]$line,
                '(?i)product(?:Id|_id)["\\]*\s*[:=]\s*([0-9]+)'
            )
            $powerMatch = [regex]::Match(
                [string]$line,
                '(?i)isPowerOn["\\]*\s*[:=]\s*(true|false)'
            )

            if ($idMatch.Success -and $powerMatch.Success) {
                $logicalLatest[[string]$idMatch.Groups[1].Value] =
                    ([string]$powerMatch.Groups[1].Value -ieq 'true')
            }
        }
    }
    catch {
        Add-ScanError 'AppEngine main.log' $_.Exception
    }
}

foreach ($id in @($logicalLatest.Keys | Sort-Object)) {
    if ($logicalLatest[$id]) {
        $logical.Add([string]$id) | Out-Null
    }
}

# Windows PowerShell 5.1 can throw "Argument types do not match" when
# generic List[T] instances containing ordered dictionaries are embedded
# directly in another [ordered] hashtable. Materialize every generic list
# as a plain PowerShell array first.
$productArray = @()
if ($products.Count -gt 0) {
    $productArray = [object[]]$products.ToArray()
}

$connectionArray = @()
if ($connections.Count -gt 0) {
    $connectionArray = [object[]]$connections.ToArray()
}

$logicalArray = @()
if ($logical.Count -gt 0) {
    $logicalArray = [string[]]$logical.ToArray()
}

$pidArray = @()
if ($pids.Count -gt 0) {
    $pidArray = [string[]]$pids.ToArray()
}

$registryArray = @()
if ($registryRows.Count -gt 0) {
    $registryArray = [object[]]$registryRows.ToArray()
}

$driverStoreInfArray = @()
if ($allRazerInf.Count -gt 0) {
    $driverStoreInfArray = [string[]]$allRazerInf.ToArray()
}

$errorArray = @()
if ($errors.Count -gt 0) {
    $errorArray = [object[]]$errors.ToArray()
}

# ---------------------------------------------------------------------------
# Persist generic connection learning. Observed PID values are data keys only;
# no PID is assigned a role by source-code constants.
# ---------------------------------------------------------------------------
$historyNow = (Get-Date).ToUniversalTime().ToString('o')
$currentHistoryKeys = @{}
$historyConnectionOut = @(
    foreach ($c in $connectionArray) {
        $key = Get-HistoryKey ([string]$c['pid'])
        $currentHistoryKeys[$key] = $true
        $old = $null
        if ($historyMap.ContainsKey($key)) { $old = $historyMap[$key] }

        $firstSeenAt = $historyNow
        $seenCount = 0
        $presentCount = 0
        $transitionCount = 0
        $calibrated = $false
        $calibratedAt = ''
        if ($null -ne $old) {
            $v = Get-OptionalPropertyString $old 'firstSeenAt'
            if ($v) { $firstSeenAt = $v }
            try { $seenCount = [int]$old.seenCount } catch { $seenCount = 0 }
            try { $presentCount = [int]$old.presentCount } catch { $presentCount = 0 }
            try { $transitionCount = [int]$old.transitionEvidenceCount } catch { $transitionCount = 0 }
            try { $calibrated = [bool]$old.calibrated } catch { $calibrated = $false }
            $calibratedAt = Get-OptionalPropertyString $old 'calibratedAt'
        }

        $seenCount++
        if ([bool]$c['presentAtScan']) { $presentCount++ }
        $currentRoleSource = [string]$c['connectionTypeSource']
        while ($currentRoleSource -like 'history:*') {
            $currentRoleSource = $currentRoleSource.Substring(8)
        }
        if ($currentRoleSource -like 'user-guided-*') {
            $calibrated = $true
            $calibratedAt = $historyNow
        }

        $persistRoleSource = [string]$c['connectionTypeSource']
        while ($persistRoleSource -like 'history:*') {
            $persistRoleSource = $persistRoleSource.Substring(8)
        }

        [ordered]@{
            key = $key
            vendorId = $VendorId
            pid = [string]$c['pid']
            connectionFingerprint = [string]$c['connectionFingerprint']
            productKey = [string]$c['productKey']
            productName = [string]$c['modelName']
            deviceClass = [string]$c['deviceClass']
            productIdentitySource = [string]$c['productIdentitySource']
            productIdentityConfidence = [string]$c['productIdentityConfidence']
            connectionType = [string]$c['connectionType']
            connectionTypeConfidence = [string]$c['connectionTypeConfidence']
            connectionTypeSource = $persistRoleSource
            firstSeenAt = $firstSeenAt
            lastSeenAt = $historyNow
            seenCount = $seenCount
            presentCount = $presentCount
            lastPresent = [bool]$c['presentAtScan']
            transitionEvidenceCount = $transitionCount
            calibrated = $calibrated
            calibratedAt = $calibratedAt
            topology = $c['topology']
        }
    }
)

# Preserve dormant historical connections that are not discoverable in the
# current PnP/registry/DriverStore snapshot.
if ($null -ne $history) {
    foreach ($old in @($history.connections)) {
        $oldKey = [string]$old.key
        if ($oldKey -and -not $currentHistoryKeys.ContainsKey($oldKey)) {
            $historyConnectionOut += $old
        }
    }
}

$historySnapshotProducts = @(
    foreach ($group in $groups) {
        $presentPids = @(
            $group.Group |
            Where-Object { [bool]$_['presentAtScan'] } |
            ForEach-Object { ([string]$_['pid']).ToUpperInvariant() } |
            Sort-Object -Unique
        )
        if ($presentPids.Count -gt 0) {
            [ordered]@{
                productKey = [string]$group.Name
                presentPids = $presentPids
            }
        }
    }
)

$historyOut = [ordered]@{
    schemaVersion = 2
    toolVersion = $ToolVersion
    scannerVersion = $ScanVersion
    updatedAt = $historyNow
    vendorId = $VendorId
    connections = @($historyConnectionOut)
    lastSnapshot = [ordered]@{
        scannedAt = $historyNow
        products = $historySnapshotProducts
    }
}

$historyTempPath = ''
$historyShouldStage = ($CalibrationMode -eq 'none' -or [string]$calibrationResult.status -eq 'success')
if ($HistoryPath -and $historyShouldStage -and $productArray.Count -gt 0 -and $connectionArray.Count -gt 0) {
    try {
        $historyParent = Split-Path -Parent $HistoryPath
        if ($historyParent -and -not (Test-Path -LiteralPath $historyParent)) {
            New-Item -ItemType Directory -Force -Path $historyParent | Out-Null
        }
        $historyTempPath = "$HistoryPath.tmp"
        [System.IO.File]::WriteAllText(
            $historyTempPath,
            ($historyOut | ConvertTo-Json -Depth 16),
            $utf8NoBom
        )
    }
    catch {
        Add-ScanError 'Connection history stage' $_.Exception
        $historyTempPath = ''
    }
}

# Re-materialize errors after history staging.
$errorArray = @()
if ($errors.Count -gt 0) {
    $errorArray = [object[]]$errors.ToArray()
}

$inventory = [ordered]@{
    schemaVersion = 2
    toolVersion = $ToolVersion
    scanVersion = $ScanVersion
    createdAt = (Get-Date).ToUniversalTime().ToString('o')
    vendorId = $VendorId
    computer = $env:COMPUTERNAME
    products = $productArray
    productGroups = @(
        $groups |
        ForEach-Object {
            [ordered]@{
                key = [string]$_.Name
                count = @($_.Group).Count
                pids = @(
                    $_.Group |
                    ForEach-Object { [string]$_['pid'] } |
                    Where-Object { $_ } |
                    Sort-Object -Unique
                )
            }
        }
    )
    connections = $connectionArray
    logicalProductIds = $logicalArray
    calibrationResult = $calibrationResult
    sourceSummary = @(
        "Get-PnpDevice=$($pnpCmdRows.Count)",
        "CIM-PnP=$($cimPnp.Count)",
        "SignedDriver=$($signed.Count)",
        "Registry=$($registryArray.Count)",
        "DriverStoreINF=$($driverStoreInfArray.Count)"
    )
}

$debug = [ordered]@{
    schemaVersion = 1
    scannerVersion = $ScanVersion
    toolVersion = $ToolVersion
    startedAt = $started.ToUniversalTime().ToString('o')
    finishedAt = (Get-Date).ToUniversalTime().ToString('o')
    outputPath = $OutputPath
    counts = [ordered]@{
        getPnpDevicePresent = $pnpCmdRows.Count
        cimPnp = $cimPnp.Count
        signedDrivers = $signed.Count
        registryRows = $registryArray.Count
        driverStoreRazerInf = $driverStoreInfArray.Count
        discoveredPids = $pidArray.Count
        connections = $connectionArray.Count
        requiredProducts = $productArray.Count
        logicalProductIds = $logicalArray.Count
    }
    discoveredPids = @($pidArray | Sort-Object)
    presentPnpDevices = @($pnpCmdRows | Select-Object -First 200)
    cimPnpDevices = @(
        $cimPnp |
        Select-Object -First 200 |
        ForEach-Object {
            [ordered]@{
                pnpDeviceId = [string]$_.PNPDeviceID
                name = [string]$_.Name
                service = [string]$_.Service
                problemCode = [int]$_.ConfigManagerErrorCode
            }
        }
    )
    signedDriverSample = @(
        $signed |
        Select-Object -First 200 |
        ForEach-Object {
            [ordered]@{
                deviceId = [string]$_.DeviceID
                deviceName = [string]$_.DeviceName
                provider = [string]$_.DriverProviderName
                infName = [string]$_.InfName
                driverVersion = [string]$_.DriverVersion
            }
        }
    )
    registrySample = @($registryArray | Select-Object -First 200)
    driverStoreInf = $driverStoreInfArray
    products = $productArray
    connections = $connectionArray
    logicalProductIds = $logicalArray
    calibration = $calibrationResult
    connectionHistory = [ordered]@{
        path = $HistoryPath
        loaded = ($null -ne $history)
        staged = [bool]$historyTempPath
        lastSnapshot = $historyOut.lastSnapshot
    }
    errors = $errorArray
}

$debugJson = $debug | ConvertTo-Json -Depth 14
[System.IO.File]::WriteAllText($DebugJsonPath, $debugJson, $utf8NoBom)

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("=== RAZER SETUP SCANNER DEBUG $ScanVersion ===") | Out-Null
$lines.Add("Zeit: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff'))") | Out-Null
$lines.Add("OutputPath: $OutputPath") | Out-Null
$lines.Add("") | Out-Null
$lines.Add("Get-PnpDevice present: $($pnpCmdRows.Count)") | Out-Null
$lines.Add("CIM PnP:               $($cimPnp.Count)") | Out-Null
$lines.Add("SignedDriver:          $($signed.Count)") | Out-Null
$lines.Add("Registry rows:         $($registryRows.Count)") | Out-Null
$lines.Add("DriverStore Razer INF: $($allRazerInf.Count)") | Out-Null
$lines.Add("PIDs:                  $(@($pids | Sort-Object) -join ', ')") | Out-Null
$lines.Add("Connections:           $($connections.Count)") | Out-Null
$lines.Add("Required products:     $($products.Count)") | Out-Null
$lines.Add("") | Out-Null

foreach ($p in $products) {
    $lines.Add("PRODUCT: key=$($p.key) | $($p.name) | PIDs=$($p.connectionPids -join ',')") | Out-Null
}
foreach ($c in $connections) {
    $lines.Add(
        "CONNECTION: PID=$($c.pid) present=$($c.presentAtScan) identity=$($c.productIdentityConfidence)/$($c.productIdentitySource) type=$($c.connectionType) roleConfidence=$($c.connectionTypeConfidence) roleSource=$($c.connectionTypeSource) hidCollections=$($c.topology.hidCollectionCount) stack=$($c.driverStack) rzv=$($c.capabilities.requiresRzVirtual) rzc=$($c.capabilities.requiresRzControl) filters=$($c.capabilities.requiresDeviceFilters) model=$($c.modelName)"
    ) | Out-Null
}
if ($CalibrationMode -ne 'none') {
    $lines.Add("CALIBRATION: mode=$CalibrationMode productKey=$CalibrationProductKey status=$($calibrationResult.status) role=$($calibrationResult.role) PIDs=$(@($calibrationResult.assignedPids) -join ',') source=$($calibrationResult.source)") | Out-Null
}
if ($errors.Count -gt 0) {
    $lines.Add("") | Out-Null
    $lines.Add("ERRORS:") | Out-Null
    foreach ($e in $errors) {
        $lines.Add("$($e.stage): $($e.type) | $($e.message)") | Out-Null
    }
}

[System.IO.File]::WriteAllText(
    $DebugTextPath,
    ($lines -join [Environment]::NewLine),
    $utf8NoBom
)

if ($productArray.Count -eq 0 -or $connectionArray.Count -eq 0) {
    Write-Error "Keine aktuell verbundenen Razer-Produkte erkannt. Debug: $DebugJsonPath"
    exit 2
}

$inventoryJson = $inventory | ConvertTo-Json -Depth 16
[System.IO.File]::WriteAllText($OutputPath, $inventoryJson, $utf8NoBom)

if ($historyTempPath) {
    try {
        Move-Item -LiteralPath $historyTempPath -Destination $HistoryPath -Force
    }
    catch {
        # Inventory remains valid even if role-learning persistence fails.
        try { Remove-Item -LiteralPath $historyTempPath -Force -ErrorAction SilentlyContinue } catch {}
    }
}

Write-Output "SETUP_OK products=$($productArray.Count) connections=$($connectionArray.Count) calibration=$($calibrationResult.status) history=$HistoryPath debug=$DebugJsonPath"
exit 0
