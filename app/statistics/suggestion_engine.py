from app.database import Database

class SuggestionEngine:
    def __init__(self, database: Database): self.database=database
    def match(self, remaining_rate):
        if remaining_rate is None: return []
        value=float(remaining_rate)
        return [r["suggestion"] for r in self.database.get_suggestion_rules() if r["enabled"] and r["metric"]=="remaining_rate" and r["min_value"] <= value < r["max_value"]]
