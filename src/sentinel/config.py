
from pathlib import Path

import yaml


# Find the root directory of the project.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_config():
    """
    Load Sentinel configuration from settings.yaml.
    """

    config_path = PROJECT_ROOT / "config" / "settings.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("Invalid Sentinel configuration.")

    return config


if __name__ == "__main__":
    configuration = load_config()

    print("Sentinel Configuration Loaded Successfully")
    print(configuration)
