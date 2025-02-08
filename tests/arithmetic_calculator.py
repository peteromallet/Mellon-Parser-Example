# file: custom/arithmetic_calculator.py
class Calculator:
    """Calculator node for arithmetic operations"""
    label = "Calc"
    description = "Arithmetic calculator"
    category = "math"
    execution_type = "auto"
    
    # Define parameters for arithmetic operations
    params = {
        "a": {
            "label": "Operand A",
            "type": "number",
            "display": "input"
        },
        "b": {
            "label": "Operand B",
            "type": "number",
            "display": "input"
        },
        "op": {
            "label": "Operation",
            "type": "string",
            "display": "dropdown",
            "options": ["add", "subtract", "multiply", "divide"]
        }
    }
    
    def execute(self, a: float, b: float, op: str) -> float:
        if op == "add":
            result = a + b
        elif op == "subtract":
            result = a - b
        elif op == "multiply":
            result = a * b
        elif op == "divide":
            result = a / b if b != 0 else None
        else:
            result = None
        return result
    
    def helper_method(self):
        # This method is for internal use and is not related to the params.
        print("Helper method executed") 