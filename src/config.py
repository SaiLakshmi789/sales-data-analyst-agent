from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class PipelineConfig:
    output_dir: Path = Path("outputs")
    charts_dir: Path = Path("outputs/charts")
    tables_dir: Path = Path("outputs/tables")

    # Cleaning rules
    drop_zero_quantity: bool = True
    drop_zero_price: bool = True
    require_core_fields: bool = True

def ensure_dirs(cfg: PipelineConfig) -> None:
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    cfg.charts_dir.mkdir(parents=True, exist_ok=True)
    cfg.tables_dir.mkdir(parents=True, exist_ok=True)
