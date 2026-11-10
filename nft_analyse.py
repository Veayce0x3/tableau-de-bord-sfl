"""Rentabilité des NFT : ce que chacun rapporte par jour et par an, à partir de TA production.

Effets tirés du code du jeu (collectibleItemBuffs.ts / bumpkinItemBuffs.ts).
Ta production par jour se règle dans ma_ferme.json → "ma_production".
"""

import json
import re

TAX = 0.075

# Production par jour (actions ou cycles). Valeurs par défaut = une grosse ferme de niveau ~90.
DEFAULT_PROD = {
    "Stone": 132, "Iron": 43, "Gold": 9, "Crimstone": 3.7, "Wood": 108,   # coups de pioche / hache par jour
    "cycles_vaches": 15, "cycles_poules": 30, "vaches": 15,
    "recoltes": {"Wheat": 60, "Barley": 25, "Corn": 21, "Kale": 10},      # champs récoltés par jour (moyenne sur l'année)
    "rendement_culture": 2.72,                                           # récolte par champ
    "rendement_bois": 3.2,
}

# kind : add (+X par action), mult (×X sur la récolte), chance (p de +X), crop_add (+X par champ récolté),
#        crops_mult (×X sur toutes les cultures), time (×X sur le temps, efficacité réduite par la nuit),
#        feed (×X sur la nourriture), xp (×X d'XP, pas de Flower), fixed (gain/jour estimé)
B = {
    "Tunnel Mole": [("add", "Stone", 0.25)],
    "Rock Golem": [("chance", "Stone", 0.10, 2)],
    "Tin Turtle": [("add", "Stone", 0.1, 0.3)],          # 3×3 : ~30 % des rochers
    "Rocky the Mole": [("add", "Iron", 0.25)],
    "Iron Idol": [("add", "Iron", 1)],
    "Nugget": [("add", "Gold", 0.25)],
    "Emerald Turtle": [("add", "Stone", 0.5, 0.3), ("add", "Iron", 0.5, 0.3), ("add", "Gold", 0.5, 0.3)],
    "Crim Peckster": [("add", "Crimstone", 0.1)],
    "Crimson Carp": [("add", "Crimstone", 0.05)],
    "Woody the Beaver": [("mult", "Wood", 1.2)],
    "Apprentice Beaver": [("mult", "Wood", 1.2)],
    "Tiki Totem": [("add", "Wood", 0.1)],
    "Wood Nymph Wendy": [("add", "Wood", 0.2)],
    "Scarecrow": [("crops_mult", None, 1.2), ("time", "crops", 0.85)],
    "Nancy": [("time", "crops", 0.85)],
    "Lunar Calendar": [("time", "crops", 0.9)],
    "Kernaldo": [("time", "Corn", 0.75)],
    "Sheaf of Plenty": [("crop_add", "Barley", 2)],
    "Sickle": [("crop_add", "Wheat", 2)],
    "Corn Silk Hair": [("crop_add", "Corn", 2)],
    "Queen Cornelia": [("crop_add", "Corn", 1, 0.25)],    # zone 3×4
    "Poppy": [("crop_add", "Corn", 0.1)],
    "Corn Onesie": [("crop_add", "Corn", 0.1)],
    "Foliant": [("crop_add", "Kale", 0.2)],
    "Giant Kale": [("crop_add", "Kale", 2)],
    "Longhorn Cowfish": [("animal", "Milk", 0.2)],
    "Milk Apron": [("animal", "Milk", 0.5)],
    "Spa Cow": [("animal", "Milk", 0.1)],
    "Moo-ver": [("animal", "Leather", 0.25)],
    "Mootant": [("animal", "Leather", 0.1)],
    "Rich Chicken": [("hen", "Egg", 0.1)],
    "Undead Rooster": [("hen", "Egg", 0.1)],
    "Squid Chicken": [("hen", "Egg", 0.1)],
    "Ayam Cemani": [("hen", "Egg", 0.2)],
    "Alien Chicken": [("hen", "Feather", 0.1)],
    "Fat Chicken": [("feed", "hen", 0.9)],
    "Speed Chicken": [("time", "hen", 0.9)],
    "El Pollo Veloz": [("time", "hen", 0.75)],
    "Mammoth": [("time", "cow", 0.75)],
    "Baby Cow": [("fixed", None, 0.28 / 15)],            # +10 XP par caresse ≈ 0,28 FLW/jour pour 15 vaches
    "Observatory": [("xp", None, 1.05)],
    "Grain Grinder": [("xp", None, 1.2, "gâteaux")],
    "Blossombeard": [("xp", None, 1.1)],
}
CONFLITS = {  # n'apporte rien de plus si l'autre est déjà là
    "Apprentice Beaver": "Woody the Beaver", "Woody the Beaver": "Apprentice Beaver",
    "Nancy": "Scarecrow",
}
WEARABLES = {"Milk Apron", "Corn Silk Hair", "Corn Onesie"}


FR = {"Stone": "pierre", "Iron": "fer", "Gold": "or", "Crimstone": "crimstone", "Wood": "bois", "Wheat": "blé",
      "Barley": "orge", "Corn": "maïs", "Kale": "chou kale", "Milk": "lait", "Leather": "cuir", "Egg": "œuf",
      "Feather": "plume", "Sunflower": "tournesol", "Potato": "pomme de terre", "Rhubarb": "rhubarbe",
      "Pumpkin": "citrouille", "Zucchini": "courgette", "Carrot": "carotte", "Yam": "igname", "Cabbage": "chou",
      "Broccoli": "brocoli", "Soybean": "soja", "Beetroot": "betterave", "Pepper": "poivron", "Cauliflower": "chou-fleur",
      "Parsnip": "panais", "Eggplant": "aubergine", "Onion": "oignon", "Radish": "radis", "Turnip": "navet",
      "Artichoke": "artichaut"}
OUTIL = {"Stone": "coup de pioche sur un rocher de pierre", "Iron": "coup de pioche sur un rocher de fer",
         "Gold": "coup de pioche sur un rocher d'or", "Crimstone": "coup de pioche sur un rocher de crimstone",
         "Wood": "arbre coupé"}
ZONE = {"Tin Turtle": " (seulement les rochers dans une zone de 3×3 autour de lui)",
        "Emerald Turtle": " (seulement les rochers dans une zone de 3×3 autour de lui)",
        "Queen Cornelia": " (seulement les champs dans une zone de 3×4 autour d'elle)"}
SPECIAL = {"Baby Cow": "+10 XP pour la vache à chaque caresse → tes vaches montent de niveau plus vite",
           "Mammoth": "Les vaches dorment 25 % moins longtemps (inutile si tu es limité par les bounties de vaches)",
           "Scarecrow": "+20 % de récolte sur toutes tes cultures, et elles poussent 15 % plus vite",
           "Speed Chicken": "Les poules dorment 10 % moins longtemps → plus d'œufs par jour",
           "El Pollo Veloz": "Les poules dorment 2 h de moins → plus d'œufs par jour",
           "Fat Chicken": "Les poules mangent 10 % de nourriture en moins",
           "Grain Grinder": "+20 % d'XP quand tu manges des gâteaux"}


def effet(name):
    """L'effet du NFT en clair : +combien, de quoi, quand."""
    if name in SPECIAL:
        return SPECIAL[name]
    out = []
    for e in B[name]:
        k = e[0]
        if k == "add":
            out.append(f"+{e[2]:g} {FR[e[1]]} à chaque {OUTIL[e[1]]}")
        elif k == "chance":
            out.append(f"{e[2]:.0%} de chance d'avoir +{e[3]:g} {FR[e[1]]} à chaque {OUTIL[e[1]]}")
        elif k == "mult":
            out.append(f"+{(e[2] - 1) * 100:.0f} % de {FR[e[1]]} à chaque {OUTIL[e[1]]}")
        elif k == "crop_add":
            out.append(f"+{e[2]:g} {FR[e[1]]} à chaque champ de {FR[e[1]]} récolté")
        elif k == "time":
            if e[1] == "crops":
                out.append(f"Toutes tes cultures poussent {(1 - e[2]) * 100:.0f} % plus vite")
            else:
                out.append(f"Le {FR.get(e[1], e[1])} pousse {(1 - e[2]) * 100:.0f} % plus vite")
        elif k == "animal":
            out.append(f"+{e[2]:g} {FR[e[1]]} à chaque fois qu'une vache produit")
        elif k == "hen":
            out.append(f"+{e[2]:g} {FR[e[1]]} à chaque fois qu'une poule produit")
        elif k == "xp":
            out.append(f"+{(e[2] - 1) * 100:.0f} % d'XP sur tout ce que tu fais")
    import re
    txt = " · ".join(out) + ZONE.get(name, "")
    txt = re.sub(r"(\d)\.(\d)", r"\1,\2", txt).replace("de orge", "d'orge").replace("(\d)%", "")
    return re.sub(r"(\d)%", r"\1 %", txt)


# Saisons de chaque culture (code du jeu, seeds.ts → SEASONAL_SEEDS)
SAISONS = {"Sunflower": ["spring", "summer"], "Potato": ["summer", "autumn", "winter"], "Rhubarb": ["spring"], "Pumpkin": ["autumn"], "Zucchini": ["summer"], "Carrot": ["spring", "autumn"], "Yam": ["autumn"], "Cabbage": ["spring", "winter"], "Broccoli": ["autumn"], "Soybean": ["spring", "autumn"], "Beetroot": ["summer", "winter"], "Pepper": ["summer"], "Cauliflower": ["summer", "winter"], "Parsnip": ["winter"], "Eggplant": ["summer"], "Corn": ["spring"], "Onion": ["winter"], "Radish": ["summer"], "Wheat": ["spring", "summer", "autumn", "winter"], "Turnip": ["winter"], "Kale": ["spring", "winter"], "Artichoke": ["autumn"], "Barley": ["spring", "autumn"]}
SAISON_FR = {"spring": "printemps", "summer": "été", "autumn": "automne", "winter": "hiver"}
PART_EN_SAISON = 0.5  # on suppose que tu mettrais la moitié de tes champs sur cette culture pendant sa saison

PRIX_COURANT = {}
VOYELLE = lambda w: w[:1].lower() in "aeiouyéèh"
art = lambda r: ("l'" if VOYELLE(FR.get(r, r)) else "le ") + FR.get(r, r)
de = lambda r: ("d'" if VOYELLE(FR.get(r, r)) else "de ") + FR.get(r, r)
du = lambda r: ("de l'" if VOYELLE(FR.get(r, r)) else "du ") + FR.get(r, r)

RES_NODES = {"Stone", "Iron", "Gold", "Crimstone", "Wood"}
FRUITS = ["Tomato", "Lemon", "Blueberry", "Orange", "Apple", "Banana", "Grape", "Rice", "Olive"]
CROPS = ["Sunflower", "Potato", "Rhubarb", "Pumpkin", "Zucchini", "Carrot", "Yam", "Cabbage", "Broccoli", "Soybean",
         "Beetroot", "Pepper", "Cauliflower", "Parsnip", "Eggplant", "Corn", "Onion", "Radish", "Wheat", "Turnip",
         "Kale", "Artichoke", "Barley"]


def effets_auto(textes):
    """Transforme le texte d'effet du jeu (ex. « +0.25 Iron ») en effet chiffrable. Ce qui ne se chiffre pas est ignoré."""
    out, aoe = [], any("AOE" in t or "Affects plots" in t or "Area of Effect" in t for t in textes)
    for t in textes:
        m = re.match(r"^\+(\d*\.?\d+) (Stone|Iron|Gold|Crimstone|Wood)s?$", t)
        if m:
            out.append(("add", m.group(2), float(m.group(1)), 0.3 if aoe else 1)); continue
        m = re.match(r"^\+(\d*\.?\d+) Stone, Iron, Gold", t)
        if m:
            out += [("add", r, float(m.group(1)), 0.3 if aoe else 1) for r in ("Stone", "Iron", "Gold")]; continue
        m = re.match(r"^\+(\d*\.?\d+) Wood & Minerals", t)
        if m:
            out += [("add", r, float(m.group(1)), 0.3 if aoe else 1) for r in ("Wood", "Stone", "Iron", "Gold", "Crimstone")]; continue
        m = re.match(r"^\+(\d*\.?\d+) Crimstone every 5th mine", t)
        if m:
            out.append(("add", "Crimstone", float(m.group(1)) / 5)); continue
        m = re.match(r"^x(\d*\.?\d+) Wood$", t)
        if m:
            out.append(("mult", "Wood", float(m.group(1)))); continue
        m = re.match(r"^\+(\d*\.?\d+) (" + "|".join(CROPS) + r")$", t)
        if m:
            out.append(("crop_add", m.group(2), float(m.group(1)), 0.15 if aoe else 1)); continue
        m = re.match(r"^\+(\d*\.?\d+) (?:Crops & Fruits|crop yield|Crops)$", t, re.I)
        if m:
            out += [("crop_add", c, float(m.group(1)), 0.15 if aoe else 1) for c in CROPS]; continue
        m = re.match(r"^x(\d*\.?\d+) Crop Yield$", t)
        if m:
            out.append(("crops_mult", None, float(m.group(1)))); continue
        m = re.match(r"^\+(\d*\.?\d+) (Milk|Leather)$", t)
        if m:
            out.append(("animal", m.group(2), float(m.group(1)))); continue
        m = re.match(r"^\+(\d*\.?\d+) (Egg|Feather)s?$", t)
        if m:
            out.append(("hen", m.group(2), float(m.group(1)))); continue
        m = re.match(r"^x(0\.\d+) (?:Crop|Crop Plot) Growth Time$", t)
        if m and not aoe:
            out.append(("time", "crops", float(m.group(1)))); continue
        m = re.match(r"^x(0\.\d+) (" + "|".join(CROPS) + r") Growth Time$", t)
        if m:
            out.append(("time", m.group(2), float(m.group(1)))); continue
        m = re.match(r"^x(0\.\d+) Chicken Sleep Time$", t)
        if m:
            out.append(("time", "hen", float(m.group(1)))); continue
        m = re.match(r"^x(0\.\d+) Cow Sleep Time$", t)
        if m:
            out.append(("time", "cow", float(m.group(1)))); continue
        m = re.match(r"^x(1\.\d+) Bumpkin XP", t)
        if m:
            out.append(("xp", None, float(m.group(1)))); continue
    return out


def _effets_jeu():
    try:
        from pathlib import Path
        return json.loads((Path(__file__).resolve().parent / "nft_effets_jeu.json").read_text())
    except Exception:
        return {}


def _prod(cfg):
    mp = cfg.get("ma_production") or {}
    if not mp:   # rien de lu ni mesuré : ferme type (les conseils d'achat sont alors masqués)
        return {**DEFAULT_PROD, "recoltes": dict(DEFAULT_PROD["recoltes"])}
    # Ferme lue ou mesurée : ce qui n'est pas connu compte pour zéro, jamais les chiffres d'une autre ferme
    base = {k: v for k, v in DEFAULT_PROD.items() if k.startswith("rendement_")}
    base.update({k: 0 for k in DEFAULT_PROD if not k.startswith("rendement_") and k != "recoltes"})
    p = {**base, **mp}
    p["recoltes"] = dict(mp.get("recoltes") or {})
    return p


def _base_cultures(prod, pr):
    """Valeur de tes récoltes par jour, avec TON mélange de cultures (habitudes) et tes rendements."""
    rc = prod.get("rendements_cultures") or {}
    parts = prod.get("parts_vie") or {}
    total = sum(prod["recoltes"].values())
    if parts and total:
        return sum(total * p * rc.get(c, prod["rendement_culture"]) * pr(c) for c, p in parts.items())
    return sum(n * rc.get(c, prod["rendement_culture"]) * pr(c) for c, n in prod["recoltes"].items())


def gain_par_jour(name, prices, prod, owned, entries=None):
    """Gain net (après taxe) en Flower par jour, et une phrase d'explication."""
    pr = lambda k: (prices.get(k) or 0) * (1 - TAX)
    total, why, xp = 0.0, [], None
    seuils = []
    for e in (entries if entries is not None else B[name]):
        kind = e[0]
        if kind == "add":
            res, v = e[1], e[2]
            share = e[3] if len(e) > 3 else 1
            g = v * prod.get(res, 0) * share * pr(res)
            why.append(f"+{v:g} × {prod.get(res, 0) * share:g} coups/jour")
        elif kind == "chance":
            res, p_, v = e[1], e[2], e[3]
            g = p_ * v * prod[res] * pr(res)
            why.append(f"{p_:.0%} de chance de +{v:g} × {prod[res]:g} coups/jour")
        elif kind == "mult":
            res, m = e[1], e[2]
            base = prod[res] * prod["rendement_bois"]          # bois récolté par jour
            g = base * (1 - 1 / m) * pr(res)                   # part de la récolte due au bonus
            why.append(f"×{m:g} sur ~{base:.0f} bois/jour")
        elif kind == "crop_add":
            res, v = e[1], e[2]
            share = e[3] if len(e) > 3 else 1
            ss = SAISONS.get(res, ["spring", "summer", "autumn", "winter"])
            saison_txt = " et ".join(SAISON_FR[x] for x in ss) if len(ss) < 4 else "toute l'année"
            parts = prod.get("parts_vie") or {}
            if parts and (len(ss) < 4 or not prod.get("mesure_reelle")):
                # Culture de saison : ta part habituelle (depuis le début de ta ferme) × ton rythme actuel de récolte
                part = parts.get(res, 0)
                n = sum(prod["recoltes"].values()) * part * share
                why.append(f"+{v:g} × ~{n:.0f} champs/jour en moyenne sur l'année : {art(res)} fait {part:.0%} "
                           f"de tout ce que tu as récolté depuis le début ({saison_txt})"
                           + ("" if prod.get("mesure_reelle") else " · rythme de récolte estimé jusqu'au relevé de demain"))
            elif prod.get("mesure_reelle"):
                # Ce que tu récoltes vraiment (moyenne des derniers jours), sans hypothèse
                n = prod["recoltes"].get(res, 0) * share
                why.append(f"+{v:g} × {n:g} champs {de(res)} que tu récoltes vraiment par jour (moyenne mesurée)")
            else:
                champs = prod.get("champs_total") or sum(prod["recoltes"].values()) / 1.7
                n = max(prod["recoltes"].get(res, 0), champs * 1.7 * PART_EN_SAISON) * len(ss) / 4 * share
                why.append(f"⏳ hypothèse : +{v:g} × ~{n:.0f} champs/jour (moitié de tes champs en {FR.get(res, res)} en "
                           f"{saison_txt}) — remplacé par tes vraies récoltes dès demain")
            g = v * n * pr(res)
            if pr(res) > 0:
                seuils.append((res, v * pr(res), saison_txt))
        elif kind == "crops_mult":
            m = e[2]
            g = _base_cultures(prod, pr) * (1 - 1 / m)
            why.append(f"×{m:g} sur toutes tes récoltes (avec ton mélange habituel de cultures)")
        elif kind == "time":
            target, m = e[1], e[2]
            eff = 0.5  # la nuit et tes horaires limitent le gain de vitesse
            if target in RES_NODES:
                base = 0  # rochers et arbres : tu passes déjà ~6 fois par jour, plus de vitesse ne change presque rien
            elif target == "crops":
                base = _base_cultures(prod, pr)
            elif target == "hen":
                base = prod["cycles_poules"] * 2 * pr("Egg")
            elif target == "cow":
                base = 0  # limité par les bounties de vaches
            else:
                # une culture précise : ce que TU en récoltes d'habitude (pas d'hypothèse)
                parts = prod.get("parts_vie") or {}
                n = sum(prod["recoltes"].values()) * parts.get(target, 0) if parts else prod["recoltes"].get(target, 0)
                base = n * (prod.get("rendements_cultures") or {}).get(target, prod["rendement_culture"]) * pr(target)
            if target == "crops" or target in CROPS:
                eff = 1.0   # tes champs ne restent jamais vides (plantations calées sur la nuit) : toute la vitesse compte
                why.append(f"temps ×{m:g} : tes cultures poussent {(1 - m) * 100:.0f} % plus vite, donc {(1 / m - 1) * 100:.0f} % de récoltes en plus. "
                           f"⚠️ Compté à 100 % : ça suppose que tes champs ne restent jamais vides (tu replantes dès qu'ils sont prêts "
                           f"et tu cales des cultures longues pour la nuit). Si tes champs restent souvent vides, le gain réel est plus faible")
            else:
                why.append(f"temps ×{m:g} (gain réduit de moitié : la nuit, tu ne ramasses pas)")
            g = base * (1 / m - 1) * eff
        elif kind == "animal":
            res, v = e[1], e[2]
            g = v * prod["cycles_vaches"] * pr(res)
            why.append(f"+{v:g} × {prod['cycles_vaches']:g} récoltes de lait/jour")
        elif kind == "hen":
            res, v = e[1], e[2]
            g = v * prod["cycles_poules"] * pr(res)
            why.append(f"+{v:g} × {prod['cycles_poules']:g} récoltes d'œufs/jour")
        elif kind == "feed":
            g = prod["cycles_poules"] * 1.92 * (prices.get("Wheat") or 0) * (1 - e[2])
            why.append(f"−{1 - e[2]:.0%} de nourriture pour les poules")
        elif kind == "fixed":
            g = e[2] * prod["vaches"]
            why.append("+10 XP par caresse → vaches plus vite au niveau suivant (estimation)")
        elif kind == "xp":
            g = 0
            xp = f"×{e[2]:g} XP" + (f" ({e[3]})" if len(e) > 3 else "")
            why.append(xp + " : rapporte de l'XP, pas de Flower")
        total += g
    other = CONFLITS.get(name)
    if other and other in owned and name not in owned:
        total, why = 0.0, [f"ne s'ajoute pas à ton {other}"]
    price = PRIX_COURANT.get(name)
    if seuils and price and len(seuils) == 1 and prod.get("champs_total"):
        res, par_champ, saison_txt = seuils[0]
        plein = prod["champs_total"]
        gain_plein = par_champ * plein                         # un champ complet récolté avec ce bonus
        besoin_an = price * 0.35 / gain_plein                  # récoltes complètes par an pour 35 %/an
        fait_4s = (total / gain_plein) * 28 if gain_plein else 0
        why[:] = [w for w in why]
        virg = lambda x, d=1: f"{x:.{d}f}".replace(".", ",")
        why.append(f"🌾 1 récolte complète {de(res)} ({plein} champs) = +{virg(gain_plein, 2)} FLW avec ce bonus · "
                   f"rentable (35 %/an) à partir de {virg(besoin_an / 13)} récoltes complètes toutes les 4 semaines "
                   f"(saison : {saison_txt}) · avec tes habitudes tu en fais ~{virg(fait_4s)}")
    return total, " · ".join(why), xp


NOM_NOEUD = {"Stone": "rochers de pierre", "Iron": "rochers de fer", "Gold": "rochers d'or", "Crimstone": "rochers de crimstone",
             "Wood": "arbres"}


def _fr(x, d=0):
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def potentiel(entries, prices, prod, owned=(), textes=None):
    """Ce que tu fais aujourd'hui (en clair) et le gain par jour si tu optimises au maximum."""
    pr = lambda k: (prices.get(k) or 0) * (1 - TAX)
    if not entries:
        return None
    e = entries[0]
    k, res = e[0], e[1]
    mesure = prod.get("mesure_reelle")
    quand = "mesuré sur tes derniers jours" if mesure else "estimé, mesuré à partir du prochain relevé"
    noeuds = (prod.get("noeuds") or {}).get(res) if res else None
    if k in ("add", "chance") and res in NOM_NOEUD:
        actu = prod.get(res, 0)
        mx = (prod.get("max_actions") or {}).get(res) or actu
        share = e[3] if k == "add" and len(e) > 3 else 1
        par_action = (e[2] * share if k == "add" else e[2] * e[3]) * pr(res)
        verbe = "coupes" if res == "Wood" else "mines"
        txt = (f"Aujourd'hui tu {verbe} {_fr(actu)} fois par jour" + (f" sur tes {noeuds} {NOM_NOEUD[res]}" if noeuds else "")
               + f" ({quand})")
        opt = (f"si tu récoltes chacun de tes {noeuds} {NOM_NOEUD[res]} dès qu'il est prêt (~{_fr(mx)} fois par jour)"
               if noeuds else None)
        return {"actuel": txt, "g_max": mx * par_action, "opt": opt,
                "cur": {"unite": "coups par jour" if res != "Wood" else "arbres coupés par jour", "actu": actu, "max": mx, "gain_u": par_action}}
    if k in ("animal", "hen"):
        bete = "vache" if k == "animal" else "poule"
        nb = prod.get("vaches" if k == "animal" else "poules") or 0
        actu = prod.get("cycles_vaches" if k == "animal" else "cycles_poules", 0)
        mx = nb * (1 if k == "animal" else 2)
        txt = (f"Aujourd'hui tu récoltes une {bete} {_fr(actu)} fois par jour (chaque clic sur une {bete} qui a produit)"
               + (f" · tu as {nb} {bete}s" if nb else "") + f" ({quand})")
        opt = f"si tu récoltes tes {nb} {bete}s à chaque cycle (~{_fr(mx)} récoltes par jour)" if nb else None
        return {"actuel": txt, "g_max": mx * e[2] * pr(res), "opt": opt,
                "cur": {"unite": f"récoltes de {bete} par jour", "actu": actu, "max": mx, "gain_u": e[2] * pr(res)}}
    if k == "crop_add":
        ss = SAISONS.get(res, ["spring", "summer", "autumn", "winter"])
        plein = prod.get("champs_total") or 0
        freq = prod.get("frequence_recolte", 1.7)
        share = e[3] if len(e) > 3 else 1
        parts = prod.get("parts_vie") or {}
        n_actu = sum(prod["recoltes"].values()) * parts.get(res, 0) if parts else prod["recoltes"].get(res, 0)
        rec4 = n_actu * 28 / plein if plein else 0
        mx = plein * freq * len(ss) / 4
        mx4 = mx * 28 / plein if plein else 0
        saison_txt = " et ".join(SAISON_FR[x] for x in ss) if len(ss) < 4 else "toute l'année"
        txt = (f"Aujourd'hui tu fais ~{_fr(rec4, 1)} récoltes complètes {de(res)} ({plein} champs) toutes les 4 semaines ({quand})")
        opt = f"si tu plantes tous tes champs en {FR.get(res, res)} pendant sa saison ({saison_txt}) : ~{_fr(mx4, 1)} récoltes complètes toutes les 4 semaines"
        # Planter plus de cette culture = moins d'une autre (ta culture principale) : ce que tu perds en face
        rd = prod.get("rendements_cultures") or {}
        autres = {c: v for c, v in (parts or prod["recoltes"]).items() if c != res and v}
        alt = max(autres, key=autres.get) if autres else None
        bonus_alt = 0.0
        if alt:
            for o in owned:
                for e2 in (B.get(o) or effets_auto((textes or {}).get(o, []))):
                    if e2[0] == "crop_add" and e2[1] == alt:
                        bonus_alt += e2[2] * (e2[3] if len(e2) > 3 else 1)
        y_res, y_alt = rd.get(res, prod.get("rendement_culture", 2.7)), rd.get(alt, prod.get("rendement_culture", 2.7)) if alt else 0
        jour_u = plein / 28   # une récolte complète en plus toutes les 4 semaines = plein/28 champs par jour
        return {"actuel": txt, "g_max": mx * e[2] * share * pr(res), "opt": opt,
                "cur": {"unite": "récoltes complètes toutes les 4 semaines", "actu": rec4, "max": mx4,
                        "gain_u": e[2] * share * pr(res) * jour_u,
                        "culture": FR.get(res, res), "alt": FR.get(alt, alt) if alt else None,
                        "echange_u": ((y_res * pr(res)) - (y_alt * pr(alt) + bonus_alt * pr(alt))) * jour_u if alt else 0}}
    return None


# Catégories de cultures du jeu (basiques, moyennes, avancées)
CAT_CULTURE = {**{c: "Basiques" for c in ("Sunflower", "Potato", "Rhubarb", "Pumpkin", "Zucchini")},
               **{c: "Moyennes" for c in ("Carrot", "Yam", "Cabbage", "Broccoli", "Soybean", "Beetroot", "Pepper",
                                           "Cauliflower", "Parsnip")},
               **{c: "Avancees" for c in ("Eggplant", "Corn", "Onion", "Radish", "Wheat", "Turnip", "Kale", "Artichoke",
                                           "Barley")}}
ACTIVITE_FR = {"Basiques": "🌱 cultures basiques", "Moyennes": "🥕 cultures moyennes", "Avancees": "🌽 cultures avancées",
               "Wood": "🪵 bois", "Stone": "🪨 pierre", "Iron": "⛓️ fer", "Gold": "🥇 or", "Crimstone": "💎 crimstone",
               "Vaches": "🐄 vaches", "Poules": "🐔 poules"}


def cibles_nft(entries):
    """Activités de la ferme qu'un NFT améliore (pour ne conseiller que ce qui colle à ta façon de jouer)."""
    out = set()
    for e in entries or []:
        k, res = e[0], e[1]
        if k in ("add", "chance", "mult") and res in RES_NODES:
            out.add(res)
        elif k in ("crop_add", "time") and res in CAT_CULTURE:
            out.add("crop:" + res)   # une culture précise : il faut que TU la plantes beaucoup
        elif k == "crops_mult" or (k == "time" and res == "crops"):
            out |= {"Basiques", "Moyennes", "Avancees"}
        elif k == "animal" or (k == "time" and res == "cow") or (k == "fixed" and res is None):
            out.add("Vaches")
        elif k == "hen" or (k in ("time", "feed") and res == "hen"):
            out.add("Poules")
    return sorted(out)


def profil_ferme(prod, prices, rendements=None):
    """Ce que la ferme fait vraiment : quantité et valeur (FLW/jour, après taxe) par activité, et ses activités principales."""
    pr = lambda k: (prices.get(k) or 0) * (1 - TAX)
    y = {"Stone": 4.13, "Iron": 1.93, "Gold": 1.81, "Crimstone": 4.2, "Wood": prod.get("rendement_bois", 3.2),
         **{k: v for k, v in (rendements or {}).items() if isinstance(v, (int, float))}}
    act = {}
    def ajoute(cle, actions, unite, valeur, detail=None):
        a = act.setdefault(cle, {"cle": cle, "nom": ACTIVITE_FR[cle], "actions": 0.0, "unite": unite, "flw": 0.0, "detail": {}})
        a["actions"] += actions
        a["flw"] += valeur
        if detail:
            a["detail"][detail] = a["detail"].get(detail, 0) + actions
    for k in ("Stone", "Iron", "Gold", "Crimstone", "Wood"):
        n = prod.get(k) or 0
        if n >= 0.5:
            ajoute(k, n, "arbres coupés/jour" if k == "Wood" else "coups/jour", n * y[k] * pr(k))
    rc = prod.get("rendements_cultures") or {}
    for c, n in (prod.get("recoltes") or {}).items():
        if n and c in CAT_CULTURE:
            ajoute(CAT_CULTURE[c], n, "champs/jour", n * rc.get(c, y.get(c, prod.get("rendement_culture", 2.7))) * pr(c), c)
    if prod.get("cycles_vaches"):
        n = prod["cycles_vaches"]
        ajoute("Vaches", n, "récoltes/jour", n * (y.get("Milk") or 1) * pr("Milk"))
    if prod.get("cycles_poules"):
        n = prod["cycles_poules"]
        ajoute("Poules", n, "récoltes/jour", n * (y.get("Egg") or 1) * pr("Egg"))
    rows = sorted(act.values(), key=lambda a: -a["flw"])
    tot_flw = sum(a["flw"] for a in rows) or 1
    champs = sum(a["actions"] for a in rows if a["cle"] in ("Basiques", "Moyennes", "Avancees")) or 1
    for a in rows:
        a["part"] = a["flw"] / tot_flw
        a["actions"] = round(a["actions"], 1)
        a["flw"] = round(a["flw"], 2)
        a["detail"] = [c for c, _ in sorted(a["detail"].items(), key=lambda x: -x[1])[:4]]
        # Rochers et arbres : quelle part de ce qu'ils pourraient donner tu exploites vraiment
        mx = (prod.get("max_actions") or {}).get(a["cle"])
        a["usage"] = round(min(1.0, a["actions"] / mx), 2) if mx else None
        # Principale : pèse au moins 10 % de ce que rapporte la ferme (et, pour les rochers, tu les exploites à 20 % ou plus),
        # ou (cultures) au moins 25 % des champs récoltés
        a["principale"] = ((a["part"] >= 0.10 and (a["usage"] is None or a["usage"] >= 0.20))
                           or (a["cle"] in ("Basiques", "Moyennes", "Avancees") and a["actions"] / champs >= 0.25))
    # Cultures principales : au moins 10 % de tes champs récoltés (rythme mesuré, sinon tes habitudes depuis le début)
    rec = {c: n for c, n in (prod.get("recoltes") or {}).items() if n}
    parts = {c: n / sum(rec.values()) for c, n in rec.items()} if rec else dict(prod.get("parts_vie") or {})
    cultures = [c for c, x in sorted(parts.items(), key=lambda x: -x[1]) if x >= 0.10]
    return {"activites": rows, "principales": [a["cle"] for a in rows if a["principale"]] + ["crop:" + c for c in cultures],
            "cultures": cultures}


def analyse_nft(holdings, prices, cfg, source="défaut", fiable=True):
    prod = _prod(cfg)
    PRIX_COURANT.clear()
    PRIX_COURANT.update({k: v for k, v in prices.items() if isinstance(v, (int, float))})
    textes = _effets_jeu()
    pas_nft = set(CROPS) | set(FRUITS) | {"Wood", "Stone", "Iron", "Gold", "Crimstone", "Obsidian", "Milk", "Leather", "Egg",
                                          "Feather", "Wool", "Honey", "Truffle", "Pig Bristles"}
    portes = set(cfg.get("nft_possedes") or [])
    noms = (set(B) | {n for n in textes if prices.get(n) or (holdings.get(n) or 0) > 0} | portes) - pas_nft
    owned = {n for n in noms if (holdings.get(n) or 0) > 0} | portes
    rows = []
    for name in noms:
        price = prices.get(name)
        entries = B.get(name) or effets_auto(textes.get(name, []))
        texte_jeu = " · ".join(t for t in textes.get(name, []) if "{{" not in t)
        chiffrable = bool(entries)
        if chiffrable:
            g, why, xp = gain_par_jour(name, prices, prod, owned, entries)
        else:
            g, why, xp = 0.0, "effet qui ne se chiffre pas en Flower", None
        an = g * 365 / price * 100 if price else None
        mine = name in owned
        if mine:
            if xp:
                v, c = "💤 À vendre si ton but est de gagner des Flower (il ne donne que de l'XP)", "neutral"
            elif not chiffrable:
                v, c = "➖ Effet non chiffrable en Flower (confort, cuisine, pêche, marks…)", "neutral"
            elif an is None:
                v, c = "Garder", "pos"
            elif g <= 0.001:
                v, c = "➖ Ne rapporte rien sur ta ferme actuelle : tu peux le vendre", "neutral"
            elif an >= 40:
                v, c = "✅ Garder : il rapporte bien", "pos"
            elif an >= 15:
                v, c = "👍 Garder : rapporte correctement", "pos"
            else:
                v, c = "➖ Rapporte peu : tu peux le vendre si tu as besoin de Flower", "neutral"
        else:
            if xp:
                v, c = "Seulement si ton objectif est l'XP", "neutral"
            elif not chiffrable:
                v, c = "➖ Effet non chiffrable en Flower", "neutral"
            elif not fiable:
                v, c = "⚠️ Pas calculable : ta ferme n'a pas pu être lue (réessaie Actualiser)", "neutral"
            elif g <= 0.001 and why.startswith("ne s'ajoute"):
                v, c = "❌ Inutile : " + why, "neg"
            elif g <= 0.001:
                v, c = "❌ N'apporte rien sur ta ferme (tu ne produis pas ce qu'il améliore)", "neg"
            elif an is None:
                v, c = "Prix inconnu", "neutral"
            elif an >= 60:
                v, c = "🟢 Bon achat", "pos"
            elif an >= 35:
                v, c = "🟡 Correct", "neutral"
            else:
                v, c = "❌ Trop cher pour ce qu'il rapporte", "neg"
        if not fiable and not mine:
            g, an = 0.0, None
        pot = potentiel(entries, prices, prod, owned, textes) if chiffrable and not xp else None
        # Pertinence : le NFT améliore-t-il quelque chose que tu produis vraiment ?
        pas_pour_toi = None
        if chiffrable and not xp and entries:
            e0 = entries[0]
            parts = prod.get("parts_vie") or {}
            cible = e0[1] if e0[0] in ("crop_add", "time") and e0[1] in CROPS else None
            if cible and parts and parts.get(cible, 0) < 0.03:
                pas_pour_toi = f"tu ne plantes presque jamais {de(cible)} ({parts.get(cible, 0):.0%} de tes récoltes)"
            elif e0[0] in ("add", "chance") and e0[1] in RES_NODES and prod.get(e0[1], 0) < 1:
                pas_pour_toi = f"tu n'as pas de {NOM_NOEUD.get(e0[1], e0[1])} ou tu ne les récoltes pas"
            elif e0[0] == "animal" and not prod.get("vaches"):
                pas_pour_toi = "tu n'as pas de vaches"
            elif e0[0] == "hen" and not prod.get("cycles_poules"):
                pas_pour_toi = "tu n'as pas de poules"
        an_max = (pot["g_max"] * 365 / price * 100) if (pot and price and pot.get("opt")) else None
        mois = (price / g / 30) if (price and g > 0.001) else None
        note = ("🔴 Pas rentable" if mois is None else "🟢 Très rentable" if mois < 12 else "🟡 Correct" if mois < 24
                else "🟠 Moyen" if mois < 36 else "🔴 Pas rentable")
        if pas_pour_toi and not mine:
            note = "🚫 Pas pour toi"
        rows.append({"cibles": cibles_nft(entries) if chiffrable and not xp else [], "pas_pour_toi": pas_pour_toi, "note": note if chiffrable and not xp and fiable else None, "pot": pot, "an_max": an_max,
                     "mois_max": (price / pot["g_max"] / 30) if (pot and price and pot["g_max"] > 0.001) else None,
                     "n": name, "effet": effet(name) if name in B else texte_jeu, "owned": mine,
                     "wearable": name in WEARABLES, "price": price, "jour": g, "chiffrable": chiffrable,
                     "mois": g * 30, "an_pct": an, "rembourse_jours": (price / g) if price and g > 0.001 else None,
                     "why": why, "xp": xp, "verdict": v, "cls": c})
    rows.sort(key=lambda r: (not r["owned"], not r["chiffrable"], -(r["an_pct"] or -1)))
    return {"rows": rows, "prod": prod, "source": source,
            "profil": profil_ferme(prod, prices, cfg.get("rendements")) if fiable else None}


def mesure_production(stock_hist, trades, rendements, jours_min=3):
    """Production réelle par jour, mesurée sur ta ferme : (stock fin − stock début + vendu − acheté) ÷ jours.

    Retourne (production, nb_jours). Sous-estime un peu ce que tu consommes toi-même (outils, nourriture).
    """
    from datetime import date
    h = sorted(stock_hist, key=lambda x: x["date"])[-15:]
    if len(h) < 2:
        return {}, 0
    a, b = h[0], h[-1]
    d0, d1 = date.fromisoformat(a["date"]), date.fromisoformat(b["date"])
    jours = (d1 - d0).days
    if jours < jours_min:
        return {}, jours
    import datetime as _dt
    t0 = _dt.datetime(d0.year, d0.month, d0.day).timestamp() * 1000
    t1 = _dt.datetime(d1.year, d1.month, d1.day).timestamp() * 1000
    flux = {}
    for t in trades:
        if t0 <= t["at"] < t1:
            flux[t["name"]] = flux.get(t["name"], 0) + (t["quantity"] if t["sold"] else -t["quantity"])
    par_jour = lambda k: max(0.0, ((b["stock"].get(k) or 0) - (a["stock"].get(k) or 0) + flux.get(k, 0)) / jours)
    y = {"Stone": 4.13, "Iron": 1.93, "Gold": 1.81, "Crimstone": 4.2, "Wood": 3.2, **(rendements or {})}
    prod = {k: round(par_jour(k) / y[k], 1) for k in ("Stone", "Iron", "Gold", "Crimstone", "Wood")}
    prod["cycles_vaches"] = round(par_jour("Milk") / 3.6, 1)
    prod["vaches"] = prod["cycles_vaches"]
    prod["cycles_poules"] = round(par_jour("Egg") / 2, 1)
    prod["recoltes"] = {c: round(par_jour(c) / 2.72, 1) for c in ("Wheat", "Barley", "Corn", "Kale")}
    return prod, jours


def lire_ferme_sflworld(page_html, skills):
    """Rochers, arbres et champs de LA ferme (page publique sfl.world/land/<numéro>), convertis en actions par jour.

    Hypothèse : tu passes ~6 fois par jour (7 h-23 h) ; un rocher prêt plus souvent n'est pas plus récolté.
    """
    import html as _h
    t = re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", page_html)))
    def nb(name):
        return sum(int(x) for x in re.findall(r"Nodes (?:\d+x [A-Za-z ]+\(Tier \d\) )*?(\d+)x " + name + r" \(Tier", t)) or \
            sum(int(x) for x in re.findall(r"(\d+)x " + name + r" \(Tier", t))
    noeuds = {"Stone": nb("Stone Rock"), "Iron": nb("Iron Rock"), "Gold": nb("Gold Rock"),
              "Crimstone": nb("Crimstone Rock"), "Wood": nb("Tree") + nb("Ancient Tree")}
    if not any(noeuds.values()):
        return None
    sk = skills or {}
    rec = {"Stone": 4 * (0.8 if "Speed Miner" in sk else 1),
           "Iron": 8 * (0.7 if "Iron Hustle" in sk else 1),
           "Gold": 24 * (0.9 if "Midas Sprint" in sk else 1) * (0.8 if "Midas Rush" in sk else 1),
           "Crimstone": 24 * (0.85 if "Fireside Alchemist" in sk else 1),
           "Wood": 2 * (0.9 if "Tree Charge" in sk else 1)}
    par_noeud = lambda h: min(6.0, 16 / h + 1) if h < 16 else 24 / h
    prod = {k: round(noeuds[k] * par_noeud(rec[k]), 1) for k in noeuds}
    max_actions = dict(prod)   # le maximum possible : chaque rocher/arbre récolté dès qu'il est prêt (7 h-23 h)
    champs = {}
    for c in CROPS:
        m = re.findall(r"(\d+)x " + c + r" \d", t)
        if m:
            champs[c] = int(m[0])
    prod["recoltes"] = {c: round(n * 1.7, 1) for c, n in champs.items()}
    prod["champs_total"] = sum(champs.values())
    for c in ("Wheat", "Barley", "Corn", "Kale"):
        prod["recoltes"].setdefault(c, 0)
    return {"prod": prod, "noeuds": noeuds, "champs": champs, "max_actions": max_actions}


def lire_animaux_sflworld(page_html):
    """Nombre de vaches et de poules (page publique sfl.world/land/<numéro>/animals)."""
    import html as _h
    t = re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", page_html)))
    out = {}
    for batiment, niveau, animal, n in re.findall(r"(Hen House|Barn) Level (\d+) Animal Amount ([A-Za-z]+) (\d+)", t):
        out[animal] = {"nombre": int(n), "batiment": batiment, "niveau": int(niveau)}
    return out


def lire_activite_sflworld(page_html):
    """Compteurs à vie de la ferme (page sfl.world/land/<numéro>/activity) : « Iron Mined 2089 », « Egg Collected »…"""
    import html as _h
    t = re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", page_html)))
    return {f"{n.strip()} {v}": float(x) for n, v, x in
            re.findall(r"([A-Z][A-Za-z' ]*?) (Mined|Harvested|Chopped|Collected|Points Earned) (\d+(?:\.\d+)?)", t)}


def rythme_reel(hist, jours_max=30):
    """Ce que tu fais vraiment par jour : écart des compteurs entre aujourd'hui et un relevé d'il y a 1 à 30 jours."""
    from datetime import date
    if len(hist) < 2:
        return None, 0
    fin = hist[-1]
    d1 = date.fromisoformat(fin["date"])
    debut = None
    for h in hist[:-1]:
        d = (d1 - date.fromisoformat(h["date"])).days
        if 1 <= d <= jours_max:
            debut = h
            break
    if not debut:
        return None, 0
    jours = (d1 - date.fromisoformat(debut["date"])).days
    r = lambda k: max(0.0, (fin["c"].get(k, 0) - debut["c"].get(k, 0)) / jours)
    prod = {"Stone": r("Stone Mined"), "Iron": r("Iron Mined"), "Gold": r("Gold Mined"),
            "Crimstone": r("Crimstone Mined"), "Wood": r("Tree Chopped"),
            "cycles_vaches": r("Milk Collected"), "cycles_poules": r("Egg Collected"),
            "recoltes": {c: r(f"{c} Harvested") for c in CROPS}}
    return {k: (round(v, 1) if isinstance(v, float) else {c: round(x, 1) for c, x in v.items()}) for k, v in prod.items()}, jours


COMPTEUR = {"Stone": "Stone Mined", "Iron": "Iron Mined", "Gold": "Gold Mined", "Crimstone": "Crimstone Mined",
            "Wood": "Tree Chopped", "Milk": "Milk Collected", "Leather": "Milk Collected", "Egg": "Egg Collected",
            "Feather": "Egg Collected"}
UNITE = {"Stone": "pierres minées", "Iron": "coups sur le fer", "Gold": "coups sur l'or", "Crimstone": "coups sur la crimstone",
         "Wood": "arbres coupés", "Milk": "récoltes de lait", "Leather": "récoltes de lait", "Egg": "récoltes d'œufs",
         "Feather": "récoltes d'œufs"}


def objectifs_saison(owned, prices, prod, saison, c_debut, c_now, jours_saison=7):
    """Pour chaque NFT que tu possèdes : ce qu'il faut faire cette saison pour qu'il rapporte au moins 35 %/an."""
    pr = lambda k: (prices.get(k) or 0) * (1 - TAX)
    textes = _effets_jeu()
    out = []
    for name in sorted(owned):
        price = prices.get(name)
        entries = B.get(name) or effets_auto(textes.get(name, []))
        if not price or not entries:
            continue
        e = entries[0]
        kind, res, v = e[0], e[1], e[2] if len(e) > 2 else 0
        share = e[3] if kind in ("add", "crop_add") and len(e) > 3 else 1
        if kind == "chance":
            v = e[2] * e[3]
        par_jour_35 = price * 0.35 / 365
        if kind in ("add", "chance", "animal", "hen") and res in COMPTEUR and pr(res) > 0 and v:
            cible = par_jour_35 / (v * share * pr(res)) * jours_saison
            fait = (c_now.get(COMPTEUR[res], 0) - c_debut.get(COMPTEUR[res], 0)) if c_debut else None
            out.append({"nft": name, "texte": f"{cible:.0f} {UNITE[res]}", "cible": cible, "fait": fait,
                        "quoi": f"{effet(name) if name in B else ' · '.join(textes.get(name, []))}"})
        elif kind == "crop_add" and pr(res) > 0 and prod.get("champs_total"):
            ss = SAISONS.get(res, ["spring", "summer", "autumn", "winter"])
            plein = prod["champs_total"]
            if saison not in ss:
                out.append({"nft": name, "texte": f"hors saison ({FR.get(res, res)} : {' et '.join(SAISON_FR[x] for x in ss)})",
                            "cible": None, "fait": None, "quoi": effet(name) if name in B else " · ".join(textes.get(name, []))})
                continue
            par_recolte = v * share * plein * pr(res)
            cible = par_jour_35 * 365 / par_recolte / (52 * len(ss) / 4)        # récoltes complètes par semaine de saison
            fait = ((c_now.get(f"{res} Harvested", 0) - c_debut.get(f"{res} Harvested", 0)) / plein) if c_debut else None
            out.append({"nft": name, "texte": f"{cible:.1f} récoltes complètes {de(res)} ({plein} champs)".replace(".", ","),
                        "cible": cible, "fait": fait, "quoi": effet(name) if name in B else " · ".join(textes.get(name, []))})
    return out


ORDRE_SAISONS = ["spring", "summer", "autumn", "winter"]


def objectifs_cycle(owned, prices, prod, hs, c_now, aujourdhui):
    """Bilan sur le cycle complet (printemps → hiver = une année du jeu) : en avance ou en retard ?"""
    from datetime import date
    if not hs:
        return None
    # début du cycle = dernier printemps noté, sinon le premier relevé (cycle partiel)
    debut_idx = max([i for i, h in enumerate(hs) if h["saison"] == "spring"] or [0])
    debut = hs[debut_idx]
    saison_debut = debut["saison"]
    k0 = ORDRE_SAISONS.index(saison_debut)
    saisons_cycle = ORDRE_SAISONS[k0:]                  # cycle partiel si on n'a pas commencé au printemps
    cur = hs[-1]["saison"]
    k_cur = saisons_cycle.index(cur) if cur in saisons_cycle else 0
    jours_cur = (date.fromisoformat(aujourdhui) - date.fromisoformat(hs[-1]["debut"])).days + 1
    avance = min(1.0, jours_cur / 7)
    par_saison = {s: {o["nft"]: o for o in objectifs_saison(owned, prices, prod, s, None, {})} for s in saisons_cycle}
    out = []
    for name in sorted(owned):
        cibles = [(s, par_saison[s].get(name)) for s in saisons_cycle]
        if not any(o and o["cible"] for _, o in cibles):
            continue
        total = sum(o["cible"] for _, o in cibles if o and o["cible"])
        attendu = sum(o["cible"] for s, o in cibles[:k_cur] if o and o["cible"])
        oc = cibles[k_cur][1]
        attendu += (oc["cible"] if oc and oc["cible"] else 0) * avance
        ref = next(o for _, o in cibles if o and o["cible"])
        unite = re.sub(r"^[\d,\.]+ ", "", ref["texte"])
        # fait = compteurs depuis le début du cycle
        cle = None
        for res, k in COMPTEUR.items():
            if UNITE[res] in ref["texte"]:
                cle = k
        if "récoltes complètes" in ref["texte"]:
            crop = next((c for c in CROPS if FR.get(c, c) in ref["texte"]), None)
            fait = (c_now.get(f"{crop} Harvested", 0) - debut["c"].get(f"{crop} Harvested", 0)) / max(1, prod.get("champs_total") or 1) if crop else None
        else:
            fait = (c_now.get(cle, 0) - debut["c"].get(cle, 0)) if cle else None
        out.append({"nft": name, "unite": unite, "total": total, "attendu": attendu, "fait": fait,
                    "saisons": [{"s": s, "cible": (o["cible"] if o else None)} for s, o in cibles]})
    return {"debut": debut["debut"], "saison_debut": saison_debut, "partiel": saison_debut != "spring", "nfts": out}


def bonus_totaux(owned_nft, skills_owned, prices, prod):
    """Tous tes bonus (NFT + compétences) additionnés par ressource, avec le détail de chaque ligne."""
    textes = _effets_jeu()
    noms = {"Stone": "Pierre", "Iron": "Fer", "Gold": "Or", "Crimstone": "Crimstone", "Wood": "Bois", "Milk": "Lait",
            "Leather": "Cuir", "Egg": "Œufs", "Feather": "Plumes", "Wool": "Laine", "Adv": "Cultures avancées (blé, maïs, orge, chou kale…)",
            "BasMed": "Cultures basiques et moyennes", "Cultures": "Toutes les cultures"}
    R = {r: {"add": 0.0, "add_nft": 0.0, "add_comp": 0.0, "temps": 1.0, "mult": 1.0, "chances": [], "lignes": []} for r in noms}
    def ajoute(res, src, quoi, v=0.0, nft=True):
        R[res]["add"] += v
        R[res]["add_nft" if nft else "add_comp"] += v
        R[res]["lignes"].append(f"{src} : {quoi}")
    f = lambda v: (f"+{v:g}" if v >= 0 else f"{v:g}").replace(".", ",")
    for name in owned_nft:
        for e in (B.get(name) or effets_auto(textes.get(name, []))):
            k, res = e[0], e[1]
            if k == "add" and res in R:
                v = e[2] * (e[3] if len(e) > 3 else 1)
                ajoute(res, name, f"{f(e[2])} par action" + (" (zone autour de l'objet, compté à 30 %)" if len(e) > 3 and e[3] < 1 else ""), v)
            elif k == "chance" and res in R:
                R[res]["chances"].append(f"{e[2]:.0%} de +{e[3]:g}"); ajoute(res, name, f"{e[2]:.0%} de chance de +{e[3]:g}")
            elif k == "mult" and res in R:
                R[res]["mult"] *= e[2]; ajoute(res, name, f"×{e[2]:g}".replace(".", ","))
            elif k in ("animal", "hen") and res in R:
                ajoute(res, name, f"{f(e[2])} à chaque récolte", e[2])
            elif k == "crops_mult":
                R["Cultures"]["mult"] *= e[2]; ajoute("Cultures", name, f"×{e[2]:g} de récolte".replace(".", ","))
            elif k == "time" and res == "crops":
                R["Cultures"]["temps"] *= e[2]; ajoute("Cultures", name, f"pousse {(1 - e[2]) * 100:.0f} % plus vite")
            elif k == "crop_add" and len(e) < 4:
                pass
    MAP = {"stone": "Stone", "iron": "Iron", "gold": "Gold", "crimstone": "Crimstone", "wood": "Wood", "tree": "Wood"}
    for name, effets in skills_owned:
        for t in effets:
            s = t.lower().strip()
            m = re.match(r"([+-]\d*\.?\d+) (stone|iron|gold|crimstone|wood) yield( on 5th)?", s)
            if m:
                res = MAP[m.group(2)]
                if m.group(3):
                    R[res]["chances"].append(f"+{float(m.group(1)):g} au 5e coup"); ajoute(res, name, f"+{float(m.group(1)):g} au 5e coup d'affilée", nft=False)
                else:
                    ajoute(res, name, f"{f(float(m.group(1)))} par action", float(m.group(1)), nft=False)
                continue
            m = re.match(r"x(0\.\d+) (stone|iron|gold|crimstone|tree) (?:recovery|growth) time", s)
            if m:
                res = MAP[m.group(2)]; R[res]["temps"] *= float(m.group(1))
                ajoute(res, name, f"repousse {(1 - float(m.group(1))) * 100:.0f} % plus vite", nft=False); continue
            m = re.match(r"1/10 chance of x3 wood", s)
            if m:
                R["Wood"]["chances"].append("10 % de ×3"); ajoute("Wood", name, "10 % de chance de ×3", nft=False); continue
            m = re.match(r"(\d+)% chance for trees to grow instantly", s)
            if m:
                R["Wood"]["chances"].append(f"{m.group(1)} % de repousse immédiate"); ajoute("Wood", name, f"{m.group(1)} % de chance que l'arbre repousse tout de suite", nft=False); continue
            m = re.search(r"([+-]\d*\.?\d+) (advanced crop|basic and medium crop|basic crop|medium crop)", s)
            if m:
                res = "Adv" if m.group(2).startswith("advanced") else "BasMed"
                ajoute(res, name, f"{f(float(m.group(1)))} par champ récolté", float(m.group(1)), nft=False); continue
            m = re.match(r"x(0\.\d+) (advanced crop|plot crop|basic crop|crop) growth time", s)
            if m:
                res = "Adv" if "advanced" in m.group(2) else "Cultures"
                R[res]["temps"] *= float(m.group(1)); ajoute(res, name, f"pousse {(1 - float(m.group(1))) * 100:.0f} % plus vite", nft=False); continue
            m = re.match(r"([+-]\d*\.?\d+) (.*?) yield", s)
            if m:
                v = float(m.group(1))
                for k, res in (("milk", "Milk"), ("leather", "Leather"), ("egg", "Egg"), ("feather", "Feather"), ("wool", "Wool")):
                    if k in m.group(2):
                        ajoute(res, name, f"{f(v)} à chaque récolte", v, nft=False)
    out = []
    for res, x in R.items():
        if not x["lignes"]:
            continue
        out.append({"res": res, "nom": noms[res], "add": round(x["add"], 3), "add_nft": round(x["add_nft"], 3),
                    "add_comp": round(x["add_comp"], 3), "temps": round(x["temps"], 3), "mult": round(x["mult"], 3),
                    "chances": x["chances"], "lignes": x["lignes"], "sources": [l.split(" : ")[0] for l in x["lignes"]]})
    return out


def production(act, stock, prices, rendements, aujourdhui):
    """Ce que tu as produit aujourd'hui / 7 jours / 30 jours, ressource par ressource (compteurs du jeu × quantité par action)."""
    from datetime import date, timedelta
    if not act:
        return []
    fin = act[-1]
    d1 = date.fromisoformat(fin["date"])
    def avant(n):
        lim = (d1 - timedelta(days=n)).isoformat()
        older = [a for a in act[:-1] if a["date"] <= lim]
        return older[-1] if older else None
    refs = {"1": avant(1), "7": avant(7), "30": avant(30)}
    y = {**{r: q for r, _, q in PRODUITS}, **(rendements or {})}
    rows = []
    for res, cle, _ in PRODUITS:
        if not fin["c"].get(cle):
            continue  # jamais produit : on ne l'affiche pas
        p = (prices.get(res) or 0) * (1 - TAX)
        row = {"res": res, "stock": stock.get(res, 0), "valeur_stock": stock.get(res, 0) * p}
        for k, ref in refs.items():
            if ref is None:
                row["a" + k] = row["q" + k] = row["v" + k] = None
                continue
            a = max(0.0, fin["c"].get(cle, 0) - ref["c"].get(cle, 0))
            row["a" + k] = a
            row["q" + k] = a * y.get(res, 1)
            row["v" + k] = a * y.get(res, 1) * p
        if row["stock"] >= 1 or any((row.get("a" + k) or 0) > 0 for k in ("1", "7", "30")):
            rows.append(row)
    rows.sort(key=lambda r: -((r["v30"] or r["v7"] or r["v1"] or 0) or r["valeur_stock"]))
    return rows


def ressources_jour(jours, trades, prices, exclure, n_jours, aujourdhui):
    """Ressources gagnées / utilisées sur les n derniers jours (comme SFL Tool) :
    stock de fin de journée − stock du début de journée + vendu − acheté (achats/ventes du marché exclus)."""
    from datetime import date, timedelta, datetime, timezone
    lim = (date.fromisoformat(aujourdhui) - timedelta(days=n_jours - 1)).isoformat()
    tot, nb = {}, 0
    for day, j in sorted(jours.items()):
        if day < lim or not j.get("opening") or not j.get("close"):
            continue
        nb += 1
        flux = {}
        for t in trades:
            if datetime.fromtimestamp(t["at"] / 1000, timezone.utc).date().isoformat() == day:
                flux[t["name"]] = flux.get(t["name"], 0) + (t["quantity"] if t["sold"] else -t["quantity"])
        for k in set(j["opening"]) | set(j["close"]) | set(flux):
            if k in exclure or not prices.get(k):
                continue
            d = (j["close"].get(k) or 0) - (j["opening"].get(k) or 0) + flux.get(k, 0)
            if abs(d) >= 0.01:
                tot[k] = tot.get(k, 0) + d
    rows = [{"n": k, "q": q, "v": q * prices[k] * (1 - TAX)} for k, q in tot.items()]
    rows.sort(key=lambda r: -r["v"])
    return {"jours": nb, "gagne": [r for r in rows if r["q"] > 0], "utilise": sorted([r for r in rows if r["q"] < 0], key=lambda r: r["v"])}


def amortissement(fichier_data, rows, aujourdhui, c_now=None, prices=None, c_premier=None):
    """Combien chaque NFT t'a déjà rapporté depuis que l'outil le suit (comme si tu l'avais acheté ce jour-là).
    Calculé avec tes vraies actions (pierres minées, champs récoltés, œufs collectés…) dès qu'elles sont comptées,
    sinon avec le gain moyen par jour."""
    from datetime import datetime
    c_now = c_now or {}
    prices = prices or {}
    pr = lambda k: (prices.get(k) or 0) * (1 - TAX)
    textes = _effets_jeu()
    maintenant = datetime.now().isoformat(timespec="minutes")
    for r in rows:
        if not r["owned"] or not r.get("price") or r.get("xp") or not r.get("chiffrable"):
            continue
        a = fichier_data.setdefault(r["n"], {"debut": aujourdhui, "prix": r["price"], "cumul": 0.0, "maj": maintenant})
        a.setdefault("c_debut", c_premier if (c_premier and a["debut"] == aujourdhui) else c_now)
        entries = B.get(r["n"]) or effets_auto(textes.get(r["n"], []))
        fait, mesurable = 0.0, True
        for e in entries:
            k, res = e[0], e[1]
            share = e[3] if k in ("add", "crop_add") and len(e) > 3 else 1
            if k in ("add", "animal", "hen") and res in COMPTEUR:
                d = c_now.get(COMPTEUR[res], 0) - a["c_debut"].get(COMPTEUR[res], 0)
                fait += max(0.0, d) * e[2] * share * pr(res)
            elif k == "chance" and res in COMPTEUR:
                d = c_now.get(COMPTEUR[res], 0) - a["c_debut"].get(COMPTEUR[res], 0)
                fait += max(0.0, d) * e[2] * e[3] * pr(res)
            elif k == "crop_add":
                d = c_now.get(f"{res} Harvested", 0) - a["c_debut"].get(f"{res} Harvested", 0)
                fait += max(0.0, d) * e[2] * share * pr(res)
            else:
                mesurable = False
        if not mesurable:
            # effets en % ou en vitesse : gain moyen par jour × temps écoulé (à la minute près)
            try:
                h = (datetime.fromisoformat(maintenant) - datetime.fromisoformat(a["maj"] if "T" in a["maj"] else a["maj"] + "T00:00")).total_seconds() / 86400
            except ValueError:
                h = 0
            a["cumul"] += max(0.0, r["jour"]) * max(0.0, h)
            a["maj"] = maintenant
            fait = a["cumul"]
        else:
            a["cumul"] = fait
        reste = max(0.0, a["prix"] - fait)
        r["amorti"] = {"debut": a["debut"], "prix": a["prix"], "fait": fait, "reste": reste, "mesure": mesurable,
                       "pct": min(100.0, fait / a["prix"] * 100) if a["prix"] else 0,
                       "mois": (reste / (r["jour"] * 30)) if r["jour"] > 0.001 else None}
    for n in list(fichier_data):
        if not any(r["n"] == n and r["owned"] for r in rows):
            fichier_data.pop(n)   # NFT vendu : on arrête de le suivre
    return fichier_data

def lire_vetements_sflworld(page_html):
    """Vêtements à bonus portés par ton Bumpkin et tes Farm Hands (page sfl.world/land/<numéro>)."""
    import html as _h
    t = re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", page_html)))
    i = t.find("Wearables with boost")
    if i < 0:
        return []
    j = t.find(" Bumpkin ", i)
    sec = t[j if j > 0 else i: (j if j > 0 else i) + 3000]
    return sorted(n for n in _effets_jeu() if len(n) > 3 and re.search(r"\b" + re.escape(n) + r"\b", sec))


# Temps de pousse des cultures en heures (code du jeu, sans bonus)
POUSSE_H = {"Sunflower": 1 / 60, "Potato": 5 / 60, "Rhubarb": 10 / 60, "Pumpkin": 0.5, "Zucchini": 0.5, "Carrot": 1,
            "Yam": 1, "Cabbage": 2, "Broccoli": 2, "Soybean": 3, "Beetroot": 4, "Pepper": 4, "Cauliflower": 8,
            "Parsnip": 12, "Eggplant": 16, "Corn": 20, "Onion": 20, "Radish": 24, "Wheat": 24, "Turnip": 24,
            "Kale": 36, "Artichoke": 36, "Barley": 48}


def _recoltes_par_jour(pousse_h, passages):
    """Récoltes par champ et par jour : limitée par tes passages (7 h-23 h) et par le temps de pousse (la nuit compte)."""
    return min(passages, 16 / pousse_h + 1) if pousse_h < 16 else min(passages, 24 / pousse_h)


# Prix des graines en coins (boutique du jeu)
GRAINE_COINS = {"Sunflower": 0.01, "Potato": 0.1, "Rhubarb": 0.15, "Pumpkin": 0.2, "Zucchini": 0.2, "Carrot": 0.5, "Yam": 0.5,
                "Cabbage": 1, "Broccoli": 1, "Soybean": 1.5, "Beetroot": 2, "Pepper": 2, "Cauliflower": 3, "Parsnip": 5,
                "Eggplant": 6, "Corn": 7, "Onion": 7, "Radish": 7, "Wheat": 5, "Turnip": 5, "Kale": 7, "Artichoke": 7,
                "Barley": 10}


def plan_progression(nft, prices, saison, skills=None, rendements=None, costs=None, coins_par_flower=1500):
    """Plan pour progresser sans rien investir : 1) gains gratuits, 2) premier achat qui se paie avec ces gains, 3) la suite."""
    prod, prof = nft.get("prod") or {}, nft.get("profil")
    if not prof:
        return None
    pr = lambda k: (prices.get(k) or 0) * (1 - TAX)
    rd = {**{k: v for k, v in (rendements or {}).items() if isinstance(v, (int, float))}, **(prod.get("rendements_cultures") or {})}
    y_res = {"Stone": 4.13, "Iron": 1.93, "Gold": 1.81, "Crimstone": 4.2, "Wood": prod.get("rendement_bois", 3.2), **rd}
    act = {a["cle"]: a for a in prof["activites"]}
    gagne_jour = sum(a["flw"] for a in prof["activites"])
    gratuit = []
    # 1a. Points de compétence à placer
    if skills and skills.get("libres", 0) > 0:
        def utile(r):
            # Une compétence de vitesse (repousse plus vite) ne sert que si tu exploites déjà ces rochers/arbres
            m = re.search(r"(stone|iron|gold|crimstone|tree) recovery time", r.get("effet") or "", re.I)
            if m:
                k = {"tree": "Wood"}.get(m.group(1).lower(), m.group(1).capitalize())
                return ((act.get(k) or {}).get("usage") or 0) >= 0.5
            return True
        dispo = sorted([r for r in skills["rows"] if not r["owned"] and r.get("accessible") and (r.get("jour") or 0) > 0.001
                        and utile(r)], key=lambda r: -(r.get("par_point") or 0))
        choix, reste = [], skills["libres"]
        for r in dispo:
            if r["points"] <= reste:
                choix.append(r); reste -= r["points"]
        gratuit.append({"type": "competences", "libres": skills["libres"],
                        "liste": [{"n": r["n"], "effet": r["effet"], "points": r["points"], "jour": r["jour"]} for r in choix[:4]],
                        "gain": sum(r["jour"] for r in choix[:4])})
    # 1b. Rochers et arbres que tu as déjà mais que tu récoltes peu
    noeuds = prod.get("noeuds") or {}
    mx_all = prod.get("max_actions") or {}
    extra_actions = {}
    for k in ("Iron", "Gold", "Stone", "Crimstone", "Wood"):
        mx, n = mx_all.get(k) or 0, noeuds.get(k) or 0
        actu = (act.get(k) or {}).get("actions", 0) or 0
        if not mx or not n:
            continue
        cible = mx * 0.6   # objectif réaliste : 60 % du maximum (2-3 passages par jour)
        if actu >= cible * 0.9:
            continue
        c = next((r for r in costs or [] if r.get("item") == k and r.get("par_action")), None)
        # Ce que rapporte vraiment un coup en plus : vente − coût de l'outil (pioche, hache). Si c'est à perte, on ne le conseille pas.
        v_u = (c.get("marge_reelle", c["marge"]) * c["par_action"]) if c else y_res.get(k, 1) * pr(k)
        if v_u <= 0:
            continue
        gain = (cible - actu) * v_u
        if gain < 0.1:
            continue
        extra_actions[k] = cible - actu
        gratuit.append({"type": "noeuds", "res": k, "nom": NOM_NOEUD.get(k, k), "noeuds": n, "actu": round(actu, 1),
                        "cible": round(cible, 1), "par_noeud_actu": round(actu / n, 1), "par_noeud_cible": round(cible / n, 1),
                        "gain": gain})
    # 1c. Cultures : la plus rentable de la saison, avec ta fréquence de passage
    champs = prod.get("champs_total") or 0
    rec = {c: v for c, v in (prod.get("recoltes") or {}).items() if v}
    if champs and rec and saison:
        passages = min(12.0, sum(rec.values()) / champs)
        actuel = sum(n * rd.get(c, prod.get("rendement_culture", 1)) * pr(c) for c, n in rec.items()) / champs
        options = []
        for c, h in POUSSE_H.items():
            if saison not in SAISONS.get(c, []) or not pr(c):
                continue
            r = _recoltes_par_jour(h, passages)
            graine = GRAINE_COINS.get(c, 1) / max(1, coins_par_flower)
            options.append({"c": c, "par_champ": r * (rd.get(c, prod.get("rendement_culture", 1)) * pr(c) - graine),
                            "recoltes": r, "pousse_h": h})
        options.sort(key=lambda o: -o["par_champ"])
        if options and options[0]["par_champ"] > actuel * 1.2:
            gratuit.append({"type": "cultures", "champs": champs, "passages": round(passages, 1), "saison": saison,
                            "actuel": actuel * champs, "top": options[:3], "gain": (options[0]["par_champ"] - actuel) * champs})
    gain_gratuit = sum(g["gain"] for g in gratuit)
    # 2. Premier achat qui se paie avec tes gains (après les étapes gratuites)
    apres = []
    for r in nft.get("rows") or []:
        if r["owned"] or not r.get("price") or r.get("xp") or not r.get("chiffrable"):
            continue
        g = r["jour"] or 0
        cur = (r.get("pot") or {}).get("cur") or {}
        utiles = set(prof.get("principales") or []) | set(extra_actions)
        meilleure = next((g["top"][0]["c"] for g in gratuit if g["type"] == "cultures"), None)
        if meilleure:
            utiles.add("crop:" + meilleure)
        if not (set(r.get("cibles") or []) & utiles):
            continue   # n'améliore rien de ce que tu fais (ou feras après les étapes gratuites)
        e_res = next((k for k in (r.get("cibles") or []) if k in extra_actions), None)
        if e_res and cur.get("gain_u") and cur.get("unite", "").endswith("par jour"):
            g += cur["gain_u"] * extra_actions[e_res]   # ce NFT rapporte plus si tu récoltes plus
        if g <= 0.001:
            continue
        mois = r["price"] / g / 30
        if mois <= 24:
            apres.append({"n": r["n"], "price": r["price"], "jour": g, "mois": mois, "effet": r.get("effet", ""),
                          "jours_pour_payer": r["price"] / max(0.01, gagne_jour + gain_gratuit)})
    apres.sort(key=lambda x: x["mois"])
    return {"gagne_jour": gagne_jour, "gratuit": gratuit, "gain_gratuit": gain_gratuit, "achats": apres[:3]}


def lire_livraisons_sflworld(page_html):
    """Livraisons de la ferme (page publique sfl.world/land/<numéro>/delivery) : coins, tickets et Flower."""
    out = []
    for bloc in page_html.split('<table class="table m-bottom-10">')[1:]:
        m_nom = re.search(r'<th class="va-middle w75 small b">([^<]+)', bloc)
        m_etat = re.search(r'<tr title="([^"]+)"', bloc)
        if not m_nom or not m_etat or m_etat.group(1) == "Completed":
            continue
        items = [{"n": n, "a": int(a), "b": int(b)} for n, a, b in
                 re.findall(r'alt="([^"]+)" class="img-15 m-right-5"/>[^<]*</div><div>(?:<div>)?<small>(\d+)</small> / <b>(\d+)</b>', bloc)]
        m_r = re.search(r'Reward</td><td[^>]*><img src="/img/([^"]+?)\.png"[^>]*/><b>([\d.]+)</b>', bloc)
        if not items or not m_r:
            continue
        sorte = "flower" if m_r.group(1) == "Flower" else "coins" if m_r.group(1) == "coin" else "tickets"
        m_f = re.search(r'In Flower <small>[^<]*</small></td><td[^>]*><img[^>]*/><b>([\d.]+)</b>', bloc)
        m_p = re.search(r'P2P <small>-10%</small></td><td[^>]*><img[^>]*/><b>([\d.]+)</b>', bloc)
        out.append({"pnj": m_nom.group(1).strip().title(), "type": sorte, "pret": m_etat.group(1) == "Ready for delivery",
                    "vip": "VIP Access" in bloc and "bi-ban" in bloc.split("VIP Access")[0][-200:],
                    "items": items, "recompense": float(m_r.group(2)),
                    "en_flower": float(m_f.group(1)) if m_f else (float(m_r.group(2)) if sorte == "flower" else None),
                    "cout": float(m_p.group(1)) if m_p else 0.0})
    return out


def lire_chapitre_sflworld(page_html):
    """Bounties (récompense en gemmes) et corvées de la semaine (page sfl.world/land/<numéro>/chapter)."""
    bounties, corvees = [], []
    i_ch, i_bo = page_html.find("collapseChores"), page_html.find(">Bounties")
    if i_ch >= 0:
        zone = page_html[i_ch:i_bo if i_bo > i_ch else None]
        for txt, a, b, img, r in re.findall(r'</i>(?:<img[^>]*/>)?([^<]+)</div></div><div class="mb-auto ta-right">(?:<div class="hide">\d+</div>)?'
                                             r'<div><small>(\d+)</small> / <b>(\d+)</b></div><div><div><img src="/img/(?:[^"/]+/)?([^"/]+?)\.png"[^>]*/>(?:[^<\d]*x)?(\d+)',
                                             zone):
            corvees.append({"t": txt.strip(), "a": int(a), "b": int(b), "recompense": int(r),
                            "monnaie": {"coin": "coins", "Gem": "gemmes"}.get(img, "tickets")})
    if i_bo >= 0:
        zone = page_html[i_bo:]
        fin = zone.find("collapseATrade")
        for n, a, b, r in re.findall(r'<img src="/img/delivery/[^"]+" class="img-15 m-right-5"/>([^<]+)</div></div>'
                                     r'<div class="mb-auto ta-right"><div><small>(\d+)</small> / (\d+)</div><div><div>'
                                     r'<img src="/img/Gem.png"[^>]*/>(\d+)', zone[:fin if fin > 0 else None]):
            bounties.append({"n": n.strip(), "a": int(a), "b": int(b), "gemmes": int(r)})
    return {"bounties": bounties, "corvees": corvees}


def conseils_livraisons(livraisons, chapitre, prof, prices):
    """Ce qui vaut le coup de livrer, en partant de ce que tu as et de ce que tu produis."""
    pr = lambda k: (prices.get(k) or 0) * (1 - TAX)
    principales = set((prof or {}).get("principales") or [])
    cultures = set((prof or {}).get("cultures") or [])
    def produit(n):
        return n in cultures or ("crop:" + n) in principales or CAT_CULTURE.get(n) in principales or n in principales
    flower, autres = [], []
    for d in livraisons or []:
        manque = [dict(i, manque=i["b"] - i["a"], produit=produit(i["n"])) for i in d["items"] if i["a"] < i["b"]]
        cout_manque = sum(x["manque"] * (prices.get(x["n"]) or 0) for x in manque)
        gain = (d["en_flower"] or 0) - d["cout"]
        e = {**d, "manque": manque, "gain": gain, "cout_manque": cout_manque}
        if d["type"] == "flower":
            if d["vip"]:
                e["verdict"] = "vip"
            elif d["cout"] > (d["en_flower"] or 0):
                e["verdict"] = "vendre"     # les ingrédients valent plus que la récompense
            elif d["pret"]:
                e["verdict"] = "livrer"
            elif all(x["produit"] for x in manque):
                e["verdict"] = "produire"
            elif manque and all(not prices.get(x["n"]) for x in manque) and d["cout"] < (d["en_flower"] or 0):
                e["verdict"] = "cuisiner"   # plat ou objet à fabriquer : ingrédients moins chers que la récompense
            else:
                e["verdict"] = "acheter" if cout_manque and cout_manque < (d["en_flower"] or 0) - d["cout"] else "attendre"
            flower.append(e)
        elif d["pret"] and (d["type"] == "tickets" or gain > 0):
            autres.append(e)
    flower.sort(key=lambda e: ["livrer", "produire", "cuisiner", "acheter", "attendre", "vendre", "vip"].index(e["verdict"]))
    ch = chapitre or {}
    bounties = sorted([b for b in ch.get("bounties", []) if b["a"] >= b["b"]], key=lambda b: -b["gemmes"])
    mots = {c.lower() for c in cultures} | {"tree", "trees", "stone", "stones"} if prof else set()
    corvees = [c for c in ch.get("corvees", []) if c["a"] < c["b"] and
               (c["a"] / c["b"] >= 0.3 or any(m.rstrip("s") in c["t"].lower() for m in mots))]
    return {"flower": flower, "autres": autres, "bounties": bounties, "corvees": corvees,
            "total_flower": sum((e["en_flower"] or 0) for e in flower if e["verdict"] in ("livrer", "produire", "cuisiner"))}


# --- Objectifs à ressources (bâtiments, agrandissement) : acheter ou produire ? ---
NON_ACHETABLE = {"Oil": "huile : ne s'achète pas, il faut forer", "Mud": "boue : ne s'achète pas, fouilles « Mud »"}


def acheter_ou_produire(goals, holdings, prices, couts, rythme, rendements, coin_rate, tax=0.075):
    """Pour chaque objectif pas encore fait qui demande des ressources :
    ce qui manque, prix si on l'achète, coût si on le produit, jours pour le produire soi-même.

    rythme = actions par jour (coups de pioche, arbres coupés) mesurées sur la ferme.
    Produire soi-même « coûte » ce qu'on aurait gagné en vendant (prix − taxe) ou,
    si c'est moins, ce que coûtent les outils : on garde le plus bas des deux.
    """
    rythme, rendements = rythme or {}, rendements or {}
    out = []
    for g in goals:
        res = g.get("ressources")
        if not res or g.get("fait"):
            out.append(g)
            continue
        lignes, achat, surcout, a_acheter = [], 0.0, 0.0, []
        jours_prod, jours_bloque = 0.0, 0.0
        for item, need in res.items():
            have = (holdings.get("Coins") if item == "coins" else holdings.get(item)) or 0
            left = max(0.0, need - have)
            if left <= 0:
                continue
            l = {"item": item, "besoin": need, "stock": round(have, 1), "manque": round(left, 1)}
            if item == "coins":
                l["prix"] = round(left / coin_rate, 2)
                l["note"] = "s'achètent avec des Flower (ou chasse au trésor)"
                achat += l["prix"]
            elif item in NON_ACHETABLE:
                l["note"] = NON_ACHETABLE[item]
                par_j = (rythme.get(item) or 0) * (rendements.get(item) or 0)
                if par_j:
                    l["par_jour"] = round(par_j, 1)
                    l["jours"] = round(left / par_j, 1)
                    jours_bloque = max(jours_bloque, l["jours"])
                else:
                    jours_bloque = max(jours_bloque, 0.01)
            else:
                p = prices.get(item)
                c = couts.get(item)
                par_j = (rythme.get(item) or 0) * (rendements.get(item) or 0)
                if p:
                    l["prix"] = round(left * p, 2)
                    achat += l["prix"]
                    perdu = p * (1 - tax) if c is None else min(p * (1 - tax), c)
                    l["surcout"] = round(left * (p - perdu), 2)
                    surcout += l["surcout"]
                if par_j:
                    l["par_jour"] = round(par_j, 1)
                    l["jours"] = round(left / par_j, 1)
                    jours_prod = max(jours_prod, l["jours"])
                elif p:
                    l["note"] = "tu n'en produis pas : à acheter"
                    a_acheter.append(l)
            lignes.append(l)
        if not lignes:
            out.append(g)
            continue
        # le surcoût des ressources que tu ne produis pas ne compte pas : tu dois les acheter de toute façon
        sur_choix = surcout - sum(l.get("surcout") or 0 for l in a_acheter)
        gagnes = max(0.0, jours_prod - jours_bloque) if jours_prod else 0.0
        if gagnes < 1:
            verdict = "produire"
            texte = ("Produis-le toi-même : acheter ne te ferait presque pas gagner de temps"
                     + (" (l'huile ou la boue, qui ne s'achètent pas, te bloquent de toute façon)." if jours_bloque >= jours_prod and jours_bloque > 0 else "."))
        elif sur_choix <= 0:
            verdict = "acheter"
            texte = f"Acheter te fait gagner ≈ {gagnes:.0f} jour(s) sans surcoût : achète."
        else:
            seuil = sur_choix / gagnes
            verdict = "produire" if seuil >= 1 else "selon"
            texte = (f"Acheter te ferait gagner ≈ {gagnes:.0f} jour(s) et coûterait ≈ {sur_choix:.1f} FLW de plus que de le produire. "
                     f"Ça vaut le coup seulement si cette amélioration te rapporte plus de {seuil:.2f} FLW par jour. "
                     "Sinon, garde ta production (ne la vends pas) jusqu'à avoir tout, et achète seulement le petit reste à la fin.")
        if a_acheter:
            texte += " Tu ne produis pas : " + ", ".join(l["item"] for l in a_acheter) + " → à acheter."
        nb = [l for l in lignes if l["item"] in NON_ACHETABLE]
        if nb:
            texte += " À côté, il te faut de toute façon " + " et ".join(
                f"{l['manque']:.0f} {'huiles' if l['item'] == 'Oil' else 'boues'}" for l in nb) + " (ne s'achètent pas)."
        texte = re.sub(r"(\d)\.(\d)", r"\1,\2", texte)
        out.append({**g, "achat_ou_prod": {"lignes": lignes, "achat": round(achat, 2), "surcout": round(surcout, 2),
                                           "jours_prod": round(jours_prod, 1), "jours_bloque": round(jours_bloque, 1),
                                           "jours_gagnes": round(gagnes, 1), "verdict": verdict, "texte": texte}})
    return out


# --- Pass du chapitre : points, rythme à tenir, coût de chaque mission ---
POINTS_TACHE = {"delivery": 5, "bounty": 5, "chore": 3, "coinDelivery": 10, "flowerDelivery": 10}   # tracks.ts


def plan_pass(chapitres, activite, livraisons, chapitre, aujourdhui, palier_vise=40, vip=False, possedes=(), double=False):
    """Où tu en es dans le pass du chapitre, combien de points par jour il faut, et ce que coûte chaque mission.

    Points (code du jeu) : 5 par ticket d'une livraison ou d'une bounty, 3 par ticket d'une corvée,
    10 par livraison contre des coins ou des Flower.
    """
    from datetime import date
    auj = date.fromisoformat(aujourdhui)
    regles = (chapitres or {}).get("_regles") or {}
    nom = next((n for n, c in (chapitres or {}).items() if not n.startswith("_")
                and date.fromisoformat(c["debut"]) <= auj < date.fromisoformat(c["fin"])), None)
    if not nom:
        return None
    ch = chapitres[nom]
    cle = f"{nom} Points Earned"
    act = [a for a in activite or [] if a["date"] >= ch["debut"]]
    pts = max([a["c"].get(cle, 0) for a in act] or [0])
    debut, fin = date.fromisoformat(ch["debut"]), date.fromisoformat(ch["fin"])
    reste_j = max(1, (fin - auj).days)
    # Rythme : depuis le plus ancien relevé du chapitre qui a le compteur (au moins 1 jour), sinon depuis le début
    avec = [a for a in act if cle in a["c"]]
    vieux = next((a for a in avec if (auj - date.fromisoformat(a["date"])).days >= 1), None)
    if vieux:
        j = (auj - date.fromisoformat(vieux["date"])).days
        rythme, rythme_src = (pts - vieux["c"][cle]) / j, f"mesuré sur {j} jour(s)"
    else:
        j = max(1, (auj - debut).days)
        rythme, rythme_src = pts / j, f"moyenne depuis le début du chapitre ({j} j)"
    paliers = ch["paliers"]
    niveau = sum(1 for p in paliers if p["points"] <= pts)
    cibles = []
    for i, p in enumerate(paliers, 1):
        lit = any("Bed" in r for r in p["vip"] + p["gratuit"])
        if lit or i == palier_vise or (i == niveau + 1 and i < palier_vise):
            manque = max(0, p["points"] - pts)
            par_j = manque / reste_j
            date_fin = None
            if rythme > 0 and manque > 0:
                from datetime import timedelta
                date_fin = (auj + timedelta(days=manque / rythme)).isoformat()
            cibles.append({"palier": i, "points": p["points"], "dans_palier": p["points"] - (paliers[i - 2]["points"] if i > 1 else 0), "gratuit": p["gratuit"], "vip": p["vip"], "lit": lit,
                           "manque": manque, "par_jour": round(par_j), "ok": manque == 0 or rythme >= par_j,
                           "date_atteinte": date_fin, "vise": i == palier_vise})
    # Tickets recalculés avec les règles du jeu (sfl.world n'est pas toujours à jour)
    objets = [o for o in ch.get("objets_tickets", []) if o in set(possedes or ())]
    bonus = (regles.get("bonus_vip", 2) if vip else 0) + len(objets)
    table = regles.get("tickets_livraison") or {}
    calc = {"vip": vip, "objets": objets, "double": double, "bonus": bonus}
    missions = []
    for d in livraisons or []:
        if d.get("vip"):
            continue
        if d["type"] == "tickets":
            base = table.get(d["pnj"].lower())
            if base is not None:
                t = (base + bonus) * (2 if double else 1)
                detail = f"{base} de base" + (" + 2 VIP" if vip else "") + (f" + {len(objets)} tenue(s) du chapitre" if objets else "")
                if double:
                    detail = f"({detail}) × 2 (double livraison du jour)"
                detail += f" = {t} tickets"
            else:
                t, detail = d["recompense"], f"{d['recompense']:g} tickets (sfl.world)"
            p = POINTS_TACHE["delivery"] * t
            cout = d["cout"]
        elif d["type"] in ("coins", "flower"):
            p = POINTS_TACHE["coinDelivery" if d["type"] == "coins" else "flowerDelivery"]
            cout = d["cout"] - (d.get("en_flower") or 0)    # négatif = tu gagnes en plus
        else:
            continue
        manque = [f"{i['b'] - i['a']} {i['n']}" for i in d["items"] if i["a"] < i["b"]]
        if d["type"] != "tickets":
            detail = "10 points par livraison"
        missions.append({"quoi": f"Livraison {d['pnj']}", "sorte": d["type"], "points": p, "cout": round(cout, 2), "calcul": detail,
                         "flw_100": round(cout / p * 100, 2) if p else None, "pret": d["pret"], "manque": manque})
    for c in (chapitre or {}).get("corvees", []):
        if c["monnaie"] != "tickets" or c["a"] >= c["b"]:
            continue
        caps = c["recompense"] + bonus
        missions.append({"quoi": c["t"], "sorte": "corvee", "points": POINTS_TACHE["chore"] * caps, "tickets": caps,
                         "cout": None, "flw_100": None, "pret": False, "avance": [c["a"], c["b"]]})
    payantes = sorted([m for m in missions if m["flw_100"] is not None], key=lambda m: m["flw_100"])
    # « À faire absolument » : les livraisons qui coûtent moins de 3 FLW pour 100 points (ou qui rapportent)
    for m in payantes:
        m["absolument"] = m["flw_100"] <= 3
    vise = next((c for c in cibles if c["vise"]), cibles[-1] if cibles else None)
    corv_sem = sum(POINTS_TACHE["chore"] * (c["recompense"] + bonus) for c in (chapitre or {}).get("corvees", []) if c["monnaie"] == "tickets")
    # Ordre de grandeur du coût pour finir : corvées (gratuites) + le reste en livraisons au coût médian du jour
    vals = sorted(max(0, m["flw_100"]) for m in payantes if m["sorte"] == "tickets")
    cout_median = vals[len(vals) // 2] / 100 if vals else None
    cout_fin = None
    if vise and cout_median is not None:
        cout_fin = round(max(0, vise["manque"] - corv_sem * reste_j / 7) * cout_median, 1)
    dispo = sum(m["points"] for m in payantes)
    dispo_bon = [m for m in payantes if m["absolument"]]
    return {"chapitre": nom, "debut": ch["debut"], "fin": ch["fin"], "points": pts, "niveau": niveau,
            "reste_jours": reste_j, "rythme": round(rythme), "rythme_src": rythme_src, "cibles": cibles,
            "missions": payantes + [m for m in missions if m["sorte"] == "corvee"],
            "corvees_semaine": corv_sem, "cout_median_100": round(cout_median * 100, 2) if cout_median is not None else None,
            "cout_fin": cout_fin, "points_dispo": dispo, "points_bon": sum(m["points"] for m in dispo_bon),
            "cout_bon": round(sum(max(0, m["cout"]) for m in dispo_bon), 2), "calcul": calc}
