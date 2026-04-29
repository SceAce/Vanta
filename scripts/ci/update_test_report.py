#!/usr/bin/env python3
"""Update state/test-report.json: set updated_at=now UTC, status=passed.

Leaves all other fields untouched.
Only called by CI after all verify steps succeed.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

path = Path("state/test-report.json")
data = json.loads(path.read_text())
data["updated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
data["status"] = "passed"
path.write_text(json.dumps(data, indent=2) + "\n")
print(f"state/test-report.json updated: status=passed, updated_at={data['updated_at']}")
