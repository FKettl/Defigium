import yaml
from typing import Dict, Any

def load_config(path: str = 'config.yaml') -> Dict[str, Any]:
    """
    Load our YAML config file.
    """
    print(f"Loading configuration from '{path}'...")
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config   