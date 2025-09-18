import os, json

PARTICIPANT_FILE = os.path.join("data", "participants.json")

def load_next_participant_id():
    # participants.json structure: {"last_id": int}
    if not os.path.exists(PARTICIPANT_FILE):
        return 1  # start at 1
    try:
        with open(PARTICIPANT_FILE, "r", encoding="utf-8") as f:
            obj = json.load(f)
        return int(obj.get("last_id", 0)) + 1
    except Exception:
        return 1

def save_participant_id(pid:int):
    os.makedirs(os.path.dirname(PARTICIPANT_FILE), exist_ok=True)
    with open(PARTICIPANT_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_id": int(pid)}, f)
