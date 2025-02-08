# file: custom/multiple_classes.py
from parser import NodeBase

class Alpha(NodeBase):
    """Alpha class with parameters."""
    label = "Alpha"
    description = "Alpha Node"
    category = "alpha"
    execution_type = "cycle"
    
    params = {
        "param1": {
            "label": "Parameter 1",
            "type": "string",
            "display": "input"
        }
    }
    
    def execute(self, param1: str) -> str:
        return param1[::-1]

class Beta(NodeBase):
    """Beta class without parameters."""
    label = "Beta"
    description = "Beta Node"
    category = "beta"
    execution_type = "single"
    
    def execute(self, value: int) -> int:
        return value * 3 