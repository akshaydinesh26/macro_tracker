from pathlib import Path


class Database:

    def __init__(self, database_path: Path, indicators: dict):
        self.database_path = database_path
        self.indicators = indicators.get("indicator",[])
        # create the database
        self.database_path.mkdir(parents=True, exist_ok=True)
        self.create_database()

    def create_database(self):
        for indicator in self.indicators:
            indicator_db = self.database_path / f"{indicator['fred_code']}.db"
            if not indicator_db.exists():
                indicator_db.touch()