# Tuto d'installation — Tableau de bord Sunflower Land

Durée : 10 minutes, une seule fois. Ensuite, un double-clic par jour.

L'outil ne touche jamais au jeu. Il ne demande ni mot de passe, ni wallet, ni clé.
Il suffit de ton **numéro de ferme** : l'outil va chercher tout seul les données sur SFL Tool (primerascripto.com) et sfl.world.
Tu n'as **plus besoin d'aller sur ces sites** : tout s'affiche dans ton tableau de bord.

---

## Étape 1 — Dézipper
1. Enregistre `Tableau-de-bord-SFL.zip` où tu veux (par exemple dans Documents).
2. Double-clic dessus (Mac) ou clic droit → **Extraire tout** (Windows).
3. Tu obtiens un dossier avec 9 fichiers. **Ne les sépare pas.**

## Étape 2 — Installer Python 3

### Sur Mac
1. Ouvre **Terminal** (Cmd + Espace, tape « Terminal », Entrée).
2. Tape `python3 --version` puis Entrée.
   - Si ça affiche `Python 3.x.x` → c'est bon, passe à l'étape 3.
   - Si une fenêtre propose d'installer des « outils de développement » → clique **Installer**, attends la fin, puis recommence.
   - Sinon : va sur **python.org** → Downloads → télécharge la version pour macOS → installe-la (suivant, suivant…).

### Sur Windows
1. Va sur **python.org** → Downloads → **Download Python 3.x**.
2. Lance l'installateur. ⚠️ **Coche « Add Python to PATH »** tout en bas de la première fenêtre, puis **Install Now**.
3. Vérifie : touche Windows, tape `cmd`, Entrée, puis tape `python --version`. Ça doit afficher `Python 3.x.x`.

## Étape 3 — Mettre ton numéro de ferme
1. Trouve ton numéro de ferme dans le jeu (le long nombre affiché dans ton profil / à côté de ton nom).
2. Dans le dossier, ouvre **`ma_ferme.json`** avec un éditeur de texte :
   - Mac : clic droit → Ouvrir avec → **TextEdit**
   - Windows : clic droit → Ouvrir avec → **Bloc-notes**
3. Remplace `METS_TON_NUMERO_ICI` par ton numéro. **Garde les guillemets.** Exemple :
   ```json
   {
     "numero_de_ferme": "1234567890123456",
     "nft_a_suivre": []
   }
   ```
4. Enregistre (Cmd + S / Ctrl + S) et ferme.

C'est la **seule** info à donner : à partir de ce numéro, l'outil récupère tes échanges, ton stock, ton niveau, tes compétences et les prix du marché.

## Étape 4 — Lancer l'outil
- **Mac** : double-clic sur **`Lancer le relevé.command`**.
  La première fois, macOS peut bloquer : fais **clic droit → Ouvrir → Ouvrir**.
  (Si ça bloque encore : Réglages Système → Confidentialité et sécurité → « Ouvrir quand même ».)
- **Windows** : double-clic sur **`Lancer le relevé.bat`**.
  Si Windows affiche « Windows a protégé votre ordinateur » : **Informations complémentaires → Exécuter quand même**.

Une petite fenêtre noire s'ouvre, travaille 30 secondes à 1 minute, puis **le tableau de bord s'ouvre dans ton navigateur**.
👉 **Laisse la fenêtre noire ouverte** tant que tu utilises le tableau de bord (c'est elle qui fait marcher le bouton 🔄 Actualiser). Ferme-la quand tu as fini.

## Étape 5 — Chaque jour
- Relance **`Lancer le relevé`** une fois par jour (le soir, par exemple).
- Important : le jeu ne garde que tes **50 derniers échanges**. Si tu attends plus d'une semaine, les plus anciens sont perdus.
- Tes données restent sur ton ordinateur, dans le dossier `donnees/` (créé tout seul). **Ne le supprime pas.**

Astuce : pour aller plus vite, fais glisser `Lancer le relevé` dans ton Dock (Mac) ou sur ton Bureau (Windows, clic droit → Envoyer vers → Bureau).

---

## Ça ne marche pas ?
| Problème | Solution |
|---|---|
| « python3: command not found » / « python n'est pas reconnu » | Python n'est pas installé, ou (Windows) la case « Add Python to PATH » n'a pas été cochée → réinstalle en la cochant. |
| La fenêtre se ferme tout de suite | Vérifie `ma_ferme.json` : le numéro doit être entre guillemets, sans espace. |
| Le tableau est vide | Normal le premier jour s'il n'y a eu aucun échange récent. Reviens après quelques jours de relevés. |
| Le bouton Actualiser ne marche pas | La fenêtre noire a été fermée → relance `Lancer le relevé`. |
| Les graphiques ne s'affichent pas | Il faut être connecté à internet (la librairie des graphiques se charge en ligne). |

Plus de détails sur chaque onglet : voir **`LISEZMOI.md`**.
