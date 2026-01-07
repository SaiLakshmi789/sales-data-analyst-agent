from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class EngineArtifacts:
    kpis: Dict[str, Any]
    data_quality: Dict[str, Any]
    eda: Dict[str, Any]
    ingestion_meta: Dict[str, Any]
    executive_summary_text: Optional[str]


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text_if_exists(path: Path) -> Optional[str]:
    return path.read_text(encoding="utf-8") if path.exists() else None


def load_engine_artifacts(outputs_dir: str = "outputs") -> EngineArtifacts:
    out = Path(outputs_dir)

    kpis = _read_json(out / "kpi_summary.json")
    data_quality = _read_json(out / "data_quality_report.json")
    eda = _read_json(out / "eda_report.json")
    ingestion_meta = _read_json(out / "ingestion_meta.json")

    # Your file name might be executive_summary.md or executive_summary.txt
    # We’ll try common options without guessing too much.
    exec_text = (
        _read_text_if_exists(out / "executive_summary.md")
    )

    return EngineArtifacts(
        kpis=kpis,
        data_quality=data_quality,
        eda=eda,
        ingestion_meta=ingestion_meta,
        executive_summary_text=exec_text,
    )
