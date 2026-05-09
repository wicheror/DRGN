from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from collections import defaultdict
import math
import os

def _font(size=14, bold=False):
    # Force a Unicode font that supports Polish characters.
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

def _stage_color(node):
    if node.get("external"):
        return (234, 241, 248)  # external parent: pale blue
    pet = node.get("pet", node)
    if pet.get("has_departed"):
        return (226, 222, 216)
    if pet.get("status") == "Reproduktor / Matka linii":
        return (244, 223, 157)
    stage = pet.get("stage")
    if stage == "starość":
        return (235, 221, 205)
    if stage == "dorosłość":
        return (240, 235, 224)
    if stage == "młodość":
        return (232, 240, 230)
    return (245, 242, 236)

def _node_lines(node):
    if node.get("external"):
        name = node.get("name", "Rodzic spoza hodowli")
        origin = node.get("origin_label", "spoza hodowli")
        return [
            f"{name}",
            f"{origin}",
            f"gen. {node.get('generation', '?')}",
        ]

    pet = node.get("pet", node)
    crown = " [GŁOWA]" if pet.get("status") == "Reproduktor / Matka linii" else ""
    gone = " / odszedł" if pet.get("has_departed") else ""
    return [
        f"{pet.get('name', 'Smok')}{crown}",
        f"gen. {pet.get('generation', '?')} · {pet.get('stage', '?')}{gone}",
        f"{pet.get('status', 'W hodowli')}",
    ]

def _draw_arrow(draw, x1, y1, x2, y2, color, width=3):
    # Individual direct line. No shared horizontal bus, so it cannot suggest false co-parenthood.
    draw.line((x1, y1, x2, y2), fill=color, width=width)

    angle = math.atan2(y2 - y1, x2 - x1)
    arrow_len = 10
    arrow_w = 6
    p1 = (
        x2 - arrow_len * math.cos(angle) + arrow_w * math.sin(angle),
        y2 - arrow_len * math.sin(angle) - arrow_w * math.cos(angle),
    )
    p2 = (
        x2 - arrow_len * math.cos(angle) - arrow_w * math.sin(angle),
        y2 - arrow_len * math.sin(angle) + arrow_w * math.cos(angle),
    )
    draw.polygon([(x2, y2), p1, p2], fill=color)

def _build_nodes(pets, external_parents=None):
    pets = list(pets or [])
    external_parents = external_parents or {}

    internal_nodes = []
    by_id = {}

    for p in pets:
        node = {
            "id": p["id"],
            "generation": p.get("generation", 1),
            "external": False,
            "pet": p,
            "name": p.get("name", "Smok"),
        }
        internal_nodes.append(node)
        by_id[p["id"]] = node

    external_nodes = {}
    # Any parent id that is not in pets becomes an external node.
    for child in pets:
        child_gen = child.get("generation", 2)
        for parent_id in child.get("parents", []):
            if parent_id in by_id or parent_id in external_nodes:
                continue

            info = external_parents.get(parent_id, {}) if isinstance(external_parents, dict) else {}
            owner = info.get("owner_id") or info.get("owner") or "external"
            if owner == "wild":
                origin = "dziki partner"
            elif owner == "npc":
                origin = "obca hodowla"
            else:
                origin = "spoza hodowli"

            node = {
                "id": parent_id,
                "generation": info.get("generation", max(1, child_gen - 1)),
                "external": True,
                "name": info.get("name", "Rodzic spoza hodowli"),
                "origin_label": origin,
                "status": origin,
            }
            external_nodes[parent_id] = node

    nodes = internal_nodes + list(external_nodes.values())
    by_id = {n["id"]: n for n in nodes}
    return nodes, by_id

def render_genealogy_png(pets, external_parents=None, width=None):
    """
    Render a real visual genealogy graph as PNG.

    v7.3 fixes:
    - Polish characters are rendered using a Unicode font.
    - Parent-child edges are individual direct lines, not shared generation rails.
    - External parents are shown as separate pale-blue dashed nodes.
    """
    pets = list(pets or [])
    external_parents = external_parents or {}

    if not pets:
        img = Image.new("RGB", (900, 260), (250, 248, 244))
        d = ImageDraw.Draw(img)
        d.text((40, 40), "Brak smoków w genealogii.", font=_font(24, True), fill=(45, 42, 38))
        bio = BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)
        return bio

    nodes, by_id = _build_nodes(pets, external_parents)

    gens = defaultdict(list)
    for n in nodes:
        gens[n.get("generation", 1)].append(n)

    for g in gens:
        # external parents slightly before internal in the same generation
        gens[g].sort(key=lambda n: (0 if n.get("external") else 1, n.get("name", "")))

    generations = sorted(gens.keys())

    node_w = 215
    node_h = 94
    x_gap = 46
    y_gap = 120
    margin_x = 56
    margin_y = 68

    max_count = max(len(gens[g]) for g in generations)
    canvas_w = max(1050, margin_x * 2 + max_count * node_w + (max_count - 1) * x_gap)
    canvas_h = max(360, margin_y * 2 + len(generations) * node_h + (len(generations) - 1) * y_gap)

    if width and width > canvas_w:
        canvas_w = width

    img = Image.new("RGB", (canvas_w, canvas_h), (250, 248, 244))
    d = ImageDraw.Draw(img)

    title_font = _font(25, True)
    small_font = _font(14)
    label_font = _font(15, True)
    meta_font = _font(12)

    d.text((margin_x, 18), "Drzewo genealogiczne hodowli", font=title_font, fill=(45, 42, 38))

    positions = {}

    for row_idx, gen in enumerate(generations):
        row = gens[gen]
        row_width = len(row) * node_w + max(0, len(row) - 1) * x_gap
        start_x = (canvas_w - row_width) // 2
        y = margin_y + row_idx * (node_h + y_gap)

        d.text((margin_x, y + node_h // 2 - 8), f"Gen. {gen}", font=small_font, fill=(100, 92, 82))

        for i, node in enumerate(row):
            x = start_x + i * (node_w + x_gap)
            positions[node["id"]] = (x, y, x + node_w, y + node_h)

    # Edges: draw each actual parent->child relation independently.
    # No shared horizontal rail. If a child has two parents, it gets two separate lines.
    line_color = (138, 122, 99)
    external_line_color = (86, 118, 150)

    for child in pets:
        child_box = positions.get(child["id"])
        if not child_box:
            continue

        # Multiple parents should connect to slightly different points on child top.
        parent_ids = [pid for pid in child.get("parents", []) if pid in by_id and pid in positions]
        count = len(parent_ids)

        for idx, parent_id in enumerate(parent_ids):
            parent_box = positions.get(parent_id)
            if not parent_box:
                continue

            px = (parent_box[0] + parent_box[2]) // 2
            py = parent_box[3]

            # Offset child connection points so two parents do not look like one common rail.
            child_center = (child_box[0] + child_box[2]) // 2
            if count == 1:
                cx = child_center
            else:
                cx = child_center + (idx - (count - 1) / 2) * 42
            cy = child_box[1]

            parent_node = by_id.get(parent_id, {})
            color = external_line_color if parent_node.get("external") else line_color
            _draw_arrow(d, px, py, cx, cy, color=color, width=3)

    # Nodes
    for node in nodes:
        box = positions[node["id"]]
        x1, y1, x2, y2 = box
        fill = _stage_color(node)
        outline = (86, 118, 150) if node.get("external") else (138, 122, 99)

        # External parents get dashed-ish outline: draw multiple short segments around rounded-ish box.
        d.rounded_rectangle(box, radius=13, fill=fill, outline=outline, width=2)

        if node.get("external"):
            # overlay a dotted accent line at top
            for x in range(x1 + 8, x2 - 8, 16):
                d.line((x, y1 + 5, min(x + 8, x2 - 8), y1 + 5), fill=outline, width=2)

        lines = _node_lines(node)
        d.text((x1 + 12, y1 + 12), lines[0], font=label_font, fill=(43, 39, 35))
        d.text((x1 + 12, y1 + 38), lines[1], font=meta_font, fill=(86, 78, 68))
        d.text((x1 + 12, y1 + 60), lines[2], font=meta_font, fill=(105, 93, 78))

    # Legend
    legend_y = canvas_h - 38
    d.text(
        (margin_x, legend_y),
        "[GŁOWA] = głowa linii · niebieskie węzły = rodzice spoza hodowli · szare = odszedł/sprzedany · każda linia to konkretna relacja rodzic → dziecko",
        font=small_font,
        fill=(105, 93, 78),
    )

    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio
