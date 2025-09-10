# gta_node_parser/visualizer.py
from PIL import Image, ImageDraw
from pathlib import Path
from typing import Dict, Any, Union, List
from ..parsers.factory import ParserFactory

class NodeVisualizer:
    """Visualizer for GTA:SA node data."""
    
    def __init__(self, width: int = 7000, height: int = 7000):
        self.width = width
        self.height = height
        self.offset_x = width // 2
        self.offset_y = height // 2
        self.scale = min(width, height) / 6000  # GTA:SA map is approx 6000x6000 units
    
    def _game_to_image_coords(self, x: float, y: float) -> tuple:
        """Convert game coordinates to image coordinates."""
        img_x = int(self.offset_x + x * self.scale)
        img_y = int(self.offset_y - y * self.scale)  # Invert y-axis
        return img_x, img_y
    
    def draw_data(self, data: Dict[str, Any], output_path: Union[str, Path]) -> None:
        """Draw nodes based on the parsed data type."""
        parser = ParserFactory.get_parser(Path(data["filename"]))
        
        if parser.parser_name == "NodeParser":
            self.draw_nodes(data, output_path)
        elif parser.parser_name == "TrainParser":
            self.draw_trains(data, output_path)
    
    def draw_nodes(self, nodes_data: Dict[str, Any], output_path: Union[str, Path]) -> None:
        """Draw all nodes from parsed NODES*.DAT data."""
        image = Image.new('RGB', (self.width, self.height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Access data through the new structure
        data = nodes_data.get("data", {})
        
        # Draw vehicle nodes (black)
        vehicle_nodes = data.get("vehicle_nodes", [])
        for node in vehicle_nodes:
            x, y = self._game_to_image_coords(node["x"], node["y"])
            draw.ellipse([x-2, y-2, x+2, y+2], fill='black')
        
        # Draw pedestrian nodes (blue)
        ped_nodes = data.get("ped_nodes", [])
        for node in ped_nodes:
            x, y = self._game_to_image_coords(node["x"], node["y"])
            draw.ellipse([x-2, y-2, x+2, y+2], fill='blue')
        
        # Draw navigation nodes (green)
        navi_nodes = data.get("navi_nodes", [])
        for node in navi_nodes:
            x, y = self._game_to_image_coords(node["x"], node["y"])
            draw.ellipse([x-2, y-2, x+2, y+2], fill='green')
        
        image.save(output_path)
    
    def draw_single_node(self, node: Dict[str, Any], node_type: str, output_path: Union[str, Path]) -> None:
        """Draw a single node on a map background."""
        image = Image.new('RGB', (self.width, self.height), 'white')
        draw = ImageDraw.Draw(image)
        
        x, y = self._game_to_image_coords(node["x"], node["y"])
        
        # Determine color based on node type
        if node_type == "pedestrian":
            color = 'blue'
        elif node_type == "train":
            color = 'red'
        elif node_type == "navigation":
            color = 'green'
        else:  # vehicle
            color = 'black'
        
        # Draw the node
        draw.ellipse([x-5, y-5, x+5, y+5], fill=color)
        
        image.save(output_path)
    
    def draw_trains(self, train_data: Dict[str, Any], output_path: Union[str, Path]) -> None:
        """Draw train nodes."""
        image = Image.new('RGB', (self.width, self.height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Access data through the new structure
        nodes = train_data.get("data", [])
        
        for node in nodes:
            x, y = self._game_to_image_coords(node["x"], node["y"])
            draw.ellipse([x-3, y-3, x+3, y+3], fill='red')
        
        image.save(output_path)
    
    def _is_pedestrian_node(self, node: Dict[str, Any]) -> bool:
        """Check if a node is for pedestrians based on flags."""
        flags = node.get("flags", {})
        if isinstance(flags, dict):
            return flags.get("is_pedestrian", False)
        else:
            # Fallback for integer flags
            return (flags & 0x1) != 0
    
    def _is_vehicle_node(self, node: Dict[str, Any]) -> bool:
        """Check if a node is for vehicles based on flags."""
        flags = node.get("flags", {})
        if isinstance(flags, dict):
            return flags.get("is_vehicle", False)
        else:
            # Fallback for integer flags
            return (flags & 0x2) != 0
    
    def _is_navi_node(self, node: Dict[str, Any]) -> bool:
        """Check if a node is for navigation based on flags."""
        flags = node.get("flags", {})
        if isinstance(flags, dict):
            return flags.get("is_navi", False)
        else:
            # Fallback for integer flags
            return (flags & 0x4) != 0