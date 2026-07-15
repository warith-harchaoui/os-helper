# OS Helper

[🇫🇷](https://github.com/warith-harchaoui/os-helper/blob/main/LISEZMOI.md) · [🇬🇧](https://github.com/warith-harchaoui/os-helper/blob/main/README.md)

[![CI](https://github.com/warith-harchaoui/os-helper/actions/workflows/ci.yml/badge.svg)](https://github.com/warith-harchaoui/os-helper/actions/workflows/ci.yml) [![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](LICENSE) [![Python](https://img.shields.io/badge/python-3.10%E2%80%933.13-blue.svg)](#)

`OS Helper` fait partie d'une collection de bibliothèques appelée `AI Helpers`, développée pour bâtir des applications d'intelligence artificielle.

[🌍 AI Helpers](https://harchaoui.org/warith/ai-helpers)

[![logo](https://raw.githubusercontent.com/warith-harchaoui/os-helper/main/assets/logo.png)](https://harchaoui.org/warith/ai-helpers)

OS Helper est une bibliothèque Python qui fournit des fonctions utilitaires pour travailler avec différents systèmes d'exploitation. Elle propose un ensemble d'outils pour simplifier les opérations système courantes, la manipulation de fichiers et les tâches spécifiques à chaque OS.

## Documentation

[💻 Documentation](https://harchaoui.org/warith/ai-helpers/docs/os-helper-doc/)

[📋 Exemples](https://github.com/warith-harchaoui/os-helper/blob/main/EXAMPLES.md)

## Fonctionnalités

- Détection du système d'exploitation (Windows, Linux, macOS, Unix)
- Opérations de fichiers (création, suppression, déplacement, copie)
- Récupération d'informations système (CPU, mémoire, disque)
- Gestion de chemins multi-plateformes
- Utilitaires de hash de fichiers et de chaînes
- Gestion et exécution de processus

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
pip install "git+https://github.com/warith-harchaoui/os-helper.git@v1.5.2"

# Jumelle CLI click optionnelle
pip install "os-helper[cli] @ git+https://github.com/warith-harchaoui/os-helper.git@v1.5.2"
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
pip install "os-helper[cli] @ git+https://github.com/warith-harchaoui/os-helper.git@v1.5.2"
os-helper-click hash file ./pyproject.toml
```

Un plan d'IHM innovant (Tree Radar / Dedupe Lens / Config Explorer) est
détaillé dans [GUI.md](GUI.md).

Le paysage concurrentiel (stdlib, pathlib, click, python-dotenv, psutil,
fsspec, …) est analysé dans [LANDSCAPE.md](LANDSCAPE.md).

## Auteur

 - [Warith HARCHAOUI](https://linkedin.com/in/warith-harchaoui)

## Remerciements

Remerciements chaleureux à [Mohamed Chelali](https://mchelali.github.io) et [Bachir Zerroug](https://www.linkedin.com/in/bachirzerroug) pour nos échanges fructueux.

## Licence

Ce projet est distribué sous la licence BSD-3-Clause — voir le fichier [LICENSE](LICENSE) pour plus de détails.
