//go:build windows

package main

import (
	"sync"
	"time"
)

const (
	appVersion                   = "3.0.8.9"
	referenceVersion             = "3.0.8.9"
	legacyHistoryFallbackVersion = "1.7.0"
	engineVersion                = "1.4.6"
	gateCount                    = 13

	overallUnchecked  = "UNCHECKED"
	overallChecking   = "CHECKING"
	overallHealthy    = "HEALTHY"
	overallIncomplete = "UNCLEAR"
	overallFailed     = "FAILED"

	gateUnchecked = "UNCHECKED"
	gateWaiting   = "WAITING"
	gateChecking  = "CHECKING"
	gatePassed    = "PASS"
	gateHint      = "WARN"
	gateUnclear   = "UNKNOWN"
	gateFailed    = "FAIL"

	measurementHealthy = "HEALTHY"
	measurementHint    = "HINT"
	measurementUnclear = "UNCLEAR"
	measurementFailed  = "FAILED"
)

func appName() string { return tr("app.title") }

type Gate struct {
	Name   string `json:"Name"`
	Status string `json:"Status"`
	Label  string `json:"Label,omitempty"`
	Detail string `json:"Detail"`
}

type EngineCheck struct {
	Section      string `json:"Section"`
	Status       string `json:"Status"`
	Check        string `json:"Check"`
	Actual       string `json:"Actual"`
	Expected     string `json:"Expected"`
	Detail       string `json:"Detail"`
	EvidenceRole string `json:"EvidenceRole,omitempty"`
}

type EngineResult struct {
	SchemaVersion    int           `json:"schemaVersion"`
	ToolVersion      string        `json:"toolVersion"`
	EngineVersion    string        `json:"engineVersion"`
	BaselineDate     string        `json:"baselineDate"`
	Timestamp        string        `json:"timestamp"`
	Computer         string        `json:"computer"`
	User             string        `json:"user"`
	Elevated         bool          `json:"elevated"`
	Overall          string        `json:"overall"`
	OverallLabel     string        `json:"overallLabel"`
	RawDiagnostic    string        `json:"rawDiagnostic"`
	Gates            []Gate        `json:"gates"`
	Checks           []EngineCheck `json:"checks"`
	TechnicalDetails []string      `json:"technicalDetails"`
}

type GateInspection struct {
	Available  bool
	GateDetail string
	Checks     []EngineCheck
}

type MeasurementExportState struct {
	Stamp       string    `json:"stamp"`
	StartedAt   time.Time `json:"startedAt"`
	CompletedAt time.Time `json:"completedAt"`
	Overall     string    `json:"overall"`
	Files       []string  `json:"files"`
}

type HistoricalMeasurement struct {
	Stamp                   string
	StartedAt               time.Time
	CompletedAt             time.Time
	Overall                 string
	Duration                time.Duration
	AppSession              string
	SessionResolved         bool
	AppVersion              string
	EngineVersion           string
	Files                   []string
	DetailAvailable         bool
	DetailUnavailableReason string
	GateStates              [gateCount]string
	GateInspections         [gateCount]GateInspection
}

type DiagnosticsExportManifest struct {
	SchemaVersion         int                     `json:"schemaVersion"`
	App                   string                  `json:"app"`
	AppVersion            string                  `json:"appVersion"`
	ExportedAt            string                  `json:"exportedAt"`
	ExportMode            string                  `json:"exportMode"`
	AppSession            string                  `json:"appSession"`
	SessionResolved       bool                    `json:"sessionResolved"`
	MeasurementInProgress bool                    `json:"measurementInProgress"`
	LastMeasurement       *MeasurementExportState `json:"lastMeasurement,omitempty"`
	SelectedMeasurement   *MeasurementExportState `json:"selectedMeasurement,omitempty"`
	IncludedSessionFiles  []string                `json:"includedSessionFiles"`
	IncludedMeasureFiles  []string                `json:"includedMeasurementFiles"`
}

type FailureDump struct {
	SchemaVersion  int    `json:"schemaVersion"`
	ToolVersion    string `json:"toolVersion"`
	Timestamp      string `json:"timestamp"`
	Overall        string `json:"overall"`
	Reason         string `json:"reason"`
	EngineExitCode int    `json:"engineExitCode"`
	Gates          []Gate `json:"gates"`
}

type AdminHelperDone struct {
	Version  string `json:"version"`
	ExitCode int    `json:"exitCode"`
	RunError string `json:"runError"`
	Duration string `json:"duration"`
}

type point struct{ X, Y int32 }
type rect struct{ Left, Top, Right, Bottom int32 }
type size struct{ CX, CY int32 }

type msg struct {
	HWnd     uintptr
	Message  uint32
	_        uint32
	WParam   uintptr
	LParam   uintptr
	Time     uint32
	Pt       point
	LPrivate uint32
}

type paintStruct struct {
	Hdc         uintptr
	FErase      int32
	RcPaint     rect
	FRestore    int32
	FIncUpdate  int32
	RgbReserved [32]byte
}

type trackMouseEvent struct {
	CbSize      uint32
	DwFlags     uint32
	HwndTrack   uintptr
	DwHoverTime uint32
}

type measureItemStruct struct {
	CtlType    uint32
	CtlID      uint32
	ItemID     uint32
	ItemWidth  uint32
	ItemHeight uint32
	ItemData   uintptr
}

type drawItemStruct struct {
	CtlType    uint32
	CtlID      uint32
	ItemID     uint32
	ItemAction uint32
	ItemState  uint32
	HwndItem   uintptr
	HDC        uintptr
	RcItem     rect
	ItemData   uintptr
}

type wndClassEx struct {
	CbSize        uint32
	Style         uint32
	LpfnWndProc   uintptr
	CbClsExtra    int32
	CbWndExtra    int32
	HInstance     uintptr
	HIcon         uintptr
	HCursor       uintptr
	HbrBackground uintptr
	LpszMenuName  *uint16
	LpszClassName *uint16
	HIconSm       uintptr
}

type notifyIconData struct {
	CbSize           uint32
	_                uint32
	HWnd             uintptr
	UID              uint32
	UFlags           uint32
	UCallbackMessage uint32
	_2               uint32
	HIcon            uintptr
	SzTip            [128]uint16
	DwState          uint32
	DwStateMask      uint32
	SzInfo           [256]uint16
	UVersion         uint32
	SzInfoTitle      [64]uint16
	DwInfoFlags      uint32
	GuidItem         [16]byte
	HBalloonIcon     uintptr
}

type App struct {
	mu                                                                                                                                                                                                  sync.Mutex
	setupProbeMu                                                                                                                                                                                        sync.Mutex
	hwnd                                                                                                                                                                                                uintptr
	dpi                                                                                                                                                                                                 int
	iconIdle, iconPass, iconFail                                                                                                                                                                        uintptr
	iconApp, iconAppSmall, iconAppInfo                                                                                                                                                                  uintptr
	iconStatusReady, iconStatusPass, iconStatusFail                                                                                                                                                     uintptr
	iconStatusPulse                                                                                                                                                                                     [8]uintptr
	sidebarIcons                                                                                                                                                                                        [4][2]uintptr
	componentIcons                                                                                                                                                                                      [13][4]uintptr
	fontTitle, fontSubtitle, fontH1, fontBody, fontBodySemi, fontSmall, fontTiny                                                                                                                        uintptr
	fontBrand, fontOverall, fontRuntime, fontAction, fontActionIcon, fontNav, fontDetailClose                                                                                                           uintptr
	modalHwnd                                                                                                                                                                                           uintptr
	dataDir, logsDir, diagDir, runtimeDir, exportsDir, enginePath, debugPath, session                                                                                                                   string
	lastMeasurement                                                                                                                                                                                     MeasurementExportState
	lastGateStates                                                                                                                                                                                      [gateCount]string
	lastGateInspections                                                                                                                                                                                 [gateCount]GateInspection
	checking                                                                                                                                                                                            bool
	overall                                                                                                                                                                                             string
	states                                                                                                                                                                                              [gateCount]string
	liveGateDisplay                                                                                                                                                                                     [gateCount]string
	gateInspections                                                                                                                                                                                     [gateCount]GateInspection
	hoverGate, detailGate, detailScroll                                                                                                                                                                 int
	detailScrollMax, detailScrollTrackTop, detailScrollTrackBottom                                                                                                                                      int
	detailScrollThumbTop, detailScrollThumbBottom, detailScrollDragOffset                                                                                                                               int
	detailScrollDragging                                                                                                                                                                                bool
	detailRawExpanded                                                                                                                                                                                   bool
	detailCopyFeedback                                                                                                                                                                                  string
	lastCheck                                                                                                                                                                                           time.Time
	lastDuration                                                                                                                                                                                        time.Duration
	checkStarted                                                                                                                                                                                        time.Time
	currentGate                                                                                                                                                                                         string
	completedGates                                                                                                                                                                                      int
	quitting, exporting                                                                                                                                                                                 bool
	exportDialogVisible                                                                                                                                                                                 bool
	exportDialogPath                                                                                                                                                                                    string
	exportResultPath                                                                                                                                                                                    string
	exportResultErr                                                                                                                                                                                     error
	repairScriptPath, repairAppEngineScriptPath, diagnosticChromaServicesPath, diagnosticAppEnginePath                                                                                                  string
	repairing                                                                                                                                                                                           bool
	repairDialogVisible                                                                                                                                                                                 bool
	repairDialogStage                                                                                                                                                                                   int
	repairTargets                                                                                                                                                                                       []string
	repairID, repairResultPath, repairLogPath, repairResultErr, repairProblemID, repairRecipeID                                                                                                         string
	repairResult                                                                                                                                                                                        RepairResult
	problemFindings                                                                                                                                                                                     []ProblemFinding
	problemSnapshotPath                                                                                                                                                                                 string
	elevated, adminCheck                                                                                                                                                                                bool
	hoverAction, hoverSidebar, hoverDetailButton, hoverModalButton, hoverRepairButton, hoverSetupCalibrationButton, hoverSetupNoticeButton, hoverSetupProductRow, hoverLogRow, hoverLogTab, currentView int
	hoverDetailClose                                                                                                                                                                                    bool
	logMeasurements                                                                                                                                                                                     []HistoricalMeasurement
	logSelected, logScroll                                                                                                                                                                              int
	logHistoricalStamp                                                                                                                                                                                  string
	logHistoricalOpen, logHistoricalActive, hoverLogClose, hoverLogDetails                                                                                                                              bool
	logsLoading                                                                                                                                                                                         bool
	logsLastScan                                                                                                                                                                                        time.Time
	pressedAction                                                                                                                                                                                       int
	mouseTracking                                                                                                                                                                                       bool
	tracePath                                                                                                                                                                                           string
	startupDebugPath                                                                                                                                                                                    string
	traceStop                                                                                                                                                                                           chan struct{}
	traceDone                                                                                                                                                                                           chan struct{}
	tracePongSeq                                                                                                                                                                                        uint64
	traceLastPongNs                                                                                                                                                                                     int64
	traceLastMsg                                                                                                                                                                                        uint32
	traceInWndProc                                                                                                                                                                                      int32
	traceWndStartNs                                                                                                                                                                                     int64
	traceLastWndNs                                                                                                                                                                                      int64
	traceMaxWndNs                                                                                                                                                                                       int64
	traceMouseMoves                                                                                                                                                                                     uint64
	tracePaints                                                                                                                                                                                         uint64
	traceInvalidations                                                                                                                                                                                  uint64
	traceInPaint                                                                                                                                                                                        int32
	tracePaintStartNs                                                                                                                                                                                   int64
	traceLastPaintNs                                                                                                                                                                                    int64
	traceMaxPaintNs                                                                                                                                                                                     int64
	traceGUIThreadID                                                                                                                                                                                    uint32
	traceLoopThreadID                                                                                                                                                                                   uint32
	traceLastWndThreadID                                                                                                                                                                                uint32
	traceThreadMismatches                                                                                                                                                                               uint64
	versionStatus                                                                                                                                                                                       VersionStatus
	versionStatusPath                                                                                                                                                                                   string
	versionChecking                                                                                                                                                                                     bool
	setupDir, inventoryPath, connectionHistoryPath, setupScriptPath                                                                                                                                     string
	setupReady, setupScanning, setupContinueHealth                                                                                                                                                      bool
	setupLastError                                                                                                                                                                                      string
	inventory                                                                                                                                                                                           DeviceInventory
	setupLiveFresh, setupLiveRefreshing, setupLiveRefreshRunning, setupLiveRefreshQueued                                                                                                                bool
	setupLiveLast                                                                                                                                                                                       time.Time
	setupLiveLastError, setupLiveRefreshReason                                                                                                                                                          string
	setupLiveRefreshGeneration                                                                                                                                                                          uint64
	deviceNotifyHandle                                                                                                                                                                                  uintptr
	setupCalibrationVisible                                                                                                                                                                             bool
	setupCalibrationStage                                                                                                                                                                               int
	setupCalibrationProductIndex                                                                                                                                                                        int
	setupCalibrationError                                                                                                                                                                               string
	setupCalibrationLearned                                                                                                                                                                             int
	setupCalibrationGeneration                                                                                                                                                                          uint64
	setupCalibrationMode, setupCalibrationProductKey                                                                                                                                                    string
	setupCalibrationSuccessPID, setupCalibrationSuccessRole                                                                                                                                             string
	setupCalibrationBaseline                                                                                                                                                                            map[string]bool
	setupCalibrationVerifyRunning, setupCalibrationVerifyQueued                                                                                                                                         bool
	setupCalibrationNeedsInventoryRefresh                                                                                                                                                               bool
	setupNoticeVisible                                                                                                                                                                                  bool
	setupNoticeTitle, setupNoticeDetail                                                                                                                                                                 string
	trayMenuHwnd                                                                                                                                                                                        uintptr
	trayMenuHover, trayMenuPressed                                                                                                                                                                      int
}

var gateNameKeys = [gateCount]string{
	"gate.appengine.name", "gate.driverstore.name", "gate.kernel.name",
	"gate.devices.name", "gate.virtual.name", "gate.filters.name",
	"gate.chroma_registry.name", "gate.chroma_services.name", "gate.synapse_services.name", "gate.game_manager.name",
	"gate.rzcom.name", "gate.power.name", "gate.lamparray.name",
}

var gateDetailKeys = [gateCount]string{
	"gate.appengine.detail", "gate.driverstore.detail", "gate.kernel.detail",
	"gate.devices.detail", "gate.virtual.detail", "gate.filters.detail",
	"gate.chroma_registry.detail", "gate.chroma_services.detail",
	"gate.synapse_services.detail", "gate.game_manager.detail",
	"gate.rzcom.detail", "gate.power.detail", "gate.lamparray.detail",
}

func gateName(index int) string {
	if index < 0 || index >= gateCount {
		return ""
	}
	return tr(gateNameKeys[index])
}

func gateDetail(index int) string {
	if index < 0 || index >= gateCount {
		return ""
	}
	return tr(gateDetailKeys[index])
}

var componentIconNames = [gateCount]string{
	"appengine", "driverstore", "kernel", "keyboard", "virtual", "filters", "registry",
	"chroma-services", "synapse-services", "game-manager", "rzcom", "power", "lamparray",
}
