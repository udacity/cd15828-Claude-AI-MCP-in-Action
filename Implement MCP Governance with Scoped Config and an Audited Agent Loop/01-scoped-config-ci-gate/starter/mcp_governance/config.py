"""Central configuration: paths and the default model. No scattered constants."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent

DATA_DIR = PROJECT_ROOT / "data"
CLAIMS_DIR = DATA_DIR / "claims"
POLICIES_DIR = DATA_DIR / "policies"
INTEGRATION_NEEDS_PATH = DATA_DIR / "integration_needs.json"
FIXTURES_DIR = PROJECT_ROOT / "fixtures"

# Cheap, sufficient for tool dispatch. Configurable where it matters (loop/runner).
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
