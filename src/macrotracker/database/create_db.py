from pathlib import Path


class Database:

    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.database_path.mkdir(parents=True, exist_ok=True)