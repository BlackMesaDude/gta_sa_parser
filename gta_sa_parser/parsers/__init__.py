# gta_node_parser/parsers/__init__.py
from pathlib import Path
from typing import List, Optional
import fnmatch

from .base import BaseParser
from .schema_parser import SchemaParser

__all__ = ["BaseParser", "SchemaParser", "load_parsers_from_schemas", "find_parser_for_file"]

def load_parsers_from_schemas(schema_dir: Path) -> List[SchemaParser]:
    """
    Load all SchemaParser instances from JSON schema files in the given folder.
    
    Args:
        schema_dir: Path to the directory containing schema files
        
    Returns:
        List of SchemaParser instances
        
    Raises:
        ValueError: If schema_dir is not a valid directory
    """
    if not schema_dir.exists():
        raise ValueError(f"Schema directory does not exist: {schema_dir}")
    
    if not schema_dir.is_dir():
        raise ValueError(f"Schema path is not a directory: {schema_dir}")
    
    parsers = []
    for schema_file in schema_dir.glob("*.json"):
        try:
            parser = SchemaParser(schema_file)
            parsers.append(parser)
        except Exception as e:
            print(f"[WARN] Failed to load schema {schema_file}: {e}")
    
    return parsers


def find_parser_for_file(parsers: List[BaseParser], file_path: Path) -> Optional[BaseParser]:
    """
    Find a parser whose file pattern matches the given file.
    
    Args:
        parsers: List of parser instances to search through
        file_path: Path to the file to find a parser for
        
    Returns:
        Matching parser instance or None if no match found
    """
    if not parsers:
        return None
        
    filename = file_path.name
    for parser in parsers:
        pattern = parser.file_pattern
        
        # Handle exact matches
        if pattern == filename:
            return parser
            
        # Handle patterns with wildcards using fnmatch
        if '*' in pattern or '?' in pattern:
            if fnmatch.fnmatch(filename, pattern):
                return parser
        # Handle case-insensitive matching for extensions
        elif filename.lower() == pattern.lower():
            return parser
    
    return None