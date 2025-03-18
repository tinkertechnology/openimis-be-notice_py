import json
import uuid
from datetime import datetime, timedelta
import random

# Sample data
titles = [
    "Maintenance Alert", "Staff Meeting", "Equipment Update", "Policy Change",
    "Emergency Drill", "Health Camp", "Training Session", "System Downtime",
    "New Procedure", "Compliance Notice"
]
descriptions = [
    "Scheduled maintenance on all systems.",
    "Mandatory meeting for all staff members.",
    "Update on new equipment installation.",
    "Changes to existing health policies.",
    "Emergency preparedness drill scheduled.",
    "Community health camp announcement.",
    "Training for new staff on procedures.",
    "System will be down for upgrades.",
    "Introduction of a new medical procedure.",
    "Reminder to comply with regulations."
]
priorities = ["LOW", "MEDIUM", "HIGH"]

# Generate 50 notices
notices = []
for i in range(1, 51):
    created_at = datetime.now() - timedelta(days=random.randint(0, 90))
    schedule_publish = random.random() < 0.2
    notice = {
        "model": "notice.Notice",
        "pk": i,
        "fields": {
            "uuid": str(uuid.uuid4()),
            "title": f"{random.choice(titles)} {i}",
            "description": f"{random.choice(descriptions)} (Notice #{i})",
            "priority": random.choice(priorities),
            "health_facility": random.randint(1, 10) if random.random() > 0.3 else None,
            "created_at": created_at.isoformat(),
            "updated_at": (created_at + timedelta(days=random.randint(1, 10))).isoformat(),
            "schedule_publish": schedule_publish,
            "publish_start_date": (
                (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat()
                if schedule_publish else None
            ),
            "validity_from": created_at.isoformat(),
            "validity_to": (
                (created_at + timedelta(days=random.randint(30, 365))).isoformat()
                if random.random() > 0.1 else None
            ),
            "is_active": random.random() > 0.2,
        }
    }
    notices.append(notice)

# Save to JSON file
with open("notice_fixtures.json", "w") as f:
    json.dump(notices, f, indent=2)

print("Fixtures generated and saved to 'notice_fixtures.json'")