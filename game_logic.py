import random
from models import clamp, life_score, get_stage
from content import need_report, adventure_result_text

def dominant_need(pet):
    if pet["health"] < 45:
        return "care"
    if pet["energy"] < 35:
        return "rest"
    if pet["stress"] > 65:
        return "calm"
    if pet["happiness"] < 45:
        return "play"
    if pet["health"] < 65 and pet["happiness"] < 60:
        return "hungry"
    return "well"

def apply_action(pet, action):
    msg = ""
    if action == "feed":
        pet["health"] = clamp(pet["health"] + 4)
        pet["happiness"] = clamp(pet["happiness"] + 2)
        pet["energy"] = clamp(pet["energy"] + 3)
        pet["stress"] = clamp(pet["stress"] - 1)
        pet["bond"] = clamp(pet["bond"] + 1)
        msg = f"{pet['name']} przyjmuje jedzenie z miną kogoś, kto nie zamierza okazać wdzięczności."
    elif action == "play":
        pet["happiness"] = clamp(pet["happiness"] + 8)
        pet["energy"] = clamp(pet["energy"] - 5)
        pet["stress"] = clamp(pet["stress"] - 4)
        pet["bond"] = clamp(pet["bond"] + 2)
        msg = f"{pet['name']} daje się wciągnąć w zabawę. Udaje, że to był jego pomysł."
    elif action == "rest":
        pet["energy"] = clamp(pet["energy"] + 12)
        pet["stress"] = clamp(pet["stress"] - 6)
        pet["happiness"] = clamp(pet["happiness"] + 1)
        msg = f"{pet['name']} odpoczywa. Przez chwilę hodowla wydaje się bezpiecznie cicha."
    elif action == "train":
        pet["energy"] = clamp(pet["energy"] - 10)
        pet["stress"] = clamp(pet["stress"] + 5)
        pet["happiness"] = clamp(pet["happiness"] + random.randint(-2, 5))
        pet["bond"] = clamp(pet["bond"] + 2)
        msg = f"{pet['name']} trenuje niechętnie, ale z wyraźnym poczuciem własnej wielkości."
    elif action == "calm":
        pet["stress"] = clamp(pet["stress"] - 12)
        pet["happiness"] = clamp(pet["happiness"] + 2)
        pet["bond"] = clamp(pet["bond"] + 1)
        msg = f"{pet['name']} nie od razu się uspokaja, ale przestaje patrzeć na świat jak na osobistą zniewagę."
    elif action == "adventure":
        msg = send_on_adventure(pet)
    else:
        msg = "Nic się nie stało."
    pet.setdefault("history", []).append(msg)
    return msg

def send_on_adventure(pet):
    pet["energy"] = clamp(pet["energy"] - random.randint(10, 22))
    pet["stress"] = clamp(pet["stress"] + random.randint(3, 15))
    roll = random.randint(1, 100)

    if roll <= 45:
        pet["happiness"] = clamp(pet["happiness"] + random.randint(3, 10))
        outcome = "good"
    elif roll <= 65:
        pet["genotype"]["mutation"] = clamp(pet["genotype"]["mutation"] + random.randint(1, 4))
        pet["genotype"]["rarity"] = clamp(pet["genotype"]["rarity"] + random.randint(1, 6))
        outcome = "mutation"
    elif roll <= 85:
        pet["stress"] = clamp(pet["stress"] + random.randint(5, 15))
        outcome = "stress"
    else:
        pet["health"] = clamp(pet["health"] - random.randint(5, 18))
        outcome = "injury"

    return adventure_result_text(pet, outcome)

def advance_day(state):
    migrate_v6_state(state)
    state["day"] += 1
    reports = []

    for pet in state["pets"]:
        if pet.get("has_departed"):
            continue

        # Naturalny upływ czasu
        pet["age_days"] += 1
        old_stage = pet["stage"]
        pet["stage"] = get_stage(pet["age_days"])

        pet["health"] = clamp(pet["health"] - random.randint(0, 3))
        pet["happiness"] = clamp(pet["happiness"] - random.randint(1, 5))
        pet["energy"] = clamp(pet["energy"] - random.randint(1, 5))
        pet["stress"] = clamp(pet["stress"] + random.randint(0, 4))

        if old_stage != pet["stage"]:
            pet["history"].append(f"Smok wszedł w etap: {pet['stage']}.")

        # Stare smoki odchodzą, jeśli nie są związane na zawsze
        if pet["stage"] == "starość" and pet["age_days"] > 18 and not pet.get("is_bound_forever"):
            departure_chance = max(8, 25 - int(pet.get("bond", 0) / 5))
            if random.randint(1, 100) <= departure_chance:
                pet["has_departed"] = True
                msg = f"{pet['name']} odszedł w dzikość. Nie wyglądało to jak śmierć. Bardziej jak decyzja."
                pet["history"].append(msg)
                reports.append(msg)
                continue

        need = dominant_need(pet)
        report = need_report(pet, need)
        pet["life_score_cache"] = life_score(pet)
        reports.append(f"### {pet['name']}\n{report}")

    # Statusy v6: praca, dzikość, odpoczynek, przygotowanie i głowa linii.
    migrate_v6_state(state)
    work_income = 0
    work_msgs = []
    for pet in state["pets"]:
        if pet.get("has_departed"):
            continue
        ensure_v6_pet_fields(pet, state)

        if pet.get("status") == "Smok pracujący":
            income, msg = working_income_this_turn(pet)
            work_income += income
            if msg:
                work_msgs.append(msg)

        elif pet.get("status") == "W dzikości":
            # Wildness is not a one-off adventure now; it gently pushes mutation/risk over time.
            if random.randint(1, 100) <= 28:
                pet["genotype"]["mutation"] = clamp(pet["genotype"].get("mutation", 0) + random.randint(1, 3))
                pet["stress"] = clamp(pet["stress"] + random.randint(1, 5))
                work_msgs.append(f"{pet['name']} wraca z dzikości z czymś nieuchwytnym w spojrzeniu. Mutacyjność linii lekko rośnie.")
            if random.randint(1, 100) <= 10:
                pet["health"] = clamp(pet["health"] - random.randint(2, 7))
                work_msgs.append(f"{pet['name']} wrócił z dzikości z zadrapaniem i urażoną dumą.")

        elif pet.get("status") == "Odpoczynek":
            pet["stress"] = clamp(pet["stress"] - random.randint(8, 14))
            pet["energy"] = clamp(pet["energy"] + random.randint(8, 14))
            pet["health"] = clamp(pet["health"] + random.randint(4, 8))
            pet["happiness"] = clamp(pet["happiness"] + random.randint(2, 6))

        elif pet.get("status") == "Przygotowany do schadzki":
            pet["stress"] = clamp(pet["stress"] - random.randint(1, 4))
            pet["happiness"] = clamp(pet["happiness"] + random.randint(0, 3))

    eco = economy_projection(state)
    actual_income = work_income + eco.get("line_head_bonus", 0)
    upkeep = eco["upkeep"]
    net = actual_income - upkeep
    state["coins"] = max(0, state.get("coins", 0) + net)

    for msg in work_msgs:
        reports.append(msg)

    if net != 0 or actual_income or upkeep:
        sign = "+" if net > 0 else ""
        ub = eco.get("upkeep_breakdown", {})
        reports.append(
            f"**💰 Ekonomia hodowli:** {sign}{net} monet "
            f"(🛠 praca {work_income}, 👑 głowa linii {eco.get('line_head_bonus', 0)}, "
            f"utrzymanie {upkeep}: aktywne {ub.get('base_active', 0)}, młode +{ub.get('young_extra', 0)}, "
            f"stare +{ub.get('old_extra', 0)}, jaja +{ub.get('egg_cost', 0)})."
        )

    # Jajka
    hatched = []
    for egg in state["eggs"]:
        egg["hatch_in"] -= 1
        if egg["hatch_in"] <= 0:
            hatched.append(egg)

    return reports, hatched

def bind_forever(state, pet):
    cost = 100
    if state["coins"] < cost:
        return False, f"Potrzeba {cost} monet, żeby związać smoka z hodowlą na zawsze."
    state["coins"] -= cost
    pet["is_bound_forever"] = True
    msg = f"{pet['name']} zostaje związany z hodowlą. Nie jest własnością. Raczej wspólnikiem z pazurami."
    pet["history"].append(msg)
    return True, msg


def condition_label(pet):
    score = life_score(pet)
    if pet.get("has_departed"):
        return "odszedł"
    if score >= 80:
        return "świetny"
    if score >= 60:
        return "dobry"
    if score >= 40:
        return "niepewny"
    return "słaby"

def mood_label(pet):
    if pet["stress"] > 70:
        return "spięty"
    if pet["happiness"] > 75:
        return "zadowolony"
    if pet["happiness"] < 40:
        return "kapryśny"
    if pet["energy"] < 35:
        return "zmęczony"
    return "czujny"

def breeding_readiness_label(pet):
    if pet["stage"] not in ["dorosłość", "starość"]:
        return "za młody"
    score = life_score(pet)
    if score >= 75 and pet["stress"] < 45:
        return "wysoka"
    if score >= 55:
        return "średnia"
    return "niska"

def dragon_value(pet):
    """Simple MVP valuation for selling a dragon to another off-screen breeder."""
    if pet.get("has_departed"):
        return 0
    genotype = pet.get("genotype", {})
    rarity = genotype.get("rarity", 40)
    fertility = genotype.get("fertility", 40)
    mutation = genotype.get("mutation", 5)
    generation = pet.get("generation", 1)
    children_bonus = len(pet.get("children", [])) * 6
    life_bonus = int(life_score(pet) / 5)
    stage_bonus = {
        "młodość": 5,
        "dorosłość": 25,
        "starość": -10,
        "jajo": 0,
    }.get(pet.get("stage"), 0)

    visual_bonus = 0
    ph = pet.get("phenotype", {})
    if ph.get("pattern") in ["z lśniącymi plamami", "z marmurkowaniem"]:
        visual_bonus += 12
    if ph.get("horns") in ["asymetryczne rogi", "zakrzywione rogi"]:
        visual_bonus += 8
    if ph.get("eyes") in ["czerwone", "srebrne", "złote"]:
        visual_bonus += 6

    value = 20 + generation * 7 + int(rarity / 2.2) + int(fertility / 4) + int(mutation / 2) + stage_bonus + children_bonus + life_bonus + visual_bonus
    return max(8, int(value))

def care_strategy(pet, strategy):
    """
    Replaces micro-care clicking with one day-level decision.
    These are intentionally broad and narrative.
    """
    name = pet["name"]

    if strategy == "nourish":
        pet["health"] = clamp(pet["health"] + 7)
        pet["energy"] = clamp(pet["energy"] + 4)
        pet["happiness"] = clamp(pet["happiness"] + 2)
        pet["stress"] = clamp(pet["stress"] - 2)
        pet["bond"] = clamp(pet.get("bond", 0) + 1)
        msg = f"{name} dostaje spokojny dzień, dobre jedzenie i brak niepotrzebnych ambicji. Pod wieczór wygląda mniej jak problem, a bardziej jak smok."

    elif strategy == "bond":
        pet["happiness"] = clamp(pet["happiness"] + 9)
        pet["stress"] = clamp(pet["stress"] - 5)
        pet["energy"] = clamp(pet["energy"] - 3)
        pet["bond"] = clamp(pet.get("bond", 0) + 3)
        msg = f"{name} przez większość dnia udaje, że nie potrzebuje uwagi. Potem sam układa się bliżej wejścia, dokładnie tam, gdzie będziesz go mijać."

    elif strategy == "prepare":
        pet["happiness"] = clamp(pet["happiness"] + 3)
        pet["stress"] = clamp(pet["stress"] - 8)
        pet["energy"] = clamp(pet["energy"] + 2)
        pet["bond"] = clamp(pet.get("bond", 0) + 1)
        msg = f"{name} ma dziś spokojny rytm: jedzenie, odpoczynek, czyszczenie łusek i żadnych dramatów. Wygląda na trochę bardziej gotowego do ważnych spraw."

    elif strategy == "train":
        pet["energy"] = clamp(pet["energy"] - 9)
        pet["stress"] = clamp(pet["stress"] + 5)
        pet["happiness"] = clamp(pet["happiness"] + random.randint(-2, 6))
        pet["bond"] = clamp(pet.get("bond", 0) + 2)
        msg = f"{name} trenuje z obrażoną godnością. Jeśli robi postępy, to wyłącznie dlatego, że nie chce, żebyś miał rację."

    elif strategy == "observe":
        pet["stress"] = clamp(pet["stress"] - 3)
        pet["energy"] = clamp(pet["energy"] + 1)
        msg = f"Nie naciskasz dziś na {name}. Obserwujesz. Smok też obserwuje. Bilans spojrzeń pozostaje nierozstrzygnięty."

    elif strategy == "adventure":
        msg = send_on_adventure(pet)

    else:
        msg = f"{name} ma zwykły dzień. W hodowli nic spektakularnego się nie dzieje, co u smoków bywa podejrzane."

    pet.setdefault("history", []).append(msg)
    return msg

def sell_dragon(state, pet):
    if pet.get("has_departed"):
        return False, "Tego smoka już nie ma w hodowli."
    if pet.get("is_bound_forever"):
        return False, f"{pet['name']} jest związany z hodowlą na zawsze. Nie da się go sprzedać."
    value = stable_market_value(pet)
    state["coins"] += value
    pet["has_departed"] = True
    pet["sold"] = True
    msg = f"{pet['name']} trafia do innej hodowli. Otrzymujesz {value} monet. Przez chwilę wygląda, jakby zapamiętywał drogę powrotną."
    pet.setdefault("history", []).append(msg)
    return True, msg

def release_dragon(state, pet):
    if pet.get("has_departed"):
        return False, "Tego smoka już nie ma w hodowli."
    if pet.get("is_bound_forever"):
        return False, f"{pet['name']} jest związany z hodowlą na zawsze. Nie chce odejść. Albo udaje, że nie chce."
    pet["has_departed"] = True
    pet["released"] = True
    msg = f"{pet['name']} zostaje wypuszczony w dzikość. Nie dostajesz monet, ale ta linia zostawia ślad poza hodowlą."
    pet.setdefault("history", []).append(msg)
    return True, msg

def economy_projection(state):
    active = [p for p in state["pets"] if not p.get("has_departed")]
    adults_good = [p for p in active if p.get("stage") in ["dorosłość", "starość"] and life_score(p) >= 50]
    young = [p for p in active if p.get("stage") == "młodość"]
    eggs = state.get("eggs", [])

    income = 3 * len(adults_good)
    upkeep = len(young) + len(eggs)
    net = income - upkeep
    return {
        "income": income,
        "upkeep": upkeep,
        "net": net,
        "adults_good": len(adults_good),
        "young": len(young),
        "eggs": len(eggs),
    }


KNOWLEDGE_LABELS = {
    0: "obserwacja",
    1: "wycena rynkowa",
    2: "ocena hodowlana",
    3: "test genetyczny",
}

PREP_LABELS = {
    0: "brak",
    1: "zadbany",
    2: "gotowy",
    3: "rytualnie przygotowany",
}

def knowledge_label(pet):
    return KNOWLEDGE_LABELS.get(pet.get("knowledge_level", 0), "obserwacja")

def prep_label(pet):
    return PREP_LABELS.get(pet.get("prep_level", 0), "brak")

def hidden_trait_effects(traits):
    effects = {
        "fertility": 0,
        "rarity": 0,
        "mutation": 0,
        "risk": 0,
        "value": 0,
        "egg_chance": 0,
    }
    for trait in traits or []:
        if trait == "silna linia":
            effects["value"] += 12
            effects["egg_chance"] += 4
        elif trait == "ukryty gen srebrnych oczu":
            effects["rarity"] += 12
            effects["value"] += 10
        elif trait == "wysoka płodność recesywna":
            effects["fertility"] += 14
            effects["egg_chance"] += 8
        elif trait == "stabilny temperament":
            effects["risk"] -= 8
            effects["egg_chance"] += 2
        elif trait == "dziki potencjał":
            effects["mutation"] += 10
            effects["rarity"] += 8
            effects["risk"] += 8
        elif trait == "długowieczność":
            effects["value"] += 8
        elif trait == "krucha odporność":
            effects["risk"] += 12
            effects["value"] -= 8
        elif trait == "niska płodność ukryta":
            effects["fertility"] -= 18
            effects["egg_chance"] -= 12
        elif trait == "niestabilna mutacja":
            effects["mutation"] += 14
            effects["risk"] += 14
        elif trait == "trudny temperament":
            effects["risk"] += 8
            effects["egg_chance"] -= 4
        elif trait == "ryzyko słabych jaj":
            effects["risk"] += 12
            effects["value"] -= 6
        elif trait == "dzika krew":
            effects["mutation"] += 10
            effects["risk"] += 6
            effects["rarity"] += 6
        elif trait == "stara linia":
            effects["value"] += 14
            effects["egg_chance"] -= 4
        elif trait == "kapryśna ekspresja genów":
            effects["mutation"] += 7
            effects["risk"] += 7
    return effects

def stable_market_value(pet):
    """More stable than the old dynamic sale value; still changes at major events."""
    if pet.get("base_market_value") is not None:
        return int(pet["base_market_value"])
    value = dragon_value(pet)
    pet["base_market_value"] = int(value)
    return int(value)

def visible_market_range(pet):
    base = stable_market_value(pet)
    knowledge = pet.get("knowledge_level", 0)
    if knowledge <= 0:
        return (max(5, int(base * 0.75)), int(base * 1.30))
    if knowledge == 1:
        return (max(5, int(base * 0.90)), int(base * 1.10))
    return (base, base)

def appraise_dragon(state, pet, level):
    """
    level:
    1 - market appraisal
    2 - breeding assessment
    3 - genetic test
    """
    current = pet.get("knowledge_level", 0)
    if level <= current:
        return False, f"{pet['name']} ma już ten poziom rozpoznania albo lepszy."

    costs = {1: 10, 2: 22, 3: 45}
    cost = costs[level]
    if state.get("coins", 0) < cost:
        return False, f"Potrzeba {cost} monet."

    state["coins"] -= cost
    pet["knowledge_level"] = level

    traits = pet.get("hidden_traits", [])
    revealed = pet.setdefault("revealed_hidden_traits", [])

    if level == 3 and traits:
        # reveal up to 2 hidden traits
        for t in traits[:2]:
            if t not in revealed:
                revealed.append(t)
    elif level == 2 and traits:
        # reveal a vague hint, not the exact full genetic truth
        t = traits[0]
        if t not in revealed and random.randint(1, 100) <= 45:
            revealed.append(t)

    if level == 1:
        low, high = visible_market_range(pet)
        msg = f"Rzeczoznawca ocenia {pet['name']}. Wartość sprzedaży jest teraz znacznie czytelniejsza: około {low}–{high} monet."
    elif level == 2:
        msg = f"Ocena hodowlana {pet['name']} daje lepszy obraz potencjału linii. Nie wszystko jest jasne, ale mniej rzeczy jest już czystą zgadywanką."
    else:
        if revealed:
            msg = f"Test genetyczny {pet['name']} ujawnia: {', '.join(revealed)}."
        else:
            msg = f"Test genetyczny {pet['name']} nie wykazał nic spektakularnego. To też jest informacja."

    pet.setdefault("history", []).append(msg)
    return True, msg

def paid_preparation(state, pet, prep_level):
    """
    Paid preparation for breeding.
    1: good care, 10
    2: breeding ritual, 25
    3: luxury conditions, 45
    """
    current = pet.get("prep_level", 0)
    if prep_level <= current:
        return False, f"{pet['name']} ma już taki lub lepszy poziom przygotowania."

    costs = {1: 10, 2: 25, 3: 45}
    cost = costs[prep_level]
    if state.get("coins", 0) < cost:
        return False, f"Potrzeba {cost} monet."

    state["coins"] -= cost
    pet["prep_level"] = prep_level

    if prep_level == 1:
        pet["stress"] = clamp(pet["stress"] - 6)
        pet["happiness"] = clamp(pet["happiness"] + 3)
        msg = f"{pet['name']} dostaje lepsze warunki przed schadzką. Nie jest zachwycony. Jest mniej spięty, co u smoków bywa tym samym."
    elif prep_level == 2:
        pet["stress"] = clamp(pet["stress"] - 10)
        pet["happiness"] = clamp(pet["happiness"] + 5)
        pet["energy"] = clamp(pet["energy"] + 4)
        msg = f"Rytuał hodowlany wokół {pet['name']} przebiega bez widocznej katastrofy. Smok wygląda na gotowego, choć udaje obojętność."
    else:
        pet["stress"] = clamp(pet["stress"] - 16)
        pet["happiness"] = clamp(pet["happiness"] + 8)
        pet["energy"] = clamp(pet["energy"] + 6)
        pet["health"] = clamp(pet["health"] + 3)
        msg = f"{pet['name']} spędza dzień w luksusowych warunkach. Zachowuje się, jakby od dawna uważał to za minimum."

    pet.setdefault("history", []).append(msg)
    return True, msg

def offspring_value_range(parent_a, parent_b, known_only=True):
    a = stable_market_value(parent_a)
    b = stable_market_value(parent_b)
    avg = (a + b) / 2

    visible_bonus = 0
    for p in [parent_a, parent_b]:
        ph = p.get("phenotype", {})
        if ph.get("pattern") in ["z lśniącymi plamami", "z marmurkowaniem"]:
            visible_bonus += 8
        if ph.get("horns") in ["asymetryczne rogi", "zakrzywione rogi"]:
            visible_bonus += 5
        if ph.get("eyes") in ["czerwone", "srebrne", "złote"]:
            visible_bonus += 4

    hidden_effect = hidden_trait_effects(parent_a.get("hidden_traits", []))
    hidden_effect_b = hidden_trait_effects(parent_b.get("hidden_traits", []))
    true_bonus = hidden_effect["value"] + hidden_effect_b["value"] + int((hidden_effect["rarity"] + hidden_effect_b["rarity"]) / 2)

    knowledge = min(parent_a.get("knowledge_level", 0), parent_b.get("knowledge_level", 0))
    uncertainty = {0: 0.65, 1: 0.45, 2: 0.30, 3: 0.18}.get(knowledge, 0.55)

    center = avg + visible_bonus
    if not known_only or knowledge >= 3:
        center += true_bonus
    elif knowledge >= 2:
        center += int(true_bonus * 0.45)

    low = max(5, int(center * (1 - uncertainty)))
    high = max(low + 8, int(center * (1 + uncertainty)))
    return low, high

def rare_potential_label(parent_a, parent_b):
    rarity = parent_a["genotype"].get("rarity", 40) + parent_b["genotype"].get("rarity", 40)
    mutation = parent_a["genotype"].get("mutation", 5) + parent_b["genotype"].get("mutation", 5)
    effects = hidden_trait_effects(parent_a.get("hidden_traits", []) + parent_b.get("hidden_traits", []))
    score = rarity / 2 + mutation + effects["rarity"] + effects["mutation"]

    knowledge = max(parent_a.get("knowledge_level", 0), parent_b.get("knowledge_level", 0))
    if knowledge < 2:
        return "nieznany"
    if score >= 105:
        return "bardzo wysoki"
    if score >= 80:
        return "wysoki"
    if score >= 55:
        return "średni"
    return "niski"

def hidden_risk_label(parent_a, parent_b):
    effects = hidden_trait_effects(parent_a.get("hidden_traits", []) + parent_b.get("hidden_traits", []))
    score = effects["risk"] + int((parent_a["stress"] + parent_b["stress"]) / 8)
    knowledge = max(parent_a.get("knowledge_level", 0), parent_b.get("knowledge_level", 0))
    if knowledge < 2:
        return "nieznane"
    if score >= 30:
        return "wysokie"
    if score >= 15:
        return "średnie"
    return "niskie"

def compatibility_label(parent_a, parent_b):
    t1 = parent_a.get("temperament")
    t2 = parent_b.get("temperament")
    difficult = {("dziki", "lękliwy"), ("złośliwy", "dumny"), ("wyrachowany", "dziki"), ("leniwy", "dziki")}
    good = {("przywiązany", "stabilny"), ("ciekawski", "dziki"), ("dumny", "wyrachowany"), ("przywiązany", "ciekawski")}

    pair = (t1, t2)
    pair_rev = (t2, t1)
    if pair in difficult or pair_rev in difficult:
        return "trudna"
    if pair in good or pair_rev in good:
        return "obiecująca"
    if t1 == t2:
        return "spójna"
    return "niepewna"

def breeding_preview(parent_a, parent_b):
    # approximate, deterministic-ish enough for UI
    life_a = life_score(parent_a)
    life_b = life_score(parent_b)
    fert_a = parent_a["genotype"].get("fertility", 50)
    fert_b = parent_b["genotype"].get("fertility", 50)
    prep_bonus = parent_a.get("prep_level", 0) * 7 + parent_b.get("prep_level", 0) * 3
    effects = hidden_trait_effects(parent_a.get("hidden_traits", []) + parent_b.get("hidden_traits", []))

    chance = 35 + int((fert_a + fert_b) / 8) + int((life_a + life_b) / 8) - int((parent_a["stress"] + parent_b["stress"]) / 4)
    chance += prep_bonus + effects["egg_chance"]
    chance = clamp(chance, 5, 95)

    value_low, value_high = offspring_value_range(parent_a, parent_b, known_only=True)
    return {
        "egg_chance": chance,
        "multi_egg": "wysoka" if chance > 75 else "średnia" if chance > 50 else "niska",
        "value_low": value_low,
        "value_high": value_high,
        "rare_potential": rare_potential_label(parent_a, parent_b),
        "hidden_risk": hidden_risk_label(parent_a, parent_b),
        "compatibility": compatibility_label(parent_a, parent_b),
    }



# ---------- V6: statuses, reports, market appraisal ----------

DRAGON_STATUSES = [
    "W hodowli",
    "Przygotowany do schadzki",
    "Smok pracujący",
    "W dzikości",
    "Odpoczynek",
    "Reproduktor / Matka linii",
]

TRAIT_METADATA = {
    "silna linia": {
        "type": "pozytywna",
        "effects": "+ wartość potomstwa, + szansa jajka, + stabilność linii",
        "description": "Ta linia ma dobrą strukturę hodowlaną. Potomstwo może być cenione wyżej i częściej dawać stabilne wyniki.",
    },
    "ukryty gen srebrnych oczu": {
        "type": "pozytywna",
        "effects": "+ potencjał rzadkich cech, + wartość wizualna potomstwa",
        "description": "W linii może ujawniać się rzadka cecha oczu, nawet jeśli nie widać jej u tego smoka.",
    },
    "wysoka płodność recesywna": {
        "type": "pozytywna",
        "effects": "+ płodność, + szansa jajka",
        "description": "Ukryty wariant płodności może zwiększać szanse na jajka, zwłaszcza w kolejnych pokoleniach.",
    },
    "stabilny temperament": {
        "type": "pozytywna",
        "effects": "- ryzyko, + przewidywalność potomstwa",
        "description": "Smok wnosi do linii spokojniejszą ekspresję zachowania i mniejsze ryzyko problematycznych wyników.",
    },
    "dziki potencjał": {
        "type": "mieszana",
        "effects": "+ mutacyjność, + rzadkość, + ryzyko",
        "description": "Ta cecha może dawać spektakularne potomstwo, ale jest mniej przewidywalna.",
    },
    "długowieczność": {
        "type": "pozytywna",
        "effects": "+ wartość linii, + znaczenie genealogiczne",
        "description": "Linia może mieć lepszą trwałość i większą wartość dla hodowców myślących długoterminowo.",
    },
    "krucha odporność": {
        "type": "negatywna",
        "effects": "+ ryzyko, - wartość, - odporność potomstwa",
        "description": "Potomstwo może częściej dziedziczyć słabszą kondycję albo wymagać ostrożniejszego prowadzenia.",
    },
    "niska płodność ukryta": {
        "type": "negatywna",
        "effects": "- płodność, - szansa jajka",
        "description": "Smok może wyglądać obiecująco, ale w praktyce dawać mniej jaj niż oczekiwano.",
    },
    "niestabilna mutacja": {
        "type": "mieszana",
        "effects": "+ mutacyjność, + ryzyko słabych albo dziwnych wyników",
        "description": "Cecha może prowadzić do rzadkich rezultatów, ale także do nieudanych lub mniej wartościowych potomków.",
    },
    "trudny temperament": {
        "type": "negatywna",
        "effects": "+ ryzyko, - kompatybilność niektórych schadzek",
        "description": "Charakter smoka może utrudniać udane kojarzenia i zwiększać nieprzewidywalność potomstwa.",
    },
    "ryzyko słabych jaj": {
        "type": "negatywna",
        "effects": "+ ryzyko, - wartość potomstwa",
        "description": "Nawet dobra schadzka może dać słabsze wyniki niż sugeruje wygląd rodziców.",
    },
    "dzika krew": {
        "type": "mieszana",
        "effects": "+ mutacyjność, + rzadkość, + ryzyko",
        "description": "Dzika krew zwiększa potencjał zaskakujących cech, ale obniża kontrolę nad wynikiem.",
    },
    "stara linia": {
        "type": "mieszana",
        "effects": "+ wartość potomstwa, - liczba jaj",
        "description": "Linia może być prestiżowa i cenna, ale mniej płodna.",
    },
    "kapryśna ekspresja genów": {
        "type": "mieszana",
        "effects": "+ nietypowe rezultaty, + ryzyko",
        "description": "Geny tej linii mogą ujawniać się niekonsekwentnie. To ciekawe, ale trudne do planowania.",
    },
}

def ensure_v6_pet_fields(pet, state=None):
    pet.setdefault("status", "W hodowli")
    pet.setdefault("work_type", None)
    pet.setdefault("line_head", pet.get("status") == "Reproduktor / Matka linii")
    pet.setdefault("market_appraisal_price", None)
    pet.setdefault("market_appraisal_day", None)
    pet.setdefault("breeding_report", None)
    pet.setdefault("genetic_report", None)
    pet.setdefault("revealed_hidden_traits", [])
    pet.setdefault("hidden_traits", [])
    return pet

def migrate_v6_state(state):
    for pet in state.get("pets", []):
        ensure_v6_pet_fields(pet, state)
    state.setdefault("status_feed", [])
    return state

def has_market_appraisal(pet, state=None):
    ensure_v6_pet_fields(pet, state)
    if pet.get("knowledge_level", 0) < 1:
        return False
    if pet.get("market_appraisal_price") is None:
        return False
    if state is not None and pet.get("market_appraisal_day") != state.get("day"):
        return False
    return True

def current_sale_price(pet, state=None):
    ensure_v6_pet_fields(pet, state)
    # Price for the current turn. This is concrete after appraisal.
    return stable_market_value(pet)

def sale_button_label(pet, state=None):
    if has_market_appraisal(pet, state):
        return f"Sprzedaj za {pet['market_appraisal_price']} monet"
    return "Sprzedaj bez wyceny"

def visible_sale_text(pet, state=None):
    if has_market_appraisal(pet, state):
        return f"{pet['market_appraisal_price']} monet"
    return "nieznana — wykonaj wycenę rynkową"

def trait_explanation(trait):
    meta = TRAIT_METADATA.get(trait, {
        "type": "nieznana",
        "effects": "brak danych",
        "description": "Brak opisu tej cechy.",
    })
    return meta

def format_trait_line(trait):
    meta = trait_explanation(trait)
    return f"**{trait}** — {meta['type']}. Efekt: {meta['effects']}. {meta['description']}"

def generate_breeding_report(pet):
    ensure_v6_pet_fields(pet)
    genotype = pet.get("genotype", {})
    fertility = genotype.get("fertility", 50)
    mutation = genotype.get("mutation", 5)
    rarity = genotype.get("rarity", 50)
    risk = hidden_trait_effects(pet.get("hidden_traits", [])).get("risk", 0)

    if fertility >= 70:
        fertility_text = "wysoka"
    elif fertility >= 45:
        fertility_text = "średnia"
    else:
        fertility_text = "niska"

    if mutation >= 25:
        mutation_text = "wysoka / niestabilna"
    elif mutation >= 10:
        mutation_text = "umiarkowana"
    else:
        mutation_text = "niska"

    if rarity >= 75:
        potential = "wysoki"
    elif rarity >= 45:
        potential = "średni"
    else:
        potential = "niski"

    if risk >= 20:
        risk_text = "wysokie"
    elif risk >= 8:
        risk_text = "średnie"
    else:
        risk_text = "niskie"

    recommendation = "Łączyć z linią stabilną i dobrze rozpoznaną."
    if fertility >= 70 and risk < 10:
        recommendation = "Dobry kandydat do budowania stabilnej linii."
    elif mutation >= 25:
        recommendation = "Używać ostrożnie: możliwe ciekawe, ale niestabilne potomstwo."
    elif rarity >= 75:
        recommendation = "Warto testować z partnerami o mocnych cechach wizualnych."

    report = {
        "title": f"Ocena hodowlana: {pet['name']}",
        "potential": potential,
        "fertility": fertility_text,
        "mutation": mutation_text,
        "risk": risk_text,
        "recommendation": recommendation,
        "summary": (
            f"Potencjał hodowlany: {potential}. Płodność: {fertility_text}. "
            f"Mutacyjność: {mutation_text}. Ryzyko linii: {risk_text}. "
            f"Rekomendacja: {recommendation}"
        ),
    }
    return report

def generate_genetic_report(pet):
    ensure_v6_pet_fields(pet)
    traits = pet.get("revealed_hidden_traits", [])
    lines = []
    for trait in traits:
        lines.append({
            "trait": trait,
            "type": trait_explanation(trait)["type"],
            "effects": trait_explanation(trait)["effects"],
            "description": trait_explanation(trait)["description"],
        })

    report = {
        "title": f"Test genetyczny: {pet['name']}",
        "traits": lines,
        "summary": "Brak wykrytych cech ukrytych." if not lines else "Wykryto cechy ukryte: " + ", ".join(t["trait"] for t in lines),
    }
    return report

# Override appraise_dragon from v5 with v6 behavior
def appraise_dragon(state, pet, level):
    """
    level:
    1 - market appraisal
    2 - breeding assessment
    3 - genetic test
    """
    ensure_v6_pet_fields(pet, state)
    current = pet.get("knowledge_level", 0)
    labels = {1: "wycena rynkowa", 2: "ocena hodowlana", 3: "test genetyczny"}

    # Allow market appraisal once per day, but don't allow re-paying if already current.
    if level == 1 and has_market_appraisal(pet, state):
        return False, f"{pet['name']} ma już aktualną wycenę rynkową na tę turę: {pet['market_appraisal_price']} monet."
    if level > 1 and level <= current:
        return False, f"{pet['name']} ma już wykonane: {labels[level]}."

    costs = {1: 10, 2: 22, 3: 45}
    cost = costs[level]
    if state.get("coins", 0) < cost:
        return False, f"Potrzeba {cost} monet."

    state["coins"] -= cost

    if level > current:
        pet["knowledge_level"] = level

    if level == 1:
        price = current_sale_price(pet, state)
        pet["market_appraisal_price"] = price
        pet["market_appraisal_day"] = state.get("day")
        msg = f"Wycena rynkowa {pet['name']}: w tej turze możesz sprzedać tego smoka za dokładnie {price} monet."

    elif level == 2:
        report = generate_breeding_report(pet)
        pet["breeding_report"] = report
        msg = (
            f"{report['title']}\n\n"
            f"{report['summary']}"
        )

    else:
        traits = pet.get("hidden_traits", [])
        revealed = pet.setdefault("revealed_hidden_traits", [])
        for t in traits[:2]:
            if t not in revealed:
                revealed.append(t)
        pet["genetic_report"] = generate_genetic_report(pet)

        if revealed:
            trait_lines = "\n".join([f"- {format_trait_line(t)}" for t in revealed])
            msg = f"Test genetyczny {pet['name']} ujawnia:\n{trait_lines}"
        else:
            msg = f"Test genetyczny {pet['name']} nie wykazał cech ukrytych. To zmniejsza niepewność tej linii."

    pet.setdefault("history", []).append(msg)
    state.setdefault("status_feed", []).insert(0, msg)
    state["status_feed"] = state["status_feed"][:30]
    return True, msg

def set_dragon_status(state, pet, new_status):
    ensure_v6_pet_fields(pet, state)
    if new_status not in DRAGON_STATUSES:
        return False, "Nieznany status."
    old = pet.get("status", "W hodowli")
    pet["status"] = new_status
    pet["line_head"] = new_status == "Reproduktor / Matka linii"

    if new_status != "Smok pracujący":
        pet["work_type"] = None

    descriptions = {
        "W hodowli": f"{pet['name']} wraca do zwykłego rytmu hodowli. Udaje, że to nie ma znaczenia.",
        "Przygotowany do schadzki": f"{pet['name']} zostaje przygotowany do schadzki. Dostaje spokój, lepsze warunki i ilość uwagi, którą uznaje za minimalnie akceptowalną.",
        "Smok pracujący": f"{pet['name']} zostaje wpisany jako smok pracujący. Nadal może być wystawiony do reprodukcji.",
        "W dzikości": f"{pet['name']} znika częściej poza granicą hodowli. Dzikość zwiększa szanse przygód, mutacji i nieprzewidywalnych cech.",
        "Odpoczynek": f"{pet['name']} trafia na odpoczynek. Mniej ambicji, mniej stresu, więcej oceniającego milczenia.",
        "Reproduktor / Matka linii": f"{pet['name']} zostaje głową linii. Od tej pory jego znaczenie wpływa na całą hodowlę.",
    }
    msg = descriptions[new_status]
    pet.setdefault("history", []).append(msg)
    return True, msg

WORK_TYPES = [
    "pilnowanie karawany",
    "ogrzewanie miejskiej łaźni",
    "stróżowanie przy składzie kupieckim",
    "praca przy kuźni",
    "transport ciężkich ładunków",
    "odstraszanie gołębi z wieży ratuszowej",
    "pilnowanie piwnicy z winem",
    "nocny zwiad",
    "przenoszenie wiadomości",
]

def work_affinity(pet, work_type):
    ensure_v6_pet_fields(pet)
    ph = pet.get("phenotype", {})
    genotype = pet.get("genotype", {})
    temperament = pet.get("temperament")
    color = ph.get("color")
    size = ph.get("size")
    horns = ph.get("horns")
    pattern = ph.get("pattern")

    score = 0
    reasons = []

    def add(points, reason):
        nonlocal score, reasons
        score += points
        reasons.append(reason)

    if work_type == "transport ciężkich ładunków":
        if size in ["duży", "krępy"]:
            add(5, "rozmiar pomaga w transporcie")
        if temperament == "leniwy":
            add(-2, "leniwy temperament obniża tempo")
    elif work_type == "ogrzewanie miejskiej łaźni":
        if color in ["rdzawy", "złoty", "miedziany"]:
            add(4, "ciepła linia dobrze pasuje do pracy przy ogniu")
        if temperament == "złośliwy":
            add(-2, "złośliwość zwiększa ryzyko incydentu")
    elif work_type == "praca przy kuźni":
        if color in ["czarny", "rdzawy", "miedziany"]:
            add(4, "fenotyp dobrze pasuje do kuźni")
        if horns in ["zakrzywione rogi", "asymetryczne rogi"]:
            add(2, "rogi pomagają przy pracy fizycznej")
    elif work_type == "pilnowanie karawany":
        if size in ["duży", "krępy"]:
            add(3, "duży smok odstrasza napastników")
        if temperament in ["dumny", "wyrachowany", "dziki"]:
            add(3, "charakter dobrze pasuje do ochrony")
    elif work_type == "stróżowanie przy składzie kupieckim":
        if temperament in ["wyrachowany", "złośliwy", "dumny"]:
            add(4, "ten smok umie wyglądać jak problem")
        if color in ["czarny", "granatowy"]:
            add(2, "ciemny fenotyp sprzyja stróżowaniu")
    elif work_type == "odstraszanie gołębi z wieży ratuszowej":
        if temperament in ["złośliwy", "ciekawski"]:
            add(4, "ma naturalny talent do przesadzonych reakcji")
        if size == "mały":
            add(2, "mały smok łatwiej porusza się po wieży")
    elif work_type == "pilnowanie piwnicy z winem":
        if temperament in ["wyrachowany", "leniwy"]:
            add(3, "umie długo siedzieć i osądzać")
        if color in ["czarny", "granatowy", "purpurowy"]:
            add(2, "wygląda odpowiednio poważnie")
    elif work_type == "nocny zwiad":
        if color in ["czarny", "granatowy"]:
            add(4, "ciemny fenotyp sprzyja nocnemu zwiadowi")
        if temperament in ["dziki", "ciekawski", "wyrachowany"]:
            add(3, "charakter dobrze pasuje do zwiadu")
        if size in ["smukły", "mały"]:
            add(2, "lżejsza budowa pomaga w ruchu")
    elif work_type == "przenoszenie wiadomości":
        if size in ["mały", "smukły"]:
            add(4, "lekka budowa ułatwia szybki ruch")
        if temperament in ["ciekawski", "przywiązany"]:
            add(2, "łatwiej wraca z wiadomością niż z obrazą majestatu")

    if genotype.get("rarity", 0) > 75:
        add(1, "rzadkość budzi respekt")
    if pattern in ["z lśniącymi plamami", "z marmurkowaniem"]:
        add(1, "wygląd robi wrażenie")

    return score, reasons

def best_work_for_dragon(pet):
    scored = []
    for work in WORK_TYPES:
        score, reasons = work_affinity(pet, work)
        scored.append((score, work, reasons))
    scored.sort(reverse=True, key=lambda x: x[0])
    return scored[0]

def work_income_range(pet, work_type=None):
    if work_type is None:
        _, work_type, _ = best_work_for_dragon(pet)
    score, reasons = work_affinity(pet, work_type)
    base = 4 + max(0, score)
    if pet.get("status") == "Reproduktor / Matka linii":
        base += 1
    if life_score(pet) < 45:
        base -= 2
    low = max(1, base - 2)
    high = max(low + 1, base + 3)
    risk = "wysokie" if score < 0 else "średnie" if score < 4 else "niskie"
    return low, high, risk, reasons

def working_income_this_turn(pet):
    if pet.get("status") != "Smok pracujący":
        return 0, None
    work = pet.get("work_type")
    if not work:
        _, work, _ = best_work_for_dragon(pet)
        pet["work_type"] = work
    low, high, risk, reasons = work_income_range(pet, work)
    income = random.randint(low, high)
    # work has a small cost
    pet["stress"] = clamp(pet["stress"] + random.randint(0, 4))
    pet["energy"] = clamp(pet["energy"] - random.randint(1, 5))
    msg = f"{pet['name']} pracuje: {work}. Zarabia {income} monet. Ryzyko pracy: {risk}."
    if random.randint(1, 100) <= (12 if risk == "średnie" else 22 if risk == "wysokie" else 6):
        pet["stress"] = clamp(pet["stress"] + 6)
        msg += " Wrócił z miną smoka, który ma kilka uwag do organizacji pracy."
    return income, msg

def line_head_bonus(state):
    heads = [p for p in state.get("pets", []) if not p.get("has_departed") and p.get("status") == "Reproduktor / Matka linii"]
    if not heads:
        return 0
    # Keep it capped for MVP.
    return min(10, 3 + len(heads) * 2)

# Override economy_projection from v4/v5
def economy_projection(state):
    migrate_v6_state(state)
    active = [p for p in state["pets"] if not p.get("has_departed")]
    working = [p for p in active if p.get("status") == "Smok pracujący"]
    young = [p for p in active if p.get("stage") == "młodość"]
    eggs = state.get("eggs", [])
    projected_income = 0
    for p in working:
        low, high, risk, reasons = work_income_range(p, p.get("work_type"))
        projected_income += int((low + high) / 2)
    upkeep = len(young) + len(eggs)
    bonus = line_head_bonus(state)
    net = projected_income + bonus - upkeep
    return {
        "income": projected_income + bonus,
        "work_income": projected_income,
        "line_head_bonus": bonus,
        "upkeep": upkeep,
        "net": net,
        "working": len(working),
        "young": len(young),
        "eggs": len(eggs),
    }

# Override sell_dragon with concrete appraisal behavior
def sell_dragon(state, pet):
    ensure_v6_pet_fields(pet, state)
    if pet.get("has_departed"):
        return False, "Tego smoka już nie ma w hodowli."
    if pet.get("is_bound_forever"):
        return False, f"{pet['name']} jest związany z hodowlą na zawsze. Nie da się go sprzedać."
    if has_market_appraisal(pet, state):
        value = pet["market_appraisal_price"]
        msg = f"{pet['name']} trafia do innej hodowli za wcześniej wycenione {value} monet. Przez chwilę wygląda, jakby zapamiętywał drogę powrotną."
    else:
        value = current_sale_price(pet, state)
        msg = f"{pet['name']} trafia do innej hodowli bez wcześniejszej wyceny. Dopiero po fakcie okazuje się, że otrzymujesz {value} monet."
    state["coins"] += value
    pet["has_departed"] = True
    pet["sold"] = True
    pet.setdefault("history", []).append(msg)
    return True, msg



# ---------- V7: recovery, bond, lifecycle helpers ----------

YOUTH_DAYS = 3
ADULT_DAYS = 14
OLD_DEPARTURE_SOFT_DAY = 18

def lifecycle_info(pet):
    age = pet.get("age_days", 0)
    stage = pet.get("stage", "młodość")
    if stage == "młodość":
        return {
            "stage": stage,
            "next_stage": "dorosłość",
            "days_to_next": max(0, YOUTH_DAYS - age),
            "warning": None,
        }
    if stage == "dorosłość":
        days_to_old = max(0, ADULT_DAYS - age)
        warning = "Niedługo wejdzie w starość." if days_to_old <= 3 else None
        return {
            "stage": stage,
            "next_stage": "starość",
            "days_to_next": days_to_old,
            "warning": warning,
        }
    # old age
    days_to_departure = max(0, OLD_DEPARTURE_SOFT_DAY - age)
    warning = "Może wkrótce odejść w dzikość. To moment na związanie z hodowlą." if not pet.get("is_bound_forever") else None
    return {
        "stage": stage,
        "next_stage": "możliwe odejście",
        "days_to_next": days_to_departure,
        "warning": warning,
    }

def full_recovery_cost(pet):
    # Higher for older/rarer dragons, lower with bond.
    rarity = pet.get("genotype", {}).get("rarity", 50)
    bond = pet.get("bond", 0)
    base = 35 + int(rarity / 8)
    discount = int(bond / 12)
    return max(20, base - discount)

def full_recovery(state, pet):
    ensure_v6_pet_fields(pet, state)
    cost = full_recovery_cost(pet)
    if state.get("coins", 0) < cost:
        return False, f"Potrzeba {cost} monet na pełną kurację."
    state["coins"] -= cost
    pet["health"] = max(pet.get("health", 0), 96)
    pet["happiness"] = max(pet.get("happiness", 0), 94)
    pet["energy"] = max(pet.get("energy", 0), 96)
    pet["stress"] = min(pet.get("stress", 100), 4)
    pet["bond"] = clamp(pet.get("bond", 0) + 2)
    msg = f"{pet['name']} przechodzi pełną kurację. Wraca do formy tak dobrej, że przez chwilę wygląda, jakby to wszystko było jego pomysłem."
    pet.setdefault("history", []).append(msg)
    return True, msg

def bond_action_cost(pet):
    return 8

def build_bond(state, pet):
    ensure_v6_pet_fields(pet, state)
    cost = bond_action_cost(pet)
    if state.get("coins", 0) < cost:
        return False, f"Potrzeba {cost} monet, żeby poświęcić smokowi dzień uważnej opieki."
    state["coins"] -= cost
    gain = random.randint(5, 10)
    if pet.get("status") == "Odpoczynek":
        gain += 2
    pet["bond"] = clamp(pet.get("bond", 0) + gain)
    pet["happiness"] = clamp(pet.get("happiness", 0) + 4)
    pet["stress"] = clamp(pet.get("stress", 0) - 5)
    msg = f"Spędzasz czas z {pet['name']}. Nie ma wielkiego gestu — tylko kilka drobnych momentów, po których smok przestaje udawać, że jesteś całkiem zbędny. Więź +{gain}."
    pet.setdefault("history", []).append(msg)
    return True, msg

# Override bind_forever to use bond discount and clearer timing
def bind_forever(state, pet):
    ensure_v6_pet_fields(pet, state)
    base_cost = 100
    bond_discount = min(60, int(pet.get("bond", 0) * 0.6))
    cost = max(35, base_cost - bond_discount)
    if state["coins"] < cost:
        return False, f"Potrzeba {cost} monet, żeby związać smoka z hodowlą na zawsze. Wyższa więź obniża koszt."
    state["coins"] -= cost
    pet["is_bound_forever"] = True
    msg = f"{pet['name']} zostaje związany z hodowlą na zawsze. To nie jest własność. Raczej obietnica, którą smok łaskawie uznał za wartą rozważenia. Koszt po uwzględnieniu więzi: {cost} monet."
    pet.setdefault("history", []).append(msg)
    return True, msg

def compact_stage_rank(pet):
    stage = pet.get("stage", "młodość")
    if stage == "starość":
        return 0
    if stage == "dorosłość":
        return 1
    if stage == "młodość":
        return 2
    return 3


# ---------- V9: economy upkeep breakdown ----------

def upkeep_breakdown(state):
    migrate_v6_state(state)
    active = [p for p in state.get("pets", []) if not p.get("has_departed")]
    young = [p for p in active if p.get("stage") == "młodość"]
    old = [p for p in active if p.get("stage") == "starość"]
    eggs = state.get("eggs", [])
    return {
        "active_count": len(active),
        "young_count": len(young),
        "old_count": len(old),
        "egg_count": len(eggs),
        "base_active": len(active),
        "young_extra": len(young),
        "old_extra": len(old),
        "egg_cost": len(eggs),
        "total": len(active) + len(young) + len(old) + len(eggs),
    }

def economy_projection(state):
    migrate_v6_state(state)
    active = [p for p in state["pets"] if not p.get("has_departed")]
    working = [p for p in active if p.get("status") == "Smok pracujący"]
    projected_work_income = 0
    for p in working:
        low, high, risk, reasons = work_income_range(p, p.get("work_type"))
        projected_work_income += int((low + high) / 2)
    upkeep = upkeep_breakdown(state)
    bonus = line_head_bonus(state)
    income = projected_work_income + bonus
    net = income - upkeep["total"]
    return {
        "income": income,
        "work_income": projected_work_income,
        "line_head_bonus": bonus,
        "upkeep": upkeep["total"],
        "upkeep_breakdown": upkeep,
        "net": net,
        "working": len(working),
        "young": upkeep["young_count"],
        "eggs": upkeep["egg_count"],
        "active": upkeep["active_count"],
    }


# ---------- V12: line quality economy, market saturation and breeding value ----------

RARE_VISUALS_V12 = {
    "colors": {
        "szafirowy", "perłowy", "karminowy", "lawendowy", "bursztynowy", "kościany", "dymny",
        "purpurowy", "biały", "złoty"
    },
    "patterns": {
        "z lśniącymi plamami", "z marmurkowaniem", "z gwiezdnymi plamkami",
        "z popękanymi łuskami", "z maską na pysku"
    },
    "eyes": {"srebrne", "złote", "czerwone", "fioletowe", "dymne"},
    "horns": {"asymetryczne rogi", "koronne rogi", "baranie rogi", "pojedynczy róg", "pęknięte rogi"},
}

def ensure_v12_state(state):
    migrate_v6_state(state)
    state.setdefault("market_saturation", 0)
    state.setdefault("total_sales", 0)
    state.setdefault("quality_sales", 0)
    state.setdefault("line_prestige", 0)
    state.setdefault("line_name", "Nienazwana linia")
    return state

def visual_rarity_score(pet):
    ph = pet.get("phenotype", {})
    score = 0
    if ph.get("color") in RARE_VISUALS_V12["colors"]:
        score += 10
    if ph.get("pattern") in RARE_VISUALS_V12["patterns"]:
        score += 12
    if ph.get("eyes") in RARE_VISUALS_V12["eyes"]:
        score += 8
    if ph.get("horns") in RARE_VISUALS_V12["horns"]:
        score += 8
    if ph.get("size") in ["smukły", "krępy"]:
        score += 4
    return score

def breeding_value(pet):
    """How valuable the dragon is to the line, not necessarily how much the market pays now."""
    if pet.get("has_departed"):
        return 0
    g = pet.get("genotype", {})
    hidden = hidden_trait_effects(pet.get("hidden_traits", []))
    value = 0
    value += int(g.get("rarity", 40) * 0.55)
    value += int(g.get("fertility", 40) * 0.32)
    value += int(g.get("immunity", 40) * 0.25)
    value += int(life_score(pet) * 0.25)
    value += visual_rarity_score(pet)
    value += len(pet.get("children", [])) * 4
    value += pet.get("generation", 1) * 3
    value += hidden.get("value", 0)
    value += hidden.get("rarity", 0)
    value += max(0, hidden.get("fertility", 0) // 2)

    if pet.get("status") == "Reproduktor / Matka linii" or pet.get("line_head"):
        value += 18
    if pet.get("stage") == "dorosłość":
        value += 12
    elif pet.get("stage") == "młodość":
        value -= 12
    elif pet.get("stage") == "starość":
        value += 2 if pet.get("is_bound_forever") else -10

    # Risk matters for breeding value, but does not erase rare potential entirely.
    value -= max(0, hidden.get("risk", 0) // 2)
    return max(1, int(value))

def compute_line_prestige(state):
    ensure_v12_state(state)
    active = [p for p in state.get("pets", []) if not p.get("has_departed")]
    if not active:
        return 0
    values = sorted([breeding_value(p) for p in active], reverse=True)
    top = values[:3]
    top_score = sum(top) / max(1, len(top))
    line_heads = [p for p in active if p.get("status") == "Reproduktor / Matka linii" or p.get("line_head")]
    head_bonus = max([breeding_value(p) for p in line_heads], default=0) * 0.25
    generations = max([p.get("generation", 1) for p in active], default=1)
    diversity = len(set((p.get("phenotype", {}).get("color"), p.get("phenotype", {}).get("pattern")) for p in active))
    prestige = int(top_score * 0.45 + head_bonus + generations * 2 + diversity * 1.5)
    state["line_prestige"] = clamp(prestige, 0, 100)
    return state["line_prestige"]

def dragon_value(pet):
    """Base market price. Stronger quality signal; low-quality young dragons no longer print money."""
    if pet.get("has_departed"):
        return 0
    g = pet.get("genotype", {})
    value = 8
    value += int(g.get("rarity", 40) * 0.36)
    value += int(g.get("fertility", 40) * 0.18)
    value += int(g.get("immunity", 40) * 0.12)
    value += int(life_score(pet) * 0.16)
    value += int(visual_rarity_score(pet) * 0.75)
    value += len(pet.get("children", [])) * 3
    value += pet.get("generation", 1) * 2

    stage = pet.get("stage")
    if stage == "młodość":
        value -= 24  # selling babies is no longer a dominant strategy
    elif stage == "dorosłość":
        value += 10
    elif stage == "starość":
        value -= 12
        if pet.get("is_bound_forever") or pet.get("status") == "Reproduktor / Matka linii":
            value += 14

    if pet.get("knowledge_level", 0) >= 2:
        value += 4
    if pet.get("knowledge_level", 0) >= 3:
        value += 5

    hidden = hidden_trait_effects(pet.get("revealed_hidden_traits", []))
    value += hidden.get("value", 0)
    value += max(-12, hidden.get("fertility", 0) // 2)
    value -= max(0, hidden.get("risk", 0) // 2)

    return max(3, int(value))

def stable_market_value(pet):
    """
    Baseline value of the dragon. Actual sale price may be modified by market saturation
    through current_sale_price(state, pet).
    """
    if pet.get("base_market_value") is None:
        pet["base_market_value"] = int(dragon_value(pet))
    # Allow value to rise when the dragon clearly matures/improves, but not jump down every turn.
    pet["base_market_value"] = max(int(pet["base_market_value"]), int(dragon_value(pet) * 0.85))
    return int(pet["base_market_value"])

def market_multiplier(state, pet):
    ensure_v12_state(state)
    saturation = state.get("market_saturation", 0)
    prestige = compute_line_prestige(state)

    mult = 1.0
    mult -= min(0.45, saturation * 0.045)  # mass-selling depresses the market
    if pet.get("stage") == "młodość":
        mult -= 0.18
    if breeding_value(pet) >= 85:
        mult += 0.10
    if breeding_value(pet) >= 110:
        mult += 0.10
    mult += min(0.18, prestige / 600)
    if pet.get("status") == "Reproduktor / Matka linii" or pet.get("line_head"):
        mult += 0.08
    return max(0.35, min(1.45, mult))

def current_sale_price(pet, state=None):
    ensure_v6_pet_fields(pet, state)
    base = stable_market_value(pet)
    if state is None:
        return base
    return max(1, int(base * market_multiplier(state, pet)))

def visible_market_range(pet):
    base = stable_market_value(pet)
    knowledge = pet.get("knowledge_level", 0)
    if knowledge <= 0:
        return (max(1, int(base * 0.55)), int(base * 1.35))
    if knowledge == 1:
        return (max(1, int(base * 0.85)), int(base * 1.15))
    return (base, base)

def sell_dragon(state, pet):
    ensure_v12_state(state)
    if pet.get("has_departed"):
        return False, "Tego smoka już nie ma w hodowli."
    if pet.get("is_bound_forever"):
        return False, f"{pet['name']} jest związany z hodowlą na zawsze. Nie da się go sprzedać."

    # If appraised today, honour that exact price. Otherwise sell at unknown current market.
    if has_market_appraisal(pet, state):
        value = int(pet["market_appraisal_price"])
    else:
        value = current_sale_price(pet, state)

    bval = breeding_value(pet)
    state["coins"] += value
    state["total_sales"] = state.get("total_sales", 0) + 1
    if bval >= 85:
        state["quality_sales"] = state.get("quality_sales", 0) + 1
        state["market_saturation"] = max(0, state.get("market_saturation", 0) - 1)
        quality_note = "Kupcy zapisują nazwę twojej hodowli. To była sprzedaż jakościowa."
    else:
        state["market_saturation"] = min(18, state.get("market_saturation", 0) + (2 if pet.get("stage") == "młodość" else 1))
        quality_note = "Rynek robi się trochę bardziej nasycony podobnymi smokami."

    pet["has_departed"] = True
    pet["sold"] = True
    compute_line_prestige(state)

    msg = (
        f"{pet['name']} trafia do innej hodowli. Otrzymujesz {value} monet. "
        f"Wartość hodowlana utracona dla linii: {bval}. {quality_note}"
    )
    pet.setdefault("history", []).append(msg)
    return True, msg

def economy_projection(state):
    ensure_v12_state(state)
    active = [p for p in state["pets"] if not p.get("has_departed")]
    working = [p for p in active if p.get("status") == "Smok pracujący"]

    projected_work_income = 0
    for p in working:
        low, high, risk, reasons = work_income_range(p, p.get("work_type"))
        projected_work_income += int((low + high) / 2)

    upkeep = upkeep_breakdown(state)
    prestige = compute_line_prestige(state)
    bonus = line_head_bonus(state)
    # Prestige is not a money printer; it is a small stabilizer.
    prestige_income = 1 if prestige >= 35 else 0
    prestige_income += 1 if prestige >= 70 else 0

    income = projected_work_income + bonus + prestige_income
    net = income - upkeep["total"]

    return {
        "income": income,
        "work_income": projected_work_income,
        "line_head_bonus": bonus,
        "prestige_income": prestige_income,
        "upkeep": upkeep["total"],
        "upkeep_breakdown": upkeep,
        "net": net,
        "working": len(working),
        "young": upkeep["young_count"],
        "eggs": upkeep["egg_count"],
        "active": upkeep["active_count"],
        "line_prestige": prestige,
        "market_saturation": state.get("market_saturation", 0),
    }

def appraise_dragon(state, pet, level):
    ensure_v12_state(state)
    current = pet.get("knowledge_level", 0)
    if level <= current:
        return False, f"{pet['name']} ma już ten poziom rozpoznania albo lepszy."

    costs = {1: 10, 2: 22, 3: 45}
    cost = costs[level]
    if state.get("coins", 0) < cost:
        return False, f"Potrzeba {cost} monet."

    state["coins"] -= cost
    pet["knowledge_level"] = level

    traits = pet.get("hidden_traits", [])
    revealed = pet.setdefault("revealed_hidden_traits", [])

    if level == 3 and traits:
        for t in traits[:2]:
            if t not in revealed:
                revealed.append(t)
    elif level == 2 and traits:
        t = traits[0]
        if t not in revealed and random.randint(1, 100) <= 45:
            revealed.append(t)

    if level == 1:
        price = current_sale_price(pet, state)
        pet["market_appraisal_price"] = price
        pet["market_appraisal_day"] = state.get("day")
        msg = (
            f"Rzeczoznawca ocenia {pet['name']}. W tej turze możesz sprzedać go za **{price} monet**. "
            f"Nasycenie rynku: {state.get('market_saturation', 0)}."
        )
    elif level == 2:
        bval = breeding_value(pet)
        prestige = compute_line_prestige(state)
        pet["breeding_report"] = (
            f"Wartość hodowlana: {bval}/120. "
            f"Prestiż linii: {prestige}/100. "
            f"{pet['name']} jest {'ważnym kandydatem do pracy nad linią' if bval >= 85 else 'raczej materiałem pomocniczym, nie fundamentem linii'}."
        )
        msg = f"Ocena hodowlana {pet['name']}: {pet['breeding_report']}"
    else:
        if revealed:
            lines = [format_trait_line(t) for t in revealed]
            pet["genetic_report"] = "\n".join(lines)
            msg = f"Test genetyczny {pet['name']} ujawnia: " + "; ".join(lines)
        else:
            pet["genetic_report"] = "Brak spektakularnych ukrytych cech. Stabilność też bywa wartością."
            msg = f"Test genetyczny {pet['name']} nie wykazał nic spektakularnego. To też jest informacja."

    pet.setdefault("history", []).append(msg)
    return True, msg


# ---------- V12.1 hotfix: missing temperament compatibility ----------

def temperament_compatibility(parent_a, parent_b):
    """
    Lightweight breeding-preview helper.
    Returns a readable compatibility label based on temperament pairing.
    This is intentionally simple and does not change breeding mechanics.
    """
    a = parent_a.get("temperament", "")
    b = parent_b.get("temperament", "")

    if not a or not b:
        return "nieznana"

    if a == b:
        if a in ["dziki", "złośliwy", "wyrachowany"]:
            return "iskrząca — duży potencjał, ale trudne prowadzenie"
        if a in ["przywiązany", "leniwy", "ciekawski"]:
            return "łagodna — stabilna, ale bez wielkiego napięcia"
        return "spójna"

    strong_pairs = {
        frozenset(["dumny", "wyrachowany"]),
        frozenset(["ciekawski", "dziki"]),
        frozenset(["przywiązany", "lękliwy"]),
        frozenset(["dumny", "złośliwy"]),
    }
    risky_pairs = {
        frozenset(["dziki", "lękliwy"]),
        frozenset(["złośliwy", "lękliwy"]),
        frozenset(["wyrachowany", "przywiązany"]),
        frozenset(["leniwy", "dziki"]),
    }
    funny_pairs = {
        frozenset(["leniwy", "złośliwy"]),
        frozenset(["ciekawski", "wyrachowany"]),
        frozenset(["dumny", "przywiązany"]),
    }

    pair = frozenset([a, b])
    if pair in strong_pairs:
        return "wysoka — cechy mogą ciekawie zagrać"
    if pair in risky_pairs:
        return "ryzykowna — możliwe napięcia i kapryśne potomstwo"
    if pair in funny_pairs:
        return "dziwna, ale obiecująca"
    return "neutralna"

def breeding_preview(parent_a, parent_b):
    life_a = life_score(parent_a)
    life_b = life_score(parent_b)
    fert_a = parent_a["genotype"].get("fertility", 50)
    fert_b = parent_b["genotype"].get("fertility", 50)
    prep_bonus = parent_a.get("prep_level", 0) * 7 + parent_b.get("prep_level", 0) * 3
    effects = hidden_trait_effects(parent_a.get("hidden_traits", []) + parent_b.get("hidden_traits", []))

    chance = 35 + int((fert_a + fert_b) / 8) + int((life_a + life_b) / 8) - int((parent_a["stress"] + parent_b["stress"]) / 4)
    chance += prep_bonus + effects["egg_chance"]
    chance = clamp(chance, 5, 95)

    value_low, value_high = offspring_value_range(parent_a, parent_b, known_only=True)
    visible_mix = len({
        parent_a.get("phenotype", {}).get("color"),
        parent_b.get("phenotype", {}).get("color"),
        parent_a.get("phenotype", {}).get("pattern"),
        parent_b.get("phenotype", {}).get("pattern"),
    })
    bpot = int((breeding_value(parent_a) + breeding_value(parent_b)) / 2)

    return {
        "egg_chance": chance,
        "multi_egg": "możliwa" if (fert_a + fert_b) > 115 else "mało prawdopodobna",
        "value_low": value_low,
        "value_high": value_high,
        "rare_potential": "wysoki" if effects["rarity"] > 10 or bpot >= 90 or visible_mix >= 4 else "średni" if (parent_a["genotype"].get("rarity", 0) + parent_b["genotype"].get("rarity", 0)) > 100 else "niski",
        "hidden_risk": "wysokie" if effects["risk"] > 15 else "średnie" if effects["risk"] > 5 else "niskie",
        "compatibility": temperament_compatibility(parent_a, parent_b),
        "line_potential": bpot,
    }

def migrate_v6_state(state):
    for pet in state.get("pets", []):
        ensure_v6_pet_fields(pet, state)
    state.setdefault("status_feed", [])
    state.setdefault("market_saturation", 0)
    state.setdefault("total_sales", 0)
    state.setdefault("quality_sales", 0)
    state.setdefault("line_prestige", 0)
    state.setdefault("line_name", "Nienazwana linia")
    return state

def sale_button_label(pet, state=None):
    if has_market_appraisal(pet, state):
        return f"Sprzedaj za {pet['market_appraisal_price']} monet"
    return "Sprzedaj bez wyceny"

def visible_sale_text(pet, state=None):
    if has_market_appraisal(pet, state):
        return f"{pet['market_appraisal_price']} monet"
    if state is not None:
        return f"nieznana — wycena pokaże cenę tej tury; rynek: {state.get('market_saturation', 0)}"
    return "nieznana — wykonaj wycenę rynkową"


# ---------- V13: core loop redesign — hatchlings, work economy, premium breeding ----------

def ensure_v13_egg_fields(egg, state=None):
    egg.setdefault("name", "")
    egg.setdefault("initial_hatch_in", egg.get("hatch_in", 3))
    egg.setdefault("promise", "zwykłe")
    egg.setdefault("omen", "jajo rozwija się spokojnie")
    egg.setdefault("origin_story", "Jajo złożone w hodowli.")
    egg.setdefault("parent_ids", [])
    return egg

def ensure_v13_state(state):
    migrate_v6_state(state)
    state.setdefault("market_saturation", 0)
    state.setdefault("total_sales", 0)
    state.setdefault("quality_sales", 0)
    state.setdefault("line_prestige", 0)
    state.setdefault("line_name", "Nienazwana linia")
    for egg in state.get("eggs", []):
        ensure_v13_egg_fields(egg, state)
    return state

def upkeep_breakdown(state):
    ensure_v13_state(state)
    active = [p for p in state.get("pets", []) if not p.get("has_departed")]
    young = [p for p in active if p.get("stage") == "młodość"]
    adults = [p for p in active if p.get("stage") == "dorosłość"]
    old = [p for p in active if p.get("stage") == "starość"]
    eggs = state.get("eggs", [])

    active_count = len(active)
    # v13: every dragon costs something, and large farms cost increasingly more.
    base_active = active_count
    scale_tax = max(0, active_count - 4) + max(0, active_count - 8)
    young_extra = len(young)  # young need attention and training
    old_extra = len(old)      # old dragons need care
    egg_cost = len(eggs)
    total = base_active + scale_tax + young_extra + old_extra + egg_cost

    return {
        "active_count": active_count,
        "young_count": len(young),
        "adult_count": len(adults),
        "old_count": len(old),
        "egg_count": len(eggs),
        "base_active": base_active,
        "scale_tax": scale_tax,
        "young_extra": young_extra,
        "old_extra": old_extra,
        "egg_cost": egg_cost,
        "total": total,
    }

def work_affinity(pet, work_type):
    ensure_v6_pet_fields(pet)
    ph = pet.get("phenotype", {})
    genotype = pet.get("genotype", {})
    temperament = pet.get("temperament")
    color = ph.get("color")
    size = ph.get("size")
    horns = ph.get("horns")
    pattern = ph.get("pattern")
    stage = pet.get("stage")
    score = 0
    reasons = []

    def add(points, reason):
        nonlocal score, reasons
        score += points
        reasons.append(reason)

    if stage == "młodość":
        add(-3, "młody smok może pracować tylko lekko")
    elif stage == "starość":
        add(-2, "stary smok pracuje ostrożniej")
    if life_score(pet) < 50:
        add(-3, "słaba kondycja obniża wydajność")
    if pet.get("bond", 0) >= 60:
        add(2, "wysoka więź poprawia współpracę")

    if work_type == "transport ciężkich ładunków":
        if size in ["duży", "krępy"]:
            add(6, "rozmiar pomaga w transporcie")
        if genotype.get("immunity", 50) > 65:
            add(2, "odporność pomaga znosić wysiłek")
        if temperament == "leniwy":
            add(-3, "leniwy temperament obniża tempo")
    elif work_type == "ogrzewanie miejskiej łaźni":
        if color in ["rdzawy", "złoty", "miedziany", "karminowy", "bursztynowy"]:
            add(5, "ciepła linia dobrze pasuje do pracy przy ogniu")
        if temperament == "złośliwy":
            add(-2, "złośliwość zwiększa ryzyko incydentu")
    elif work_type == "praca przy kuźni":
        if color in ["czarny", "rdzawy", "miedziany", "stalowy", "dymny"]:
            add(5, "fenotyp dobrze pasuje do kuźni")
        if horns in ["zakrzywione rogi", "asymetryczne rogi", "baranie rogi", "koronne rogi"]:
            add(2, "rogi pomagają przy pracy fizycznej")
    elif work_type == "pilnowanie karawany":
        if size in ["duży", "krępy"]:
            add(3, "duży smok odstrasza napastników")
        if temperament in ["dumny", "wyrachowany", "dziki"]:
            add(4, "charakter dobrze pasuje do ochrony")
    elif work_type == "stróżowanie przy składzie kupieckim":
        if temperament in ["wyrachowany", "przywiązany", "dumny"]:
            add(4, "ten temperament dobrze znosi pilnowanie")
        if temperament == "ciekawski":
            add(-1, "ciekawość przeszkadza przy nudnym stróżowaniu")
    elif work_type == "pilnowanie piwnicy z winem":
        if temperament in ["leniwy", "przywiązany", "wyrachowany"]:
            add(4, "dobrze nadaje się do spokojnego pilnowania")
        if color in ["miedziany", "rdzawy", "bursztynowy"]:
            add(1, "pasuje klimatem do piwnicy")
    elif work_type == "nocny zwiad":
        if temperament in ["dziki", "ciekawski", "wyrachowany"]:
            add(5, "temperament pomaga w zwiadzie")
        if color in ["czarny", "granatowy", "dymny", "szafirowy"]:
            add(3, "ciemny fenotyp pomaga nocą")
    elif work_type == "przenoszenie wiadomości":
        if size in ["mały", "smukły"]:
            add(4, "lekka budowa pomaga w szybkim locie")
        if temperament in ["ciekawski", "przywiązany"]:
            add(2, "łatwiej wraca do hodowli")
    elif work_type == "odstraszanie gołębi z wieży ratuszowej":
        if temperament in ["złośliwy", "ciekawski"]:
            add(4, "ma do tej pracy niepokojący entuzjazm")
        if pattern in ["w pręgi", "z maską na pysku"]:
            add(1, "wygląda wystarczająco teatralnie")
    else:
        add(0, "brak szczególnej predyspozycji")

    if genotype.get("rarity", 0) > 80 and work_type in ["pilnowanie karawany", "stróżowanie przy składzie kupieckim", "nocny zwiad"]:
        add(1, "rzadkość robi wrażenie")
    return score, reasons

def work_income_range(pet, work_type=None):
    if work_type is None:
        _, work_type, _ = best_work_for_dragon(pet)
    score, reasons = work_affinity(pet, work_type)
    base = 5 + max(0, score)
    if pet.get("stage") == "młodość":
        base = int(base * 0.55)
    elif pet.get("stage") == "starość":
        base = int(base * 0.75)
    if pet.get("status") == "Reproduktor / Matka linii":
        base -= 1  # line heads are too valuable to exploit at full pace
    if life_score(pet) < 45:
        base -= 3
    low = max(1, base - 2)
    high = max(low + 1, base + 3)
    risk = "wysokie" if score < 0 or life_score(pet) < 45 else "średnie" if score < 5 else "niskie"
    return low, high, risk, reasons

def working_income_this_turn(pet):
    if pet.get("status") != "Smok pracujący":
        return 0, None
    work = pet.get("work_type")
    if not work:
        _, work, _ = best_work_for_dragon(pet)
        pet["work_type"] = work
    low, high, risk, reasons = work_income_range(pet, work)
    income = random.randint(low, high)

    # v13: work finances the kennel, but it has a real cost.
    if pet.get("stage") == "młodość":
        pet["energy"] = clamp(pet["energy"] - random.randint(3, 7))
        pet["stress"] = clamp(pet["stress"] + random.randint(1, 5))
    else:
        pet["energy"] = clamp(pet["energy"] - random.randint(4, 10))
        pet["stress"] = clamp(pet["stress"] + random.randint(2, 7))
    pet["happiness"] = clamp(pet["happiness"] + random.randint(-3, 1))

    incident_chance = 7 if risk == "niskie" else 15 if risk == "średnie" else 27
    if pet.get("bond", 0) >= 60:
        incident_chance = max(3, incident_chance - 5)

    msg = f"{pet['name']} pracuje: {work}. Zarabia {income} monet. Ryzyko pracy: {risk}."
    if random.randint(1, 100) <= incident_chance:
        pet["stress"] = clamp(pet["stress"] + 8)
        pet["health"] = clamp(pet["health"] - random.randint(0, 4))
        msg += " Wrócił zmęczony i wyraźnie obrażony na ideę pracy zarobkowej."
    return income, msg

def line_head_bonus(state):
    heads = [p for p in state.get("pets", []) if not p.get("has_departed") and p.get("status") == "Reproduktor / Matka linii"]
    if not heads:
        return 0
    # Bigger as prestige, still capped as income.
    prestige_bonus = max([breeding_value(p) for p in heads], default=0) // 35
    return min(12, 3 + len(heads) * 2 + prestige_bonus)

def compute_line_prestige(state):
    ensure_v13_state(state)
    active = [p for p in state.get("pets", []) if not p.get("has_departed")]
    if not active:
        state["line_prestige"] = 0
        return 0
    values = sorted([breeding_value(p) for p in active], reverse=True)
    top = values[:3]
    top_score = sum(top) / max(1, len(top))
    line_heads = [p for p in active if p.get("status") == "Reproduktor / Matka linii" or p.get("line_head")]
    head_bonus = max([breeding_value(p) for p in line_heads], default=0) * 0.30
    generations = max([p.get("generation", 1) for p in active], default=1)
    diversity = len(set((p.get("phenotype", {}).get("color"), p.get("phenotype", {}).get("pattern")) for p in active))
    bound_bonus = len([p for p in active if p.get("is_bound_forever")]) * 2
    prestige = int(top_score * 0.43 + head_bonus + generations * 2 + diversity * 1.5 + bound_bonus)
    state["line_prestige"] = clamp(prestige, 0, 100)
    return state["line_prestige"]

def economy_projection(state):
    ensure_v13_state(state)
    active = [p for p in state["pets"] if not p.get("has_departed")]
    working = [p for p in active if p.get("status") == "Smok pracujący"]
    projected_work_income = 0
    for p in working:
        low, high, risk, reasons = work_income_range(p, p.get("work_type"))
        projected_work_income += int((low + high) / 2)

    upkeep = upkeep_breakdown(state)
    prestige = compute_line_prestige(state)
    bonus = line_head_bonus(state)
    prestige_income = 1 if prestige >= 35 else 0
    prestige_income += 1 if prestige >= 70 else 0

    income = projected_work_income + bonus + prestige_income
    net = income - upkeep["total"]
    return {
        "income": income,
        "work_income": projected_work_income,
        "line_head_bonus": bonus,
        "prestige_income": prestige_income,
        "upkeep": upkeep["total"],
        "upkeep_breakdown": upkeep,
        "net": net,
        "working": len(working),
        "young": upkeep["young_count"],
        "eggs": upkeep["egg_count"],
        "active": upkeep["active_count"],
        "line_prestige": prestige,
        "market_saturation": state.get("market_saturation", 0),
    }

def lifecycle_info(pet):
    age = pet.get("age_days", 0)
    stage = pet.get("stage", get_stage(age))
    if stage == "młodość":
        next_stage = "dorosłość"
        target = 6
    elif stage == "dorosłość":
        next_stage = "starość"
        target = 32
    else:
        next_stage = "odejście / związanie"
        target = 44
    days = max(0, target - age)
    warning = None
    if stage == "dorosłość" and days <= 3:
        warning = "Smok zbliża się do starości. To moment na decyzje o linii, więzi i sukcesji."
    if stage == "starość" and not pet.get("is_bound_forever") and age >= 40:
        warning = "Smok jest w późnej starości. Jeśli ma zostać z hodowlą na zawsze, nie zwlekaj."
    return {"stage": stage, "next_stage": next_stage, "days_to_next": days, "warning": warning}

def breeding_preview(parent_a, parent_b):
    if parent_a.get("stage") == "młodość" or parent_b.get("stage") == "młodość":
        return {
            "egg_chance": 0,
            "multi_egg": "niemożliwa",
            "value_low": 0,
            "value_high": 0,
            "rare_potential": "brak — młode smoki nie mogą się rozmnażać",
            "hidden_risk": "brak",
            "compatibility": "blokada wieku",
            "line_potential": 0,
        }

    life_a = life_score(parent_a)
    life_b = life_score(parent_b)
    fert_a = parent_a["genotype"].get("fertility", 50)
    fert_b = parent_b["genotype"].get("fertility", 50)
    prep_bonus = parent_a.get("prep_level", 0) * 8 + parent_b.get("prep_level", 0) * 4
    effects = hidden_trait_effects(parent_a.get("hidden_traits", []) + parent_b.get("hidden_traits", []))
    old_penalty = 0
    for p in [parent_a, parent_b]:
        if p.get("stage") == "starość":
            old_penalty += 10

    chance = 30 + int((fert_a + fert_b) / 8) + int((life_a + life_b) / 8) - int((parent_a["stress"] + parent_b["stress"]) / 4)
    chance += prep_bonus + effects["egg_chance"] - old_penalty
    chance = clamp(chance, 5, 95)

    value_low, value_high = offspring_value_range(parent_a, parent_b, known_only=True)
    visible_mix = len({
        parent_a.get("phenotype", {}).get("color"),
        parent_b.get("phenotype", {}).get("color"),
        parent_a.get("phenotype", {}).get("pattern"),
        parent_b.get("phenotype", {}).get("pattern"),
    })
    bpot = int((breeding_value(parent_a) + breeding_value(parent_b)) / 2)
    long_hatch_hint = "możliwy dłuższy czas wykluwania" if bpot >= 85 or effects["rarity"] > 10 else "raczej standardowy czas wykluwania"

    return {
        "egg_chance": chance,
        "multi_egg": "możliwa" if (fert_a + fert_b) > 125 else "mało prawdopodobna",
        "value_low": value_low,
        "value_high": value_high,
        "rare_potential": "wysoki" if effects["rarity"] > 10 or bpot >= 90 or visible_mix >= 4 else "średni" if (parent_a["genotype"].get("rarity", 0) + parent_b["genotype"].get("rarity", 0)) > 100 else "niski",
        "hidden_risk": "wysokie" if effects["risk"] > 15 else "średnie" if effects["risk"] > 5 else "niskie",
        "compatibility": temperament_compatibility(parent_a, parent_b),
        "line_potential": bpot,
        "hatch_hint": long_hatch_hint,
    }

def hatch_egg_message(egg, dragon):
    promise = egg.get("promise", "zwykłe")
    name = dragon.get("name", "smok")
    ph = dragon.get("phenotype", {})
    desc = f"{ph.get('size', '')}, {ph.get('color', '')} smok {ph.get('pattern', '')}".strip()
    if promise in ["wyjątkowe", "dziwne"]:
        return (
            f"🥚 **Wyklucie!** Jajo pęka po {egg.get('initial_hatch_in', '?')} dniach. "
            f"Przez chwilę hodowla cichnie. Wykluwa się **{name}** — {desc}. "
            f"To było jajo: **{promise}**."
        )
    if promise == "obiecujące":
        return f"🥚 **Wyklucie:** z obiecującego jaja wykluwa się **{name}** — {desc}."
    return f"🥚 Z jaja wykluwa się **{name}** — {desc}."

def advance_day(state):
    from models import egg_to_dragon
    ensure_v13_state(state)
    state["day"] += 1
    reports = []

    for pet in state["pets"]:
        if pet.get("has_departed"):
            continue

        pet["age_days"] += 1
        old_stage = pet["stage"]
        pet["stage"] = get_stage(pet["age_days"])

        # Slower decay than early MVP, because lives are longer.
        pet["health"] = clamp(pet["health"] - random.randint(0, 2))
        pet["happiness"] = clamp(pet["happiness"] - random.randint(0, 3))
        pet["energy"] = clamp(pet["energy"] - random.randint(0, 3))
        pet["stress"] = clamp(pet["stress"] + random.randint(0, 3))

        if old_stage != pet["stage"]:
            msg = f"{pet['name']} wszedł w etap: {pet['stage']}."
            pet["history"].append(msg)
            reports.append("🐉 " + msg)

        # Old dragons leave later, giving time for succession.
        if pet["stage"] == "starość" and pet["age_days"] > 44 and not pet.get("is_bound_forever"):
            departure_chance = max(5, 18 - int(pet.get("bond", 0) / 7))
            if random.randint(1, 100) <= departure_chance:
                pet["has_departed"] = True
                msg = f"{pet['name']} odszedł w dzikość. Nie wyglądało to jak śmierć. Bardziej jak decyzja."
                pet["history"].append(msg)
                reports.append("🐉 " + msg)
                continue

        need = dominant_need(pet)
        report = need_report(pet, need)
        pet["life_score_cache"] = life_score(pet)
        reports.append(f"### {pet['name']}\n{report}")

    work_income = 0
    work_msgs = []
    for pet in state["pets"]:
        if pet.get("has_departed"):
            continue
        ensure_v6_pet_fields(pet, state)
        if pet.get("status") == "Smok pracujący":
            income, msg = working_income_this_turn(pet)
            work_income += income
            if msg:
                work_msgs.append("🛠 " + msg)
        elif pet.get("status") == "W dzikości":
            if random.randint(1, 100) <= 18:
                pet["genotype"]["mutation"] = clamp(pet["genotype"].get("mutation", 5) + 1)
                msg = f"🌲 {pet['name']} wraca z dzikości z pyłem pod łuskami. Coś w tej linii minimalnie się poruszyło."
                pet.setdefault("history", []).append(msg)
                work_msgs.append(msg)
        elif pet.get("status") == "Odpoczynek":
            pet["energy"] = clamp(pet["energy"] + random.randint(5, 10))
            pet["stress"] = clamp(pet["stress"] - random.randint(4, 9))
            pet["health"] = clamp(pet["health"] + random.randint(0, 3))

    hatch_msgs = []
    remaining_eggs = []
    for egg in state.get("eggs", []):
        ensure_v13_egg_fields(egg, state)
        egg["hatch_in"] = int(egg.get("hatch_in", 1)) - 1
        if egg["hatch_in"] <= 0:
            baby = egg_to_dragon(egg, name=egg.get("name") or None)
            state["pets"].append(baby)
            for parent_id in egg.get("parent_ids", []):
                for p in state["pets"]:
                    if p.get("id") == parent_id:
                        p.setdefault("children", []).append(baby["id"])
            hatch_msgs.append(hatch_egg_message(egg, baby))
        else:
            remaining_eggs.append(egg)
    state["eggs"] = remaining_eggs

    eco = economy_projection(state)
    actual_income = work_income + eco.get("line_head_bonus", 0) + eco.get("prestige_income", 0)
    upkeep = eco["upkeep"]
    net = actual_income - upkeep
    state["coins"] = max(0, state.get("coins", 0) + net)

    for msg in work_msgs:
        reports.append(msg)

    if net != 0 or actual_income or upkeep:
        ub = eco.get("upkeep_breakdown", {})
        sign = "+" if net > 0 else ""
        reports.append(
            f"**💰 Ekonomia hodowli:** {sign}{net} monet "
            f"(🛠 praca {work_income}, 👑 głowa linii {eco.get('line_head_bonus', 0)}, "
            f"🏛 prestiż {eco.get('prestige_income', 0)}, utrzymanie {upkeep}: "
            f"aktywne {ub.get('base_active', 0)}, skala +{ub.get('scale_tax', 0)}, "
            f"młode +{ub.get('young_extra', 0)}, stare +{ub.get('old_extra', 0)}, jaja +{ub.get('egg_cost', 0)})."
        )

    reports.extend(hatch_msgs)
    compute_line_prestige(state)
    return reports, hatch_msgs

def set_egg_name(state, egg_id, name):
    ensure_v13_state(state)
    for egg in state.get("eggs", []):
        if egg.get("id") == egg_id:
            egg["name"] = str(name).strip()
            return True, f"Jajo otrzymuje imię robocze: **{egg['name'] or 'bez imienia'}**."
    return False, "Nie znaleziono jaja."

# Override migration at the very end.
def migrate_v6_state(state):
    for pet in state.get("pets", []):
        ensure_v6_pet_fields(pet, state)
    state.setdefault("status_feed", [])
    state.setdefault("market_saturation", 0)
    state.setdefault("total_sales", 0)
    state.setdefault("quality_sales", 0)
    state.setdefault("line_prestige", 0)
    state.setdefault("line_name", "Nienazwana linia")
    for egg in state.get("eggs", []):
        ensure_v13_egg_fields(egg, state)
    return state


# ---------- v14 gameplay & genetics overrides ----------

VISIBLE_TRAIT_KEYS = ["color", "pattern", "eyes", "horns", "size", "temperament"]

def log_telemetry(state, key, amount=1):
    state.setdefault("telemetry", {})
    state["telemetry"][key] = state["telemetry"].get(key, 0) + amount

def telemetry_snapshot(state):
    state.setdefault("telemetry", {})
    return state["telemetry"]

def ensure_v6_pet_fields(pet, state=None):
    pet.setdefault("status", "W hodowli")
    pet.setdefault("work_type", None)
    pet.setdefault("line_head", pet.get("status") == "Reproduktor / Matka linii")
    pet.setdefault("market_appraisal_price", None)
    pet.setdefault("market_appraisal_day", None)
    pet.setdefault("breeding_report", None)
    pet.setdefault("genetic_report", None)
    pet.setdefault("revealed_hidden_traits", [])
    pet.setdefault("hidden_traits", [])
    pet.setdefault("carrier_genes", {k: pet.get("genotype", {}).get(k) for k in VISIBLE_TRAIT_KEYS})
    pet.setdefault("appraisal_flags", {"market": False, "breeding": False, "genetic": False})
    return pet

def migrate_v6_state(state):
    for pet in state.get("pets", []):
        ensure_v6_pet_fields(pet, state)
    state.setdefault("status_feed", [])
    state.setdefault("telemetry", {})
    state.setdefault("inline_notice", "")
    return state

def trait_strength_label(count):
    if count >= 4:
        return "bardzo wysoka"
    if count >= 3:
        return "wysoka"
    if count >= 2:
        return "średnia"
    return "niska"

def get_all_alleles(pet, key):
    ensure_v6_pet_fields(pet)
    expressed = pet.get("genotype", {}).get(key)
    carried = pet.get("carrier_genes", {}).get(key, expressed)
    return [expressed, carried]

def inheritance_summary(parent_a, parent_b):
    lines = []
    labels = {
        "eyes": "Oczy",
        "color": "Kolor",
        "pattern": "Wzór",
        "horns": "Rogi",
        "size": "Sylwetka",
    }
    for key in ["eyes", "color", "pattern", "horns", "size"]:
        pool = get_all_alleles(parent_a, key) + get_all_alleles(parent_b, key)
        counts = {}
        for v in pool:
            counts[v] = counts.get(v, 0) + 1
        top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:2]
        for val, cnt in top:
            lines.append(f"{labels[key]} — **{val}**: {trait_strength_label(cnt)} szansa")
    return lines[:8]

def carrier_report_lines(pet):
    ensure_v6_pet_fields(pet)
    lines = []
    labels = {
        "color": "kolor",
        "pattern": "wzór",
        "eyes": "oczy",
        "horns": "rogi",
        "size": "sylwetka",
        "temperament": "temperament",
    }
    for key in VISIBLE_TRAIT_KEYS:
        expressed = pet.get("genotype", {}).get(key)
        carried = pet.get("carrier_genes", {}).get(key, expressed)
        if carried and carried != expressed:
            lines.append(f"Niesie ukrytą cechę: **{labels[key]} — {carried}**.")
    return lines

def line_head_effect_text(state, pet):
    if pet.get("status") != "Reproduktor / Matka linii":
        return "Ten smok nie jest obecnie głową linii."
    prestige = compute_line_prestige(state)
    return (
        f"Głowa linii: wzmacnia prestiż hodowli (teraz około {prestige}/100), "
        f"lekko stabilizuje dziedziczenie i podnosi rzadkość potomstwa."
    )

def rest_effect_text(pet):
    return "Odpoczynek: zwykle +5 do +10 energii, -4 do -9 stresu i czasem lekka poprawa zdrowia w kolejnej turze."

def stat_impact_lines(pet):
    return [
        f"Zdrowie wpływa na life score i bezpieczeństwo pracy.",
        f"Energia wpływa na wydajność pracy i gotowość do schadzki.",
        f"Stres obniża szanse na jaja i zwiększa ryzyko problemów.",
        f"Szczęście i więź pomagają utrzymać stabilne zachowanie.",
    ]

def has_market_appraisal(pet, state=None):
    ensure_v6_pet_fields(pet, state)
    if pet.get("market_appraisal_price") is None:
        return False
    if state is not None and pet.get("market_appraisal_day") != state.get("day"):
        return False
    return True

def visible_sale_text(pet, state=None):
    if has_market_appraisal(pet, state):
        return f"{pet.get('market_appraisal_price')} monet"
    return "nieznana — wykonaj wycenę rynkową"

def sell_dragon(state, pet):
    ensure_v6_pet_fields(pet, state)
    if pet.get("has_departed"):
        return False, "Tego smoka już nie ma w hodowli."
    if pet.get("is_bound_forever"):
        return False, f"{pet['name']} jest związany z hodowlą na zawsze. Nie da się go sprzedać."

    value = current_sale_price(pet, state)
    state["coins"] += value
    pet["has_departed"] = True
    pet["sold"] = True
    state["market_saturation"] = min(100, state.get("market_saturation", 0) + 3)
    log_telemetry(state, "sell")
    if has_market_appraisal(pet, state):
        log_telemetry(state, "sell_after_appraisal")
    else:
        log_telemetry(state, "sell_without_appraisal")
    msg = f"{pet['name']} trafia do innej hodowli za **{value} monet**. Przez chwilę wygląda, jakby zapamiętywał drogę powrotną."
    pet.setdefault("history", []).append(msg)
    state["inline_notice"] = msg
    return True, msg

def appraise_dragon(state, pet, level):
    ensure_v6_pet_fields(pet, state)
    state.setdefault("inline_notice", "")
    costs = {1: 10, 2: 22, 3: 45}
    labels = {1: "wycenę rynkową", 2: "ocenę hodowlaną", 3: "test genetyczny"}
    cost = costs[level]
    if state.get("coins", 0) < cost:
        return False, f"Potrzeba {cost} monet."

    if level == 1:
        # appraisal can always be rerun, because player wants the current sale price.
        state["coins"] -= cost
        price = current_sale_price(pet, state)
        pet["market_appraisal_price"] = price
        pet["market_appraisal_day"] = state.get("day")
        pet["appraisal_flags"]["market"] = True
        pet["knowledge_level"] = max(pet.get("knowledge_level", 0), 1)
        log_telemetry(state, "market_appraisal")
        msg = f"Wycena rynkowa: {pet['name']} ma aktualną cenę sprzedaży **{price} monet**."
        pet.setdefault("history", []).append(msg)
        state["inline_notice"] = msg
        return True, msg

    if level == 2 and pet.get("breeding_report"):
        return False, f"{pet['name']} ma już wykonaną ocenę hodowlaną."
    if level == 3 and pet.get("genetic_report"):
        return False, f"{pet['name']} ma już wykonany test genetyczny."

    state["coins"] -= cost
    traits = pet.get("hidden_traits", [])
    revealed = pet.setdefault("revealed_hidden_traits", [])
    if level == 3 and traits:
        for t in traits[:2]:
            if t not in revealed:
                revealed.append(t)
    elif level == 2 and traits:
        t = traits[0]
        if t not in revealed and random.randint(1, 100) <= 45:
            revealed.append(t)

    if level == 2:
        sale_price = current_sale_price(pet, state)
        bval = breeding_value(pet)
        carriers = carrier_report_lines(pet)
        recommendation = "zostawić w linii" if bval >= sale_price or carriers else "rozważyć sprzedaż lub pracę"
        report = {
            "summary": (
                f"Ocena hodowlana: wartość hodowlana około **{bval}/120**. "
                f"Cena rynkowa w tej turze wynosi około **{sale_price} monet**. "
                f"Najbardziej sensowna decyzja: **{recommendation}**."
            ),
            "traits": [
                {"trait": "potencjał linii", "type": "strategiczny", "effects": f"wartość hodowlana {bval}/120", "description": recommendation},
            ] + [
                {"trait": "nosicielstwo", "type": "ukryte", "effects": "może wrócić w kolejnych pokoleniach", "description": line}
                for line in carriers[:3]
            ]
        }
        pet["breeding_report"] = report
        pet["knowledge_level"] = max(pet.get("knowledge_level", 0), 2)
        pet["appraisal_flags"]["breeding"] = True
        log_telemetry(state, "breeding_assessment")
        msg = f"Ocena hodowlana {pet['name']} gotowa. W raporcie widać bardziej sens linii niż samej sprzedaży."
        pet.setdefault("history", []).append(msg)
        state["inline_notice"] = msg
        return True, msg

    if level == 3:
        carrier_lines = carrier_report_lines(pet)
        revealed_traits = []
        for t in revealed:
            meta = trait_explanation(t)
            revealed_traits.append({
                "trait": t,
                "type": meta.get("type", "cecha"),
                "effects": meta.get("effects", ""),
                "description": meta.get("description", ""),
            })
        for line in carrier_lines[:4]:
            revealed_traits.append({
                "trait": "nosicielstwo",
                "type": "ukryta cecha linii",
                "effects": "może ujawnić się przy odpowiednim partnerze",
                "description": line,
            })
        if not revealed_traits:
            revealed_traits.append({
                "trait": "stabilny genotyp",
                "type": "neutralne",
                "effects": "brak wyraźnych niespodzianek",
                "description": "Ten smok nie pokazuje na razie silnych ukrytych anomalii.",
            })
        report = {
            "summary": "Test genetyczny ujawnia ukryte cechy i nosicielstwo. To najpewniejsza droga do planowania linii.",
            "traits": revealed_traits,
        }
        pet["genetic_report"] = report
        pet["knowledge_level"] = max(pet.get("knowledge_level", 0), 3)
        pet["appraisal_flags"]["genetic"] = True
        log_telemetry(state, "genetic_test")
        msg = f"Test genetyczny {pet['name']} gotowy. Raport ujawnia ukryte cechy i nosicielstwo."
        pet.setdefault("history", []).append(msg)
        state["inline_notice"] = msg
        return True, msg

    return False, f"Nie udało się wykonać: {labels[level]}."

def breeding_preview(parent_a, parent_b):
    if parent_a.get("stage") == "młodość" or parent_b.get("stage") == "młodość":
        return {
            "egg_chance": 0,
            "multi_egg": "niemożliwa",
            "value_low": 0,
            "value_high": 0,
            "rare_potential": "brak — młode smoki nie mogą się rozmnażać",
            "hidden_risk": "brak",
            "compatibility": "blokada wieku",
            "line_potential": 0,
            "hatch_hint": "brak",
            "trait_forecast": [],
        }

    life_a = life_score(parent_a)
    life_b = life_score(parent_b)
    fert_a = parent_a["genotype"].get("fertility", 50)
    fert_b = parent_b["genotype"].get("fertility", 50)
    prep_bonus = parent_a.get("prep_level", 0) * 8 + parent_b.get("prep_level", 0) * 4
    effects = hidden_trait_effects(parent_a.get("hidden_traits", []) + parent_b.get("hidden_traits", []))
    old_penalty = sum(10 for p in [parent_a, parent_b] if p.get("stage") == "starość")

    chance = 30 + int((fert_a + fert_b) / 8) + int((life_a + life_b) / 8) - int((parent_a["stress"] + parent_b["stress"]) / 4)
    chance += prep_bonus + effects["egg_chance"] - old_penalty
    chance = clamp(chance, 5, 95)

    value_low, value_high = offspring_value_range(parent_a, parent_b, known_only=True)
    visible_mix = len({
        parent_a.get("phenotype", {}).get("color"),
        parent_b.get("phenotype", {}).get("color"),
        parent_a.get("phenotype", {}).get("pattern"),
        parent_b.get("phenotype", {}).get("pattern"),
    })
    bpot = int((breeding_value(parent_a) + breeding_value(parent_b)) / 2)
    long_hatch_hint = "możliwy dłuższy czas wykluwania" if bpot >= 85 or effects["rarity"] > 10 else "raczej standardowy czas wykluwania"

    return {
        "egg_chance": chance,
        "multi_egg": "możliwa" if (fert_a + fert_b) > 125 else "mało prawdopodobna",
        "value_low": value_low,
        "value_high": value_high,
        "rare_potential": "wysoki" if effects["rarity"] > 10 or bpot >= 90 or visible_mix >= 4 else "średni" if (parent_a["genotype"].get("rarity", 0) + parent_b["genotype"].get("rarity", 0)) > 100 else "niski",
        "hidden_risk": "wysokie" if effects["risk"] > 15 else "średnie" if effects["risk"] > 5 else "niskie",
        "compatibility": temperament_compatibility(parent_a, parent_b),
        "line_potential": bpot,
        "hatch_hint": long_hatch_hint,
        "trait_forecast": inheritance_summary(parent_a, parent_b),
    }
