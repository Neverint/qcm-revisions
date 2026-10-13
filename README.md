# Révisions Admin SecOps

QCM de révision pour l'administration systèmes, le réseau et la cybersécurité, utilisable sur téléphone **sans connexion**.

Plus de 440 questions sur 26 thèmes : Linux, systemd, SSH, réseau et sous-réseaux, pare-feu, sécurité, cryptographie, SOC/SIEM, virtualisation, Ceph, Docker, Kubernetes, Ansible, supervision, Windows/AD, scripts, Git, IA, ITIL, et des scénarios de dépannage. Le niveau visé est celui des certifications d'entrée (Linux Essentials / LPIC-1, Network+ / CCNA, Security+ / ISC2 CC, ITIL Foundation).

## Utilisation

- **Entraînement** : questions tirées au hasard, avec priorité à celles qu'on rate (répétition espacée, boîtes de Leitner).
- **Nouvelles** : seulement les questions jamais vues.
- **Mes erreurs** : seulement les questions ratées.
- **Examen** : 40 questions en 45 minutes, correction à la fin.

L'ordre des questions et des réponses change à chaque fois. Une explication courte s'affiche après chaque réponse. La progression est enregistrée sur l'appareil (localStorage).

### Installer sur iPhone (hors ligne)

1. Ouvrir le site GitHub Pages du dépôt dans **Safari**.
2. **Partager → Sur l'écran d'accueil**.
3. Ouvrir l'appli une fois avec du réseau. Ensuite elle fonctionne sans connexion.

Les nouvelles questions arrivent automatiquement : l'appli récupère la nouvelle version en arrière-plan et l'affiche à l'ouverture suivante.

## Structure du dépôt

```
questions/        banque de questions, un fichier texte par domaine
src/app.html      l'application (HTML, CSS et JavaScript, sans dépendance)
build.py          valide les questions et génère le site
tools/patch.py    remplace les réponses de questions existantes, par identifiant
.github/workflows/deploy.yml   CI : validation, build et publication sur GitHub Pages
```

Chaque push sur `main` lance la CI, qui valide toutes les questions puis publie le site. Une question invalide fait échouer le build : rien n'est publié.

## Ajouter des questions

Format d'une question dans `questions/*.txt` :

```
## net

Q: Quel port utilise HTTPS par défaut ?
+ 443/TCP
- 80/TCP
- 8443/UDP
- 22/TCP
E: HTTP = 80, HTTPS = 443.
```

- `## id` : le thème des questions qui suivent (liste des thèmes dans `build.py`).
- `Q:` l'énoncé (`Q!:` garde les réponses dans l'ordre écrit).
- `+` la bonne réponse (une seule), `-` 2 à 4 mauvaises réponses plausibles.
- `E:` l'explication affichée après la réponse.
- `` `code` `` et `**gras**` sont acceptés.

Les identifiants (`net-012`…) dépendent de l'ordre dans chaque thème : **ajouter les nouvelles questions à la fin de leur thème** pour ne pas mélanger la progression enregistrée.

Le build vérifie : une seule bonne réponse, 3 à 5 réponses, pas de doublon, une explication, pas d'option du type « toutes les réponses ». Il affiche aussi la part de questions où la bonne réponse est nettement la plus longue (à garder sous 25 %).

## Build en local

```bash
pip install pillow
python3 build.py 1.0
python3 -m http.server -d dist/gh 8000   # puis http://localhost:8000
```

`dist/gh/` contient le site hors ligne (manifest, service worker, icônes). `dist/artifact.html` est une version en un seul fichier, sans service worker.
