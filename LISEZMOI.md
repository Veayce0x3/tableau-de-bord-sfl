# Tableau de bord Sunflower Land

Un petit outil qui enregistre chaque jour les données **publiques** de ta ferme (échanges sur le marché, prix des ressources, compteurs du jeu) et les affiche dans un tableau de bord à ouvrir dans ton navigateur.

- **Lecture seule** : il ne touche jamais au jeu, ne demande ni mot de passe, ni clé, ni wallet. Il lit seulement ce que SFL Tool (primerascripto.com) et sfl.world affichent publiquement pour un numéro de ferme.
- **Tout reste sur ton ordinateur**, dans le dossier `donnees/`.

## 1. Installer (une seule fois)
1. Il faut **Python 3**.
   - Mac : il est souvent déjà là. Sinon, tape `python3` dans le Terminal : macOS propose de l'installer.
   - Windows : installe-le depuis python.org (coche « Add Python to PATH »).
2. Ouvre **`ma_ferme.json`** avec un éditeur de texte et mets **ton numéro de ferme** (le nombre à côté de ton nom dans le jeu) :
   ```json
   {
     "numero_de_ferme": "1234567890123456",
     "nft_a_suivre": ["Scarecrow", "Milk Apron"]
   }
   ```
   `nft_a_suivre` (facultatif) : les NFT dont tu veux suivre le prix.

   Facultatif aussi : `"rendements"` pour régler ce que te rapporte une action sur TA ferme
   (ex. `{"Stone": 4.13, "Iron": 1.93, "Gold": 1.81, "Crimstone": 4.2, "Wood": 3.2, "Wheat": 2.72, "axe_coins": 16}`)
   et `"coins_par_flower"` (1525 par défaut). Ils servent à l'onglet Rentabilité.

   Facultatif : `"date_depart": "2026-11-07"` pour compter tes gains seulement à partir de cette date (les anciens échanges restent dans Historique).

## Mises à jour
À chaque lancement, `maj.py` vérifie sur GitHub (Veayce0x3/tableau-de-bord-sfl) s'il y a une nouvelle version et remplace seulement les fichiers du programme. Tes données et réglages ne sont jamais touchés.

## 2. Utiliser
- **Mac** : double-clic sur **`Lancer le relevé.command`** (la première fois : clic droit → Ouvrir).
- **Windows** : double-clic sur **`Lancer le relevé.bat`**.

Le relevé enregistre les données du jour, puis ouvre le tableau de bord dans ton navigateur.
**Garde la petite fenêtre ouverte** : tant qu'elle est ouverte, le bouton **🔄 Actualiser** du tableau de bord refait un relevé quand tu cliques dessus (environ 30 secondes à 1 minute). Ferme-la quand tu as fini.

Tu peux aussi ouvrir `tableau_de_bord.html` directement (double-clic) pour consulter tes données : tout s'affiche, seul le bouton Actualiser ne marche pas dans ce cas.

**Lance-le une fois par jour** (le soir, par exemple). Le jeu ne garde que tes 50 derniers échanges : si tu attends plus d'une semaine, les plus anciens sont perdus. Les prix, eux, ne sont enregistrés que les jours où tu lances le relevé.

## 3. Le tableau de bord
- **Aperçu** : ce que tu as gagné aujourd'hui, sur 7 jours, sur 30 jours et depuis le début (ventes, achats, taxe), le détail par ressource, et tes ventes faites trop en dessous du prix du marché.
- **Objectifs** : ta liste d'objectifs (fichier `objectifs.json`). Se valident tout seuls : NFT achetés (`"type": "nft"`) ou vendus (`"vendre"`), compétences (`"competence"`), niveau (`"niveau"`), « dans le vert » sur 7 jours (`"dans_le_vert"`). Les autres (`"manuel"`) se cochent avec `"fait": true`. Prix des NFT et coût des ressources qui te manquent (`"ressources"`) mis à jour à chaque relevé.
- **Vente** : ton stock de ressources, ce qu'il vaut, et pour chacune un conseil (🟢 bon moment pour vendre, ⚪ prix normal, 🟠 attends si tu peux, 🔵 à garder pour ta ferme, 🔴 prix sous ton coût), avec le prix minimum à ne pas dépasser vers le bas et une alerte si tes dernières ventes étaient trop basses. Les ressources sont rangées en « à vendre » et « pour ta ferme » (seul le surplus est proposé) : réglable avec `"a_vendre"` et `"pour_ma_ferme"`. Réserves à garder réglables avec `"stock_a_garder"` dans `ma_ferme.json` (ex. `{"Wood": 300, "Stone": 300}`).
- **Objectifs** (haut de l'onglet) : choisis ton objectif principal (gagner des Flower, monter de niveau, agrandir la ferme) → l'outil propose quoi faire, calculé avec tes chiffres.
- **NFT** : chaque NFT à bonus (les tiens et ceux à acheter) avec son prix, son gain par jour et par mois, son rendement par an et un verdict (garder, vendre, bon achat). Règle ta production dans `ma_ferme.json` → `"ma_production"` (coups de pioche/hache par jour, cycles de vaches/poules, champs récoltés par jour) et ajoute tes vêtements à bonus dans `"nft_possedes"` (ex. `["Milk Apron"]`).
- **Compétences** : tes skills (lus automatiquement), ce que chacun fait et rapporte par jour, tes arbres et leurs paliers, et des conseils : points libres, compétences peu utiles à changer au prochain reset (sans bloquer un palier), les plus rentables à prendre.
- **Rentabilité** : combien te coûte la production d'une unité (pioches, haches, graines, nourriture) comparé à son prix de vente, la marge de tes vaches, cochons et poules par cycle, et ce que rapporte l'échange d'un cochon contre ses poils (niveaux 10 et 15).
- **Une ressource** : le cours d'une ressource sur 1, 3 ou 6 mois, avec tes prix de vente et d'achat.
- **Historique** : par jour, par semaine, par mois.
- **Échanges** : tous tes échanges, filtrables.
- **Compteurs** : solde, déposé, retiré, dépensé dans le jeu.

Il y a aussi un bilan écrit dans `releves/` et un fichier `donnees/prix.csv` qui s'ouvre dans un tableur.

## Bon à savoir
- Les graphiques ont besoin d'internet. Les tableaux marchent sans.
- Les données viennent d'outils communautaires (SFL Tool, sfl.world). Ils peuvent être lents ou changer ; si le relevé échoue, relance-le plus tard.
- Le petit serveur ne fonctionne que sur ton ordinateur (adresse 127.0.0.1) : personne d'autre ne peut y accéder.
- Outil non officiel, sans lien avec les créateurs de Sunflower Land.
