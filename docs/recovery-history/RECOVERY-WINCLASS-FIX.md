# Recovery Win32 class fix — r3

Native Windows r2 reached the Go program and unpacked Runtime successfully, then failed in `RegisterClassExW` with `ERROR_INVALID_PARAMETER`.

The r2 reconstructed `wndClassEx` allocated the correct 80-byte structure but omitted `LpszClassName`, leaving it NULL even though the class-name UTF-16 buffer had been created. Golden v1.7.0 objdump/DWARF proves the original assigns `RazerHealthMonitorMainWindow` at offset 64 and registers a second `RazerHealthMonitorModalWindow` class.

r3 reconstructs the startup window path directly from Golden v1.7.0 main.go:1236-1283:

- exact main class: `RazerHealthMonitorMainWindow`
- exact modal class: `RazerHealthMonitorModalWindow`
- `WNDCLASSEXW.cbSize = 80` and non-NULL `lpszClassName`
- exact Golden title: `Razer Synapse + Chroma Health Monitor v1.7.0`
- exact Golden main style: `0x00CA0000`
- logical client size 1180x800, DPI-scaled
- `AdjustWindowRectEx` and primary-screen centering
- class/window-stage debug logging for the next native test

The modal callback remains a recovered compatibility stub until modal behavior itself is reconstructed.
