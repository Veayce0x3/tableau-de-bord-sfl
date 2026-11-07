#!/usr/bin/env python3
"""Relevé Sunflower Land (lecture seule) — à lancer une fois par jour.

Lit les données publiques de la ferme sur SFL Tool (primerascripto.com) et
les prix du marché (SFL Tool + sfl.world). Garde l'historique dans donnees/
(le jeu ne montre que 50 échanges) et écrit le bilan dans releves/AAAA-MM-JJ.md.

Usage : python3 releve_hebdo.py
"""
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

RATES_URL = "https://primerascripto.com/api/sfl/rates"
SFLWORLD_URL = "https://sfl.world/api/v1/prices"
ROOT = Path(__file__).resolve().parent
CONFIG_FILE = ROOT / "ma_ferme.json"


def read_config():
    """Réglages de l'utilisateur : numéro de ferme et NFT à suivre."""
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit("Il manque le fichier ma_ferme.json : ouvre-le et mets ton numéro de ferme (voir LISEZMOI.md).")
    fid = str(cfg.get("numero_de_ferme", "")).strip()
    if not fid.isdigit():
        sys.exit("Dans ma_ferme.json, « numero_de_ferme » doit être ton numéro de ferme (que des chiffres).")
    return fid, cfg


FARM_ID, CONFIG = read_config()
DATA = ROOT / "donnees"
REPORTS = ROOT / "releves"
TRADES_FILE = DATA / "echanges.json"
SNAP_FILE = DATA / "compteurs.json"
PRICES_FILE = DATA / "prix.json"
PRICES_CSV = DATA / "prix.csv"
DAYS = 7
TAX = 0.075

# Ce que la ferme produit ou utilise, par famille (ordre d'affichage).
WATCH = {
    "Mines": ["Stone", "Iron", "Gold", "Crimstone", "Obsidian", "Wood"],
    "Animaux": ["Milk", "Leather", "Egg", "Feather", "Truffle", "Pig Bristles"],
    "Cave": ["Green Beetle", "Blue Beetle", "Pink Beetle", "Amber Beetle"],
    "Cultures": ["Wheat", "Barley", "Corn", "Kale", "Soybean"],
    "Fruits et autres": ["Tomato", "Lemon", "Honey", "Salt", "Refined Salt"],
    "Objets de pet": ["Ruffroot", "Chewed Bone", "Heart Leaf", "Ribbon", "Dewberry",
                      "Wild Grass", "Frost Pebble", "Moonfur"],
    "Tes NFT (prix plancher)": CONFIG.get("nft_a_suivre", []),
}
NAMES_FR = {
    "Stone": "Pierre", "Iron": "Fer", "Gold": "Or", "Crimstone": "Crimstone", "Obsidian": "Obsidienne",
    "Wood": "Bois", "Milk": "Lait", "Leather": "Cuir", "Egg": "Œuf", "Feather": "Plume",
    "Truffle": "Truffe", "Pig Bristles": "Poil de cochon", "Wheat": "Blé", "Barley": "Orge",
    "Corn": "Maïs", "Kale": "Chou kale", "Soybean": "Soja", "Tomato": "Tomate", "Lemon": "Citron",
    "Honey": "Miel", "Salt": "Sel", "Refined Salt": "Sel raffiné", "Oil": "Huile", "Mud": "Boue",
}


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "releve-hebdo-sfl"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.URLError as e:
        # Python de python.org sur Mac sans certificats : on passe par curl (toujours présent sur Mac)
        if "CERTIFICATE" not in str(e).upper() and "SSL" not in str(e).upper():
            raise
        import subprocess
        out = subprocess.run(["curl", "-fsSL", "-A", "releve-hebdo-sfl", "--max-time", "60", url],
                             capture_output=True, check=True).stdout
        return json.loads(out)


def try_json(url):
    try:
        return get_json(url)
    except Exception as e:  # une source de prix en panne ne bloque pas le relevé
        print(f"(source indisponible : {url} — {e})", file=sys.stderr)
        return {}


def load(path, default):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        # Fichier abîmé : on le met de côté et on repart de la dernière sauvegarde, sans rien écraser.
        bad = path.with_name(path.name + ".abime")
        path.replace(bad)
        backups = sorted((path.parent / "sauvegardes").glob("*/" + path.name))
        for b in reversed(backups):
            try:
                data = json.loads(b.read_text())
                print(f"⚠️ {path.name} était abîmé : récupéré depuis la sauvegarde {b.parent.name}.", file=sys.stderr)
                return data
            except json.JSONDecodeError:
                continue
        print(f"⚠️ {path.name} était abîmé et aucune sauvegarde n'est lisible (gardé dans {bad.name}).", file=sys.stderr)
        return default


def safe_write(path, text):
    """Écrit d'abord dans un fichier temporaire : une coupure en pleine écriture n'abîme jamais l'ancien fichier."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text)
    tmp.replace(path)


def backup_data(today, keep=14):
    """Copie du dossier donnees/ une fois par jour (les 14 derniers jours sont gardés)."""
    import shutil
    dest = DATA / "sauvegardes" / today
    if dest.exists() or not DATA.exists():
        return
    dest.mkdir(parents=True)
    for f in DATA.glob("*.json"):
        shutil.copy2(f, dest / f.name)
    old = sorted(d for d in (DATA / "sauvegardes").iterdir() if d.is_dir())
    for d in old[:-keep]:
        shutil.rmtree(d, ignore_errors=True)


def fmt(x, signed=True):
    s = f"{x:+.2f}" if signed else f"{x:.2f}"
    return s.replace(".", ",")


def price_fmt(p):
    if p is None:
        return "—"
    if p >= 10:
        return f"{p:.2f}".replace(".", ",")
    return f"{p:.4f}".replace(".", ",")


def pct(new, old):
    if new is None or not old:
        return "—"
    v = (new - old) / old * 100
    arrow = "🔺" if v > 2 else "🔻" if v < -2 else "➖"
    return f"{arrow} {v:+.0f} %".replace(".", ",")


RESOURCE_KEYS = set()  # objets vendus sur le marché P2P (pas les NFT)


def collect_prices(fin):
    """Prix unitaire par objet. Les ressources P2P passent avant les NFT de même nom."""
    prices = {}
    sw = try_json(SFLWORLD_URL).get("data", {}).get("p2p", {})
    rates = try_json(RATES_URL)
    rp2p = {k: v for k, v in (rates.get("p2p") or {}).items() if isinstance(v, (int, float))}
    # 1. NFT (prix plancher) d'abord, 2. puis les ressources par-dessus
    prices.update({k: v for k, v in (rates.get("nft") or {}).items() if isinstance(v, (int, float))})
    fin_prices = {k: v for k, v in (fin.get("prices") or {}).items() if isinstance(v, (int, float))}
    resources = {k: v for k, v in sw.items() if isinstance(v, (int, float))}
    RESOURCE_KEYS.update(resources, rp2p)
    for k, v in fin_prices.items():          # SFL Tool : plus récent ; ressource si connue comme telle
        if k in RESOURCE_KEYS or k not in prices:
            prices[k] = v
    prices.update(resources)
    prices.update(rp2p)
    for k, v in fin_prices.items():
        if k in RESOURCE_KEYS:
            prices[k] = v
    return prices


def collect_farm(farm_id, trades_file, snap_file, today):
    """Complète l'historique d'échanges et de compteurs d'une ferme (publique, lecture seule)."""
    url = f"https://primerascripto.com/api/farm/{farm_id}/finances"
    for attempt in range(3):  # SFL Tool limite les requêtes rapprochées
        try:
            fin = get_json(url)
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 2:
                raise
            time.sleep(30 * (attempt + 1))
    trades = {t["id"]: t for t in load(trades_file, [])}
    new = 0
    for t in fin.get("entries", []):
        if t["id"] not in trades:
            trades[t["id"]] = {k: t.get(k) for k in
                               ("id", "at", "sold", "name", "quantity", "gross", "fee", "net", "unit")}
            new += 1
    all_trades = sorted(trades.values(), key=lambda t: t["at"])
    trades_file.parent.mkdir(parents=True, exist_ok=True)
    safe_write(trades_file, json.dumps(all_trades, ensure_ascii=False, indent=1))
    snaps = load(snap_file, [])
    snap = {"date": today, "solde": fin.get("balance"), "coins": fin.get("coins"),
            "nom": fin.get("username"), **(fin.get("lifetime") or {})}
    snaps = [s for s in snaps if s["date"] != today] + [snap]
    safe_write(snap_file, json.dumps(snaps, ensure_ascii=False, indent=1))
    return fin, all_trades, snaps, new


# --- Coût de production -------------------------------------------------------
# Rendements par défaut ; réglables dans ma_ferme.json → "rendements".
DEFAULT_YIELDS = {
    "Wood": 3.2, "Stone": 4.13, "Iron": 1.93, "Gold": 1.81, "Crimstone": 4.2,
    "Wheat": 2.72, "Barley": 2.72, "Corn": 2.72, "Kale": 2.72, "Tomato": 1.1, "Lemon": 1.1,
    "axe_coins": 16,  # 20 coins, -20 % avec Feller's Discount
}
# Ce qu'il faut pour UNE action (un coup de hache, un minage, une graine plantée).
RECIPES = {
    "Wood": {"coins": "axe_coins", "items": {}},
    "Stone": {"coins": 20, "items": {"Wood": 3}},
    "Iron": {"coins": 20, "items": {"Wood": 3, "Stone": 5}},
    "Gold": {"coins": 80, "items": {"Wood": 3, "Iron": 5}},
    "Crimstone": {"coins": 100, "items": {"Wood": 3, "Gold": 3}},
    "Wheat": {"coins": 5, "items": {}},
    "Barley": {"coins": 10, "items": {}},
    "Corn": {"coins": 7, "items": {}},
    "Kale": {"coins": 7, "items": {}},
    "Tomato": {"coins": 5 / 5, "items": {}},   # 1 graine = ~5 récoltes
    "Lemon": {"coins": 15 / 5, "items": {}},
}
PRODUCTION_INPUTS = ["Wood", "Stone", "Iron", "Gold", "Crimstone", "Wheat", "Barley", "Corn",
                     "Kale", "Tomato", "Lemon", "Milk", "Leather", "Truffle", "Pig Bristles", "Soybean"]


def production_costs(prices, cfg, coin_rate):
    """Coût pour produire UNE unité, en Flower, avec les prix du jour.

    Les ressources qui servent d'outil (bois, pierre…) sont comptées au prix du
    marché : c'est ce que tu pourrais en tirer en les vendant. Les coins sont
    comptés au meilleur taux d'échange.
    """
    y = {**DEFAULT_YIELDS, **(cfg.get("rendements") or {})}
    rows = []
    for item, r in RECIPES.items():
        coins = y[r["coins"]] if isinstance(r["coins"], str) else r["coins"]
        coin_cost = coins / coin_rate
        mat_cost = sum(q * (prices.get(i) or 0) for i, q in r["items"].items())
        per_unit = (coin_cost + mat_cost) / y[item]
        sell = (prices.get(item) or 0) * (1 - TAX)
        rows.append({"item": item, "par_action": y[item], "cout_coins": coin_cost / y[item],
                     "cout_matieres": mat_cost / y[item], "cout": per_unit, "vente_nette": sell,
                     "marge": sell - per_unit,
                     "detail": f"{coins:g} coins" + "".join(f" + {q:g} {NAMES_FR.get(i, i)}" for i, q in r["items"].items())
                               + f" → {y[item]:g} par action"})
    # Animaux : par cycle, avec 2 caresses (voir SUNFLOWER_LAND.md)
    p = lambda k: prices.get(k) or 0
    meal = 5.344  # rations par repas d'une vache (Chonky Feed, Cow-Smart, Efficient Feeding)
    for label, meals, food, milk, leather in [
        ("Vache niv. 3-5 (Hay = blé)", 2.9, p("Wheat"), 3.1, 1.45),
        ("Vache niv. 6-9 (NutriBarley = orge)", 4.0, p("Barley"), 3.6, 2.45),
        ("Vache niv. 10+ (Mixed Grain)", 3.8, p("Wheat") + p("Corn") + p("Barley"), 4.1, 3.45),
    ]:
        cost = meals * meal * food
        sell = (milk * p("Milk") + leather * p("Leather")) * (1 - TAX)
        rows.append({"item": label, "par_action": None, "cout": cost, "vente_nette": sell, "marge": sell - cost,
                     "detail": f"~{meals:g} repas × {meal} rations · produit ~{milk:g} lait + {leather:g} cuir", "cycle": True})
    pig_meal = 2.137
    for label, meals, slop, truffles in [
        ("Cochon niv. 0-2 (Basic Slop = 9 soja)", 1.6, 9 * p("Soybean"), 1),
        ("Cochon niv. 3-5 (Hearty Slop = 4 citrons)", 2.4, 4 * p("Lemon"), 2),
        ("Cochon niv. 6+ (champignons du stock)", 3.6, 0.0, 2.5),
    ]:
        cost = meals * pig_meal * slop
        sell = truffles * p("Truffle") * (1 - TAX)
        rows.append({"item": label, "par_action": None, "cout": cost, "vente_nette": sell, "marge": sell - cost,
                     "detail": f"~{meals:g} repas × {pig_meal} Slops · ~{truffles:g} truffe(s) (+ poils à l'échange)", "cycle": True})
    # Poules : 1 repas (ration 1,92) par cycle, production du code du jeu, sans tes bonus d'œufs
    hen_meal = 1.92
    for label, food, eggs, feathers in [
        ("Poule niv. 1-2 (Kernel Blend = maïs)", p("Corn"), 1, 0),
        ("Poule niv. 3-5 (Hay = blé)", p("Wheat"), 2, 1),
        ("Poule niv. 6-9 (NutriBarley = orge)", p("Barley"), 2.5, 1.25),
        ("Poule niv. 10+ (Mixed Grain)", p("Wheat") + p("Corn") + p("Barley"), 3.5, 2.2),
    ]:
        cost = hen_meal * food
        sell = (eggs * p("Egg") + feathers * p("Feather")) * (1 - TAX)
        rows.append({"item": label, "par_action": None, "cout": cost, "vente_nette": sell, "marge": sell - cost,
                     "detail": f"1 repas × {hen_meal} rations · ~{eggs:g} œuf(s) + {feathers:g} plume(s)", "cycle": True})
    # Échanger un cochon contre ses poils (puis en racheter un pour 100 coins)
    for lvl, bristles in [(10, 6), (15, 12)]:
        sell = bristles * p("Pig Bristles") * (1 - TAX)
        cost = 100 / coin_rate
        rows.append({"item": f"Échange cochon niv. {lvl} → {bristles} poils", "par_action": None, "cout": cost,
                     "vente_nette": sell, "marge": sell - cost, "trade": True,
                     "detail": f"{bristles} poils vendus − nouveau cochon 100 coins"})
    return rows


# --- Conseil de vente ---------------------------------------------------------
# Ce qu'il vaut mieux garder pour faire tourner la ferme (réglable : "stock_a_garder" dans ma_ferme.json).
DEFAULT_KEEP = {"Wood": 300, "Stone": 300, "Iron": 100, "Gold": 30, "Crimstone": 10, "Wheat": 500,
                "Barley": 500, "Corn": 150, "Lemon": 100, "Soybean": 150, "Egg": 60, "Milk": 30,
                "Honey": 10, "Refined Salt": 10, "Obsidian": 2,
                "Blue Beetle": 20, "Pink Beetle": 20, "Amber Beetle": 20}
# Pourquoi tu produis chaque ressource (réglable : "a_vendre" et "pour_ma_ferme" dans ma_ferme.json).
DEFAULT_FOR_SALE = ["Stone", "Crimstone", "Gold", "Obsidian", "Milk", "Leather", "Truffle", "Pig Bristles",
                    "Egg", "Feather", "Tomato", "Green Beetle", "Blue Beetle", "Pink Beetle", "Amber Beetle", "Honey"]
DEFAULT_FOR_FARM = ["Wheat", "Barley", "Corn", "Wood", "Iron", "Lemon", "Soybean", "Kale", "Refined Salt", "Salt"]
NEW_ITEMS = {"Truffle", "Pig Bristles", "Green Beetle", "Blue Beetle", "Pink Beetle", "Amber Beetle"}
NOT_FOR_SALE = {"Love Charm", "Basic Land", "Sunflorian Emblem", "Axe", "Pickaxe", "Stone Pickaxe",
                "Iron Pickaxe", "Gold Pickaxe", "Rod", "Sand Shovel", "Sand Drill", "Salt Rake", "Oil Drill"}


def sell_advice(holdings, prices, history, costs, cfg, trades=()):
    keep = {**DEFAULT_KEEP, **(cfg.get("stock_a_garder") or {})}
    cost = {r["item"]: r["cout"] for r in costs if not r.get("cycle")}
    since = (datetime.now(timezone.utc) - timedelta(days=14)).timestamp() * 1000
    my_sales = {}
    for t in trades:
        if t["sold"] and t["at"] >= since and t.get("quantity"):
            a = my_sales.setdefault(t["name"], [0.0, 0.0])
            a[0] += t["quantity"]
            a[1] += t.get("gross") or 0
    rows = []
    for item, qty in holdings.items():
        p = prices.get(item)
        if not p or item in NOT_FOR_SALE or qty <= 0 or item not in RESOURCE_KEYS:
            continue
        k = keep.get(item, 0)
        sellable = max(0.0, qty - k)
        vals = [h["prices"].get(item) for h in history if h["prices"].get(item)]
        last7 = [h["prices"].get(item) for h in history[-7:] if h["prices"].get(item)]
        avg7 = sum(last7) / len(last7) if last7 else None
        lo, hi = (min(vals), max(vals)) if vals else (None, None)
        net = p * (1 - TAX)
        c = cost.get(item)
        if c is not None and net < c:
            sig, txt = "cout", "Prix sous ton coût de production : garde-le pour ta ferme ou produis-en moins"
        elif len(vals) < 5:
            if item in NEW_ITEMS:
                sig, txt = "vendre", "Nouvelle ressource dont le prix baisse : vends au fil de l'eau"
            else:
                sig, txt = "normal", f"Pas encore assez d'historique ({len(vals)} jour(s)) : vends au prix du marché si tu en as besoin"
        else:
            pos = (p - lo) / (hi - lo) if hi > lo else 0.5
            if p >= avg7 * 1.05 or pos >= 0.75:
                sig, txt = "vendre", "Prix haut par rapport aux derniers jours : bon moment pour vendre"
            elif p <= avg7 * 0.95 or pos <= 0.25:
                sig, txt = "attendre", "Prix bas par rapport aux derniers jours : attends si tu peux"
            else:
                sig, txt = "normal", "Prix normal"
        if sellable <= 0 and sig != "cout":
            sig, txt = "garder", f"À garder pour ta ferme (réserve conseillée : {k:g})"
        if item in NEW_ITEMS and sig not in ("garder",):
            sig = "vendre"
            if avg7 and p < avg7 * 0.9:
                txt = "Nouvelle ressource en baisse : continue de vendre au fil de l'eau, sans casser le prix"
            else:
                txt = "Nouvelle ressource : vends au fil de l'eau tant que le prix n'est pas stable"
        floor = max(p * 0.98, (c or 0) / (1 - TAX))
        alert = None
        if item in my_sales and my_sales[item][0]:
            mine = my_sales[item][1] / my_sales[item][0]
            gap = (mine - p) / p * 100
            if gap < -10:
                alert = (f"Attention : tes ventes des 14 derniers jours étaient {gap:.0f} % sous le prix du marché "
                         f"(moyenne {mine:.4f}). Mets en vente au prix mini conseillé ou attends.")
        role = ("vente" if item in (cfg.get("a_vendre") or DEFAULT_FOR_SALE)
                else "ferme" if item in (cfg.get("pour_ma_ferme") or DEFAULT_FOR_FARM) else "autre")
        rows.append({"n": item, "role": role, "stock": qty, "keep": k, "sellable": sellable, "price": p, "avg7": avg7,
                     "lo": lo, "hi": hi, "floor": floor, "value": sellable * net, "sig": sig, "txt": txt, "alert": alert,
                     "days": len(vals)})
    rows.sort(key=lambda r: -r["value"])
    return rows


# --- Objectifs ----------------------------------------------------------------
BATIMENTS = {"porcherie": "Pigpen", "pigpen": "Pigpen", "cochon": "Pigpen", "grange": "Barn", "barn": "Barn",
             "vache": "Barn", "poulailler": "Hen House", "hen house": "Hen House", "poule": "Hen House"}
ANIMAUX_PAR_NIVEAU = {"Pigpen": (3, "cochons"), "Barn": (5, "vaches"), "Hen House": (5, "poules")}
NOM_BAT = {"Pigpen": "Porcherie", "Barn": "Grange", "Hen House": "Poulailler"}


def interpreter_objectif(g, nft_names, skill_names, expansions):
    """Objectif écrit librement (« augmenter la porcherie ») → objectif détaillé que l'outil sait suivre."""
    if g.get("type") not in (None, "auto"):
        return g
    t = g.get("titre", "")
    tl = t.lower()
    g = {**g, "type": "manuel", "groupe": g.get("groupe") or "Mes objectifs"}
    try:
        bat_costs = json.loads((ROOT / "batiments_jeu.json").read_text())
    except Exception:
        bat_costs = {}
    for mot, bat in BATIMENTS.items():
        if mot in tl and bat in bat_costs:
            m = re.search(r"(?:niveau|niv\.?|lvl|level)\s*(\d)", tl) or re.search(r"\b([23])\b", tl)
            niv = int(m.group(1)) if m else 3
            c = bat_costs[bat].get(str(niv))
            if c:
                par, quoi = ANIMAUX_PAR_NIVEAU.get(bat, (0, ""))
                g.update({"ressources": {"coins": c["coins"], **c["items"]}, "groupe": "Bâtiments",
                          "note": f"{NOM_BAT.get(bat, bat)} niveau {niv}" + (f" : jusqu'à {par * niv} {quoi}" if par else "")
                                  + " (coûts tirés du code du jeu)"})
            return g
    m = re.search(r"niveau\s*(\d+)", tl)
    if m:
        return {**g, "type": "niveau", "valeur": int(m.group(1)), "groupe": "Niveau"}
    if any(w in tl for w in ("agrandi", "expansion", "extension")) and expansions:
        nxt = next(iter(expansions.values()))
        return {**g, "ressources": {"coins": nxt.get("coins", 0), **nxt.get("resources", {})}, "groupe": "Ferme",
                "note": "Prochain agrandissement (coûts lus sur ta ferme)"}
    for n in sorted(nft_names, key=len, reverse=True):
        if n.lower() in tl:
            vend = tl.startswith("vend")
            return {**g, "type": "vendre" if vend else "nft", "nom": n, "groupe": "NFT à vendre" if vend else "NFT à acheter"}
    for n in skill_names:
        if n.lower() in tl:
            return {**g, "type": "competence", "nom": n, "groupe": "Compétences"}
    return g


def evaluate_goals(goals, holdings, prices, trades, land, coin_rate):
    """Valide automatiquement ce qui peut l'être et calcule prix / coûts restants."""
    skills = (land.get("bumpkin") or {}).get("skills") or {}
    level = (land.get("bumpkin") or {}).get("level")
    now_ms = datetime.now(timezone.utc).timestamp() * 1000
    week = [t for t in trades if t["at"] >= now_ms - 7 * 864e5]
    oil_cost = 0.10  # l'huile ne se vend pas : ~coût d'un forage
    out = []
    for g in goals:
        typ, name = g.get("type"), g.get("nom")
        done, info = bool(g.get("fait")), ""
        price = None
        if typ == "nft":
            done = (holdings.get(name) or 0) > 0
            price = prices.get(name)
            info = "Acheté ✔" if done else (f"Prix actuel ≈ {price:.2f} FLW" if price else "Prix introuvable")
        elif typ == "vendre":
            done = (holdings.get(name) or 0) <= 0
            price = prices.get(name)
            info = "Vendu ✔" if done else (f"Se vend ≈ {price:.2f} FLW" if price else "")
        elif typ == "competence":
            done = name in skills
            info = "Prise ✔" if done else "Pas encore prise"
        elif typ == "niveau":
            done = bool(level and level >= g.get("valeur", 0))
            info = f"Niveau actuel : {level}" if level else ""
        elif typ == "dans_le_vert":
            net = sum(t["net"] for t in week)
            done = net > 0
            info = f"7 derniers jours : {net:+.2f} FLW"
        elif typ == "fer":
            spent = -sum(t["net"] for t in week if not t["sold"] and t["name"] == "Iron")
            done = spent < 5
            info = f"Fer acheté sur 7 jours : {spent:.2f} FLW"
        elif typ == "prix_vente":
            s = [t for t in trades if t["sold"] and t["name"] == name and t["at"] >= now_ms - 14 * 864e5 and t.get("quantity")]
            mk = prices.get(name)
            if s and mk:
                avg = sum(t["gross"] for t in s) / sum(t["quantity"] for t in s)
                gap = (avg - mk) / mk * 100
                done = gap >= -5
                info = f"Tes ventes (14 j) : {avg:.4f} · marché {mk:.4f} ({gap:+.0f} %)"
            else:
                info = "Pas de vente récente"
        res = g.get("ressources")
        cost_total = cost_left = None
        missing = []
        if res:
            cost_total = cost_left = 0.0
            for item, need in res.items():
                unit = (1 / coin_rate) if item == "coins" else oil_cost if item == "Oil" else (prices.get(item) or 0)
                have = (holdings.get("Coins") if item == "coins" else holdings.get(item)) or 0
                left = max(0.0, need - have)
                cost_total += need * unit
                cost_left += left * unit
                if left > 0:
                    missing.append(f"{left:,.0f} {NAMES_FR.get(item, item) if item != 'coins' else 'coins'}".replace(",", " "))
            info = (info + " · " if info else "") + (f"il manque : {', '.join(missing)}" if missing else "tu as tout ✔")
        out.append({**g, "fait": done, "info": info, "prix": price, "cout_total": cost_total, "cout_restant": cost_left})
    return out


def price_on_or_before(history, date, item):
    best = None
    for snap in history:
        if snap["date"] <= date and snap["prices"].get(item) is not None:
            best = snap["prices"][item]
    return best


def main():
    DATA.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    backup_data(today)
    fin, all_trades, snaps, new = collect_farm(FARM_ID, TRADES_FILE, SNAP_FILE, today)
    life = fin.get("lifetime", {})
    prev = next((s for s in reversed(snaps) if s["date"] < today), None)
    snap = snaps[-1]

    # 3. Prix du jour (un relevé par jour) + export CSV pour un tableur
    watched = [i for items in WATCH.values() for i in items]
    # + toute ressource déjà achetée ou vendue, et tout ce qui entre dans un coût de production
    wallet = fin.get("wallet") or []
    holdings = (max(wallet, key=lambda w: w.get("day", "")).get("holdings") or {}) if wallet else {}
    extra = sorted({t["name"] for t in all_trades} | set(PRODUCTION_INPUTS)
                   | {k for k, v in holdings.items() if v and k not in NOT_FOR_SALE})
    watched += [i for i in extra if i not in watched]
    all_prices = collect_prices(fin)
    # Quantité par action de TA ferme (pierre par coup de pioche, bois par arbre…), lue sur sfl.world
    # si tu ne l'as pas réglée toi-même dans ma_ferme.json → "rendements"
    v1 = try_json(f"https://sfl.world/api/v1/land/{FARM_ID}") or {}
    lus = {}
    for groupe in ("resources", "crops", "fruits"):
        for k, v in (v1.get(groupe) or {}).items():
            if isinstance(v, dict) and v.get("avg"):
                lus[k.capitalize()] = v["avg"]
    if lus:
        # tes réglages manuels (ma_ferme.json → "rendements") restent prioritaires
        CONFIG["rendements"] = {**lus, **(CONFIG.get("rendements") or {})}
        CONFIG["rendements_source"] = "lus sur ta ferme (sfl.world)"
    # Cours du Flower en dollars (USDC) du jour, gardé avec les compteurs du compte
    try:
        usd = (try_json(RATES_URL) or {}).get("flowerUsd")
        if usd:
            for sn in snaps:
                if sn["date"] == today:
                    sn["flower_usd"] = usd
            safe_write(SNAP_FILE, json.dumps(snaps, ensure_ascii=False, indent=1))
    except Exception as e:
        print(f"(cours du Flower indisponible : {e})", file=sys.stderr)
    today_prices = {i: all_prices.get(i) for i in watched}
    history = [h for h in load(PRICES_FILE, []) if h["date"] != today]
    history.append({"date": today, "prices": today_prices})
    history.sort(key=lambda h: h["date"])
    safe_write(PRICES_FILE, json.dumps(history, ensure_ascii=False, indent=1))
    with PRICES_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["date"] + watched)
        for h in history:
            w.writerow([h["date"]] + [("" if h["prices"].get(i) is None else str(h["prices"][i]).replace(".", ","))
                                      for i in watched])

    # 4. Bilan de la semaine
    since = (now - timedelta(days=DAYS)).timestamp() * 1000
    week = [t for t in all_trades if t["at"] >= since]
    sales = sum(t["net"] for t in week if t["sold"])
    buys = -sum(t["net"] for t in week if not t["sold"])
    fees = sum(t.get("fee") or 0 for t in week if t["sold"])

    d7 = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    d28 = (now - timedelta(days=28)).strftime("%Y-%m-%d")

    L = [
        f"# Relevé Sunflower Land — semaine au {today}",
        "",
        f"Échanges sur 7 jours : {len(week)} · nouveaux enregistrés : {new} · historique conservé : {len(all_trades)}",
        "",
        "## 1. Bilan du marché",
        "| | FLW |",
        "|---|---|",
        f"| Ventes (après taxe) | {fmt(sales)} |",
        f"| Achats | {fmt(-buys)} |",
        f"| **Net de la semaine** | **{fmt(sales - buys)}** |",
        f"| Net par jour | {fmt((sales - buys) / DAYS)} |",
        f"| Taxe payée | {fmt(fees, signed=False)} |",
        "",
    ]

    # Détail des ventes et achats à l'unité, comparé au prix du marché
    agg = defaultdict(lambda: {"qs": 0.0, "gs": 0.0, "ns": 0.0, "qb": 0.0, "gb": 0.0})
    for t in week:
        a = agg[t["name"]]
        if t["sold"]:
            a["qs"] += t["quantity"] or 0
            a["gs"] += t["gross"] or 0
            a["ns"] += t["net"] or 0
        else:
            a["qb"] += t["quantity"] or 0
            a["gb"] += t["gross"] or 0
    if agg:
        L += ["## 2. Ce que tu as vendu et acheté (prix à l'unité)",
              "| Ressource | Vendu | Prix moyen de vente | Prix du marché | Écart | Acheté | Prix moyen d'achat | Total net |",
              "|---|---|---|---|---|---|---|---|"]
        warnings = []
        for name, a in sorted(agg.items(), key=lambda kv: -(abs(kv[1]["ns"]) + kv[1]["gb"])):
            mkt = all_prices.get(name)
            us = a["gs"] / a["qs"] if a["qs"] else None
            ub = a["gb"] / a["qb"] if a["qb"] else None
            gap = pct(us, mkt) if us and mkt else "—"
            if us and mkt and us < mkt * 0.9:
                warnings.append(f"- **{NAMES_FR.get(name, name)}** vendu {price_fmt(us)} alors que le marché est à {price_fmt(mkt)} "
                                f"({(us - mkt) / mkt * 100:+.0f} %) → ~{fmt((mkt - us) * a['qs'] * (1 - TAX), signed=False)} FLW laissés")
            total = a["ns"] - a["gb"]
            L.append(f"| {NAMES_FR.get(name, name)} | {a['qs']:g} | {price_fmt(us)} | {price_fmt(mkt)} | {gap} | "
                     f"{a['qb']:g} | {price_fmt(ub)} | {fmt(total)} |")
        L.append("")
        if warnings:
            L += ["⚠️ **Ventes nettement sous le prix du marché :**", *warnings, ""]

    # Évolution des prix à l'unité
    L += ["## 3. Prix à l'unité de ce que tu produis (évolution)",
          f"Historique depuis le {history[0]['date']} ({len(history)} relevé(s)). Tableur : `donnees/prix.csv`.", ""]
    for fam, items in WATCH.items():
        L += [f"**{fam}**", "",
              "| Objet | Prix aujourd'hui | Il y a 7 j | Variation | Il y a 28 j | Variation | Plus bas | Plus haut |",
              "|---|---|---|---|---|---|---|---|"]
        for i in items:
            p = today_prices.get(i)
            p7 = price_on_or_before(history[:-1], d7, i)
            p28 = price_on_or_before(history[:-1], d28, i)
            vals = [h["prices"].get(i) for h in history if h["prices"].get(i) is not None]
            lo = min(vals) if vals else None
            hi = max(vals) if vals else None
            L.append(f"| {NAMES_FR.get(i, i)} | {price_fmt(p)} | {price_fmt(p7)} | {pct(p, p7)} | "
                     f"{price_fmt(p28)} | {pct(p, p28)} | {price_fmt(lo)} | {price_fmt(hi)} |")
        L.append("")
    L += ["🔺 hausse de plus de 2 % · 🔻 baisse de plus de 2 % · ➖ stable. Les colonnes « il y a 7/28 j » se remplissent au fil des relevés.", ""]

    # Hors marché
    L += ["## 4. Hors marché (compteurs du jeu)"]
    if prev:
        def delta(k):
            return (snap.get(k) or 0) - (prev.get(k) or 0)
        L += [
            f"Depuis le relevé du {prev['date']} :",
            f"- Flower dépensés dans le jeu (gems, VIP…) : {fmt(delta('spent'), signed=False)}",
            f"- Frais sur les gems : {fmt(delta('gemFees'), signed=False)}",
            f"- Déposés : {fmt(delta('deposited'), signed=False)} · Retirés : {fmt(delta('withdrawn'), signed=False)}",
            f"- Solde : {fmt(prev.get('solde') or 0, signed=False)} → {fmt(snap['solde'] or 0, signed=False)} FLW · "
            f"Coins : {prev.get('coins') or 0:,.0f} → {snap['coins'] or 0:,.0f}".replace(",", " "),
        ]
    else:
        L.append("Premier relevé : les écarts apparaîtront la semaine prochaine.")
    L += ["",
          f"Depuis le début : déposé {fmt(life.get('deposited', 0), False)} · retiré {fmt(life.get('withdrawn', 0), False)} · "
          f"dépensé dans le jeu {fmt(life.get('spent', 0), False)} · frais gems {fmt(life.get('gemFees', 0), False)}"]

    text = "\n".join(L) + "\n"
    (REPORTS / "dernier.md").write_text(text)
    # Le bilan daté est gardé le dimanche (ou au premier relevé).
    report = REPORTS / f"{today}.md"
    if now.astimezone().weekday() == 6 or not any(REPORTS.glob("20*.md")):
        report.write_text(text)
    else:
        report = REPORTS / "dernier.md"

    sys.path.insert(0, str(ROOT))  # le script tourne en mode isolé (python3 -I)
    from tableau_de_bord import build_dashboard
    farms = [{"id": FARM_ID, "nom": fin.get("username") or CONFIG.get("nom") or FARM_ID,
              "trades": all_trades, "counters": snaps}]
    costs = production_costs(all_prices, CONFIG, float(CONFIG.get("coins_par_flower", 1525)))
    cost_hist = [c for c in load(DATA / "couts.json", []) if c["date"] != today]
    cost_hist.append({"date": today, "couts": {r["item"]: round(r["cout"], 6) for r in costs}})
    safe_write((DATA / "couts.json"), json.dumps(cost_hist, ensure_ascii=False, indent=1))
    stock = sell_advice(holdings, all_prices, history, costs, CONFIG, all_trades)
    stock_hist = [s for s in load(DATA / "stock.json", []) if s["date"] != today]
    stock_hist.append({"date": today, "stock": {k: v for k, v in holdings.items() if v}})
    safe_write((DATA / "stock.json"), json.dumps(stock_hist, ensure_ascii=False, indent=1))
    land = try_json(f"https://sfl.world/api/v1.1/land/{FARM_ID}")  # niveau et compétences
    goals = load(ROOT / "objectifs.json", [])
    try:
        skn = list(json.loads((ROOT / "competences_jeu.json").read_text()).keys())
    except Exception:
        skn = []
    goals = [interpreter_objectif(g, [k for k, v in all_prices.items() if k not in RESOURCE_KEYS], skn,
                                  fin.get("expansions") or {}) for g in goals]
    goals_eval = evaluate_goals(goals, {**holdings, "Coins": fin.get("coins") or 0}, all_prices, all_trades,
                                land, float(CONFIG.get("coins_par_flower", 1525))) if goals else []
    from nft_analyse import analyse_nft, mesure_production, lire_ferme_sflworld, lire_animaux_sflworld, lire_activite_sflworld, rythme_reel, DEFAULT_PROD
    # Production de TA ferme : réglée à la main (ma_production) > lue sur ta ferme (sfl.world) > mesurée > ferme type
    mesure, jours = mesure_production(stock_hist, all_trades, CONFIG.get("rendements"))
    ferme, saison = None, None
    try:
        req = urllib.request.Request(f"https://sfl.world/land/{FARM_ID}", headers={"User-Agent": "releve-hebdo-sfl"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                page = r.read().decode("utf-8", "replace")
        except urllib.error.URLError:
            import subprocess
            page = subprocess.run(["curl", "-fsSL", "-A", "releve-hebdo-sfl", f"https://sfl.world/land/{FARM_ID}"],
                                  capture_output=True, check=True).stdout.decode("utf-8", "replace")
        ferme = lire_ferme_sflworld(page, ((land or {}).get("bumpkin") or {}).get("skills"))
        m_s = re.search(r"Current season\s+(spring|summer|autumn|winter)", re.sub(r"<[^>]+>", " ", page))
        saison = m_s.group(1) if m_s else None
    except Exception as e:
        print(f"(ferme non lue sur sfl.world : {e})", file=sys.stderr)
    def page_sfl(url):
        req = urllib.request.Request(url, headers={"User-Agent": "releve-hebdo-sfl"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.URLError:
            import subprocess
            return subprocess.run(["curl", "-fsSL", "-A", "releve-hebdo-sfl", url],
                                  capture_output=True, check=True).stdout.decode("utf-8", "replace")
    animaux_lus = {}
    try:
        animaux_lus = lire_animaux_sflworld(page_sfl(f"https://sfl.world/land/{FARM_ID}/animals"))
    except Exception as e:
        print(f"(animaux non lus sur sfl.world : {e})", file=sys.stderr)
    # Compteurs réels (minés, coupés, récoltés, collectés) : enregistrés à chaque relevé pour mesurer ton rythme
    reel, jours_reel, parts_vie = None, 0, {}
    try:
        compteurs = lire_activite_sflworld(page_sfl(f"https://sfl.world/land/{FARM_ID}/activity"))
        if compteurs:
            act = [a for a in load(DATA / "activite.json", []) if a["date"] != today]
            act.append({"date": today, "c": compteurs})
            safe_write(DATA / "activite.json", json.dumps(act, ensure_ascii=False))
            reel, jours_reel = rythme_reel(act)
            from nft_analyse import CROPS
            tot = sum(compteurs.get(f"{c} Harvested", 0) for c in CROPS)
            parts_vie = {c: compteurs.get(f"{c} Harvested", 0) / tot for c in CROPS} if tot else {}
    except Exception as e:
        print(f"(activité non lue sur sfl.world : {e})", file=sys.stderr)
    if CONFIG.get("ma_production"):
        cfg_prod, source = CONFIG, "réglée dans ma_ferme.json"
    elif ferme:
        p = dict(ferme["prod"])
        if animaux_lus:
            vaches = (animaux_lus.get("Cow") or {}).get("nombre", 0)
            poules = (animaux_lus.get("Chicken") or {}).get("nombre", 0)
            animaux = {"vaches": vaches, "cycles_vaches": vaches, "cycles_poules": poules}
        elif mesure:
            animaux = {k: mesure[k] for k in ("cycles_vaches", "cycles_poules", "vaches")}
        else:
            animaux = {k: DEFAULT_PROD[k] for k in ("cycles_vaches", "cycles_poules", "vaches")}
        p.update(animaux)
        if (CONFIG.get("rendements") or {}).get("Wood"):
            p["rendement_bois"] = CONFIG["rendements"]["Wood"]
        rd = CONFIG.get("rendements") or {}
        cultures = {c: rd[c] for c in p.get("recoltes", {}) if rd.get(c)}
        if cultures:
            p["rendements_cultures"] = cultures
            p["rendement_culture"] = rd.get("Wheat") or sum(cultures.values()) / len(cultures)
        p["arbres"] = ferme["noeuds"]["Wood"]
        if animaux_lus:
            p["poules"] = (animaux_lus.get("Chicken") or {}).get("nombre", 0)
        n = ferme["noeuds"]
        source = (f"lue sur ta ferme : {n['Stone']} rochers de pierre, {n['Iron']} de fer, {n['Gold']} d'or, "
                  f"{n['Crimstone']} de crimstone, {n['Wood']} arbres, champs : "
                  + (", ".join(f"{v} {NAMES_FR.get(k, k)}" for k, v in ferme["champs"].items()) or "aucun planté")
                  + (" · " + ", ".join(f"{v['nombre']} { {'Cow': 'vaches', 'Chicken': 'poules', 'Sheep': 'moutons'}.get(k, k)} "
                                         f"({'grange' if v['batiment'] == 'Barn' else 'poulailler'} niv. {v['niveau']})"
                                         for k, v in animaux_lus.items()) if animaux_lus
                     else f" · animaux mesurés sur {jours} jours" if mesure else " · animaux : estimés (mesurés après 3 jours)"))
        if reel:
            # Ton vrai rythme remplace l'estimation (rochers × passages) dès qu'on a 1 jour d'écart
            for k in ("Stone", "Iron", "Gold", "Crimstone", "Wood", "cycles_vaches", "cycles_poules"):
                p[k] = reel[k]
            p["recoltes"] = reel["recoltes"]
            p["mesure_reelle"] = True
            vie = act[-1]["c"]
            from nft_analyse import CROPS
            tot = sum(vie.get(f"{c} Harvested", 0) for c in CROPS)
            if tot:
                p["parts_vie"] = {c: vie.get(f"{c} Harvested", 0) / tot for c in CROPS}
            if p.get("champs_total"):
                p["frequence_recolte"] = round(sum(reel["recoltes"].values()) / p["champs_total"], 2)
            source = (f"mesurée sur ce que tu as vraiment fait ces {jours_reel} dernier(s) jour(s) : "
                      f"{reel['Stone']:g} pierres minées, {reel['Iron']:g} fer, {reel['Gold']:g} or, {reel['Crimstone']:g} crimstone, "
                      f"{reel['Wood']:g} arbres coupés, {sum(reel['recoltes'].values()):g} champs récoltés, "
                      f"{reel['cycles_poules']:g} récoltes d'œufs et {reel['cycles_vaches']:g} de lait par jour · " + source)
        else:
            source = ("⏳ estimation (rochers × ~6 passages/jour) : ton vrai rythme sera mesuré au prochain relevé, demain · "
                      + source)
        if parts_vie:
            p["parts_vie"] = parts_vie
        cfg_prod = {**CONFIG, "ma_production": p}
    elif mesure:
        cfg_prod, source = {**CONFIG, "ma_production": mesure}, f"mesurée sur ta ferme ({jours} jours)"
    else:
        cfg_prod, source = CONFIG, "pas encore lue : sfl.world n'a pas répondu, réessaie Actualiser dans quelques minutes"
    nft = analyse_nft(holdings, all_prices, cfg_prod, source, fiable=not source.startswith("pas encore"))
    try:
        from nft_analyse import amortissement
        am = amortissement(load(DATA / "amortissement.json", {}), nft["rows"], today)
        safe_write(DATA / "amortissement.json", json.dumps(am, ensure_ascii=False, indent=1))
    except Exception as e:
        print(f"(amortissement indisponible : {e})", file=sys.stderr)
    try:
        from nft_analyse import ressources_jour
        jours = load(DATA / "jours.json", {})
        for w in fin.get("wallet") or []:
            d = w.get("day")
            if not d:
                continue
            j = jours.setdefault(d, {})
            if (w.get("opening") or {}).get("holdings") and not j.get("opening"):
                j["opening"] = w["opening"]["holdings"]
            if w.get("holdings"):
                j["close"] = w["holdings"]
        safe_write(DATA / "jours.json", json.dumps(jours, ensure_ascii=False))
        exclure = {r["n"] for r in nft["rows"]}
        nft["ressources"] = {k: ressources_jour(jours, all_trades, all_prices, exclure, n, today) for k, n in (("1", 1), ("7", 7), ("30", 30))}
    except Exception as e:
        print(f"(ressources du jour indisponibles : {e})", file=sys.stderr)
    try:
        from nft_analyse import production
        nft["production"] = production(load(DATA / "activite.json", []), holdings, all_prices, CONFIG.get("rendements"), today)
    except Exception as e:
        print(f"(production indisponible : {e})", file=sys.stderr)
    # Saisons : on note le début de chaque saison (avec tes compteurs) pour suivre tes objectifs
    try:
        from nft_analyse import objectifs_saison, objectifs_cycle
        hs = load(DATA / "saisons.json", [])
        c_now = (load(DATA / "activite.json", []) or [{}])[-1].get("c", {})
        owned_now = [r["n"] for r in nft["rows"] if r["owned"]]
        prod_now = cfg_prod.get("ma_production") or {}
        if saison and (not hs or hs[-1]["saison"] != saison):
            if hs:
                # Saison terminée : on archive son bilan
                prev = hs[-1]
                bil = load(DATA / "saisons_bilan.json", [])
                bil.append({"saison": prev["saison"], "debut": prev["debut"], "fin": today,
                            "objectifs": objectifs_saison(owned_now, all_prices, prod_now, prev["saison"], prev["c"], c_now)})
                safe_write(DATA / "saisons_bilan.json", json.dumps(bil, ensure_ascii=False, indent=1))
                if saison == "spring":
                    # Cycle terminé (hiver → printemps) : on archive le bilan du cycle complet
                    cy = objectifs_cycle(owned_now, all_prices, prod_now, hs, c_now, today)
                    if cy:
                        for o in cy["nfts"]:
                            o["attendu"] = o["total"]
                        cyc = load(DATA / "cycles.json", [])
                        cyc.append({**cy, "fin": today})
                        safe_write(DATA / "cycles.json", json.dumps(cyc, ensure_ascii=False, indent=1))
            hs.append({"saison": saison, "debut": today, "c": c_now})
            safe_write(DATA / "saisons.json", json.dumps(hs, ensure_ascii=False))
        nft["saisons_passees"] = load(DATA / "saisons_bilan.json", [])
        nft["cycles_passes"] = load(DATA / "cycles.json", [])
        if hs:
            cur = hs[-1]
            premier = len(hs) == 1   # saison déjà commencée quand l'outil a été installé
            owned = [r["n"] for r in nft["rows"] if r["owned"]]
            nft["saison"] = {"nom": cur["saison"], "debut": cur["debut"], "partielle": premier,
                             "objectifs": objectifs_saison(owned, all_prices, cfg_prod.get("ma_production") or {}, cur["saison"],
                                                           cur["c"], c_now),
                             "historique": [{"saison": h["saison"], "debut": h["debut"]} for h in hs]}
            nft["cycle"] = objectifs_cycle(owned, all_prices, cfg_prod.get("ma_production") or {}, hs, c_now, today)
    except Exception as e:
        print(f"(objectifs de saison indisponibles : {e})", file=sys.stderr)
    from competences import analyse_competences
    try:
        nft["skills"] = analyse_competences(land, all_prices, cfg_prod)
        from nft_analyse import bonus_totaux
        nft["totaux"] = bonus_totaux([r["n"] for r in nft["rows"] if r["owned"]],
                                     [(r["n"], r["effet"].split(" · ")) for r in nft["skills"]["rows"] if r["owned"]],
                                     all_prices, cfg_prod.get("ma_production") or {})
    except Exception as e:  # la page s'affiche même si sfl.world ne répond pas
        print(f"(compétences indisponibles : {e})", file=sys.stderr)
    dash = build_dashboard(ROOT, farms, history, WATCH, NAMES_FR, all_prices, costs, cost_hist, stock, goals_eval,
                           CONFIG.get("date_depart"), nft)
    print(report)
    print(dash)
    print("\n".join(L[:14]))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # message lisible si le site ne répond pas
        print(f"Relevé impossible : {e}", file=sys.stderr)
        sys.exit(1)
