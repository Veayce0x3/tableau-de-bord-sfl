"""Compétences (skills) : ce que tu as, ce que chacune rapporte, et quoi changer.

Données du jeu : competences_jeu.json (tiré de bumpkinSkills.ts et du dictionnaire du jeu).
Règles du jeu : 1 point par niveau ; un rang en plus coûte 1 / 3 / 6 points (palier 1 / 2 / 3) ;
palier 2 d'un arbre = moitié des compétences du palier 1 ; palier 3 = toutes celles du palier 1 + 1 point.
"""
import json
import re
from pathlib import Path

from nft_analyse import _prod

TAX = 0.075
RANK_COST = {1: 1, 2: 3, 3: 6}
ARBRES = {"Crops": "Cultures", "Trees": "Arbres", "Mining": "Mines", "Animals": "Animaux", "Cooking": "Cuisine",
          "Fishing": "Pêche", "Fruit Patch": "Fruits", "Greenhouse": "Serre", "Bees & Flowers": "Abeilles et fleurs",
          "Machinery": "Machines", "Compost": "Compost", "Cave": "Grotte", "Aging": "Vieillissement", "Rocks": "Rochers"}
RES = {"stone": "Stone", "iron": "Iron", "gold": "Gold", "crimstone": "Crimstone", "wood": "Wood"}
ADVANCED = ("Wheat", "Barley", "Corn", "Kale")  # cultures « avancées » du jeu que tu fais pousser


def _load_skills():
    return json.loads((Path(__file__).resolve().parent / "competences_jeu.json").read_text())


def valeur(effets, prices, prod):
    """Gain net estimé par jour (Flower) d'une compétence, et son type."""
    pr = lambda k: (prices.get(k) or 0) * (1 - TAX)
    crops_adv = sum(prod["recoltes"].get(c, 0) * pr(c) for c in ADVANCED)       # valeur de +1 par champ avancé
    txt = " / ".join(effets).lower()
    g, calc = 0.0, False
    for e in effets:
        s = e.lower()
        m = re.match(r"([+-]\d*\.?\d+) (stone|iron|gold|crimstone|wood) yield( on 5th)?", s)
        if m:
            v, r = float(m.group(1)), RES[m.group(2)]
            g += v * prod[r] * pr(r) / (5 if m.group(3) else 1)
            calc = True
            continue
        m = re.match(r"1/10 chance of x3 wood", s)
        if m:
            g += 0.2 * prod["Wood"] * prod["rendement_bois"] * pr("Wood")
            calc = True
            continue
        m = re.match(r"([+-]\d*\.?\d+) (advanced crop|basic and medium crop)", s)
        if m:
            if m.group(2) == "advanced crop":
                g += float(m.group(1)) * crops_adv
            calc = True
            continue
        m = re.match(r"([+-]\d*\.?\d+) (.*?) yield", s)
        if m and re.search(r"egg|milk|leather|feather", m.group(2)):
            v = float(m.group(1))
            for k, cyc in (("milk", "cycles_vaches"), ("leather", "cycles_vaches"), ("egg", "cycles_poules"), ("feather", "cycles_poules")):
                if k in m.group(2):
                    g += v * prod[cyc] * pr(k.capitalize())
            calc = True
            continue
        m = re.match(r"x(0\.\d+) (stone|iron|gold|crimstone|tree) (recovery|growth) time", s)
        if m:
            r = "Wood" if m.group(2) == "tree" else RES[m.group(2)]
            base = prod[r] * pr(r) * (prod["rendement_bois"] if r == "Wood" else 1)
            g += base * (1 / float(m.group(1)) - 1) * 0.5
            calc = True
            continue
        m = re.match(r"x(0\.\d+) (advanced crop|plot crop) growth time", s)
        if m:
            g += crops_adv * prod["rendement_culture"] * (1 / float(m.group(1)) - 1) * 0.5
            calc = True
            continue
    if "coin" in txt:
        typ = "🪙 Coins"
    elif "xp" in txt and not calc:
        typ = "⭐ XP"
    elif calc:
        typ = "📦 Production"
    elif "feed" in txt:
        typ = "🐄 Nourriture des animaux"
    elif any(w in txt for w in ("instantly", "instant", "1 tap", "ability to", "stock", "wakes up")):
        typ = "🖐️ Confort / temps gagné"
    else:
        typ = "➖ Autre (non chiffré)"
    return (g if calc else None), typ


def analyse_competences(land, prices, cfg):
    S = _load_skills()
    prod = _prod(cfg)
    b = (land or {}).get("bumpkin") or {}
    mine = b.get("skills") or {}
    level = b.get("level") or 0
    island = ((land or {}).get("land") or {}).get("type", "")

    # points utilisés, par arbre
    used, per_tree = 0, {}
    for n, rank in mine.items():
        s = S.get(n)
        if not s:
            continue
        cost = (s["points"] or 0) + RANK_COST.get(s["tier"] or 1, 1) * (max(rank, 1) - 1)
        used += cost
        if s["tier"] != 3:  # le jeu ne compte que les paliers 1 et 2 pour débloquer
            per_tree[s["tree"]] = per_tree.get(s["tree"], 0) + (s["points"] or 0)
    seuils = {}
    for tree in {s["tree"] for s in S.values()}:
        t1 = sorted(s["points"] for s in S.values() if s["tree"] == tree and s["tier"] == 1 and not s["off"])
        seuils[tree] = {2: sum(t1[:(len(t1) + 1) // 2]), 3: sum(t1) + 1}

    def palier(tree, pts):
        return 3 if pts >= seuils[tree][3] else 2 if pts >= seuils[tree][2] else 1

    rows = []
    for n, s in S.items():
        if s["off"] or not s["tier"] or "coming soon" in " ".join(s["effets"]).lower():
            continue
        g, typ = valeur(s["effets"], prices, prod)
        owned = n in mine
        rows.append({"n": n, "arbre": ARBRES.get(s["tree"], s["tree"]), "tree": s["tree"], "palier": s["tier"],
                     "points": s["points"], "rang": mine.get(n, 0), "rang_max": s["max"], "owned": owned,
                     "effet": " · ".join(e for e in s["effets"] if e), "jour": g, "par_point": (g / s["points"]) if g is not None and s["points"] else None,
                     "type": typ})

    # Compétences qui tiennent un palier : les enlever bloquerait des compétences de palier supérieur
    bloquant = set()
    for tree, pts in per_tree.items():
        has_t3 = any(S[n]["tree"] == tree and S[n]["tier"] == 3 for n in mine if n in S)
        has_t2 = any(S[n]["tree"] == tree and S[n]["tier"] == 2 for n in mine if n in S)
        for n in mine:
            s = S.get(n)
            if not s or s["tree"] != tree or s["tier"] == 3:
                continue
            after = pts - (s["points"] or 0)
            if (has_t3 and after < seuils[tree][3]) or (has_t2 and s["tier"] == 1 and after < seuils[tree][2]):
                bloquant.add(n)
    for r in rows:
        r["bloquant"] = r["n"] in bloquant
        if r["owned"]:
            if r["bloquant"]:
                r["verdict"] = "🔒 Garde-le : il débloque le palier supérieur de l'arbre"
            elif r["jour"] is not None and r["jour"] > 0.3:
                r["verdict"] = "✅ Rapporte bien"
            elif r["jour"] is not None and r["jour"] > 0.05:
                r["verdict"] = "👍 Rapporte un peu"
            elif r["jour"] is not None and r["jour"] < 0:
                r["verdict"] = "⚠️ Te fait perdre plus qu'il ne rapporte"
            elif r["type"].startswith("🪙"):
                r["verdict"] = "🪙 Donne des coins : utile seulement si tu en manques"
            elif r["type"].startswith("🐄"):
                r["verdict"] = "🐄 Change ce que mangent tes animaux : utile si tu nourris beaucoup ce type d'animal"
            elif r["type"].startswith("🖐️"):
                r["verdict"] = "🖐️ Confort : fait gagner du temps, pas de Flower"
            else:
                r["verdict"] = "➖ Rapporte peu ou rien en Flower"
        else:
            tree_pts = per_tree.get(r["tree"], 0)
            ok = palier(r["tree"], tree_pts) >= r["palier"]
            r["accessible"] = ok
            r["verdict"] = ("🟢 Accessible maintenant" if ok else f"🔒 Il faut d'abord {seuils[r['tree']][r['palier']] - tree_pts} point(s) de plus dans l'arbre {r['arbre']}")

    free = level - used
    best = sorted([r for r in rows if not r["owned"] and r["par_point"] and r["par_point"] > 0.02],
                  key=lambda r: -r["par_point"])
    weak = [r for r in rows if r["owned"] and not r["bloquant"] and not r["type"].startswith("🐄") and (r["jour"] is None or r["jour"] < 0.05)]
    arbres = [{"arbre": ARBRES.get(t, t), "points": p, "palier": palier(t, p), "seuil2": seuils[t][2], "seuil3": seuils[t][3]}
              for t, p in sorted(per_tree.items(), key=lambda x: -x[1])]
    rows.sort(key=lambda r: (not r["owned"], r["arbre"], -(r["jour"] or -9)))
    return {"rows": rows, "niveau": level, "utilises": used, "libres": free, "ile": island,
            "meilleurs": [r["n"] for r in best[:6]], "faibles": [r["n"] for r in weak], "arbres": arbres,
            "total_jour": sum(r["jour"] or 0 for r in rows if r["owned"])}
