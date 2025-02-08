# file: custom/text_transformer.py
from parser import NodeBase

class TextTransformer(NodeBase):
    """Transform text in various ways"""
    label = "TextTransformer"
    description = "Transforms text with different operations"
    category = "text"
    execution_type = "event"
    
    # No parameters defined intentionally to simulate a class without params
    def execute(self, text: str, operation: str = "upper") -> str:
        if operation == "upper":
            return text.upper()
        elif operation == "lower":
            return text.lower()
        elif operation == "title":
            return text.title()
        else:
            return text
    
    def reverse(self, text: str) -> str:
        return text[::-1] 