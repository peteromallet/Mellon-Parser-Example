class Utility:
    """Utility functions for miscellaneous tasks."""
    label = "Utility"
    description = "General Utility Node"
    category = "utility"
    execution_type = "on-demand"
    
    def helper_one(self, x: int) -> int:
        return x * 2

    def helper_two(self, y: int) -> int:
        return y + 10

    def execute(self, value: int) -> int:
        # Sample execution combining helper methods
        result = self.helper_one(value)
        result = self.helper_two(result)
        return result 