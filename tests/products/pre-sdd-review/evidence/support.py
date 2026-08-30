from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
EVIDENCE_ROOT = ROOT / "skills" / "pre-sdd-review" / "evidence"
if str(EVIDENCE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVIDENCE_ROOT))
