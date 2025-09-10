from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any

class BaseParser(ABC):
    """Abstract base class for all GTA:SA file parsers."""
    
    @abstractmethod
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a file and return structured data."""
        pass
    
    @abstractmethod
    def to_serializable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert parsed data to a serializable format."""
        pass
    
    @property
    @abstractmethod
    def file_pattern(self) -> str:
        """Return the file pattern this parser handles."""
        pass
    
    @property
    @abstractmethod
    def parser_name(self) -> str:
        """Return the name of this parser."""
        pass