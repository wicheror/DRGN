import random
from models import clamp, create_egg
from content import COLORS, PATTERNS, EYES, HORNS, SIZES, TEMPERAMENTS
from game_logic import hidden_trait_effects, line_head_bonus

VISIBLE_GENE_KEYS = ["color", "pattern", "eyes", "horns", "size", "temperament"]

GENE_POOLS = {
    "color": COLORS,
    "pattern": PATTERNS,
    "eyes": EYES,
    "horns": HORNS,
    "size": SIZES,
    "temperament": TEMPERAMENTS,
}

def inherit_gene(a, b, key, mutation_chance):
    parental = [a["genotype"].get(key), b["genotype"].get(key)]
    parental = [v for v in parental if v is not None]

    if random.randint(1, 100) <= mutation_chance:
        pool = [v for v in GENE_POOLS.get(key, parental) if v not in parental]
        # Most mutations are still inherited-looking; some add a genuinely new visible trait.
        if pool and random.randint(1, 100) <= 65:
            return random.choice(pool)
        return random.choice(parental)

    # Slight bias toward visible mixing: if parents differ, keep that difference alive.
    return random.choice(parental)

def breed_dragons(parent_a, parent_b):
    # v13: young dragons cannot reproduce. Old dragons can, but with a penalty.
    if parent_a.get("stage") == "młodość" or parent_b.get("stage") == "młodość":
        return False, [], 0

    life_a = parent_a.get("life_score_cache", 50)
    life_b = parent_b.get("life_score_cache", 50)
    fertility_a = parent_a["genotype"].get("fertility", 50)
    fertility_b = parent_b["genotype"].get("fertility", 50)
    stress_penalty = int((parent_a["stress"] + parent_b["stress"]) / 4)

    base_chance = 30
    old_penalty = 0
    for p in [parent_a, parent_b]:
        if p.get("stage") == "starość":
            old_penalty += 10
    prep_bonus = parent_a.get("prep_level", 0) * 8 + parent_b.get("prep_level", 0) * 4
    # V6 status effects. A working dragon can still reproduce; it just may carry stress/energy consequences.
    status_bonus = 0
    for p in [parent_a, parent_b]:
        if p.get("status") == "Przygotowany do schadzki":
            status_bonus += 12
        elif p.get("status") == "Reproduktor / Matka linii":
            status_bonus += 8
        elif p.get("status") == "W dzikości":
            status_bonus -= 4
        elif p.get("status") == "Odpoczynek":
            status_bonus += 2
    effects = hidden_trait_effects(parent_a.get("hidden_traits", []) + parent_b.get("hidden_traits", []))
    chance = base_chance + int((fertility_a + fertility_b) / 8) + int((life_a + life_b) / 8) - stress_penalty
    chance += prep_bonus + status_bonus + effects["egg_chance"] - old_penalty
    chance = clamp(chance, 5, 95)

    success = random.randint(1, 100) <= chance
    eggs = []

    if success:
        eggs_count = 1
        if random.randint(1, 100) < int((fertility_a + fertility_b) / 5):
            eggs_count += 1
        if random.randint(1, 100) < int((life_a + life_b) / 8):
            eggs_count += 1

        for _ in range(min(eggs_count, 3)):
            avg_mutation = int((parent_a["genotype"]["mutation"] + parent_b["genotype"]["mutation"]) / 2)
            care_bonus = 0 if (life_a + life_b) / 2 > 60 else 5
            hidden_mutation_bonus = effects["mutation"]
            status_mutation_bonus = 0
            if parent_a.get("status") == "W dzikości" or parent_b.get("status") == "W dzikości":
                status_mutation_bonus += 6
            if parent_a.get("status") == "Reproduktor / Matka linii" or parent_b.get("status") == "Reproduktor / Matka linii":
                status_mutation_bonus -= 2  # stable line heads preserve traits better
            # v13: rare mutations should feel rare. Wildness still matters, but not every clutch explodes into novelty.
            mutation_chance = clamp(int(avg_mutation * 0.65) + care_bonus + hidden_mutation_bonus + status_mutation_bonus, 1, 38)

            genotype = {}
            for key in VISIBLE_GENE_KEYS:
                genotype[key] = inherit_gene(parent_a, parent_b, key, mutation_chance)

            genotype["immunity"] = clamp(int((parent_a["genotype"]["immunity"] + parent_b["genotype"]["immunity"]) / 2) + random.randint(-12, 12) - max(0, effects["risk"] // 5))
            genotype["fertility"] = clamp(int((parent_a["genotype"]["fertility"] + parent_b["genotype"]["fertility"]) / 2) + random.randint(-12, 12) + effects["fertility"])
            genotype["mutation"] = clamp(avg_mutation + random.randint(-6, 5) + effects["mutation"])
            line_head_bonus_rarity = 4 if (parent_a.get("status") == "Reproduktor / Matka linii" or parent_b.get("status") == "Reproduktor / Matka linii") else 0
            genotype["rarity"] = clamp(int((parent_a["genotype"]["rarity"] + parent_b["genotype"]["rarity"]) / 2) + random.randint(-15, 18) + effects["rarity"] + line_head_bonus_rarity)

            generation = max(parent_a.get("generation", 1), parent_b.get("generation", 1)) + 1
            eggs.append(create_egg([parent_a["id"], parent_b["id"]], genotype, generation))

    parent_a["prep_level"] = 0
    parent_b["prep_level"] = 0
    return success, eggs, chance

def generate_partner(kind="wild"):
    from models import create_dragon
    if kind == "wild":
        pet = create_dragon(owner_id="wild", generation=1, wildness=20, stage="dorosłość")
        pet["name"] = "Dziki " + pet["name"]
    else:
        pet = create_dragon(owner_id="npc", generation=random.randint(1, 4), wildness=5, stage="dorosłość")
        pet["name"] = "Hodowlany " + pet["name"]
        pet["health"] = random.randint(70, 95)
        pet["happiness"] = random.randint(60, 90)
        pet["stress"] = random.randint(5, 30)
    return pet


# ---------- v14 genetics upgrade overrides ----------

def _parent_alleles(parent, key):
    visible = parent.get("genotype", {}).get(key)
    carrier = parent.get("carrier_genes", {}).get(key, visible)
    return [visible, carrier]

def _inherit_visible_and_carrier(parent_a, parent_b, key, mutation_chance):
    a1 = random.choice(_parent_alleles(parent_a, key))
    b1 = random.choice(_parent_alleles(parent_b, key))
    alleles = [a1, b1]
    parental_visible = [parent_a.get("genotype", {}).get(key), parent_b.get("genotype", {}).get(key)]

    if random.randint(1, 100) <= mutation_chance:
        pool = [v for v in GENE_POOLS.get(key, alleles) if v not in alleles]
        if pool:
            if random.randint(1, 100) <= 45:
                alleles[random.randint(0, 1)] = random.choice(pool)

    counts = {}
    for a in alleles + parental_visible:
        counts[a] = counts.get(a, 0) + 1

    # More likely to express a trait that appears multiple times across parents/carriers.
    weighted = []
    for val, count in counts.items():
        weighted.extend([val] * max(1, count))
    expressed = random.choice(weighted)
    carried_candidates = [x for x in alleles if x != expressed]
    carried = random.choice(carried_candidates) if carried_candidates else expressed
    return expressed, carried

def breed_dragons(parent_a, parent_b):
    if parent_a.get("stage") == "młodość" or parent_b.get("stage") == "młodość":
        return False, [], 0

    life_a = parent_a.get("life_score_cache", 50)
    life_b = parent_b.get("life_score_cache", 50)
    fert_a = parent_a["genotype"]["fertility"]
    fert_b = parent_b["genotype"]["fertility"]
    effects = hidden_trait_effects(parent_a.get("hidden_traits", []) + parent_b.get("hidden_traits", []))

    base_chance = 30
    old_penalty = 0
    for p in [parent_a, parent_b]:
        if p.get("stage") == "starość":
            old_penalty += 10
    prep_bonus = parent_a.get("prep_level", 0) * 8 + parent_b.get("prep_level", 0) * 4
    status_bonus = 6 if parent_a.get("status") == "Przygotowany do schadzki" else 0

    chance = base_chance + int((fert_a + fert_b) / 8) + int((life_a + life_b) / 8) - int((parent_a["stress"] + parent_b["stress"]) / 4)
    chance += prep_bonus + status_bonus + effects["egg_chance"] - old_penalty
    chance = clamp(chance, 5, 95)
    success = random.randint(1, 100) <= chance

    eggs = []
    if success:
        eggs_count = 1
        if random.randint(1, 100) < int((fert_a + fert_b) / 5):
            eggs_count += 1
        if random.randint(1, 100) < int((life_a + life_b) / 8):
            eggs_count += 1
        eggs_count = min(eggs_count, 3)

        for _ in range(eggs_count):
            avg_mutation = int((parent_a["genotype"]["mutation"] + parent_b["genotype"]["mutation"]) / 2)
            care_bonus = 0 if (life_a + life_b) / 2 > 60 else 5
            hidden_mutation_bonus = effects["mutation"]
            status_mutation_bonus = 0
            if parent_a.get("status") == "W dzikości" or parent_b.get("status") == "W dzikości":
                status_mutation_bonus += 6
            if parent_a.get("status") == "Reproduktor / Matka linii" or parent_b.get("status") == "Reproduktor / Matka linii":
                status_mutation_bonus -= 2
            mutation_chance = clamp(int(avg_mutation * 0.65) + care_bonus + hidden_mutation_bonus + status_mutation_bonus, 1, 38)

            genotype = {}
            carriers = {}
            for key in VISIBLE_GENE_KEYS:
                expressed, carried = _inherit_visible_and_carrier(parent_a, parent_b, key, mutation_chance)
                genotype[key] = expressed
                carriers[key] = carried

            genotype["immunity"] = clamp(int((parent_a["genotype"]["immunity"] + parent_b["genotype"]["immunity"]) / 2) + random.randint(-12, 12) - max(0, effects["risk"] // 5))
            genotype["fertility"] = clamp(int((parent_a["genotype"]["fertility"] + parent_b["genotype"]["fertility"]) / 2) + random.randint(-12, 12) + effects["fertility"])
            genotype["mutation"] = clamp(avg_mutation + random.randint(-6, 5) + effects["mutation"])
            line_head_bonus_rarity = 4 if (parent_a.get("status") == "Reproduktor / Matka linii" or parent_b.get("status") == "Reproduktor / Matka linii") else 0
            genotype["rarity"] = clamp(int((parent_a["genotype"]["rarity"] + parent_b["genotype"]["rarity"]) / 2) + random.randint(-15, 18) + effects["rarity"] + line_head_bonus_rarity)

            generation = max(parent_a.get("generation", 1), parent_b.get("generation", 1)) + 1
            eggs.append(create_egg([parent_a["id"], parent_b["id"]], genotype, generation, carrier_genes=carriers))

    parent_a["prep_level"] = 0
    parent_b["prep_level"] = 0
    return success, eggs, chance
