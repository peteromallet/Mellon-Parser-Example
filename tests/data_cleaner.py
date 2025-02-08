# file: custom/data_cleaner.py
class DataCleaner:
    """Clean input data for further processing."""
    label = "DataCleaner"
    description = "Data Cleaning Node"
    category = "data"
    execution_type = "manual"
    
    params = {
        "input_data": {
            "label": "Input Data",
            "type": "string",
            "display": "textarea"
        },
        "remove_duplicates": {
            "label": "Remove Duplicates",
            "type": "boolean",
            "display": "toggle"
        },
        "config": {
            "label": "Cleaning Config",
            "type": "dict",
            "display": "json",
            "settings": {"trim_spaces": True, "to_lowercase": True}
        }
    }
    
    def clean(self, input_data: str, remove_duplicates: bool, config: dict) -> str:
        # Simulated cleaning logic
        cleaned = input_data.strip()
        if config.get("to_lowercase", False):
            cleaned = cleaned.lower()
        if config.get("trim_spaces", False):
            cleaned = " ".join(cleaned.split())
        if remove_duplicates:
            tokens = cleaned.split()
            seen = set()
            cleaned = " ".join([x for x in tokens if x not in seen and not seen.add(x)])
        return cleaned 