//go:build windows

package main

import (
	"fmt"
	"os"
	"runtime"
	"sync/atomic"
	"time"
)

const wmTracePing = wmApp + 20

func updateAtomicMax(dst *int64, v int64) {
	for {
		old := atomic.LoadInt64(dst)
		if v <= old || atomic.CompareAndSwapInt64(dst, old, v) {
			return
		}
	}
}

func uiMessageName(m uint32) string {
	switch m {
	case wmPaint:
		return "WM_PAINT"
	case wmMouseMove:
		return "WM_MOUSEMOVE"
	case wmLButtonDown:
		return "WM_LBUTTONDOWN"
	case wmLButtonUp:
		return "WM_LBUTTONUP"
	case wmMouseWheel:
		return "WM_MOUSEWHEEL"
	case wmClose:
		return "WM_CLOSE"
	case wmTracePing:
		return "WM_TRACE_PING"
	case wmRefresh:
		return "WM_REFRESH"
	}
	return fmt.Sprintf("0x%04X", m)
}

func (a *App) appendUITrace(format string, args ...any) {
	if a.tracePath == "" {
		return
	}
	f, err := os.OpenFile(a.tracePath, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return
	}
	defer f.Close()
	_, _ = fmt.Fprintf(f, "%s %s\r\n", time.Now().Format("2006-01-02 15:04:05.000"), fmt.Sprintf(format, args...))
}

func (a *App) writeUIHangStack(reason string) string {
	if a.diagDir == "" {
		return ""
	}
	p := a.diagDir + `\UIHangStack-` + a.session + `-` + time.Now().Format("20060102-150405.000") + `.txt`
	buf := make([]byte, 1<<20)
	n := runtime.Stack(buf, true)
	header := fmt.Sprintf("Razer Health Center UI hang stack\r\nVersion: %s\r\nTimestamp: %s\r\nReason: %s\r\n\r\n", referenceVersion, time.Now().Format(time.RFC3339Nano), reason)
	_ = os.WriteFile(p, append([]byte(header), buf[:n]...), 0644)
	a.debugf("UI watchdog stack written: %s reason=%s", p, reason)
	return p
}

func (a *App) startUITrace() {
	if a.traceStop != nil {
		return
	}
	if a.tracePath == "" {
		a.tracePath = a.diagDir + `\UITrace-` + a.session + `.log`
	}
	_ = os.WriteFile(a.tracePath, nil, 0644)
	a.traceStop = make(chan struct{})
	a.traceDone = make(chan struct{})
	atomic.StoreInt64(&a.traceLastPongNs, time.Now().UnixNano())
	a.appendUITrace("TRACE START version=%s pid=%d hwnd=0x%X dpi=%d go=%s guiThread=%d currentThread=%d", referenceVersion, os.Getpid(), a.hwnd, a.dpi, runtime.Version(), a.traceGUIThreadID, currentThreadID())
	go a.uiTraceWatchdog()
}

func (a *App) stopUITrace() {
	if a.traceStop == nil {
		return
	}
	close(a.traceStop)
	<-a.traceDone
	a.traceStop = nil
	a.traceDone = nil
}

func (a *App) uiTraceWatchdog() {
	defer close(a.traceDone)
	a.traceLoopThreadID = currentThreadID()
	ticker := time.NewTicker(time.Second)
	defer ticker.Stop()
	var lastDump time.Time
	for {
		select {
		case <-a.traceStop:
			return
		case <-ticker.C:
			seq := atomic.AddUint64(&a.tracePongSeq, 1)
			procPostMessageW.Call(a.hwnd, wmTracePing, uintptr(seq), 0)
			last := time.Unix(0, atomic.LoadInt64(&a.traceLastPongNs))
			age := time.Since(last)
			var ms runtime.MemStats
			runtime.ReadMemStats(&ms)
			a.appendUITrace("HEARTBEAT ping=%d age=%s lastMsg=%s paints=%d mouse=%d invalid=%d goroutines=%d heap=%dKB sys=%dKB guiThread=%d wndThread=%d threadMismatch=%d", seq, age.Round(time.Millisecond), uiMessageName(atomic.LoadUint32(&a.traceLastMsg)), atomic.LoadUint64(&a.tracePaints), atomic.LoadUint64(&a.traceMouseMoves), atomic.LoadUint64(&a.traceInvalidations), runtime.NumGoroutine(), ms.HeapAlloc/1024, ms.Sys/1024, a.traceGUIThreadID, atomic.LoadUint32(&a.traceLastWndThreadID), atomic.LoadUint64(&a.traceThreadMismatches))
			if age > 3*time.Second && time.Since(lastDump) > 15*time.Second {
				reason := fmt.Sprintf("UI heartbeat delayed %s; lastMsg=%s", age.Round(time.Millisecond), uiMessageName(atomic.LoadUint32(&a.traceLastMsg)))
				a.writeUIHangStack(reason)
				lastDump = time.Now()
			}
		}
	}
}
