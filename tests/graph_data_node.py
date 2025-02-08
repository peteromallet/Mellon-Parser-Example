# file: custom/graph_data_node.py
class GraphData:
    """Prepare data for graph plotting."""
    label = "GraphData"
    description = "Graph Data Node"
    category = "data"
    execution_type = "config"
    
    # Using AnnAssign with type annotations for the params attribute
    params: dict = {
        "data_points": {
            "label": "Data Points",
            "type": "list",
            "display": "table"
        },
        "graph_type": {
            "label": "Graph Type",
            "type": "string",
            "display": "dropdown",
            "options": ["bar", "line", "pie"]
        }
    }
    
    def execute(self, data_points: list, graph_type: str) -> dict:
        # Process each point with error handling
        processed = {"type": graph_type, "points": []}
        for point in data_points:
            try:
                processed["points"].append(float(point))
            except (ValueError, TypeError):
                processed["points"].append(0.0)
        return processed
    
    def extra_method(self):
        # Additional method that does not involve params
        return "Extra info about the graph" 