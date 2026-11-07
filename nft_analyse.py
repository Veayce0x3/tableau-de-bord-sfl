"""Rentabilité des NFT : ce que chacun rapporte par jour et par an, à partir de TA production.

Effets tirés du code du jeu (collectibleItemBuffs.ts / bumpkinItemBuffs.ts).
Ta production par jour se règle dans ma_ferme.json → "ma_production".
"""

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
    "Scarecrow": [("crops_mult", None, 1.2)],
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


def _prod(cfg):
    p = {**DEFAULT_PROD, **(cfg.get("ma_production") or {})}
    p["recoltes"] = {**DEFAULT_PROD["recoltes"], **((cfg.get("ma_production") or {}).get("recoltes") or {})}
    return p


def gain_par_jour(name, prices, prod, owned):
    """Gain net (après taxe) en Flower par jour, et une phrase d'explication."""
    pr = lambda k: (prices.get(k) or 0) * (1 - TAX)
    total, why, xp = 0.0, [], None
    for e in B[name]:
        kind = e[0]
        if kind == "add":
            res, v = e[1], e[2]
            share = e[3] if len(e) > 3 else 1
            g = v * prod[res] * share * pr(res)
            why.append(f"+{v:g} × {prod[res] * share:g} coups/jour")
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
            n = prod["recoltes"].get(res, 0) * share
            g = v * n * pr(res)
            why.append(f"+{v:g} × ~{n:g} champs de {res}/jour (moyenne sur l'année)")
        elif kind == "crops_mult":
            m = e[2]
            g = sum(n * prod["rendement_culture"] * (1 - 1 / m) * pr(c) for c, n in prod["recoltes"].items())
            why.append(f"×{m:g} sur toutes tes récoltes")
        elif kind == "time":
            target, m = e[1], e[2]
            eff = 0.5  # la nuit et tes horaires limitent le gain de vitesse
            if target == "crops":
                base = sum(n * prod["rendement_culture"] * pr(c) for c, n in prod["recoltes"].items())
            elif target == "hen":
                base = prod["cycles_poules"] * 2 * pr("Egg")
            elif target == "cow":
                base = 0  # limité par les bounties de vaches
            else:
                base = prod["recoltes"].get(target, 0) * prod["rendement_culture"] * pr(target)
            g = base * (1 / m - 1) * eff
            why.append(f"temps ×{m:g} (gain réduit de moitié : la nuit, tu ne récoltes pas)")
        elif kind == "animal":
            res, v = e[1], e[2]
            g = v * prod["cycles_vaches"] * pr(res)
            why.append(f"+{v:g} × {prod['cycles_vaches']:g} cycles de vaches/jour")
        elif kind == "hen":
            res, v = e[1], e[2]
            g = v * prod["cycles_poules"] * pr(res)
            why.append(f"+{v:g} × {prod['cycles_poules']:g} cycles de poules/jour")
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
    return total, " · ".join(why), xp


def analyse_nft(holdings, prices, cfg):
    prod = _prod(cfg)
    owned = {n for n in B if (holdings.get(n) or 0) > 0} | set(cfg.get("nft_possedes") or [])
    rows = []
    for name in B:
        price = prices.get(name)
        g, why, xp = gain_par_jour(name, prices, prod, owned)
        an = g * 365 / price * 100 if price else None
        mine = name in owned
        if mine:
            if xp:
                v, c = "💤 À vendre si ton but est de gagner des Flower (il ne donne que de l'XP)", "neutral"
            elif an is None:
                v, c = "Garder", "pos"
            elif an >= 40:
                v, c = "✅ Garder : il rapporte bien", "pos"
            elif an >= 15:
                v, c = "👍 Garder : rapporte correctement", "pos"
            else:
                v, c = "➖ Rapporte peu : tu peux le vendre si tu as besoin de Flower", "neutral"
        else:
            if xp:
                v, c = "Seulement si ton objectif est l'XP", "neutral"
            elif an is None:
                v, c = "Prix inconnu", "neutral"
            elif g <= 0.001:
                v, c = "❌ N'apporte rien sur ta ferme", "neg"
            elif an >= 60:
                v, c = "🟢 Bon achat", "pos"
            elif an >= 35:
                v, c = "🟡 Correct", "neutral"
            else:
                v, c = "❌ Trop cher pour ce qu'il rapporte", "neg"
        rows.append({"n": name, "owned": mine, "wearable": name in WEARABLES, "price": price, "jour": g,
                     "mois": g * 30, "an_pct": an, "rembourse_jours": (price / g) if price and g > 0.001 else None,
                     "why": why, "xp": xp, "verdict": v, "cls": c})
    rows.sort(key=lambda r: (not r["owned"], -(r["an_pct"] or -1)))
    return {"rows": rows, "prod": prod}
