from pathlib import Path

mqtt_file: Path = Path.cwd() / "src" / "mqtt.js"
credentials_file: Path = Path.cwd() / "credentials.json"
ai_instructions_file: Path = Path.cwd() / "ai_instructions.txt"
database_file = Path.cwd() / "targets.db"