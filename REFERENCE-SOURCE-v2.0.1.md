# Canonical Reference Source v2.0.1

v2.0.1 is the canonical source reference after the PowerShell encoding patch.

Functional scope is unchanged from v2.0.0: read-only Health Engine 1.3.5 plus
the narrowly scoped, explicit Gate-8 Chroma service repair.

Encoding patch:
- embedded `health-engine-v1.3.5.ps1` remains SHA-256
  `11e441f05e8992eeea75c6e1d80282693bc6ccd29f0c21018b0e7698970928f1`;
- the ephemeral Runtime execution copy is prefixed with UTF-8 BOM for Windows
  PowerShell 5.1 source decoding;
- redirected PowerShell stdout/stderr are forced to UTF-8 before capture;
- report/JSON/EngineOutput therefore preserve German umlauts correctly.

Every future release continues to ship both Portable ZIP and complete Source ZIP.
