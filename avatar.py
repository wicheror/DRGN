from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import hashlib
import random
import math

# v11 silhouette upgrade.
# Still fully procedural. No external assets, no data model changes.
# The dragon is rendered in layers:
# card -> shadow -> wings -> tail -> body -> legs -> neck/head -> dorsal spines -> horns -> face -> patterns -> age/status -> text.

PALETTES = {
    "popielaty": {
        "body": (126, 133, 142),
        "dark": (69, 75, 83),
        "light": (176, 184, 191),
        "accent": (210, 216, 222),
    },
    "czarny": {
        "body": (42, 44, 50),
        "dark": (20, 22, 27),
        "light": (83, 88, 99),
        "accent": (145, 55, 55),
    },
    "złoty": {
        "body": (204, 159, 59),
        "dark": (112, 78, 32),
        "light": (240, 207, 111),
        "accent": (255, 238, 167),
    },
    "rdzawy": {
        "body": (174, 83, 51),
        "dark": (96, 45, 34),
        "light": (220, 126, 80),
        "accent": (241, 178, 115),
    },
    "zielonkawy": {
        "body": (81, 126, 89),
        "dark": (38, 73, 50),
        "light": (139, 176, 119),
        "accent": (205, 218, 151),
    },
    "granatowy": {
        "body": (53, 76, 134),
        "dark": (29, 39, 76),
        "light": (95, 123, 183),
        "accent": (167, 191, 233),
    },
    "biały": {
        "body": (206, 204, 195),
        "dark": (126, 121, 112),
        "light": (241, 237, 224),
        "accent": (181, 203, 222),
    },
    "miedziany": {
        "body": (174, 100, 59),
        "dark": (89, 50, 35),
        "light": (225, 144, 87),
        "accent": (239, 184, 114),
    },
    "purpurowy": {
        "body": (112, 67, 146),
        "dark": (59, 37, 82),
        "light": (160, 116, 191),
        "accent": (217, 171, 232),
    },

    "szafirowy": {
        "body": (47, 91, 158),
        "dark": (22, 43, 88),
        "light": (102, 154, 218),
        "accent": (173, 214, 245),
    },
    "perłowy": {
        "body": (210, 205, 196),
        "dark": (132, 124, 118),
        "light": (246, 241, 230),
        "accent": (190, 212, 225),
    },
    "oliwkowy": {
        "body": (113, 128, 73),
        "dark": (61, 72, 42),
        "light": (166, 184, 112),
        "accent": (218, 218, 154),
    },
    "karminowy": {
        "body": (159, 55, 63),
        "dark": (86, 30, 42),
        "light": (215, 99, 103),
        "accent": (244, 159, 145),
    },
    "lawendowy": {
        "body": (145, 121, 178),
        "dark": (78, 61, 101),
        "light": (194, 174, 220),
        "accent": (231, 211, 240),
    },
    "stalowy": {
        "body": (103, 116, 126),
        "dark": (52, 61, 68),
        "light": (166, 181, 188),
        "accent": (214, 226, 228),
    },
    "bursztynowy": {
        "body": (191, 126, 46),
        "dark": (104, 63, 24),
        "light": (235, 171, 74),
        "accent": (255, 220, 142),
    },
    "kościany": {
        "body": (198, 184, 154),
        "dark": (109, 96, 74),
        "light": (235, 224, 195),
        "accent": (245, 238, 210),
    },
    "dymny": {
        "body": (91, 91, 98),
        "dark": (42, 42, 50),
        "light": (145, 144, 151),
        "accent": (195, 192, 190),
    },
}

EYE_MAP = {
    "bursztynowe": (224, 161, 59),
    "zielone": (127, 201, 107),
    "srebrne": (217, 224, 230),
    "czarne": (30, 30, 35),
    "złote": (235, 203, 70),
    "błękitne": (114, 183, 255),
    "czerwone": (203, 75, 75),
    "fioletowe": (174, 118, 230),
    "miodowe": (218, 151, 53),
    "dymne": (134, 142, 147),
}

STATUS_BADGES = {
    "W hodowli": ("H", (111, 106, 96)),
    "Przygotowany do schadzki": ("♥", (171, 80, 107)),
    "Smok pracujący": ("P", (116, 91, 55)),
    "W dzikości": ("D", (67, 120, 75)),
    "Odpoczynek": ("Z", (74, 108, 152)),
    "Reproduktor / Matka linii": ("★", (154, 121, 32)),
}


def _font(size=14, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _stable_int(*parts):
    txt = "|".join(str(p) for p in parts)
    return int(hashlib.md5(txt.encode("utf-8")).hexdigest()[:10], 16)


def _rng(pet):
    return random.Random(_stable_int(pet.get("id", ""), pet.get("name", "")))


def _clamp(v):
    return max(0, min(255, int(v)))


def _mix(a, b, t=0.5):
    return tuple(_clamp(a[i] * (1 - t) + b[i] * t) for i in range(3))


def _shade(rgb, factor=0.75):
    return tuple(_clamp(c * factor) for c in rgb)


def _light(rgb, factor=1.20):
    return tuple(_clamp(c * factor) for c in rgb)


def _rgba(rgb, a=255):
    return rgb + (a,)


def _visual_profile(pet):
    ph = pet.get("phenotype", {})
    gt = pet.get("genotype", {})
    rng = _rng(pet)

    color_name = ph.get("color", "popielaty")
    palette = PALETTES.get(color_name, PALETTES["popielaty"]).copy()

    size = ph.get("size", "średni")
    temperament = pet.get("temperament", "ciekawski")
    mutation = gt.get("mutation", 5)
    rarity = gt.get("rarity", 45)

    if size in ["duży", "krępy"]:
        body_type = "heavy"
    elif size in ["mały", "smukły"]:
        body_type = "slim"
    elif temperament == "dziki" or mutation > 28:
        body_type = "wild"
    else:
        body_type = ["standard", "elegant"][rng.randint(0, 1)]

    if temperament in ["wyrachowany", "dumny"]:
        head_type = "noble"
    elif temperament in ["złośliwy", "dziki"]:
        head_type = "predatory"
    elif size in ["duży", "krępy"]:
        head_type = "massive"
    else:
        head_type = "feline"

    if mutation > 30 or temperament == "dziki":
        wing_type = "tattered"
    elif rarity > 75:
        wing_type = "ornamental"
    elif size in ["duży", "krępy"]:
        wing_type = "broad"
    elif size in ["mały", "smukły"]:
        wing_type = "small"
    else:
        wing_type = "classic"

    if ph.get("horns") in ["drobne kolce", "asymetryczne rogi"]:
        tail_type = "spiked"
    elif size in ["duży", "krępy"]:
        tail_type = "club"
    elif size in ["mały", "smukły"]:
        tail_type = "whip"
    else:
        tail_type = "simple"

    return {
        "palette": palette,
        "color_name": color_name,
        "eye": EYE_MAP.get(ph.get("eyes", "bursztynowe"), EYE_MAP["bursztynowe"]),
        "pattern": ph.get("pattern", "bez wzoru"),
        "horns": ph.get("horns", "krótkie rogi"),
        "size": size,
        "body_type": body_type,
        "head_type": head_type,
        "wing_type": wing_type,
        "tail_type": tail_type,
        "temperament": temperament,
        "mutation": mutation,
        "rarity": rarity,
        "rng": rng,
    }


def _rounded_card(draw, width, height, pet, prof):
    status = pet.get("status", "W hodowli")

    bg = (247, 243, 235)
    if status == "W dzikości":
        bg = (238, 244, 234)
    elif status == "Smok pracujący":
        bg = (245, 238, 228)
    elif status == "Reproduktor / Matka linii":
        bg = (248, 240, 210)
    elif status == "Odpoczynek":
        bg = (236, 242, 248)

    draw.rounded_rectangle((6, 6, width - 6, height - 6), radius=22, fill=bg, outline=(180, 164, 140), width=2)
    draw.ellipse((width * 0.08, height * 0.08, width * 0.92, height * 0.92), fill=_rgba((255, 255, 255), 20))


def _body_params(prof, width, height):
    cx = int(width * 0.56)
    cy = int(height * 0.62)

    if prof["body_type"] == "heavy":
        chest_r = (36, 28)
        hip_r = (34, 24)
        neck_len = 46
        wing_span = 1.12
    elif prof["body_type"] == "slim":
        chest_r = (31, 22)
        hip_r = (28, 20)
        neck_len = 50
        wing_span = 0.92
    elif prof["body_type"] == "wild":
        chest_r = (34, 25)
        hip_r = (31, 22)
        neck_len = 48
        wing_span = 1.03
    elif prof["body_type"] == "elegant":
        chest_r = (32, 23)
        hip_r = (29, 20)
        neck_len = 52
        wing_span = 0.98
    else:
        chest_r = (33, 24)
        hip_r = (30, 21)
        neck_len = 48
        wing_span = 1.00

    chest_c = (cx - 18, cy - 6)
    hip_c = (cx + 22, cy + 2)
    body_left = chest_c[0] - chest_r[0]
    body_right = hip_c[0] + hip_r[0]
    body_top = min(chest_c[1] - chest_r[1], hip_c[1] - hip_r[1])
    body_bottom = max(chest_c[1] + chest_r[1], hip_c[1] + hip_r[1])

    return {
        "cx": cx,
        "cy": cy,
        "chest_c": chest_c,
        "hip_c": hip_c,
        "chest_r": chest_r,
        "hip_r": hip_r,
        "neck_base": (chest_c[0] - 18, chest_c[1] - 18),
        "head_anchor": (chest_c[0] - neck_len - 18, chest_c[1] - 44),
        "wing_anchor": (chest_c[0] - 2, chest_c[1] - 18),
        "tail_base": (hip_c[0] + hip_r[0] - 6, hip_c[1] + 0),
        "bounds": (body_left, body_top, body_right, body_bottom),
        "wing_span": wing_span,
    }


def _draw_shadow(draw, layout):
    left, top, right, bottom = layout["bounds"]
    cx = (left + right) // 2
    y = bottom + 6
    draw.ellipse((cx - 72, y - 2, cx + 74, y + 20), fill=(0, 0, 0, 32))


def _wing_points(anchor_x, anchor_y, wing_type, side=1, scale=1.0):
    s = side
    root = (anchor_x, anchor_y)
    elbow = (anchor_x + int(20 * scale) * s, anchor_y - int(22 * scale))
    tip = (anchor_x + int(58 * scale) * s, anchor_y - int(66 * scale))
    finger2 = (anchor_x + int(74 * scale) * s, anchor_y - int(34 * scale))
    finger3 = (anchor_x + int(64 * scale) * s, anchor_y + int(2 * scale))
    trailing = (anchor_x + int(18 * scale) * s, anchor_y + int(20 * scale))

    if wing_type == "small":
        tip = (anchor_x + int(46 * scale) * s, anchor_y - int(50 * scale))
        finger2 = (anchor_x + int(56 * scale) * s, anchor_y - int(20 * scale))
        finger3 = (anchor_x + int(48 * scale) * s, anchor_y + int(4 * scale))
    elif wing_type == "broad":
        tip = (anchor_x + int(72 * scale) * s, anchor_y - int(74 * scale))
        finger2 = (anchor_x + int(94 * scale) * s, anchor_y - int(28 * scale))
        finger3 = (anchor_x + int(84 * scale) * s, anchor_y + int(10 * scale))
    elif wing_type == "tattered":
        tip = (anchor_x + int(66 * scale) * s, anchor_y - int(72 * scale))
        finger2 = (anchor_x + int(88 * scale) * s, anchor_y - int(24 * scale))
        finger3 = (anchor_x + int(80 * scale) * s, anchor_y + int(12 * scale))
    elif wing_type == "ornamental":
        tip = (anchor_x + int(62 * scale) * s, anchor_y - int(76 * scale))
        finger2 = (anchor_x + int(82 * scale) * s, anchor_y - int(24 * scale))
        finger3 = (anchor_x + int(74 * scale) * s, anchor_y + int(8 * scale))

    membrane = [root, elbow, tip, finger2, finger3, trailing]
    ribs = [
        (root, tip),
        (root, finger2),
        (root, finger3),
    ]
    return membrane, ribs


def _draw_wings(layer, prof, layout):
    d = ImageDraw.Draw(layer)
    pal = prof["palette"]
    wing_fill = _rgba(_mix(pal["body"], pal["light"], 0.38), 120)
    wing_outline = _rgba(_shade(pal["dark"], 0.84), 175)
    rib_color = _rgba(_shade(pal["dark"], 0.80), 165)
    anchor_x, anchor_y = layout["wing_anchor"]
    scale = layout["wing_span"]

    for side, alpha_scale, dx, dy in [(-1, 0.85, -4, 2), (1, 1.00, 2, -2)]:
        membrane, ribs = _wing_points(anchor_x + dx, anchor_y + dy, prof["wing_type"], side=side, scale=scale)
        fill = wing_fill[:-1] + (int(wing_fill[-1] * alpha_scale),)
        outline = wing_outline[:-1] + (int(wing_outline[-1] * alpha_scale),)
        d.polygon(membrane, fill=fill, outline=outline)
        if prof["wing_type"] == "tattered":
            # cut a few soft notches into the membrane edge
            for notch in membrane[2:5]:
                nx, ny = notch
                d.line((nx, ny, nx - side * 10, ny + 8), fill=_rgba((0, 0, 0), 0), width=1)
                d.line((nx, ny, nx - side * 10, ny + 8), fill=outline, width=2)
        for start, end in ribs:
            d.line((start, end), fill=rib_color[:-1] + (int(rib_color[-1] * alpha_scale),), width=2)
        if prof["wing_type"] == "ornamental":
            for ox, oy, rr in [(0, -8, 10), (side * 16, 2, 8)]:
                d.arc((anchor_x + ox - rr, anchor_y + oy - rr, anchor_x + ox + rr, anchor_y + oy + rr), 205, 350, fill=_rgba(pal["accent"], 120), width=2)


def _draw_leg(draw, x0, y0, upper_len, lower_len, direction, color, outline, foot_scale=1.0):
    knee = (x0 + int(8 * direction), y0 + upper_len)
    foot = (knee[0] + int(10 * direction), knee[1] + lower_len)
    draw.line((x0, y0, knee[0], knee[1]), fill=color, width=8)
    draw.line((knee[0], knee[1], foot[0], foot[1]), fill=color, width=7)
    foot_pts = [
        (foot[0] - 6, foot[1] - 2),
        (foot[0] + 8, foot[1] - 1),
        (foot[0] + 10, foot[1] + 5),
        (foot[0] - 5, foot[1] + 5),
    ]
    draw.polygon(foot_pts, fill=color, outline=outline)
    claw_y = foot[1] + 4
    for i in range(3):
        cx = foot[0] + i * 4 - 1
        draw.line((cx, claw_y, cx + 4, claw_y + 2), fill=outline, width=1)
    return knee, foot


def _draw_body(layer, prof, layout):
    d = ImageDraw.Draw(layer)
    pal = prof["palette"]
    outline = (32, 30, 28, 235)
    body = _rgba(pal["body"])
    chest_fill = _rgba(_mix(pal["body"], pal["light"], 0.10), 235)
    hip_fill = _rgba(_mix(pal["body"], pal["dark"], 0.06), 235)

    chest_c = layout["chest_c"]
    hip_c = layout["hip_c"]
    chest_r = layout["chest_r"]
    hip_r = layout["hip_r"]

    # Body silhouette built from chest + hips + belly connector.
    d.ellipse((chest_c[0] - chest_r[0], chest_c[1] - chest_r[1], chest_c[0] + chest_r[0], chest_c[1] + chest_r[1]), fill=chest_fill, outline=outline, width=3)
    d.ellipse((hip_c[0] - hip_r[0], hip_c[1] - hip_r[1], hip_c[0] + hip_r[0], hip_c[1] + hip_r[1]), fill=hip_fill, outline=outline, width=3)

    top_poly = [
        (chest_c[0] - 8, chest_c[1] - chest_r[1] + 1),
        (chest_c[0] + 24, chest_c[1] - chest_r[1] - 5),
        (hip_c[0] + 12, hip_c[1] - hip_r[1] - 3),
        (hip_c[0] + 24, hip_c[1] - 2),
        (chest_c[0] + 10, chest_c[1] + 2),
    ]
    belly_poly = [
        (chest_c[0] - 2, chest_c[1] + 10),
        (chest_c[0] + 28, chest_c[1] + chest_r[1] - 2),
        (hip_c[0] + 18, hip_c[1] + hip_r[1] - 2),
        (hip_c[0] + 24, hip_c[1] + 2),
        (chest_c[0] + 14, chest_c[1] - 4),
    ]
    d.polygon(top_poly, fill=body, outline=outline)
    d.polygon(belly_poly, fill=body, outline=outline)

    # Chest and belly highlight / plates.
    d.ellipse((chest_c[0] - chest_r[0] + 8, chest_c[1] - chest_r[1] + 6, chest_c[0] + 12, chest_c[1] + chest_r[1] - 4), fill=_rgba(_mix(pal["body"], pal["light"], 0.23), 100))
    for i in range(4):
        x = chest_c[0] + 4 + i * 10
        y = chest_c[1] + 4 + i * 3
        plate = [(x - 4, y - 2), (x + 8, y - 4), (x + 10, y + 4), (x - 2, y + 5)]
        d.polygon(plate, fill=_rgba(_mix(pal["light"], pal["accent"], 0.20), 155), outline=_rgba(_shade(pal["dark"], 0.94), 100))

    # Back line.
    d.arc((chest_c[0] - chest_r[0] + 10, chest_c[1] - chest_r[1] - 10, hip_c[0] + hip_r[0] + 6, hip_c[1] + 8), 190, 345, fill=_rgba(pal["light"], 170), width=4)

    # Legs with joints and claws.
    leg_color = _rgba(_shade(pal["body"], 0.78))
    front_leg_y = chest_c[1] + chest_r[1] - 2
    back_leg_y = hip_c[1] + hip_r[1] - 2
    _draw_leg(d, chest_c[0] - 10, front_leg_y, 16, 15, -1, leg_color, outline)
    _draw_leg(d, chest_c[0] + 14, front_leg_y - 2, 18, 16, 1, leg_color, outline)
    _draw_leg(d, hip_c[0] - 4, back_leg_y - 3, 15, 16, -1, leg_color, outline)
    _draw_leg(d, hip_c[0] + 18, back_leg_y - 5, 16, 15, 1, leg_color, outline)


def _draw_tail(layer, prof, layout):
    d = ImageDraw.Draw(layer)
    pal = prof["palette"]
    outline = (32, 30, 28, 230)
    base = layout["tail_base"]
    tail = prof["tail_type"]

    if tail == "whip":
        pts = [base, (base[0] + 20, base[1] - 4), (base[0] + 52, base[1] + 6), (base[0] + 90, base[1] + 0)]
        widths = [8, 6, 4]
    elif tail == "club":
        pts = [base, (base[0] + 18, base[1] - 2), (base[0] + 44, base[1] + 10), (base[0] + 72, base[1] + 24)]
        widths = [12, 9, 7]
    elif tail == "spiked":
        pts = [base, (base[0] + 20, base[1] - 2), (base[0] + 48, base[1] + 8), (base[0] + 82, base[1] + 20)]
        widths = [10, 8, 6]
    else:
        pts = [base, (base[0] + 20, base[1] - 2), (base[0] + 50, base[1] + 6), (base[0] + 84, base[1] + 16)]
        widths = [10, 7, 5]

    body_col = _rgba(_shade(pal["dark"], 0.95))
    for i in range(len(pts) - 1):
        d.line((pts[i], pts[i + 1]), fill=body_col, width=widths[i], joint="curve")
    d.line((pts[0][0] + 2, pts[0][1] - 2, pts[1][0] + 2, pts[1][1] - 1), fill=_rgba(pal["light"], 80), width=2)

    end = pts[-1]
    if tail == "club":
        d.ellipse((end[0] - 4, end[1] - 8, end[0] + 22, end[1] + 14), fill=body_col, outline=outline, width=2)
    elif tail == "spiked":
        for sx, sy in [(pts[1][0], pts[1][1]), (pts[2][0], pts[2][1] + 2), (end[0] - 4, end[1] + 2)]:
            d.polygon([(sx - 2, sy - 10), (sx + 6, sy + 1), (sx - 4, sy + 3)], fill=_rgba(pal["light"]), outline=outline)
    elif tail == "simple":
        d.polygon([(end[0] - 3, end[1] - 5), (end[0] + 14, end[1]), (end[0] - 1, end[1] + 8)], fill=body_col, outline=outline)
    else:  # whip
        d.line((end[0], end[1], end[0] + 18, end[1] - 4), fill=body_col, width=3)


def _neck_polygon(head_back, neck_base, thickness_top=14, thickness_base=22):
    # simple S-curve neck built from left/right rails
    hx, hy = head_back
    nx, ny = neck_base
    midx = (hx + nx) // 2
    upper = [
        (hx + 4, hy + 8),
        (midx - 8, hy + 18),
        (nx + 6, ny + 4),
    ]
    lower = [
        (nx + 12, ny + thickness_base),
        (midx - 2, hy + 34),
        (hx - 2, hy + thickness_top),
    ]
    return upper + lower


def _draw_head(layer, prof, layout):
    d = ImageDraw.Draw(layer)
    pal = prof["palette"]
    outline = (32, 30, 28, 235)
    hx, hy = layout["head_anchor"]
    head_type = prof["head_type"]

    # head faces left; anchor refers roughly to top-back of skull.
    if head_type == "massive":
        skull = [(hx + 40, hy + 6), (hx + 22, hy + 2), (hx + 0, hy + 10), (hx - 10, hy + 26), (hx - 6, hy + 40), (hx + 10, hy + 48), (hx + 34, hy + 46), (hx + 52, hy + 34), (hx + 56, hy + 18)]
        snout = [(hx + 6, hy + 18), (hx - 24, hy + 20), (hx - 38, hy + 28), (hx - 32, hy + 36), (hx - 6, hy + 36), (hx + 8, hy + 28)]
        brow = [(hx + 18, hy + 13), (hx - 6, hy + 16)]
        eye = (hx + 10, hy + 22)
        nostril = (hx - 25, hy + 29)
        mouth = (hx - 6, hy + 33, hx + 22, hy + 46)
        jaw_tooth = (hx - 4, hy + 38)
    elif head_type == "predatory":
        skull = [(hx + 38, hy + 7), (hx + 18, hy + 0), (hx - 2, hy + 6), (hx - 12, hy + 18), (hx - 12, hy + 31), (hx + 4, hy + 42), (hx + 28, hy + 43), (hx + 50, hy + 30), (hx + 54, hy + 16)]
        snout = [(hx + 2, hy + 16), (hx - 32, hy + 18), (hx - 46, hy + 24), (hx - 42, hy + 30), (hx - 10, hy + 32), (hx + 5, hy + 25)]
        brow = [(hx + 16, hy + 11), (hx - 8, hy + 17)]
        eye = (hx + 8, hy + 21)
        nostril = (hx - 30, hy + 25)
        mouth = (hx - 10, hy + 28, hx + 18, hy + 42)
        jaw_tooth = (hx - 6, hy + 35)
    elif head_type == "noble":
        skull = [(hx + 40, hy + 2), (hx + 22, hy - 4), (hx + 4, hy + 4), (hx - 4, hy + 18), (hx - 2, hy + 32), (hx + 12, hy + 42), (hx + 36, hy + 44), (hx + 54, hy + 34), (hx + 58, hy + 18)]
        snout = [(hx + 4, hy + 18), (hx - 22, hy + 18), (hx - 35, hy + 24), (hx - 29, hy + 31), (hx - 5, hy + 33), (hx + 10, hy + 26)]
        brow = [(hx + 18, hy + 10), (hx - 2, hy + 13)]
        eye = (hx + 10, hy + 19)
        nostril = (hx - 20, hy + 25)
        mouth = (hx - 6, hy + 27, hx + 22, hy + 40)
        jaw_tooth = None
    else:  # feline/default
        skull = [(hx + 38, hy + 7), (hx + 18, hy + 1), (hx + 0, hy + 7), (hx - 8, hy + 20), (hx - 4, hy + 34), (hx + 10, hy + 42), (hx + 34, hy + 43), (hx + 50, hy + 32), (hx + 54, hy + 18)]
        snout = [(hx + 3, hy + 19), (hx - 20, hy + 19), (hx - 30, hy + 25), (hx - 24, hy + 33), (hx - 2, hy + 33), (hx + 8, hy + 27)]
        brow = [(hx + 18, hy + 12), (hx - 2, hy + 15)]
        eye = (hx + 10, hy + 22)
        nostril = (hx - 18, hy + 28)
        mouth = (hx - 4, hy + 29, hx + 22, hy + 42)
        jaw_tooth = None

    neck_poly = _neck_polygon((hx + 46, hy + 23), layout["neck_base"], thickness_top=14, thickness_base=24)
    d.polygon(neck_poly, fill=_rgba(_shade(pal["body"], 0.94)), outline=outline)
    d.line((layout["neck_base"][0] + 5, layout["neck_base"][1] + 6, hx + 32, hy + 28), fill=_rgba(pal["light"], 120), width=3)

    d.polygon(skull, fill=_rgba(pal["body"]), outline=outline)
    d.polygon(snout, fill=_rgba(_shade(pal["body"], 0.86)), outline=outline)
    d.arc((hx - 2, hy + 4, hx + 36, hy + 28), 200, 345, fill=_rgba(pal["light"], 170), width=3)
    d.line((brow[0][0], brow[0][1], brow[1][0], brow[1][1]), fill=outline, width=3)

    return {
        "skull": skull,
        "snout": snout,
        "eye": eye,
        "nostril": nostril,
        "mouth": mouth,
        "jaw_tooth": jaw_tooth,
        "head_anchor": (hx, hy),
    }


def _draw_dorsal_spines(layer, prof, layout, head_info):
    d = ImageDraw.Draw(layer)
    pal = prof["palette"]
    outline = (32, 30, 28, 180)
    fill = _rgba(_mix(pal["dark"], pal["light"], 0.18), 230)

    hx, hy = head_info["head_anchor"]
    chest_c = layout["chest_c"]
    hip_c = layout["hip_c"]

    points = [
        (hx + 42, hy + 12),
        (hx + 50, hy + 18),
        (chest_c[0] - 10, chest_c[1] - 20),
        (chest_c[0] + 10, chest_c[1] - 26),
        (chest_c[0] + 34, chest_c[1] - 24),
        (hip_c[0] - 4, hip_c[1] - 20),
        (hip_c[0] + 18, hip_c[1] - 16),
        (layout["tail_base"][0] + 10, layout["tail_base"][1] - 8),
    ]
    heights = [12, 14, 15, 16, 14, 12, 10, 8]
    if prof["body_type"] == "wild":
        heights = [h + 3 for h in heights]
    elif prof["body_type"] == "slim":
        heights = [max(7, h - 2) for h in heights]

    for idx, (px, py) in enumerate(points):
        h = heights[idx]
        tri = [(px - 4, py + 2), (px + 3, py - h), (px + 8, py + 3)]
        d.polygon(tri, fill=fill, outline=outline)


def _draw_horns(layer, prof, head_info):
    d = ImageDraw.Draw(layer)
    pal = prof["palette"]
    horns = prof["horns"]
    hx, hy = head_info["head_anchor"]
    horn_col = _rgba(_mix(pal["dark"], (230, 220, 190), 0.32))
    outline = (32, 30, 28, 235)

    if horns == "bez rogów":
        return
    if horns == "krótkie rogi":
        polys = [
            [(hx + 28, hy + 3), (hx + 18, hy - 22), (hx + 35, hy + 1)],
            [(hx + 42, hy + 4), (hx + 50, hy - 20), (hx + 47, hy + 4)],
        ]
        for poly in polys:
            d.polygon(poly, fill=horn_col, outline=outline)
    elif horns == "zakrzywione rogi":
        d.arc((hx + 0, hy - 28, hx + 36, hy + 6), 320, 135, fill=outline, width=8)
        d.arc((hx + 0, hy - 28, hx + 36, hy + 6), 320, 135, fill=horn_col, width=5)
        d.arc((hx + 26, hy - 30, hx + 60, hy + 4), 30, 215, fill=outline, width=8)
        d.arc((hx + 26, hy - 30, hx + 60, hy + 4), 30, 215, fill=horn_col, width=5)
    elif horns == "asymetryczne rogi":
        d.polygon([(hx + 28, hy + 2), (hx + 18, hy - 28), (hx + 36, hy + 1)], fill=horn_col, outline=outline)
        d.arc((hx + 26, hy - 34, hx + 66, hy + 4), 30, 220, fill=outline, width=8)
        d.arc((hx + 26, hy - 34, hx + 66, hy + 4), 30, 220, fill=horn_col, width=5)
    elif horns == "drobne kolce":
        for xoff in [18, 28, 38, 48]:
            d.polygon([(hx + xoff, hy + 3), (hx + xoff + 5, hy - 14), (hx + xoff + 10, hy + 3)], fill=horn_col, outline=outline)
    elif horns == "koronne rogi":
        for xoff, h in [(16, 18), (28, 27), (41, 23), (54, 15)]:
            d.polygon([(hx + xoff, hy + 4), (hx + xoff + 6, hy - h), (hx + xoff + 12, hy + 4)], fill=horn_col, outline=outline)
    elif horns == "baranie rogi":
        d.arc((hx + 4, hy - 24, hx + 42, hy + 14), 120, 345, fill=outline, width=8)
        d.arc((hx + 4, hy - 24, hx + 42, hy + 14), 120, 345, fill=horn_col, width=5)
        d.arc((hx + 28, hy - 22, hx + 66, hy + 16), 185, 35, fill=outline, width=8)
        d.arc((hx + 28, hy - 22, hx + 66, hy + 16), 185, 35, fill=horn_col, width=5)
    elif horns == "pojedynczy róg":
        d.polygon([(hx + 34, hy + 2), (hx + 30, hy - 30), (hx + 44, hy + 4)], fill=horn_col, outline=outline)
    elif horns == "pęknięte rogi":
        d.polygon([(hx + 28, hy + 3), (hx + 18, hy - 24), (hx + 35, hy + 1)], fill=horn_col, outline=outline)
        d.line((hx + 22, hy - 13, hx + 30, hy - 8), fill=outline, width=2)
        d.polygon([(hx + 42, hy + 4), (hx + 50, hy - 15), (hx + 47, hy + 4)], fill=horn_col, outline=outline)
    else:
        d.polygon([(hx + 28, hy + 3), (hx + 18, hy - 26), (hx + 35, hy + 1)], fill=horn_col, outline=outline)
        d.polygon([(hx + 42, hy + 4), (hx + 52, hy - 24), (hx + 47, hy + 4)], fill=horn_col, outline=outline)


def _draw_face(layer, prof, head_info):
    d = ImageDraw.Draw(layer)
    outline = (25, 24, 23, 245)
    eye_color = prof["eye"]
    temp = prof["temperament"]
    ex, ey = head_info["eye"]
    nx, ny = head_info["nostril"]
    mouth_box = head_info["mouth"]

    slant = {
        "dumny": -3,
        "złośliwy": 4,
        "lękliwy": -4,
        "ciekawski": 0,
        "leniwy": 2,
        "wyrachowany": 2,
        "przywiązany": -1,
        "dziki": 5,
    }.get(temp, 0)

    # eye under brow ridge
    d.ellipse((ex - 8, ey - 6, ex + 8, ey + 6), fill=_rgba(eye_color), outline=outline, width=2)
    pupil_h = 4 if temp in ["dumny", "złośliwy", "wyrachowany", "dziki"] else 3
    d.ellipse((ex - 2, ey - pupil_h, ex + 2, ey + pupil_h), fill=(10, 10, 12, 255))
    d.ellipse((ex - 1, ey - 3, ex + 1, ey - 1), fill=(255, 255, 255, 170))
    d.line((ex + 6, ey - 7, ex - 10, ey - 4 + slant), fill=outline, width=2)

    # nostrils, mouth and a subtle jaw/tooth line
    d.ellipse((nx - 2, ny - 1, nx + 2, ny + 3), fill=outline)
    d.arc(mouth_box, 8, 165, fill=outline, width=2)
    if head_info["jaw_tooth"]:
        tx, ty = head_info["jaw_tooth"]
        d.line((tx, ty, tx - 3, ty + 4), fill=(245, 241, 230, 220), width=1)


def _draw_pattern(layer, prof, layout):
    d = ImageDraw.Draw(layer)
    pal = prof["palette"]
    pattern = prof["pattern"]
    left, top, right, bottom = layout["bounds"]
    dark = _rgba(_shade(pal["dark"], 0.85), 145)
    light = _rgba(pal["accent"], 120)
    chest_c = layout["chest_c"]
    hip_c = layout["hip_c"]

    if pattern == "w pręgi":
        start_x = chest_c[0] - 14
        for idx in range(4):
            x = start_x + idx * 16
            d.arc((x - 12, top + 6, x + 14, bottom - 6), 270, 70, fill=dark, width=4)
    elif pattern == "w cętki":
        for ox, oy, r in [(-18, -4, 6), (2, -14, 5), (20, 4, 7), (34, -10, 5), (8, 20, 5)]:
            d.ellipse((chest_c[0] + ox - r, chest_c[1] + oy - r, chest_c[0] + ox + r, chest_c[1] + oy + r), fill=dark)
        for ox, oy, r in [(-4, 0, 5), (14, -6, 4), (28, 10, 5)]:
            d.ellipse((hip_c[0] + ox - r, hip_c[1] + oy - r, hip_c[0] + ox + r, hip_c[1] + oy + r), fill=dark)
    elif pattern == "z marmurkowaniem":
        d.line((chest_c[0] - 24, chest_c[1] - 4, chest_c[0] + 2, chest_c[1] - 12, hip_c[0] - 6, hip_c[1] + 2, hip_c[0] + 24, hip_c[1] - 6), fill=dark, width=3)
        d.line((chest_c[0] - 14, chest_c[1] + 14, chest_c[0] + 10, chest_c[1] + 8, hip_c[0] + 8, hip_c[1] + 16), fill=dark, width=3)
    elif pattern == "z jasnym grzbietem":
        d.polygon([(left + 22, top + 6), (right - 20, top + 9), (right - 24, top + 20), (left + 28, top + 17)], fill=light)
    elif pattern == "z ciemnym brzuchem":
        d.polygon([(left + 16, bottom - 10), (right - 14, bottom - 12), (right - 18, bottom + 4), (left + 18, bottom + 2)], fill=dark)
    elif pattern == "z lśniącymi plamami":
        for ox, oy, r in [(-18, -8, 4), (6, -18, 4), (24, 0, 3), (18, 17, 3)]:
            d.ellipse((chest_c[0] + ox - r, chest_c[1] + oy - r, chest_c[0] + ox + r, chest_c[1] + oy + r), fill=_rgba((255, 255, 255), 130))
    elif pattern == "łaciaty":
        for ox, oy, r in [(-24, -4, 11), (10, -10, 9), (32, 12, 10)]:
            d.ellipse((chest_c[0] + ox - r, chest_c[1] + oy - r, chest_c[0] + ox + r, chest_c[1] + oy + r), fill=_rgba(_mix(pal["dark"], pal["body"], 0.35), 105))
    elif pattern == "z maską na pysku":
        # mask goes near the head, using approximate head anchor from layout
        hx, hy = layout["head_anchor"]
        d.polygon([(hx - 10, hy + 16), (hx + 14, hy + 11), (hx + 18, hy + 29), (hx - 8, hy + 32)], fill=_rgba(_shade(pal["dark"], 0.9), 120))
    elif pattern == "z ciemnymi końcówkami skrzydeł":
        wx, wy = layout["wing_anchor"]
        d.line((wx - 55, wy - 55, wx - 85, wy - 28), fill=dark, width=5)
        d.line((wx + 55, wy - 55, wx + 85, wy - 28), fill=dark, width=5)
    elif pattern == "z pręgą ogonową":
        tx, ty = layout["tail_base"]
        d.line((tx + 8, ty - 3, tx + 58, ty + 10), fill=dark, width=4)
    elif pattern == "z gwiezdnymi plamkami":
        for ox, oy in [(-18, -8), (0, -18), (20, -2), (35, 12), (6, 18)]:
            x, y = chest_c[0] + ox, chest_c[1] + oy
            d.line((x - 3, y, x + 3, y), fill=_rgba((255, 255, 255), 145), width=1)
            d.line((x, y - 3, x, y + 3), fill=_rgba((255, 255, 255), 145), width=1)
    elif pattern == "z popękanymi łuskami":
        crack = _rgba(pal["accent"], 135)
        d.line((chest_c[0] - 20, chest_c[1] - 14, chest_c[0] - 5, chest_c[1] - 2, chest_c[0] - 16, chest_c[1] + 10), fill=crack, width=2)
        d.line((hip_c[0] - 4, hip_c[1] - 8, hip_c[0] + 14, hip_c[1] + 7, hip_c[0] + 6, hip_c[1] + 18), fill=crack, width=2)

    if prof["mutation"] >= 30:
        glow = _rgba(prof["palette"]["accent"], 170)
        d.line((chest_c[0] - 20, chest_c[1] - 18, chest_c[0] - 8, chest_c[1] - 2, chest_c[0] - 18, chest_c[1] + 12), fill=glow, width=3)
        d.line((hip_c[0] - 4, hip_c[1] - 8, hip_c[0] + 14, hip_c[1] + 6, hip_c[0] + 6, hip_c[1] + 20), fill=glow, width=3)


def _draw_age_status(layer, pet, prof, width, height):
    d = ImageDraw.Draw(layer)
    stage = pet.get("stage", "młodość")
    status = pet.get("status", "W hodowli")

    if stage == "starość":
        d.rectangle((6, 6, width - 6, height - 6), fill=(230, 224, 213, 38))
        scar_col = (80, 70, 60, 150)
        d.line((width * 0.39, height * 0.35, width * 0.46, height * 0.39), fill=scar_col, width=2)
        d.line((width * 0.57, height * 0.34, width * 0.63, height * 0.38), fill=scar_col, width=2)

    if pet.get("has_departed"):
        d.rectangle((0, 0, width, height), fill=(255, 255, 255, 120))
        d.text((width // 2 - 42, height // 2 - 10), "ODSZEDŁ", font=_font(16, True), fill=(80, 70, 60, 230))

    badge, color = STATUS_BADGES.get(status, ("?", (111, 106, 96)))
    d.ellipse((width - 44, 16, width - 16, 44), fill=color + (235,), outline=(60, 50, 40, 255), width=2)
    d.text((width - 35, 20), badge, font=_font(15, True), fill=(255, 255, 245, 255))

    if pet.get("status") == "Reproduktor / Matka linii" or pet.get("line_head"):
        d.text((18, height - 30), "GŁOWA LINII", font=_font(13, True), fill=(115, 85, 24, 230))


def render_dragon_png(pet, width=320, height=220):
    prof = _visual_profile(pet)

    base = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    _rounded_card(draw, width, height, pet, prof)

    layout = _body_params(prof, width, height)
    _draw_shadow(draw, layout)

    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    _draw_wings(layer, prof, layout)
    _draw_tail(layer, prof, layout)
    _draw_body(layer, prof, layout)
    head_info = _draw_head(layer, prof, layout)
    _draw_dorsal_spines(layer, prof, layout, head_info)
    _draw_horns(layer, prof, head_info)
    _draw_face(layer, prof, head_info)
    _draw_pattern(layer, prof, layout)
    _draw_age_status(layer, pet, prof, width, height)

    img = Image.alpha_composite(base, layer)

    d = ImageDraw.Draw(img)
    name = pet.get("name", "Smok")
    stage = pet.get("stage", "?")
    temperament = pet.get("temperament", "?")
    d.text((18, 16), name, font=_font(18, True), fill=(43, 39, 35, 255))
    d.text((18, 40), f"{stage} · {temperament}", font=_font(12), fill=(83, 74, 62, 235))

    bio = BytesIO()
    # Keep RGBA PNG; the card itself is opaque so current UI stays visually stable,
    # while alpha is preserved safely for any future use.
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio
