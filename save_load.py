import json
import os
from models import create_dragon

SAVE_PATH = "save.json"

def new_state():
    first = create_dragon()
    first["history"].append("Trafił do hodowli jako pierwszy smok. Jeszcze nie wie, czy to awans, czy problem.")
    return {
        "day": 1,
        "coins": 150,
        "pets": [first],
        "eggs": [],
        "last_report": [
            "🐉 Zacznij od pierwszego smoka: nadaj mu imię, obejrzyj cechy, wybierz pracę albo poszukaj partnera do linii."
        ],
        "feed": [
            "🐉 Zacznij od pierwszego smoka: nadaj mu imię, obejrzyj cechy, wybierz pracę albo poszukaj partnera do linii."
        ],
        "starter_name_pending": True,
        "onboarding_seen": False,
        "telemetry": {},
        "inline_notice": "",
        "debug": False,
    }

def load_state():
    if not os.path.exists(SAVE_PATH):
        return new_state()
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return new_state()

def save_state(state):
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def reset_state():
    state = new_state()
    save_state(state)
    return state
