
import streamlit as st
import re

from save_load import load_state, save_state, reset_state
from content import describe_dragon, breeding_text
from game_logic import (
    advance_day, bind_forever,
    stable_market_value, sell_dragon, release_dragon,
    condition_label, mood_label, breeding_readiness_label,
    economy_projection, upkeep_breakdown, knowledge_label, appraise_dragon,
    breeding_preview, migrate_v6_state, DRAGON_STATUSES, set_dragon_status,
    best_work_for_dragon, work_income_range, WORK_TYPES,
    sale_button_label, visible_sale_text, has_market_appraisal,
    format_trait_line, lifecycle_info, full_recovery, full_recovery_cost,
    build_bond, bond_action_cost, compact_stage_rank,
    breeding_value, compute_line_prestige, set_egg_name,
    line_head_effect_text, rest_effect_text, stat_impact_lines,
    log_telemetry, telemetry_snapshot,
)
from breeding import generate_partner, breed_dragons
from models import egg_to_dragon, life_score
from avatar import render_dragon_png
try:
    from genealogy_renderer import render_genealogy_png
except Exception:
    render_genealogy_png = None

st.set_page_config(page_title="DRGN — hodowla smoków", page_icon="🐉", layout="wide")

# ---------- State ----------
if "state" not in st.session_state:
    st.session_state.state = load_state()

state = migrate_v6_state(st.session_state.state)
state.setdefault("external_parents", {})
state.setdefault("feed", [])
state.setdefault("starter_name_pending", False)
state.setdefault("onboarding_seen", bool(state.get("feed")))
state.setdefault("telemetry", {})
state.setdefault("inline_notice", "")
st.session_state.state = state

def log_t(event, amount=1):
    log_telemetry(state, event, amount)

if "current_view" not in st.session_state:
    st.session_state.current_view = "Hodowla"
if "selected_pet_id" not in st.session_state:
    st.session_state.selected_pet_id = None
if "selected_pet_ids" not in st.session_state:
    st.session_state.selected_pet_ids = []

def keep_current_view():
    if "main_view_radio" in st.session_state:
        st.session_state.current_view = st.session_state.main_view_radio

def add_feed(message):
    if not message:
        return
    if isinstance(message, list):
        for m in reversed(message):
            state["feed"].insert(0, m)
    else:
        state["feed"].insert(0, message)
    state["feed"] = state["feed"][:60]
    state["last_report"] = state["feed"][:10]

def active_pets():
    return [p for p in state.get("pets", []) if not p.get("has_departed")]

def get_pet_by_id(pet_id):
    for p in state.get("pets", []):
        if p.get("id") == pet_id:
            return p
    return None

def selected_pets():
    ids = st.session_state.get("selected_pet_ids", [])
    return [p for p in active_pets() if p.get("id") in ids]

def starter_pet():
    pets = active_pets()
    return pets[0] if pets else None

def onboarding_message():
    return (
        "🐉 **Pierwszy dzień hodowli.** Nadaj imię pierwszemu smokowi, obejrzyj jego cechy, "
        "sprawdź wycenę lub ocenę hodowlaną, wyślij go do pracy, daj mu odpocząć albo poszukaj partnera do linii."
    )


def render_report_block(report):
    """Render both old string reports and newer dict reports without crashing."""
    if not report:
        return
    if isinstance(report, str):
        st.write(report)
        return
    if isinstance(report, dict):
        if report.get("summary"):
            st.write(report.get("summary", ""))
        if report.get("traits"):
            for item in report.get("traits", []):
                if isinstance(item, dict):
                    st.write(
                        f"- **{item.get('trait', '')}** — {item.get('type', '')}. "
                        f"{item.get('effects', '')}. {item.get('description', '')}"
                    )
                else:
                    st.write(f"- {item}")
        # fallback for unknown dict shape
        if not report.get("summary") and not report.get("traits"):
            st.write(report)
        return
    st.write(str(report))


def economy_tooltip_text():
    eco = economy_projection(state)
    ub = eco.get("upkeep_breakdown", {})
    return (
        f"Bilans / dzień: {eco.get('net', 0)}. "
        f"Praca smoków: +{eco.get('work_income', eco.get('income', 0))}. "
        f"Bonus głowy linii: +{eco.get('line_head_bonus', 0)}. "
        f"Prestiż linii: {eco.get('line_prestige', 0)}/100; nasycenie rynku: {eco.get('market_saturation', 0)}. "
        f"Utrzymanie razem: -{eco.get('upkeep', 0)} "
        f"(aktywne -{ub.get('base_active', 0)}, skala hodowli -{ub.get('scale_tax', 0)}, "
        f"młode dodatkowo -{ub.get('young_extra', 0)}, stare dodatkowo -{ub.get('old_extra', 0)}, "
        f"jaja -{ub.get('egg_cost', 0)}). "
        "Masowa sprzedaż podobnych smoków obniża ceny. Wysoka jakość linii podnosi prestiż i pomaga w najlepszych ofertach."
    )

def feed_icon(text):
    t = str(text).lower()
    if "jajo" in t or "wyklu" in t: return "🥚"
    if "monet" in t or "ekonomia" in t or "zarabia" in t or "sprzeda" in t: return "💰"
    if "starość" in t or "odejd" in t or "warning" in t: return "⚠️"
    if "test genetyczny" in t or "gen" in t or "cech" in t: return "🧬"
    if "schadz" in t or "połączenie" in t: return "💞"
    if "dziko" in t: return "🌲"
    if "prac" in t or "kuź" in t or "karawan" in t or "zwiad" in t: return "🛠"
    return "🐉"

def short_feed_item(text, limit=115):
    raw = str(text).replace("\n", " ").replace("#", "").replace("*", "").strip()
    raw = " ".join(raw.split())
    if raw.lower().startswith("dzień"):
        return raw

    icon = feed_icon(raw)

    if "Ekonomia hodowli" in raw:
        m = re.search(r"Ekonomia hodowli:\s*([^\(]+)", raw)
        return f"💰 {m.group(1).strip() if m else 'bilans dnia zapisany'}"
    if "pracuje:" in raw and "Zarabia" in raw:
        name = raw.split(" pracuje:", 1)[0].replace("🛠", "").strip()
        money = re.search(r"Zarabia\s+(\d+)\s+monet", raw)
        return f"🛠 {name}: +{money.group(1)} monet" if money else f"🛠 {name} pracował"
    if "Wyklucie" in raw or "wykluwa się" in raw:
        match = re.search(r"\*\*(.*?)\*\*", str(text))
        return f"🥚 Wykluł się {match.group(1)}" if match else "🥚 Wykluł się smok"

    if len(raw) <= limit:
        return f"{icon} {raw}"

    # Avoid broken half-sentences in the blue bar.
    if "schadz" in raw.lower():
        return "💞 Schadzka zakończona — szczegóły w pełnym feedzie"
    if "odszedł" in raw.lower():
        return "🐉 Smok odszedł w dzikość"
    return f"{icon} {raw[: max(20, limit - 12)].rsplit(' ', 1)[0]}…"


def current_day_feed_items():
    feed = state.get("feed", [])
    items = []
    for item in feed:
        if items and str(item).strip().lower().startswith("## dzień"):
            break
        items.append(item)
        if len(items) >= 8:
            break
    return items

def action_feedback(message):
    if isinstance(message, list):
        msg = " · ".join(short_feed_item(m, 80) for m in message[:4])
    else:
        msg = short_feed_item(message, 160)
    st.toast(msg)

def do_next_day():
    # v13/v14: advance_day() already handles egg timers, hatching, adding babies,
    # parent-child links, economy and hatch feed messages.
    reports, hatch_msgs = advance_day(state)
    log_t("next_day")
    day_items = [f"## Dzień {state['day']}"] + reports
    add_feed(day_items)
    action_feedback(day_items[1:] if len(day_items) > 1 else day_items)
    save_state(state)
    keep_current_view()
    st.rerun()

def do_sell(pet):
    ok, msg = sell_dragon(state, pet)
    add_feed(msg)
    action_feedback(msg)
    if ok and st.session_state.selected_pet_id == pet.get("id"):
        remaining = active_pets()
        st.session_state.selected_pet_id = remaining[0]["id"] if remaining else None
    save_state(state)
    keep_current_view()
    st.rerun()

def do_release(pet):
    ok, msg = release_dragon(state, pet)
    if ok:
        log_t("release")
    add_feed(msg)
    action_feedback(msg)
    if ok and st.session_state.selected_pet_id == pet.get("id"):
        remaining = active_pets()
        st.session_state.selected_pet_id = remaining[0]["id"] if remaining else None
    save_state(state)
    keep_current_view()
    st.rerun()

def do_appraisal(pet, level):
    ok, msg = appraise_dragon(state, pet, level)
    add_feed(msg)
    action_feedback(msg)
    save_state(state)
    keep_current_view()
    st.rerun()

def do_full_recovery(pet):
    ok, msg = full_recovery(state, pet)
    if ok:
        log_t("full_recovery")
    add_feed(msg)
    action_feedback(msg)
    save_state(state)
    keep_current_view()
    st.rerun()

def do_build_bond(pet):
    ok, msg = build_bond(state, pet)
    if ok:
        log_t("build_bond")
    add_feed(msg)
    action_feedback(msg)
    save_state(state)
    keep_current_view()
    st.rerun()

# ---------- Top bar ----------
st.title("🐉 DRGN")
st.caption("Wersja v14 — genetyka, hodowla i playtest")

view_col, turn_col, day_col, money_col, count_col, utility_col = st.columns(
    [2.0, 1.15, 0.75, 1.05, 1.05, 0.8],
    gap="small",
)

with view_col:
    section = st.radio(
        "Widok",
        ["Hodowla", "Schadzki", "Genealogia"],
        horizontal=True,
        index=["Hodowla", "Schadzki", "Genealogia"].index(st.session_state.current_view)
        if st.session_state.current_view in ["Hodowla", "Schadzki", "Genealogia"] else 0,
        key="main_view_radio",
    )
    st.session_state.current_view = section

with turn_col:
    if st.button("⏭️ Następny dzień", type="primary", use_container_width=True):
        do_next_day()

eco = economy_projection(state)

with day_col:
    st.metric("Dzień", state.get("day", 1))

with money_col:
    st.metric("Monety", state.get("coins", 0), delta=f"{eco.get('net', 0)} / dzień", help=economy_tooltip_text())

with count_col:
    warning_count = sum(1 for p in active_pets() if lifecycle_info(p).get("warning"))
    prestige = economy_projection(state).get("line_prestige", 0)
    st.metric("Smoki / jaja", f"{len(active_pets())} / {len(state.get('eggs', []))}", delta=f"Prestiż {prestige}" if not warning_count else f"⚠️ {warning_count} · P {prestige}")

with utility_col:
    state["debug"] = st.checkbox("Debug", value=state.get("debug", False))
    util_a, util_b = st.columns(2)
    with util_a:
        if st.button("💾", help="Zapisz"):
            save_state(state)
            st.toast("Zapisano.")
    with util_b:
        if st.button("🧨", help="Reset gry"):
            st.session_state.state = reset_state()
            st.session_state.state.setdefault("feed", ["Pierwszy dzień hodowli. Wszystko pachnie kurzem, siarką i bardzo złymi decyzjami."])
            st.session_state.current_view = "Hodowla"
            st.session_state.selected_pet_id = None
            st.session_state.selected_pet_ids = []
            save_state(st.session_state.state)
            st.rerun()

feed_items = current_day_feed_items()
if not feed_items and state.get("day", 1) == 1:
    feed_items = [onboarding_message()]
if feed_items:
    visible_items = [short_feed_item(item) for item in feed_items if not str(item).strip().lower().startswith("## dzień")]
    if visible_items:
        st.info("  ·  ".join(visible_items[:5]))
    else:
        st.caption("Brak ważnych zdarzeń w ostatniej turze.")
else:
    st.caption("Feed jest pusty. Kliknij następny dzień albo wykonaj akcję.")

with st.expander("Pełny feed klimatyczny / historia", expanded=False):
    if not state.get("feed"):
        st.info("Feed jest pusty.")
    else:
        for item in state["feed"][:18]:
            st.markdown(item)
            st.divider()

# ---------- Starter onboarding ----------
if state.get("starter_name_pending") and starter_pet():
    first = starter_pet()
    with st.container(border=True):
        st.markdown("### 🐣 Nazwij pierwszego smoka")
        st.write(
            "To jest początek linii. Smok nie wygląda na pytanego o zgodę, ale najwyraźniej już tu mieszka."
        )
        col_name, col_btn = st.columns([2, 1])
        with col_name:
            starter_name = st.text_input(
                "Imię pierwszego smoka",
                value=first.get("name", ""),
                key="starter_name_input",
                placeholder="np. Zadra, Popiół, Kobalt albo coś zupełnie nierozsądnego",
            )
        with col_btn:
            st.write("")
            st.write("")
            if st.button("Zatwierdź imię", type="primary", use_container_width=True):
                new_name = starter_name.strip()
                if new_name:
                    old_name = first.get("name", "smok")
                    first["name"] = new_name
                    first.setdefault("history", []).append(f"Pierwszy smok otrzymał imię: {new_name}.")
                    state["starter_name_pending"] = False
                    state["onboarding_seen"] = True
                    add_feed(f"🐉 Pierwszy smok hodowli ma imię: **{new_name}**. {old_name} udaje, że to od początku był jego pomysł.")
                    save_state(state)
                    st.rerun()
                else:
                    st.warning("Wpisz imię albo zostaw losowe i kliknij przycisk poniżej.")
        if st.button("Zostaw losowe imię", use_container_width=True):
            state["starter_name_pending"] = False
            state["onboarding_seen"] = True
            add_feed(f"🐉 Pierwszy smok zostaje przy imieniu **{first.get('name', 'Smok')}**. Nie wygląda na szczególnie zaskoczonego.")
            save_state(state)
            st.rerun()


st.divider()

# ---------- Hodowla ----------
if section == "Hodowla":
    st.header("Hodowla")
    st.caption("Kompaktowa siatka smoków + panel wybranego smoka. Zaznacz kilka smoków, żeby wykonać akcję zbiorczą.")

    pets = active_pets()

    if not pets:
        st.error("Twoja linia wygasła. Ostatni smok odszedł albo został sprzedany.")
        st.write("To nie musi być koniec gry — raczej koniec jednej dynastii.")
        if st.button("🥚 Zacznij nową linię z dzikim jajem", type="primary"):
            from models import create_egg, new_genotype
            egg = create_egg([], new_genotype(wildness=20), generation=1, hatch_in=1)
            baby = egg_to_dragon(egg)
            baby["history"].append("Nowa linia zaczęła się od dzikiego jaja.")
            state["pets"].append(baby)
            state["coins"] = max(state.get("coins", 0), 30)
            st.session_state.selected_pet_id = baby["id"]
            add_feed(f"Nowa linia zaczyna się od dzikiego jaja. Wykluł się **{baby['name']}**.")
            save_state(state)
            st.rerun()
    else:
        if (
            not st.session_state.selected_pet_id
            or not get_pet_by_id(st.session_state.selected_pet_id)
            or get_pet_by_id(st.session_state.selected_pet_id).get("has_departed")
        ):
            st.session_state.selected_pet_id = pets[0]["id"]

        grid_col, detail_col = st.columns([2.45, 1.05], gap="medium")

        with grid_col:
            current_ids = [p["id"] for p in pets]
            st.session_state.selected_pet_ids = [
                pid for pid in st.session_state.get("selected_pet_ids", [])
                if pid in current_ids
            ]

            selected_ids = st.multiselect(
                "Zaznaczone smoki do akcji zbiorczych",
                options=current_ids,
                default=st.session_state.selected_pet_ids,
                format_func=lambda pid: get_pet_by_id(pid)["name"] if get_pet_by_id(pid) else pid,
                key="bulk_selection_multiselect",
            )
            st.session_state.selected_pet_ids = selected_ids

            with st.expander("Akcje zbiorcze", expanded=bool(selected_ids)):
                chosen = selected_pets()
                if not chosen:
                    st.caption("Zaznacz smoki, żeby wykonać akcję zbiorczą.")
                else:
                    st.write(f"Wybrano: **{len(chosen)}**")
                    bulk_status = st.selectbox("Status dla zaznaczonych", DRAGON_STATUSES, key="bulk_status")
                    if st.button("Zmień status zaznaczonym", use_container_width=True):
                        msgs = []
                        for p in chosen:
                            ok, msg = set_dragon_status(state, p, bulk_status)
                            msgs.append(msg)
                        add_feed(["**Akcja zbiorcza: zmiana statusu**"] + msgs)
                        save_state(state)
                        st.rerun()

                    not_appraised = [p for p in chosen if not has_market_appraisal(p, state)]
                    cost = 10 * len(not_appraised)
                    if st.button(f"Wycena zaznaczonych — {cost} monet", use_container_width=True, disabled=(cost == 0)):
                        if state["coins"] < cost:
                            st.error("Za mało monet.")
                        else:
                            msgs = []
                            for p in not_appraised:
                                ok, msg = appraise_dragon(state, p, 1)
                                msgs.append(msg)
                            add_feed(["**Akcja zbiorcza: wycena**"] + msgs)
                            save_state(state)
                            st.rerun()

                    sellable = [p for p in chosen if not p.get("is_bound_forever")]
                    if st.button("Sprzedaj zaznaczone", use_container_width=True, disabled=not bool(sellable)):
                        msgs = []
                        sold_ids = []
                        for p in sellable:
                            ok, msg = sell_dragon(state, p)
                            msgs.append(msg)
                            if ok:
                                sold_ids.append(p["id"])
                        st.session_state.selected_pet_ids = []
                        if st.session_state.selected_pet_id in sold_ids:
                            remaining = active_pets()
                            st.session_state.selected_pet_id = remaining[0]["id"] if remaining else None
                        add_feed(["**Akcja zbiorcza: sprzedaż**"] + msgs)
                        save_state(state)
                        st.rerun()

            def mini_card(pet):
                info = lifecycle_info(pet)
                selected = st.session_state.selected_pet_id == pet["id"]
                selected_mark = "▶ " if selected else ""
                checkbox_mark = "✓ " if pet["id"] in st.session_state.selected_pet_ids else ""

                with st.container(border=True):
                    st.image(render_dragon_png(pet, width=180, height=120), use_container_width=True)
                    if st.button(f"{selected_mark}{checkbox_mark}{pet['name']}", key=f"select_{pet['id']}", use_container_width=True):
                        st.session_state.selected_pet_id = pet["id"]
                        keep_current_view()
                        st.rerun()

                    warning = " ⚠️" if info.get("warning") else ""
                    st.caption(f"{pet.get('stage')} · gen. {pet.get('generation')} · {pet.get('status', 'W hodowli')}{warning}")
                    st.caption(f"Life {life_score(pet)}/100 · więź {pet.get('bond', 0)} · do {info['next_stage']}: {info['days_to_next']}")

                    checked = pet["id"] in st.session_state.selected_pet_ids
                    new_checked = st.checkbox("zaznacz", value=checked, key=f"check_{pet['id']}")
                    ids = set(st.session_state.selected_pet_ids)
                    if new_checked:
                        ids.add(pet["id"])
                    else:
                        ids.discard(pet["id"])
                    st.session_state.selected_pet_ids = list(ids)

            groups = [
                ("Starość / decyzje pilne", [p for p in pets if p.get("stage") == "starość"]),
                ("Dorosłe smoki", [p for p in pets if p.get("stage") == "dorosłość"]),
                ("Młode smoki", [p for p in pets if p.get("stage") == "młodość"]),
            ]

            for title, group in groups:
                if group:
                    st.subheader(title)
                    for row_start in range(0, len(group), 4):
                        cols = st.columns(4)
                        for idx, pet in enumerate(group[row_start:row_start + 4]):
                            with cols[idx]:
                                mini_card(pet)

            st.divider()
            st.subheader("Jaja — przyszłe smoki")
            eggs = state.get("eggs", [])
            if not eggs:
                st.caption("Brak jaj w hodowli.")
            else:
                for row_start in range(0, len(eggs), 3):
                    cols = st.columns(3)
                    for idx, egg in enumerate(eggs[row_start:row_start + 3]):
                        with cols[idx]:
                            with st.container(border=True):
                                promise = egg.get("promise", "zwykłe")
                                egg_name = egg.get("name") or "bez imienia"
                                st.markdown(f"### 🥚 {egg_name}")
                                st.write(f"**Wyklucie za:** {egg.get('hatch_in', '?')} tur")
                                st.caption(f"gen. {egg.get('generation', '?')} · {promise}")
                                st.caption(egg.get("omen", "jajo rozwija się spokojnie"))
                                if egg.get("parent_ids"):
                                    parent_names = []
                                    for pid in egg.get("parent_ids", []):
                                        pp = get_pet_by_id(pid)
                                        parent_names.append(pp["name"] if pp else "rodzic spoza hodowli")
                                    st.caption("Rodzice: " + " × ".join(parent_names))

                                new_egg_name = st.text_input(
                                    "Imię jaja",
                                    value=egg.get("name", ""),
                                    key=f"egg_name_{egg.get('id')}",
                                    placeholder="np. Popielne Jajo",
                                )
                                if st.button("Nadaj imię", key=f"save_egg_name_{egg.get('id')}", use_container_width=True):
                                    ok, msg = set_egg_name(state, egg.get("id"), new_egg_name)
                                    if ok:
                                        log_t("egg_named")
                                    add_feed(msg)
                                    save_state(state)
                                    st.rerun()

        with detail_col:
            pet = get_pet_by_id(st.session_state.selected_pet_id)
            if not pet:
                st.info("Wybierz smoka z siatki.")
            else:
                st.subheader(f"🐉 {pet['name']}")
                st.image(render_dragon_png(pet, width=320, height=220), use_container_width=True)
                st.write(describe_dragon(pet))

                info = lifecycle_info(pet)
                st.caption(
                    f"Etap: {pet.get('stage')} · Gen. {pet.get('generation')} · "
                    f"Status: {pet.get('status', 'W hodowli')} · Więź: {pet.get('bond', 0)}/100"
                )
                if info.get("warning"):
                    st.warning(info["warning"])

                st.write(
                    f"**Do: {info['next_stage']}** — {info['days_to_next']} tur · "
                    f"**Life:** {life_score(pet)}/100"
                )
                st.caption(f"Cena sprzedaży: {visible_sale_text(pet, state)}")
                st.progress(life_score(pet) / 100)

                with st.expander("Statystyki i ich znaczenie"):
                    st.write(
                        f"Zdrowie: {pet['health']} · Szczęście: {pet['happiness']} · "
                        f"Energia: {pet['energy']} · Stres: {pet['stress']}"
                    )
                    for line in stat_impact_lines(pet):
                        st.caption("• " + line)
                    if pet.get("status") == "Odpoczynek":
                        st.info(rest_effect_text(pet))
                    if pet.get("status") == "Reproduktor / Matka linii":
                        st.success(line_head_effect_text(state, pet))

                st.markdown("**Status smoka**")
                current_status = pet.get("status", "W hodowli")
                if current_status not in DRAGON_STATUSES:
                    current_status = "W hodowli"

                new_status = st.selectbox(
                    "Status",
                    DRAGON_STATUSES,
                    index=DRAGON_STATUSES.index(current_status),
                    key=f"status_detail_{pet['id']}",
                )
                if st.button("Zmień status", key=f"apply_status_detail_{pet['id']}", use_container_width=True):
                    ok, msg = set_dragon_status(state, pet, new_status)
                    if ok:
                        log_t("status_change")
                        if new_status == "Odpoczynek":
                            log_t("status_rest")
                        if new_status == "Reproduktor / Matka linii":
                            log_t("status_line_head")
                        if new_status == "Smok pracujący":
                            log_t("status_working")
                    add_feed(msg)
                    action_feedback(msg)
                    save_state(state)
                    st.rerun()

                if pet.get("status") == "Smok pracujący":
                    best_score, best_work, reasons = best_work_for_dragon(pet)
                    current_work = pet.get("work_type") or best_work
                    if current_work not in WORK_TYPES:
                        current_work = best_work
                    selected_work = st.selectbox(
                        "Rodzaj pracy",
                        WORK_TYPES,
                        index=WORK_TYPES.index(current_work),
                        key=f"work_detail_{pet['id']}",
                    )
                    if selected_work != pet.get("work_type"):
                        pet["work_type"] = selected_work
                        save_state(state)
                    low, high, risk, reasons = work_income_range(pet, selected_work)
                    st.caption(f"Przewidywany zarobek: {low}–{high} monet / turę · Ryzyko: {risk}")
                    if reasons:
                        st.caption("Predyspozycje: " + "; ".join(reasons[:3]))

                st.markdown("**Regeneracja i więź**")
                if st.button(f"Pełna kuracja — {full_recovery_cost(pet)} monet", key=f"recovery_detail_{pet['id']}", use_container_width=True):
                    do_full_recovery(pet)
                if st.button(f"Buduj więź — {bond_action_cost(pet)} monet", key=f"bond_detail_{pet['id']}", use_container_width=True):
                    do_build_bond(pet)

                st.markdown("**Wiedza**")
                if has_market_appraisal(pet, state):
                    st.success(f"✓ Aktualna wycena: {pet.get('market_appraisal_price')} monet")
                if st.button("Wycena rynkowa — 10 monet", key=f"appraise1_detail_{pet['id']}", use_container_width=True):
                    do_appraisal(pet, 1)
                if pet.get("breeding_report"):
                    st.success("✓ Ocena hodowlana")
                else:
                    st.caption("Ocena hodowlana podpowiada, czy zostawić smoka w linii, sprzedać czy przeznaczyć do pracy.")
                if st.button("Ocena hodowlana — 22", key=f"appraise2_detail_{pet['id']}", use_container_width=True):
                    do_appraisal(pet, 2)
                if pet.get("genetic_report"):
                    st.success("✓ Test genetyczny")
                else:
                    st.caption("Test genetyczny może ujawnić nosicielstwo ukrytych cech.")
                if st.button("Test genetyczny — 45", key=f"appraise3_detail_{pet['id']}", use_container_width=True):
                    do_appraisal(pet, 3)

                if pet.get("breeding_report"):
                    with st.expander("Raport oceny hodowlanej"):
                        render_report_block(pet.get("breeding_report"))

                if pet.get("genetic_report"):
                    with st.expander("Raport testu genetycznego"):
                        render_report_block(pet.get("genetic_report"))

                st.markdown("**Decyzje hodowlane**")
                if st.button(sale_button_label(pet, state), key=f"sell_detail_{pet['id']}", use_container_width=True):
                    do_sell(pet)
                if st.button("Wypuść w dzikość", key=f"release_detail_{pet['id']}", use_container_width=True):
                    do_release(pet)

                if pet.get("stage") == "starość" and not pet.get("is_bound_forever"):
                    if st.button("🔗 Zwiąż na zawsze", key=f"bind_detail_{pet['id']}", use_container_width=True):
                        ok, msg = bind_forever(state, pet)
                        if ok:
                            log_t("bind_forever")
                        add_feed(msg)
                        action_feedback(msg)
                        save_state(state)
                        st.rerun()
                with st.expander("Telemetria playtestu"):
                    t = telemetry_snapshot(state)
                    if not t:
                        st.caption("Brak danych playtestowych jeszcze.")
                    else:
                        for k, v in sorted(t.items()):
                            st.write(f"- {k}: {v}")

                if state.get("debug"):
                    with st.expander("Debug"):
                        st.json(pet)

# ---------- Schadzki ----------
elif section == "Schadzki":
    st.header("Schadzki")
    st.caption("Kompaktowy widok: smoki, prognoza i przycisk schadzki są widoczne wyżej.")

    adults = [p for p in active_pets() if p["stage"] in ["dorosłość", "starość"]]
    if not adults:
        st.info("Potrzebujesz dorosłego smoka. Młode smoki mogą pracować i dorastać, ale nie rozmnażają się.")
    else:
        top_left, top_right, forecast_col = st.columns([1.1, 1.1, 1.35], gap="medium")

        with top_left:
            st.subheader("Twój smok")
            selected_idx = st.selectbox(
                "Wybierz swojego smoka",
                range(len(adults)),
                format_func=lambda i: f"{adults[i]['name']} — {adults[i]['stage']} — gen. {adults[i]['generation']}",
                key="breeding_pet_select_v9",
            )
            parent = adults[selected_idx]
            c1, c2 = st.columns([0.38, 0.62])
            with c1:
                st.image(render_dragon_png(parent, width=160, height=110), use_container_width=True)
            with c2:
                st.markdown(f"### 🐉 {parent['name']}")
                st.caption(f"{parent.get('status', 'W hodowli')} · life {life_score(parent)}/100")
                st.caption(describe_dragon(parent))

        with top_right:
            st.subheader("Partner")
            pbtn1, pbtn2 = st.columns(2)
            with pbtn1:
                if st.button("🌲 Dziki", use_container_width=True):
                    st.session_state.partner = generate_partner("wild")
            with pbtn2:
                if st.button("🏛️ Hodowlany", use_container_width=True):
                    st.session_state.partner = generate_partner("npc")

            partner = st.session_state.get("partner")
            if partner:
                c1, c2 = st.columns([0.38, 0.62])
                with c1:
                    st.image(render_dragon_png(partner, width=160, height=110), use_container_width=True)
                with c2:
                    st.markdown(f"### 🐉 {partner['name']}")
                    st.caption(f"{partner.get('temperament')} · gen. {partner.get('generation')}")
                    st.caption(describe_dragon(partner))
            else:
                st.info("Wygeneruj partnera.")

        with forecast_col:
            st.subheader("Prognoza")
            partner = st.session_state.get("partner")
            if partner:
                cost = 20 if partner["owner_id"] == "wild" else 45
                remaining = state["coins"] - cost
                risk = "wysokie" if remaining < 10 else "średnie" if remaining < 35 else "niskie"
                preview = breeding_preview(parent, partner)
                st.write(f"**Koszt:** {cost} monet · po schadzce: {remaining} · ryzyko finansowe: {risk}")
                st.write(f"**🥚 Szansa jajka:** około {preview['egg_chance']}%")
                st.write(f"**🥚 Wiele jaj:** {preview['multi_egg']}")
                st.write(f"**💰 Wartość potomstwa:** {preview['value_low']}–{preview['value_high']} monet")
                st.write(f"**🧬 Rzadkie cechy:** {preview['rare_potential']}")
                st.write(f"**⚠️ Ryzyko ukrytych wad:** {preview['hidden_risk']}")
                st.write(f"**💞 Kompatybilność:** {preview['compatibility']}")
                st.write(f"**🏛️ Potencjał linii:** około {preview.get('line_potential', '?')}/120")
                st.write(f"**🥚 Omen wyklucia:** {preview.get('hatch_hint', 'brak danych')}")

                if st.button("💞 Umów schadzkę", type="primary", use_container_width=True):
                    if state["coins"] < cost:
                        st.error("Za mało monet.")
                    else:
                        state["coins"] -= cost
                        log_t("breed_attempt")
                        parent["life_score_cache"] = life_score(parent)
                        partner["life_score_cache"] = life_score(partner)
                        success, eggs, chance = breed_dragons(parent, partner)
                        if partner.get("owner_id") != "player":
                            state.setdefault("external_parents", {})[partner["id"]] = {
                                "id": partner["id"],
                                "name": partner.get("name", "Rodzic spoza hodowli"),
                                "owner_id": partner.get("owner_id", "external"),
                                "generation": partner.get("generation", max(1, parent.get("generation", 1))),
                                "stage": partner.get("stage", "dorosłość"),
                                "status": partner.get("status", "spoza hodowli"),
                                "temperament": partner.get("temperament"),
                                "phenotype": partner.get("phenotype", {}),
                            }
                        state["eggs"].extend(eggs)
                        msg = breeding_text(parent, partner, success, len(eggs))
                        if success and eggs:
                            msg += "\\n\\n🥚 Połączenie trafia do księgi hodowli. Dopiero potomstwo pokaże, czy kryło się w nim coś naprawdę cennego."
                        if state.get("debug"):
                            msg += f"\\n\\n[DEBUG] Szansa powodzenia: {chance}%"
                        if success:
                            log_t("breed_success")
                        add_feed(msg)
                        action_feedback(msg)
                        save_state(state)
                        st.rerun()
            else:
                st.caption("Prognoza pojawi się po wybraniu partnera.")

    st.divider()

# ---------- Genealogia ----------
elif section == "Genealogia":
    st.header("Genealogia")
    st.caption("Renderowany graf genealogii jako obraz PNG. Lista relacji zostaje niżej jako kontrola.")

    pets_all = state.get("pets", [])
    by_id = {p["id"]: p for p in pets_all}

    if not pets_all:
        st.info("Brak smoków w genealogii.")
    else:
        if render_genealogy_png:
            try:
                st.image(render_genealogy_png(pets_all, state.get("external_parents", {})), use_container_width=True)
            except TypeError:
                st.image(render_genealogy_png(pets_all), use_container_width=True)
        else:
            st.warning("Renderer genealogii nie jest dostępny.")

    st.divider()
    st.subheader("Relacje rodzic–dziecko")
    relations = []
    for child in pets_all:
        for parent_id in child.get("parents", []):
            parent = by_id.get(parent_id)
            if parent:
                relations.append((parent, child))
            else:
                ext = state.get("external_parents", {}).get(parent_id, {
                    "name": "Rodzic spoza hodowli",
                    "owner_id": "external",
                })
                relations.append((ext, child))

    if not relations:
        st.info("Na razie brak relacji rodzic–dziecko. Relacje pojawią się po wykluciu potomstwa ze schadzki.")
    else:
        for parent, child in relations:
            label = parent.get("name", "Rodzic spoza hodowli")
            if parent.get("owner_id") == "wild":
                label += " (dziki partner)"
            elif parent.get("owner_id") == "npc":
                label += " (obca hodowla)"
            elif parent.get("owner_id") == "external":
                label += " (spoza hodowli)"
            st.write(f"**{label}** → **{child['name']}**")

    st.divider()
    st.subheader("Karty genealogiczne")
    for p in sorted(pets_all, key=lambda x: (x.get("generation", 1), x.get("age_days", 0))):
        label = f"{p['name']} — gen. {p.get('generation', '?')} — {p.get('stage', '?')}"
        if p.get("status") == "Reproduktor / Matka linii":
            label += " 👑"
        if p.get("has_departed"):
            label += " — odszedł"
        with st.expander(label):
            st.image(render_dragon_png(p, width=220, height=150), use_container_width=False)
            st.write(describe_dragon(p))
            if p.get("parents"):
                st.write("**Rodzice:**")
                for pid in p["parents"]:
                    parent = by_id.get(pid)
                    if parent:
                        st.write(f"- {parent['name']}")
                    else:
                        ext = state.get("external_parents", {}).get(pid, {"name": "Rodzic spoza hodowli", "owner_id": "external"})
                        suffix = "dziki partner" if ext.get("owner_id") == "wild" else "obca hodowla" if ext.get("owner_id") == "npc" else "spoza hodowli"
                        st.write(f"- {ext.get('name', 'Rodzic spoza hodowli')} ({suffix})")
            else:
                st.write("**Rodzice:** nieznani / początek linii")
            children = [c for c in pets_all if p["id"] in c.get("parents", [])]
            if children:
                st.write("**Dzieci:** " + ", ".join(c["name"] for c in children))
            else:
                st.write("**Dzieci:** brak")

save_state(state)


st.divider()
st.markdown(
    """
    <div style="text-align:center; opacity:0.75; font-size:0.9rem; padding: 0.8rem 0 1.5rem 0;">
        🐉 <strong>DRGN</strong> wykluło się według konceptu <strong>Mikołaja Wicher</strong>.<br>
        Jeśli smok uciekł, ekonomia się zapętliła albo chcesz pogadać o hodowli: 
        <a href="mailto:wicher.m@gmail.com">wicher.m@gmail.com</a>.<br>
        Gra powstała we współpracy z ChatGPT — który, dla jasności, nadal nie bierze odpowiedzialności za szkody od ognia, pazurów ani decyzji hodowlanych.
    </div>
    """,
    unsafe_allow_html=True,
)
