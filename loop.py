import json
import time
from pathlib import Path
from build_db import build_db

with open(Path(__file__).parent / "config.json") as f:
    config = json.load(f)

loop_delay = config.get("loop-delay", 15)  # Default to 15 minutes

while True:
    build_db()
    time.sleep(loop_delay * 60)  # Convert to seconds
