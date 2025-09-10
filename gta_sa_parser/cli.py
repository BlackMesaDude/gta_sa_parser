# gta_node_parser/cli.py
import argparse
from pathlib import Path
from typing import List
from .parsers import load_parsers_from_schemas, find_parser_for_file
from .utils import ensure_dir, save_json

def main():
    parser = argparse.ArgumentParser(description='Parse GTA:SA NODES*.DAT and trains.dat files')
    
    # Schema options
    schema_group = parser.add_mutually_exclusive_group()
    schema_group.add_argument('--schema-dir', default='schemas', 
                             help='Directory containing schema files (default: schemas)')
    schema_group.add_argument('--schema-file', 
                             help='Specific schema file to use for parsing')
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input-dir', help='Input directory containing DAT files')
    input_group.add_argument('--input-file', help='Specific file to parse')
    
    parser.add_argument('--output-dir', default='output', help='Output directory for JSON files and images')
    parser.add_argument('--list-schemas', action='store_true', help='List all available schemas')
    
    args = parser.parse_args()
    
    # Load schema files
    schema_dir = Path(args.schema_dir)
    
    # List schemas if requested
    if args.list_schemas:
        print("Available schemas:")
        try:
            parsers = load_parsers_from_schemas(schema_dir)
            for parser in parsers:
                print(f"  {parser.parser_name}: {parser.file_pattern}")
        except Exception as e:
            print(f"Error loading schemas: {e}")
        return
    
    # Ensure output directory exists
    output_dir = ensure_dir(args.output_dir)
    
    # Load parsers
    try:
        parsers = load_parsers_from_schemas(schema_dir)
        if not parsers:
            print(f"No valid schemas found in {schema_dir}")
            return
    except Exception as e:
        print(f"Error loading schemas: {e}")
        return
    
    # Process files
    files_to_process = []
    
    if args.input_file:
        # Process a specific file
        file_path = Path(args.input_file)
        if not file_path.exists():
            print(f"Error: Input file not found: {file_path}")
            return
        files_to_process = [file_path]
    else:
        # Process all files in directory
        input_dir = Path(args.input_dir)
        if not input_dir.exists():
            print(f"Error: Input directory not found: {input_dir}")
            return
        
        # Find all files that match any parser pattern
        for parser in parsers:
            pattern = parser.file_pattern
            matching_files = list(input_dir.glob(pattern))
            files_to_process.extend(matching_files)
        
        # Remove duplicates
        files_to_process = list(set(files_to_process))
    
    if not files_to_process:
        print("No files found to process")
        return
    
    # Process each file
    processed_count = 0
    for file_path in files_to_process:
        print(f"Processing {file_path.name}...")
        
        # Find the appropriate parser for this file
        file_parser = find_parser_for_file(parsers, file_path)
        if not file_parser:
            print(f"  No parser found for {file_path.name}")
            continue
            
        try:
            # Parse the file
            parsed_data = file_parser.parse_file(file_path)
            serializable_data = file_parser.to_serializable(parsed_data)
            
            # Save as JSON
            json_filename = output_dir / f"{file_path.stem}.json"
            save_json(serializable_data, json_filename)
            print(f"  Saved JSON to {json_filename}")
            
            processed_count += 1
                    
        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")
    
    print(f"Processing complete! Processed {processed_count} files.")

if __name__ == "__main__":
    main()