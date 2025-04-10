STARBOARD_FILE = "starboards.json"

def load_starboards():
    if os.path.exists(STARBOARD_FILE):
        with open(STARBOARD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_starboards(data):
    with open(STARBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
STARBOARD_FILE = "starboards.json"

def load_starboards():
    if os.path.exists(STARBOARD_FILE):
        with open(STARBOARD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_starboards(data):
    with open(STARBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
