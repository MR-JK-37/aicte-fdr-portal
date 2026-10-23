from functools import lru_cache
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


@lru_cache
def load_table_1_4() -> dict:
    with open(CONFIG_DIR / "table_1_4.yaml") as f:
        return yaml.safe_load(f)


@lru_cache
def load_penalty_config() -> dict:
    with open(CONFIG_DIR / "penalties.yaml") as f:
        return yaml.safe_load(f)
