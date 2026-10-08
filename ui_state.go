//go:build windows

package main

// Historical log navigation is intentionally session-only. A complete process
// restart must always enter PROTOKOLLE with only the permanent tab present.
// No historical measurement identity, active-tab state, table selection or
// scroll position is restored from disk.
func (a *App) loadUIState() {
	a.logHistoricalStamp = ""
	a.logHistoricalOpen = false
	a.logHistoricalActive = false
	a.logSelected = -1
	a.logScroll = 0
}

func (a *App) openHistoricalMeasurement(index int) bool {
	a.mu.Lock()
	if index < 0 || index >= len(a.logMeasurements) || !a.logMeasurements[index].DetailAvailable {
		a.mu.Unlock()
		return false
	}
	a.logHistoricalStamp = a.logMeasurements[index].Stamp
	a.logHistoricalOpen = true
	a.logHistoricalActive = true
	a.detailGate = -1
	a.detailScroll = 0
	a.detailRawExpanded = false
	a.mu.Unlock()
	procInvalidateRect.Call(a.hwnd, 0, 0)
	return true
}

func (a *App) closeHistoricalMeasurement() {
	a.mu.Lock()
	a.logHistoricalStamp = ""
	a.logHistoricalOpen = false
	a.logHistoricalActive = false
	a.detailGate = -1
	a.detailScroll = 0
	a.detailRawExpanded = false
	a.mu.Unlock()
	procInvalidateRect.Call(a.hwnd, 0, 0)
}

func (a *App) setHistoricalLogActive(active bool) {
	a.mu.Lock()
	if active && !a.logHistoricalOpen {
		a.mu.Unlock()
		return
	}
	a.logHistoricalActive = active
	a.detailGate = -1
	a.detailScroll = 0
	a.detailRawExpanded = false
	a.mu.Unlock()
	procInvalidateRect.Call(a.hwnd, 0, 0)
}

func (a *App) historicalMeasurement() (HistoricalMeasurement, bool) {
	a.mu.Lock()
	defer a.mu.Unlock()
	if !a.logHistoricalOpen || a.logHistoricalStamp == "" {
		return HistoricalMeasurement{}, false
	}
	idx := measurementIndexByStamp(a.logMeasurements, a.logHistoricalStamp)
	if idx < 0 || !a.logMeasurements[idx].DetailAvailable {
		return HistoricalMeasurement{}, false
	}
	return a.logMeasurements[idx], true
}
