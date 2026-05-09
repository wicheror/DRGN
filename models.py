import random
import uuid
from datetime import datetime
from content import COLORS, PATTERNS, EYES, HORNS, SIZES, TEMPERAMENTS, random_name

STAGES = ["jajo", "młodość", "dorosłość", "starość"]

def clamp(value, min_value=0, max_value=100):
    return max(min_value, min(max_value, int(value)))

def roll_gene(options):
    return random.choice(options)

def new_genotype(wildness=0):
    return {
        "color": roll_gene(COLORS),
        "pattern": roll_gene(PATTERNS),
        "eyes": roll_gene(EYES),
        "horns": roll_gene(HORNS),
        "size": roll_gene(SIZES),
        "temperament": roll_gene(TEMPERAMENTS),
        "immunity": random.randint(20, 90),
        "fertility": random.randint(20, 90),
        "mutation": clamp(random.randint(1, 15) + wildness),
        "rarity": clamp(random.randint(1, 100) + wildness),
    }

def phenotype_from_genotype(genotype, life_score=50):
    # MVP: prawie bezpośrednio. Później można tu ukryć ekspresję genów.
    return {
        "color": genotype["color"],
        "pattern": genotype["pattern"],
        "eyes": genotype["eyes"],
        "horns": genotype["horns"],
        "size": genotype["size"],
    }


POSITIVE_HIDDEN_TRAITS = [
    "silna linia",
    "ukryty gen srebrnych oczu",
    "wysoka płodność recesywna",
    "stabilny temperament",
    "dziki potencjał",
    "długowieczność",
]

NEGATIVE_HIDDEN_TRAITS = [
    "krucha odporność",
    "niska płodność ukryta",
    "niestabilna mutacja",
    "trudny temperament",
    "ryzyko słabych jaj",
]

MIXED_HIDDEN_TRAITS = [
    "dzika krew",
    "stara linia",
    "kapryśna ekspresja genów",
]

def roll_hidden_traits(wildness=0):
    """Hidden traits are the early MVP version of deeper genetics."""
    traits = []
    chance = 35 + int(wildness / 2)
    if random.randint(1, 100) <= chance:
        traits.append(random.choice(POSITIVE_HIDDEN_TRAITS))
    if random.randint(1, 100) <= 20 + int(wildness / 3):
        traits.append(random.choice(NEGATIVE_HIDDEN_TRAITS))
    if random.randint(1, 100) <= 18 + int(wildness / 4):
        traits.append(random.choice(MIXED_HIDDEN_TRAITS))
    # remove duplicates, cap to 3
    out = []
    for t in traits:
        if t not in out:
            out.append(t)
    return out[:3]


def create_dragon(name=None, owner_id="player", generation=1, parents=None, wildness=0, stage="młodość"):
    genotype = new_genotype(wildness=wildness)
    pet = {
        "id": str(uuid.uuid4()),
        "owner_id": owner_id,
        "name": name or random_name(),
        "species": "dragon",
        "generation": generation,
        "stage": stage,
        "age_days": 0,
        "health": random.randint(65, 90),
        "happiness": random.randint(45, 80),
        "energy": random.randint(45, 85),
        "stress": random.randint(10, 45),
        "bond": random.randint(5, 25),
        "is_bound_forever": False,
        "has_departed": False,
        "genotype": genotype,
        "phenotype": phenotype_from_genotype(genotype),
        "temperament": genotype["temperament"],
        "parents": parents or [],
        "children": [],
        "history": [],
        "prep_level": 0,
        "knowledge_level": 0,
        "revealed_hidden_traits": [],
        "hidden_traits": roll_hidden_traits(wildness=wildness),
        "base_market_value": None,
        "market_appraisal_price": None,
        "market_appraisal_day": None,
        "breeding_report": None,
        "genetic_report": None,
        "status": "W hodowli",
        "work_type": None,
        "line_head": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    return pet

def egg_promise_from_genotype(genotype):
    rarity = genotype.get("rarity", 40)
    mutation = genotype.get("mutation", 5)
    fertility = genotype.get("fertility", 40)
    score = int(rarity * 0.45 + mutation * 0.75 + fertility * 0.15)
    if score >= 78:
        return "wyjątkowe", "jajo długo milczy, ale czasem między pęknięciami widać światło"
    if score >= 58:
        return "obiecujące", "jajo jest cięższe niż powinno i przyjemnie ciepłe"
    if mutation >= 28:
        return "dziwne", "jajo ma nieregularne ciepło i trudno powiedzieć, czy to dobry znak"
    return "zwykłe", "jajo rozwija się spokojnie"

def hatch_time_from_genotype(genotype):
    rarity = genotype.get("rarity", 40)
    mutation = genotype.get("mutation", 5)
    # Longer hatch time is a soft omen of unusual potential.
    hatch = 2
    if rarity >= 60 or mutation >= 20:
        hatch += 1
    if rarity >= 82 or mutation >= 32:
        hatch += 1
    if rarity >= 94 and mutation >= 25:
        hatch += 1
    return clamp(hatch, 2, 6)

def create_egg(parent_ids, genotype, generation, hatch_in=None, name=None):
    promise, omen = egg_promise_from_genotype(genotype)
    if hatch_in is None:
        hatch_in = hatch_time_from_genotype(genotype)
    return {
        "id": str(uuid.uuid4()),
        "name": name or "",
        "parent_ids": parent_ids,
        "genotype": genotype,
        "generation": generation,
        "hatch_in": hatch_in,
        "initial_hatch_in": hatch_in,
        "promise": promise,
        "omen": omen,
        "origin_story": "Jajo złożone w hodowli.",
        "created_at": datetime.utcnow().isoformat(),
    }

def egg_to_dragon(egg, name=None):
    genotype = egg["genotype"]
    pet_name = name or egg.get("name") or random_name()
    pet = {
        "id": str(uuid.uuid4()),
        "owner_id": "player",
        "name": pet_name,
        "species": "dragon",
        "generation": egg["generation"],
        "stage": "młodość",
        "age_days": 0,
        "health": random.randint(60, 90),
        "happiness": random.randint(40, 75),
        "energy": random.randint(50, 90),
        "stress": random.randint(15, 50),
        "bond": 5,
        "is_bound_forever": False,
        "has_departed": False,
        "genotype": genotype,
        "phenotype": phenotype_from_genotype(genotype),
        "temperament": genotype["temperament"],
        "parents": egg["parent_ids"],
        "children": [],
        "history": [egg.get("origin_story") or "Wykluł się z jajka.", f"Wykluł się z jaja: {egg.get('promise', 'zwykłe')}."],
        "prep_level": 0,
        "knowledge_level": 0,
        "revealed_hidden_traits": [],
        "hidden_traits": roll_hidden_traits(wildness=max(0, genotype.get("mutation", 0) - 5)),
        "base_market_value": None,
        "market_appraisal_price": None,
        "market_appraisal_day": None,
        "breeding_report": None,
        "genetic_report": None,
        "status": "W hodowli",
        "work_type": None,
        "line_head": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    return pet

def life_score(pet):
    return clamp(
        pet["health"] * 0.35
        + pet["happiness"] * 0.30
        + pet["energy"] * 0.15
        + (100 - pet["stress"]) * 0.20
    )

def get_stage(age_days):
    # v13: smoki żyją dłużej, żeby gracz mógł planować linię i sukcesję.
    if age_days < 6:
        return "młodość"
    if age_days < 32:
        return "dorosłość"
    return "starość"


# ---------- v14 genetics upgrade overrides ----------

VISIBLE_TRAIT_KEYS = ["color", "pattern", "eyes", "horns", "size", "temperament"]

def default_carrier_genes(genotype):
    pools = {
        "color": COLORS,
        "pattern": PATTERNS,
        "eyes": EYES,
        "horns": HORNS,
        "size": SIZES,
        "temperament": TEMPERAMENTS,
    }
    carriers = {}
    for key in VISIBLE_TRAIT_KEYS:
        expressed = genotype.get(key)
        options = [x for x in pools[key] if x != expressed]
        if options and random.randint(1, 100) <= 70:
            carriers[key] = random.choice(options)
        else:
            carriers[key] = expressed
    return carriers

def create_dragon(name=None, owner_id="player", generation=1, parents=None, wildness=0, stage="młodość"):
    genotype = new_genotype(wildness=wildness)
    pet = {
        "id": str(uuid.uuid4()),
        "owner_id": owner_id,
        "name": name or random_name(),
        "species": "dragon",
        "generation": generation,
        "stage": stage,
        "age_days": 0,
        "health": random.randint(65, 90),
        "happiness": random.randint(45, 80),
        "energy": random.randint(45, 85),
        "stress": random.randint(10, 45),
        "bond": random.randint(5, 25),
        "parents": parents or [],
        "children": [],
        "is_bound_forever": False,
        "genotype": genotype,
        "carrier_genes": default_carrier_genes(genotype),
        "phenotype": phenotype_from_genotype(genotype),
        "temperament": genotype["temperament"],
        "history": ["Pojawił się w świecie smoków."],
        "prep_level": 0,
        "knowledge_level": 0,
        "revealed_hidden_traits": [],
        "hidden_traits": roll_hidden_traits(wildness=wildness),
        "base_market_value": None,
        "market_appraisal_price": None,
        "market_appraisal_day": None,
        "breeding_report": None,
        "genetic_report": None,
        "status": "W hodowli",
        "work_type": None,
        "line_head": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    return pet

def create_egg(parent_ids, genotype, generation, hatch_in=None, name=None, carrier_genes=None):
    promise, omen = egg_promise_from_genotype(genotype)
    if hatch_in is None:
        hatch_in = hatch_time_from_genotype(genotype)
    return {
        "id": str(uuid.uuid4()),
        "name": name or "",
        "parent_ids": parent_ids,
        "genotype": genotype,
        "carrier_genes": carrier_genes or default_carrier_genes(genotype),
        "generation": generation,
        "hatch_in": hatch_in,
        "initial_hatch_in": hatch_in,
        "promise": promise,
        "omen": omen,
        "origin_story": "Jajo złożone w hodowli.",
        "created_at": datetime.utcnow().isoformat(),
    }

def egg_to_dragon(egg, name=None):
    genotype = egg["genotype"]
    pet_name = name or egg.get("name") or random_name()
    pet = {
        "id": str(uuid.uuid4()),
        "owner_id": "player",
        "name": pet_name,
        "species": "dragon",
        "generation": egg["generation"],
        "stage": "młodość",
        "age_days": 0,
        "health": random.randint(68, 92),
        "happiness": random.randint(55, 82),
        "energy": random.randint(52, 88),
        "stress": random.randint(6, 25),
        "bond": random.randint(8, 22),
        "parents": egg["parent_ids"],
        "children": [],
        "is_bound_forever": False,
        "genotype": genotype,
        "carrier_genes": egg.get("carrier_genes") or default_carrier_genes(genotype),
        "phenotype": phenotype_from_genotype(genotype),
        "temperament": genotype["temperament"],
        "history": [egg.get("origin_story") or "Wykluł się z jajka.", f"Wykluł się z jaja: {egg.get('promise', 'zwykłe')}."],
        "prep_level": 0,
        "knowledge_level": 0,
        "revealed_hidden_traits": [],
        "hidden_traits": [],
        "base_market_value": None,
        "market_appraisal_price": None,
        "market_appraisal_day": None,
        "breeding_report": None,
        "genetic_report": None,
        "status": "W hodowli",
        "work_type": None,
        "line_head": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    return pet
