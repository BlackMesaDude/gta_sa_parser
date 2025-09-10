# schema_parser.py
import construct
import json
from pathlib import Path
from typing import Dict, Any, Callable
from functools import reduce
import operator

from .base import BaseParser

class SchemaParser(BaseParser):
    """Parses schema files for GTA SA data files using Construct."""

    # Mapping from schema JSON type strings → Construct types
    TYPE_MAPPING = {
        "char": construct.Byte,
        # Unsigned
        "Int8ul": construct.Int8ul,
        "Int16ul": construct.Int16ul,
        "Int32ul": construct.Int32ul,
        "Int64ul": construct.Int64ul,
        # Signed
        "Int8sl": construct.Int8sl,
        "Int16sl": construct.Int16sl,
        "Int32sl": construct.Int32sl,
        "Int64sl": construct.Int64sl,
        # Floats
        "Float32l": construct.Float32l,
        "Float64l": construct.Float64l,
        # Convenience aliases (if your schemas use lowercase or different keywords)
        "int8": construct.Int8sl,
        "uint8": construct.Int8ul,
        "int16": construct.Int16sl,
        "uint16": construct.Int16ul,
        "int32": construct.Int32sl,
        "uint32": construct.Int32ul
    }

    def __init__(self, schema_file: Path):
        self.schema_file = schema_file
        self.schema = self.load_schema(schema_file)
        self.struct = self.build_struct_from_schema(self.schema["structure"])

    def load_schema(self, schema_file: Path) -> Dict[str, Any]:
        with open(schema_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _resolve_this_path(self, path: str) -> Callable:
        """
        Return a function that will be called by Construct at parse-time with the context,
        and will retrieve nested value using dot notation like "header.num_vehicle_nodes".
        """
        parts = path.split(".")

        def resolver(ctx):
            # ctx is a Container-like object; use reduce + operator.getitem to traverse.
            return reduce(operator.getitem, parts, ctx)

        return resolver

    def build_struct_from_schema(self, schema: Dict[str, Any]) -> construct.Construct:
        schema_type = schema.get("type", "struct")

        # STRUCT
        if schema_type == "struct":
            fields = {}
            for field in schema.get("fields", []):
                name = field["name"]
                fields[name] = self.build_struct_from_schema(field)
            return construct.Struct(**fields)

        # ARRAY
        elif schema_type == "array":
            element_struct = self.build_struct_from_schema(schema["elements"])
            if "count" in schema:
                count_expr = schema["count"]
                if isinstance(count_expr, int):
                    return construct.Array(count_expr, element_struct)
                elif isinstance(count_expr, str):
                    # support "header.num_vehicle_nodes"
                    return construct.Array(self._resolve_this_path(count_expr), element_struct)
                else:
                    raise ValueError(f"Unsupported count type: {count_expr}")
            elif schema.get("until_eof", False):
                return construct.GreedyRange(element_struct)
            else:
                raise ValueError("Array must have 'count' or 'until_eof'")

        # CHAR
        if schema_type == "char":
            return BoolBitAdapter(self.TYPE_MAPPING["char"])
        
        # BYTES
        elif schema_type == "bytes":
            size = schema.get("size", 0)
            if size <= 0:
                raise ValueError("Bytes must have a positive 'size'")
            return construct.Bytes(size)

        # STRING
        elif schema_type == "string":
            length = schema.get("length")
            if length is None:
                raise ValueError("String must have 'length'")
            encoding = schema.get("encoding", "ascii")
            return construct.PaddedString(length, encoding)

        # BITFIELD
        elif schema_type == "bitfield":
            return self.build_bitfield_struct(schema)
        
        # BASIC TYPES
        elif schema_type in self.TYPE_MAPPING:
            base_type = self.TYPE_MAPPING[schema_type]
            scale = schema.get("scale")
            if scale is not None:
                return ScaleAdapter(base_type, scale)
            return base_type
        
        else:
            raise ValueError(f"Unknown type in schema: {schema_type}")

    def build_bitfield_struct(self, schema: Dict[str, Any]) -> construct.Construct:
        """Builds bitfield structures from the given schema with support for 'bit' entries."""
        size_bits = schema.get("size", 16)
        size_bytes = (size_bits + 7) // 8

        base_type = construct.BytesInteger(size_bytes, swapped=False, signed=False)

        flags = schema.get("flags", [])
        bit_flags = sorted([ f for f in flags if "bit" in f ], key=lambda f: f["bit"])

        class BitFieldAdapter(construct.Adapter):
            def __init__(self, subcon, flags):
                super().__init__(subcon)
                self.flags = flags
                self.bit_flags = bit_flags

            def _decode(self, obj, context, path):
                value = int.from_bytes(obj, "little") if isinstance(obj, bytes) else int(obj)

                result = {}
                for i, f in enumerate(self.bit_flags):
                    name = f["name"]
                    start = f["bit"]
                    end = self.bit_flags[i + 1]["bit"] if i + 1 < len(self.bit_flags) else size_bits
                    width = end - start

                    if width == 1:
                        result[name] = bool((value >> start) & 1)
                    else:
                        mask = (1 << width) - 1
                        result[name] = (value >> start) & mask
                    print(result)
                return result
            
            def _encode(self, obj, context, path):
                value = 0

                for i, f in enumerate(self.bit_flags):
                    name = f["name"]
                    if name not in obj:
                        continue

                    start = f["bit"]
                    end = self.bit_flags[i + 1]["bit"] if i + 1 < len(self.bit_flags) else size_bits
                    width = end - start
                    if width == 1:
                        if obj[name]:
                            value |= 1 << start
                    else:
                        mask = (1 << width) - 1
                        value |= (obj[name] & mask) << start
                return value
        return BitFieldAdapter(base_type, flags)

    # -------------- Public API -----------------
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        with open(file_path, "rb") as f:
            data = self.struct.parse_stream(f)
        return {"filename": file_path.name, "schema": self.schema.get("name"), "data": data}

    def to_serializable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Construct containers (and nested types) to JSON-serializable Python types."""

        def container_to_dict(container):
            # construct.Container (most common)
            if isinstance(container, construct.Container):
                return {k: container_to_dict(v) for k, v in container.items() if not k.startswith("_")}

            # plain dict (e.g. returned by BitFieldAdapter._decode)
            if isinstance(container, dict):
                return {k: container_to_dict(v) for k, v in container.items()}

            # lists/tuples
            if isinstance(container, (list, tuple)):
                return [container_to_dict(item) for item in container]

            # bytes -> hex string
            if isinstance(container, (bytes, bytearray)):
                return container.hex()

            # primitives
            if isinstance(container, (int, float, str, bool)) or container is None:
                return container

            # any other object (Path, BufferedReader, etc.) -> stringify as a last resort
            return str(container)

        return {
            "filename": data.get("filename"),
            "schema": data.get("schema"),
            "data": container_to_dict(data.get("data")),
        }

    def write_to_file(self, data: Dict[str, Any], out_path: Path, indent: int = 2):
        serializable = self.to_serializable(data)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=indent, ensure_ascii=False)

    @property
    def file_pattern(self) -> str:
        # support either "pattern" or "file_pattern" in schema
        return self.schema.get("pattern") or self.schema.get("file_pattern") or "*"

    @property
    def parser_name(self) -> str:
        return self.schema.get("name", "SchemaParser")

class ScaleAdapter(construct.Adapter):
    def __init__(self, subcon, scale: float):
        super().__init__(subcon)
        self.scale = scale

    def _decode(self, obj, context, path):
        return obj / self.scale

    def _encode(self, obj, context, path):
        return int(obj * self.scale)

class BoolBitAdapter(construct.Adapter):
    """
    Adapter to parse a single 1-bit C++ boolean stored in a byte.
    bit_position = 0 means the LSB.
    """
    def __init__(self, subcon, bit_position=0):
        super().__init__(subcon)
        self.bit_position = bit_position

    def _decode(self, obj, context, path):
        value = obj if isinstance(obj, int) else int.from_bytes(obj, "little")
        return bool((value >> self.bit_position) & 1)

    def _encode(self, obj, context, path):
        value = 1 if obj else 0
        return value << self.bit_position