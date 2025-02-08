# Mellon Parser Example

## Overview

This is meant as an example of how to use AST to parse the new Python node structure that would show the classes and the params in a logical format with a clear data flow:

```python
class Text2(NodeBase):
    """Text node that passes through input text"""
    label = "Text2"
    description = "Text"
    category = "text"
    execution_type = "button"
    
    # Define inputs and outputs directly
    params = {
        "text": {
            "label": "Text",
            "type": "string",
            "display": "output"
        },
        "text_field": {
            "label": "Text Field", 
            "type": "string",
            "display": "textarea"
        }
    }
    
    def execute(self, text_field: str) -> str:
        return text_field
```
## How It Works

1. The parser uses the `ast` module to read and parse each Python file without executing the code.
2. It extracts class attributes such as `label`, `description`, `category`, `execution_type` and a special attribute `params` that defines the node's configurable fields.
3. Return a JSON string containing the parsed data - that could be read into Mellon.
4. Print a formatted output to the console with filename headers, class names, and parameter details for demo purposes.

## Data Format

The parser saves and returns the parsed data in JSON format. The JSON structure contains:

- **`scanned_folders`**: A list of the directories that were scanned.
- **`files`**: A list of file paths for all Python files found.
- **`classes`**: A list of dictionaries, each representing a class extracted from the files. Each dictionary includes details such as the class's name, attributes, methods, and decorators.
- **`errors`**: A list of any errors encountered during parsing (if any).

## Running the Parser

Open your terminal in the root directory of the project and run:
```bash
python parser.py
```

This will test on a bunch of different edge cases in the tests/ folder and print the results.