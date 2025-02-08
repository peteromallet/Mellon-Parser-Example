# file: custom/without_nodebase.py

class RegularProcessor:
    """A regular class that processes data but doesn't inherit from NodeBase.
    This class won't be picked up by the parser since it's not a node."""
    label = "RegularProcessor"
    description = "Regular data processor"
    category = "processing"
    execution_type = "manual"
    
    # Similar params structure but not a node
    params = {
        "input_text": {
            "label": "Input Text",
            "type": "string",
            "display": "textarea"
        },
        "processing_level": {
            "label": "Processing Level",
            "type": "number",
            "display": "slider",
            "min": 1,
            "max": 10
        }
    }
    
    def execute(self, input_text: str, processing_level: int) -> str:
        """Process the input text based on the processing level."""
        if processing_level < 1:
            return input_text
            
        operations = {
            1: str.strip,
            2: str.lower,
            3: str.upper,
            4: str.title,
            5: lambda x: x.replace(' ', '_'),
            6: lambda x: x.replace('_', ' '),
            7: lambda x: ''.join(reversed(x)),
            8: lambda x: x.replace('a', '@'),
            9: lambda x: x.replace('e', '3'),
            10: lambda x: x.replace('i', '1')
        }
        
        result = input_text
        for level in range(1, min(processing_level + 1, 11)):
            if level in operations:
                result = operations[level](result)
        
        return result
    
    def get_supported_levels(self) -> list:
        """Return list of supported processing levels."""
        return list(range(1, 11)) 