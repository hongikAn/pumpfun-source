#!/usr/bin/env python3
"""Run the unchanged pass-capture harness with the lane-local restored v1.44 SDK."""
from pathlib import Path

import capture_passes

LANE = Path(__file__).resolve().parent
RESTORED = LANE / "toolchain-v144"

# Keep fastbuild.py itself unchanged. Only this process sees these restored paths.
capture_passes.fastbuild.SDK = RESTORED / "sdk"
capture_passes.fastbuild.RECIPES["identity"]["rustc"] = (
    RESTORED / "hybrid144/rust/bin/rustc"
)
capture_passes.main()
