# OS Helper

[🇫🇷](https://github.com/warith-harchaoui/os-helper/blob/main/LISEZMOI.md) · [🇬🇧](https://github.com/warith-harchaoui/os-helper/blob/main/README.md)

[![CI](https://github.com/warith-harchaoui/os-helper/actions/workflows/ci.yml/badge.svg)](https://github.com/warith-harchaoui/os-helper/actions/workflows/ci.yml) [![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](LICENSE) [![Python](https://img.shields.io/badge/python-3.10%E2%80%933.13-blue.svg)](#) [![Local-first](https://img.shields.io/badge/privacy-local--first-2f6f5e.svg)](#la-promesse)

`OS Helper` fait partie d'une collection de bibliothèques appelée `AI Helpers`, développée pour bâtir des applications d'intelligence artificielle.

[🌍 AI Helpers](https://harchaoui.org/warith/ai-helpers)

[![logo](https://raw.githubusercontent.com/warith-harchaoui/os-helper/main/assets/logo.png)](https://harchaoui.org/warith/ai-helpers)

OS Helper est une bibliothèque Python qui fournit des fonctions utilitaires pour travailler avec différents systèmes d'exploitation. Elle propose un ensemble d'outils pour simplifier les opérations système courantes, la manipulation de fichiers et les tâches spécifiques à chaque OS.

## Documentation

[💻 Documentation](https://harchaoui.org/warith/ai-helpers/docs/os-helper-doc/)

[📋 Exemples](https://github.com/warith-harchaoui/os-helper/blob/main/EXAMPLES.md)

## Fonctionnalités

Chaque fonction est un enrobage fin, bien typé et bien documenté — sans
dépendance système lourde, en Python pur sur macOS / Linux / Windows.

- **Détection de l'OS** — `windows()`, `linux()`, `macos()`, `unix()`.
- **Exécution de commandes & processus** — `system()` (`subprocess` sans shell,
  stdout/stderr capturés, vérifications optionnelles du code de sortie et de la
  sortie attendue), `openfile()` (ouvre avec l'application par défaut de l'OS),
  `getpid()`, `get_nb_workers()` (convention `n_jobs` de scikit-learn,
  surchargeable via `NB_WORKERS`).
- **Chemins** — `join()`, `folder_name_ext()` (découpe compatible `.tar.gz`),
  `absolute2relative_path()`, `relative2absolute_path()`, `path_without_home()`,
  `recursive_glob()`.
- **Fichiers & répertoires** — `file_exists()`, `dir_exists()` (avec contrôle de
  vacuité), `size_file()`, `checkfile()`, `copyfile()`, `make_directory()`,
  `remove_directory()`, `remove_files()` (lot best-effort).
- **Ressources temporaires** — `temporary_filename()` (géré par contexte,
  répertoire cible optionnel), `temporary_folder()`, `make_temporary_directory()`
  (persistant, nettoyage à la charge de l'appelant), `temporary_remote_file()`
  (transfert vers S3/GCS/SFTP/n'importe où avec nettoyage distant garanti).
- **Hachage** — `hash_string()`, `hashfile()`, `hashfolder()` (RIPEMD-160 si
  disponible, repli sur BLAKE2b ; empreintes hex stables de 40 caractères,
  multi-plateformes).
- **Chargement de configuration** — `get_config()` avec un ordre de repli
  déterministe : fichier JSON/YAML (ou dossier) → fichiers `.env` →
  environnement du processus.
- **Chaînes** — `emptystring()` (None / vide / espaces), `asciistring()`
  (dépliage des accents, slugs sûrs pour le système de fichiers).
- **Téléchargements & réseau** — `download_file()` (en flux, mémoire plate,
  taille de bloc adaptative, barre de progression, renvoie
  `{path, content_type, bytes}`), `progress_bar()` (fabrique `tqdm` partagée
  échelonnée en octets, silencieuse hors TTY), `is_working_url()`,
  `get_user_ip()`.
- **Rapport de dossier & archivage** — `folder_description()` (carte des tailles
  + `index.html` Bootstrap + `description.json`), `zip_folder()`.
- **Durées & horodatages** — `now_string()`, `format_size()`, `time2str()`,
  `str2time()`.
- **Chronométrage & profilage** — `wall_timer()`, `cpu_timer()`, `gpu_timer()`
  (événements CUDA / MPS Apple Silicon, `torch` en import paresseux), et
  `tic()` / `toc()` à la MATLAB.
- **Surface de journalisation** — `init_logging()` (console colorée + fichier,
  modes logger nommé et flux « live »), `verbosity()` (niveau entier en
  lecture/écriture), et `debug()` / `info()` / `warning()` / `error()` /
  `critical()` / `check()`.
- **Trois surfaces, un seul code** — bibliothèque importable, une CLI argparse
  `os-helper` (toujours installée) et sa jumelle `os-helper-click` (via l'extra
  `[cli]`).

## Installation

**Prérequis** — **Python 3.10–3.13** et **git**, multiplateforme (os-helper ne nécessite aucune dépendance système lourde) :

- 🍎 **macOS** ([Homebrew](https://brew.sh)) : `brew install python git`
- 🐧 **Ubuntu/Debian** : `sudo apt update && sudo apt install -y python3 python3-pip git`
- 🪟 **Windows** (PowerShell) : `winget install Python.Python.3.12 Git.Git`

Nous recommandons l'utilisation d'environnements Python. Consultez ce lien si vous ne savez pas comment faire : [🥸 Conseils techniques](https://harchaoui.org/warith/4ml/#install).

### Depuis PyPI (recommandé)

```bash
# Utilitaires principaux (bibliothèque + CLI argparse)
pip install os-helper

# Jumelle CLI click optionnelle
pip install "os-helper[cli]"
```

### Depuis les sources (sans PyPI)

```bash
# Utilitaires principaux (bibliothèque + CLI argparse)
pip install "git+https://github.com/warith-harchaoui/os-helper.git@v1.7.2"

# Jumelle CLI click optionnelle
pip install "os-helper[cli] @ git+https://github.com/warith-harchaoui/os-helper.git@v1.7.2"
```

## Utilisation

Les exemples ci-dessous montrent comment utiliser les fonctionnalités de la bibliothèque `os_helper`. Importez la bibliothèque comme `osh` avant de commencer.

```python
import os_helper as osh
```

1. Régler le niveau de verbosité et vérifier le système d'exploitation

```python
# Régler le niveau de verbosité pour afficher les messages de débogage
osh.verbosity(3)

# Vérifier si le système est Unix (Linux ou macOS)
if osh.unix():
    osh.info("Vous êtes sur un système Unix.")
else:
    osh.info("Vous n'êtes pas sur un système Unix.")
```

2. Horodatage et vérification d'existence de fichier
```python
# Générer un horodatage formaté pour les logs
timestamp = osh.now_string("log")
osh.info(f"Horodatage actuel (format log) : {timestamp}")

# Vérifier qu'un fichier existe et n'est pas vide
test_file = "example.txt"
if osh.file_exists(test_file, check_empty=True):
    osh.info(f"Le fichier {test_file} existe et n'est pas vide.")
else:
    osh.error(f"Le fichier {test_file} n'existe pas ou est vide.")
```

3. Création de répertoires et recherche de fichiers
```python
# Créer un répertoire
test_dir = "test_directory"
osh.make_directory(test_dir)
osh.info(f"Répertoire {test_dir} créé.")

# Recherche récursive des fichiers '.txt' dans le répertoire
matching_files = osh.recursive_glob(test_dir, "*.txt")
osh.info(f"Fichiers correspondants : {matching_files}")
```

4. Copier et supprimer des fichiers
```python
# Copier un fichier de la source vers la destination
source_file = "source.txt"
destination_file = "backup_source.txt"
osh.copyfile(source_file, destination_file)
osh.info(f"Fichier {source_file} copié vers {destination_file}")

# Supprimer le fichier copié (chaque suppression est enregistrée en INFO)
osh.remove_files([destination_file])
```

5. Décomposer un chemin et créer un fichier temporaire
```python
# Décomposer un chemin en dossier, nom de base et extension
folder, basename, ext = osh.folder_name_ext("/path/to/myfile.tar.gz")
osh.info(f"Dossier : {folder}, Nom de base : {basename}, Extension : {ext}")

# Créer et écrire dans un fichier temporaire
with osh.temporary_filename(suffix=".log") as temp_log:
    osh.info(f"Fichier temporaire créé en : {temp_log}")
    with open(temp_log, "w") as log_file:
        log_file.write("Ceci est une entrée temporaire.")
```

6. Exécuter des commandes système
```python
# Exécuter une commande et capturer sa sortie
cmd_output = osh.system("echo 'Bonjour, le monde !'")
osh.info(f"Sortie de la commande : {cmd_output['out']}")
```

7. Hasher des fichiers et des chaînes
```python
# Hasher le contenu d'un fichier
file_to_hash = "testfile.txt"
if osh.file_exists(file_to_hash):
    file_hash = osh.hashfile(file_to_hash)
    osh.info(f"Hash de {file_to_hash} : {file_hash}")

# Hasher une chaîne avec une longueur spécifique
hashed_string = osh.hash_string("MyTestString", size=8)
osh.info(f"Chaîne hashée : {hashed_string}")
```

8. Conversion en ASCII et identifiant de processus
```python
# Convertir une chaîne en ASCII sûr
safe_string = osh.asciistring("Café-Con-Leche!", replacement_char="_")
osh.info(f"Chaîne ASCII sûre : {safe_string}")

# Récupérer l'identifiant du processus courant
pid = osh.getpid()
osh.info(f"PID du processus : {pid}")
```

9. Vérifier la validité d'une URL et zipper un dossier
```python
# Vérifier qu'une URL est valide et accessible
url = "https://www.example.com"
if osh.is_working_url(url):
    osh.info(f"L'URL {url} est valide et accessible.")
else:
    osh.error(f"L'URL {url} n'est pas accessible.")

# Zipper un dossier
folder_to_zip = "my_folder"
zip_output = "my_folder_backup.zip"
osh.zip_folder(folder_to_zip, zip_output)
osh.info(f"Dossier {folder_to_zip} zippé dans {zip_output}")
```

## Exposition multi-surface

`os-helper` n'est pas qu'une bibliothèque — les mêmes fonctions sont
exposées comme import Python, comme CLI argparse, et comme jumelle CLI
click :

```bash
# Bibliothèque Python (par défaut)
import os_helper as osh

# CLI basée sur argparse (installée automatiquement)
os-helper os system
os-helper path exists ~/.zshrc
os-helper hash string hello --size 8
os-helper misc format-size 12345678
os-helper misc now --fmt filename

# Jumelle click (nécessite l'extra [cli])
pip install "os-helper[cli]"
# ou depuis les sources :
pip install "os-helper[cli] @ git+https://github.com/warith-harchaoui/os-helper.git@v1.7.2"
os-helper-click hash file ./pyproject.toml
```

### IHM Tree Radar (optionnelle)

Une première tranche réelle du plan [GUI.md](GUI.md) est livrée comme
surface **optionnelle** : **Tree Radar**, un tableau de bord local de type
**treemap** d'occupation disque. Chaque rectangle est un fichier ou un
dossier (surface = taille), coloré selon l'**âge**, le statut de
**dédoublonnage par hash**, ou la **famille de types**. L'IHM lit votre
disque et l'affiche dans votre navigateur — rien n'est envoyé ailleurs.

Sa pile web vit derrière l'extra `[gui]` pour que l'import de base
`import os_helper` reste léger (pas de FastAPI dans l'installation par
défaut) :

```bash
pip install "os-helper[gui]"

# Lancer le tableau de bord local (loopback uniquement), puis ouvrir http://127.0.0.1:8017/gui
os-helper gui --root ~/Downloads
# ou le point d'entrée dédié :
os-helper-gui --root ~/Downloads
```

Les jalons suivants (actions de la Dedupe Lens, Config Explorer) restent
décrits dans [GUI.md](GUI.md).

Le paysage concurrentiel (stdlib, pathlib, click, python-dotenv, psutil,
fsspec, …) est analysé dans [PAYSAGE.md](PAYSAGE.md), avec une carte de
positionnement.

## La promesse

os-helper fait partie d'une suite « local-first », soucieuse de
souveraineté. Plutôt que d'en faire un argument marketing, voici la
réalité honnête, cas par cas :

1. **Garanti local.** os-helper est une boîte à outils purement locale
   (système de fichiers / utilitaires). Rien n'est envoyé, aucune
   télémétrie, aucun compte. L'IHM optionnelle Tree Radar lit votre disque
   et affiche la treemap localement dans votre navigateur (le serveur
   n'écoute que sur `127.0.0.1`) — vos chemins, tailles et empreintes de
   contenu ne quittent jamais la machine.

2. **Impossible d'être local — les réserves.** Deux fonctions font du HTTP
   sortant *par conception*, car récupérer quelque chose est justement leur
   raison d'être : `download_file()` (elle télécharge l'URL que vous lui
   donnez) et les vérifications d'URL (`is_working_url()` / `check_url`).
   `get_user_ip()` interroge aussi, volontairement, un service public. Ce
   sont les seuls accès réseau de la bibliothèque, et vous ne les déclenchez
   qu'en les appelant explicitement.

3. **Votre décision.** Rien ici ne force le cloud. `temporary_remote_file()`
   peut déposer vers S3/GCS/SFTP, mais seulement si *vous* le branchez sur
   un distant. Si vous construisez du comportement réseau au-dessus
   d'os-helper, c'est votre choix — jamais un défaut.

## Auteur

 - [Warith HARCHAOUI](https://linkedin.com/in/warith-harchaoui)

## Remerciements

Remerciements chaleureux à [Mohamed Chelali](https://mchelali.github.io) et [Bachir Zerroug](https://www.linkedin.com/in/bachirzerroug) pour nos échanges fructueux.

## Licence

Ce projet est distribué sous la licence BSD-3-Clause — voir le fichier [LICENSE](LICENSE) pour plus de détails.
