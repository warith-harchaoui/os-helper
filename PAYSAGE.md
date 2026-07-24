# Paysage

🇫🇷 Français · [🇬🇧 LANDSCAPE.md](https://github.com/warith-harchaoui/os-helper/blob/main/LANDSCAPE.md)

Bibliothèques Python voisines et concurrentes dans l'espace « utilitaires
multi-OS + système de fichiers + configuration », comparées à `os-helper`.
Les notes vont de ⭐ (1) à ⭐⭐⭐⭐⭐ (5), évaluées sur la tâche visée par
`os-helper` — la colle utilitaire des pipelines d'IA (détection de l'OS,
manipulation de chemins, hachage, chargement de configuration, dossiers
temporaires, petits wrappers de sous-processus, journalisation colorée). Une
bibliothèque optimisée pour un tout autre usage (par ex. un système de
fichiers asynchrone complet, du stockage objet distant) n'est pas pénalisée —
la note reflète seulement l'adéquation à *ce* créneau.

## En un coup d'œil

| Gestion de l'OS | Détection multi-OS | Utilitaires de chemins | Hachage | Chargement de config | Fichiers temporaires | Multi-surface | Cohésion de la suite |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **os-helper** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| stdlib os | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ |
| click | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ |
| python-dotenv | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ |
| pydantic-settings | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐ |
| PyYAML | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ |
| requests | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐ |
| psutil | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ |
| sh | ⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ |
| fsspec | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ | ⭐ |
| loguru | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ |
| smart_open | ⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐ | ⭐ |

## Carte de positionnement

Représentation 2D du tableau ci-dessus.

![Carte de positionnement](https://raw.githubusercontent.com/warith-harchaoui/os-helper/main/assets/paysage.png)

La carte est un résumé en 2D des 7 critères : à lire comme une forme, pas comme un classement. « os-helper » se situe dans le coin en haut à droite. Les axes se lisent **Horizontal — Chargement ↔ Utilitaires** et **Vertical — Temporaires ↔ Suite**.

## Positionnement

`os-helper` se place volontairement à l'intersection de la **complétude de la
bibliothèque standard** (rien d'exotique ici ; chaque primitive correspond à
`os` / `pathlib` / `hashlib` / `tempfile` / `dotenv` / `yaml`) et de
l'**ergonomie des pipelines d'IA** (journalisation colorée ``info`` /
``warning`` / ``error``, raccourcis ``verbosity(-2..2)``, retours ``dict`` de
``system()`` / ``get_config()`` / ``get_user_ip()``, ``get_nb_workers``
suivant la convention ``n_jobs`` de scikit-learn, gestionnaire de contexte de
mise en attente distante pour les backends de stockage objet). Il ne cherche
délibérément **pas** à concurrencer `fsspec` sur les systèmes de fichiers
distants, `psutil` sur la télémétrie système, ou `pydantic-settings` sur la
configuration typée.

Là où `os-helper` gagne dans la famille :

1. **Surfaces multiples**. Chaque utilitaire est accessible depuis Python,
   depuis une CLI argparse et depuis une CLI click — mêmes signatures, aucune
   dérive.
2. **Zéro dépendance lourde** pour le cœur (`requests`, `pyyaml`,
   `python-dotenv`, `validators`). La CLI click est un extra optionnel, donc
   `pip install os-helper` reste léger.
3. **Fondation de la famille AI Helpers** : chaque autre paquet `*-helper`
   importe ``os_helper`` pour la journalisation, les chemins, les dossiers
   temporaires, le hachage et la configuration. C'est la couche sur laquelle
   tout le reste repose.

## Quand choisir quoi

- **`os-helper`** — scripts et bibliothèques du quotidien dans la suite AI
  Helpers : journalisation cohérente, chemins multi-plateformes, ergonomie
  « donne-moi juste un hash / un dossier temporaire / une valeur `.env` ».
- **`pathlib` (stdlib)** — quand on veut zéro dépendance tierce et qu'on
  accepte de câbler soi-même journalisation / configuration / hachage.
- **`click` / `typer`** — quand la CLI *est* le produit et qu'on veut des
  décorateurs riches / la complétion shell prête à l'emploi (nous livrons déjà
  un jumeau click, les deux mondes sont couverts).
- **`pydantic-settings`** — quand la configuration est complexe, typée et
  validée contre un schéma.
- **`fsspec` / `smart_open`** — quand on a besoin d'une abstraction uniforme
  de système de fichiers sur S3 / GCS / Azure / disque local.
- **`psutil`** — quand on a besoin de télémétrie système fine (cartes mémoire,
  affinité CPU, compteurs d'E/S par processus).
- **`loguru`** — quand on veut une pile de journalisation structurée entièrement
  personnalisée (os-helper enveloppe ``logging`` et reste interopérable).
