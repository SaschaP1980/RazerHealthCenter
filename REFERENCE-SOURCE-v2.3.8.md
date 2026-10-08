# Reference Source v2.3.8

Canonical source baseline for Razer Synapse + Chroma Health Monitor v2.3.8.

This release is based on v2.3.7 and specifically corrects the product-selective
Gate 3 semantics and final structured Prüfdetails presentation. Health Engine
1.4.5 derives RzDev/RzCommon applicability solely from the currently selected
`required=true` products and their inventory connections. An empty requirement
set emits an explicit structured INFO check and is not a health failure. Real
relevant FAIL/UNKNOWN Kernel-driver checks remain gate-determining.

The normal detail popover renders all available structured JSON evidence for
FAIL/UNKNOWN findings: check/status header plus actual, expected, detail and
section/source text. The generic no-structured fallback is only used when no
mapped checks exist. Raw/clipboard paths remain technical and unchanged.

The completed-run publish path uses a final snapshot sanitizer so transient
CHECKING lifecycle values cannot survive after the worker has finalized.

A dedicated v2.3.8 structured-detail validator is part of `build.sh`. Applied to
the exact canonical v2.3.7 source it is RED; applied to this source it is GREEN.
No endpoint PID/model-specific production semantics are introduced.
