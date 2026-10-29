# Paysage

🇫🇷 Français · [🇬🇧 LANDSCAPE.md](https://github.com/warith-harchaoui/os-helper/blob/main/LANDSCAPE.md)

Bibliothèques Python voisines et concurrentes dans l'espace « utilitaires
multi-OS + système de fichiers + configuration », comparées à `os-helper`.
Les notes vont de ⭐ (1) à ⭐⭐⭐⭐⭐ (5), évaluées sur la tâche visée par
`os-helper` : la colle utilitaire des pipelines d'IA (détection de l'OS,
manipulation de chemins, hachage, chargement de configuration, dossiers
temporaires, téléchargements intelligents, petits wrappers de sous-processus,
journalisation colorée). Une
bibliothèque optimisée pour un tout autre usage (par ex. un système de
fichiers asynchrone complet, du stockage objet distant) n'est pas pénalisée ;
la note reflète seulement l'adéquation à *ce* créneau.

## En un coup d'œil

<!-- TABLE:START -->
| Gestion de l'OS | Détection multi-OS | Utilitaires de chemins | Hachage | Chargement de config | Fichiers temporaires | Téléchargements intelligents | Multi-surface | Cohésion de la suite |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **os-helper** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| stdlib os | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ |
| click | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ |
| python-dotenv | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ |
| pydantic-settings | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐ |
| PyYAML | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ |
| requests | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| psutil | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ |
| sh | ⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ |
| fsspec | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| smart_open | ⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ |
| pooch | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ |
| platformdirs | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐ |
<!-- TABLE:END -->

## Carte de positionnement

<!-- FIGURE:START -->
Représentation 2D du tableau ci-dessus.

![Carte de positionnement](https://raw.githubusercontent.com/warith-harchaoui/os-helper/main/assets/paysage.png)

La carte est un résumé en 2D des 8 critères : à lire comme une forme, pas comme un classement. « os-helper » se situe dans le coin en haut à droite. Les axes se lisent **Horizontal — Efficacité ↔ Adaptabilité** et **Vertical — Pragmatisme ↔ Intégrité**.
<!-- FIGURE:END -->

## Positionnement

`os-helper` se place volontairement à l'intersection de la **complétude de la
bibliothèque standard** (rien d'exotique ici ; chaque primitive correspond à
`os` / `pathlib` / `hashlib` / `tempfile` / `dotenv` / `yaml`) et de
l'**ergonomie des pipelines d'IA** (journalisation colorée ``info`` /
``warning`` / ``error``, raccourcis ``verbosity(-2..2)``, retours ``dict`` de
``system()`` / ``get_config()`` / ``get_user_ip()``, ``get_nb_workers``
suivant la convention ``n_jobs`` de scikit-learn, téléchargements intelligents
vérifiés par hachage avec cache local, gestionnaire de contexte de mise en
attente distante pour les backends de stockage objet, un instantané matériel
CPU/RAM/GPU en un appel). Il ne cherche délibérément **pas** à concurrencer
`pooch` sur la récupération de données scientifiques, `fsspec` sur les
systèmes de fichiers distants, `psutil` sur la télémétrie fine par processus
(cartes mémoire, affinité CPU, compteurs d'E/S par processus) ou
`pydantic-settings` sur la configuration typée.

Là où `os-helper` gagne dans la famille :

1. **Surfaces multiples**. Chaque utilitaire est accessible depuis Python,
   une API HTTP (FastAPI), des outils MCP (pour les agents) et l'interface
   Tree Radar, toujours avec les mêmes signatures, aucune dérive. Il n'y a
   pas de ligne de commande : envelopper `path exists` dans une commande
   shell ne faisait que répéter ce que le shell disait déjà, donc les deux
   CLI ont disparu en 3.0.0.
2. **Zéro dépendance lourde** pour le cœur (`requests`, `pyyaml`,
   `python-dotenv`, `validators`). Chaque surface est un extra optionnel, donc
   `pip install os-helper` reste léger.
3. **Fondation de la famille AI Helpers** : chaque autre paquet `*-helper`
   importe ``os_helper`` pour la journalisation, les chemins, les dossiers
   temporaires, le hachage et la configuration. C'est la couche sur laquelle
   tout le reste repose.

## Quand choisir quoi

- **`os-helper`** : scripts et bibliothèques du quotidien dans la suite AI
  Helpers : journalisation cohérente, chemins multi-plateformes, ergonomie
  « donne-moi juste un hash / un dossier temporaire / une valeur `.env` ».
- **`pathlib` (stdlib)** : quand on veut zéro dépendance tierce et qu'on
  accepte de câbler soi-même journalisation / configuration / hachage.
- **`click` / `typer`** : quand la CLI *est* le produit. os-helper ne l'est
  pas : il ne livre aucune ligne de commande, seulement les trois lanceurs de
  surface (`os-helper-api`, `os-helper-mcp`, `os-helper-gui`). Mieux vaut donc
  prendre click directement qu'un habillage d'ici.
- **`pydantic-settings`** : quand la configuration est complexe, typée et
  validée contre un schéma.
- **`fsspec` / `smart_open`** : quand on a besoin d'une abstraction uniforme
  de système de fichiers sur S3 / GCS / Azure / disque local.
- **`pooch`** : quand on a besoin de téléchargements vérifiés par hachage de
  fichiers de données scientifiques, avec registre, contrôles d'intégrité et
  cache local.
- **`platformdirs`** : quand on veut seulement les répertoires utilisateur
  multi-OS canoniques (cache / config / données) et rien d'autre.
- **`psutil`** : quand on a besoin de télémétrie fine par processus (cartes
  mémoire, affinité CPU, compteurs d'E/S par processus) au-delà de
  l'instantané matériel CPU/RAM/GPU en un appel d'`os-helper`.

## Sources et date de relevé

**Relevé du 2026-10-27**, comparant `os-helper` 3.1.0 (ce dépôt) aux
bibliothèques citées plus haut.

Les notes en ⭐ traduisent une lecture du **périmètre documenté** de chaque
projet, pas un banc d'essai : rien n'a été chronométré ici et aucune
affirmation n'est faite sur la qualité du code des autres. Une case se lit
« quelle part de cette colonne le projet se donne-t-il pour mission » ; la
documentation du projet reste la référence avant de parier dessus.

La ligne d'`os-helper` est mesurée dans ce dépôt plutôt qu'affirmée : la
surface publique exportée par `os_helper/__init__.py`, les routes HTTP
déclarées par l'API (`/health`, `/os`, `/hardware`, `/hash/string`,
`/str/ascii`, `/misc/format-size`, `/misc/now`, `/misc/url-ok`, `/config`) et
les trois scripts de console de `pyproject.toml`. « Cohésion de la suite » est
un décompte, pas un avis : les seize autres membres d'AI Helpers importent
tous `os_helper` depuis le code de leur paquet.

Chaque autre ligne vient de la documentation du projet concerné :

| Ligne | Source |
|---|---|
| stdlib os | [docs.python.org — `os.path`](https://docs.python.org/3/library/os.path.html) |
| click | [click.palletsprojects.com](https://click.palletsprojects.com/) |
| python-dotenv | [saurabh-kumar.com/python-dotenv](https://saurabh-kumar.com/python-dotenv/) |
| pydantic-settings | [docs.pydantic.dev — settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| PyYAML | [pyyaml.org — documentation](https://pyyaml.org/wiki/PyYAMLDocumentation) |
| requests | [requests.readthedocs.io](https://requests.readthedocs.io/en/latest/) |
| psutil | [psutil.readthedocs.io](https://psutil.readthedocs.io/en/latest/) |
| sh | [sh.readthedocs.io](https://sh.readthedocs.io/en/latest/) |
| fsspec | [filesystem-spec.readthedocs.io](https://filesystem-spec.readthedocs.io/en/latest/) |
| smart_open | [github.com/piskvorky/smart_open](https://github.com/piskvorky/smart_open) |
| pooch | [fatiando.org/pooch](https://www.fatiando.org/pooch/latest/) |
| platformdirs | [platformdirs.readthedocs.io](https://platformdirs.readthedocs.io/en/latest/) |

Tous ces liens ont répondu HTTP 200 au contrôle du 2026-10-27. Aucun numéro de
version d'une bibliothèque tierce n'est cité dans ce document, à dessein : une
version figée dans un comparatif se périme en affirmation sur un logiciel que
personne n'a relu depuis.

## Idées à reprendre

Étudié plutôt que deviné : ce que chaque voisin fait mieux, puis ce que cette bibliothèque devrait changer pour l'égaler. Rien ici n'est un engagement : c'est la liste de lecture dont part la version suivante.

- **`pydantic-settings` — une config validée au chargement, pas à l'usage** — Des réglages typés liés aux variables d'environnement, qui échouent avec une erreur lisible dès le démarrage du processus. Une config en forme de dictionnaire lue au fond d'un appel échoue plus tard puis plus loin de sa cause, or c'est la forme qu'os-helper tend aujourd'hui à chaque membre.

- **`platformdirs` — les conventions de dossiers par OS, déjà justes** — Les dossiers de cache, de config, d'état puis de données diffèrent entre macOS, Linux et Windows. os-helper arbitre les chemins temporaires avec ceux de cache pour toute la suite : le prendre d'une bibliothèque qui suit ces conventions vaut mieux que d'écrire une jointure `~/.cache` de plus.

- **`pooch` — récupérer, vérifier l'empreinte, mettre en cache, revérifier** — Plusieurs membres téléchargent des poids de modèle au premier usage. `pooch` en fait un registre déclaré avec une empreinte par fichier, revérifiée à chaque chargement, plutôt qu'un téléchargement auquel on fait confiance parce qu'il s'est terminé.

- **`fsspec` / `smart_open` — un seul `open()` pour le local, S3 puis HTTP** — Les membres bifurquent aujourd'hui entre un chemin local et une URL distante. Un open conscient des URL dans le seul module dont ils dépendent tous supprimerait cette bifurcation partout d'un coup.
