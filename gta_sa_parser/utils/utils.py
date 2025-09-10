import os
import json
from pathlib import Path
from typing import Dict, List, Any, Union

def ensure_dir(directory: Union[str, Path]) -> Path:
    """Ensure directory exists."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_json(data: Any, filename: Union[str, Path]) -> None:
    """Save data as JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def load_json(filename: Union[str, Path]) -> Any:
    """Load JSON file."""
    with open(filename, 'r') as f:
        return json.load(f)

def get_files(pattern: str) -> List[Path]:
    """Get files matching pattern."""
    return list(Path('.').glob(pattern))