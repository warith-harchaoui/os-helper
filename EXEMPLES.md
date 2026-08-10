# Exemples OS Helper

Ce document fournit des exemples détaillés pour utiliser le module `OS Helper` afin de simplifier les tâches de programmation courantes.

---

## Table des matières

1. [Installation et configuration](#installation-et-configuration)
2. [Informations système](#informations-système)
   - [Résolution du nombre de workers](#résolution-du-nombre-de-workers)
3. [Inspection matérielle](#inspection-matérielle)
   - [Instantané en un appel](#instantané-en-un-appel)
   - [Sondes individuelles](#sondes-individuelles)
   - [Métriques en direct](#métriques-en-direct)
4. [Chargement de configuration](#chargement-de-configuration)
5. [Utilitaires fichiers et dossiers](#utilitaires-fichiers-et-dossiers)
   - [Vérifier l'existence d'un fichier ou d'un dossier](#vérifier-lexistence-dun-fichier-ou-dun-dossier)
   - [Gérer les dossiers](#gérer-les-dossiers)
   - [Taille de fichier et opérations sur les chemins](#taille-de-fichier-et-opérations-sur-les-chemins)
   - [Copier, supprimer et localiser des fichiers](#copier-supprimer-et-localiser-des-fichiers)
   - [Décrire le contenu d'un dossier](#décrire-le-contenu-dun-dossier)
   - [Décomposer un chemin fichier/dossier](#décomposer-un-chemin-fichierdossier)
   - [Compresser un dossier en fichier ZIP](#compresser-un-dossier-en-fichier-zip)
6. [Utilitaires de chaînes](#utilitaires-de-chaînes)
   - [Détecter les chaînes vides](#détecter-les-chaînes-vides)
   - [Conversion en chaîne ASCII](#conversion-en-chaîne-ascii)
7. [Ressources temporaires](#ressources-temporaires)
   - [Créer un fichier temporaire](#créer-un-fichier-temporaire)
   - [Créer un dossier temporaire](#créer-un-dossier-temporaire)
   - [Créer un répertoire temporaire persistant](#créer-un-répertoire-temporaire-persistant-nettoyage-à-la-charge-de-lappelant)
   - [Déposer un fichier sur un backend distant](#déposer-un-fichier-sur-un-backend-distant)
8. [Commandes système](#commandes-système)
   - [Exécuter une commande système](#exécuter-une-commande-système)
9. [Réseau](#réseau)
   - [Vérifier qu'une URL est valide et accessible](#vérifier-quune-url-est-valide-et-accessible)
   - [Récupérer les adresses IP publiques](#récupérer-les-adresses-ip-publiques)
10. [Hachage](#hachage)
    - [Générer un hachage pour une chaîne](#générer-un-hachage-pour-une-chaîne)
    - [Hacher un fichier](#hacher-un-fichier)
    - [Hacher un dossier](#hacher-un-dossier)
11. [Utilitaires de durée](#utilitaires-de-durée)
    - [Formater des durées en chaînes lisibles](#formater-des-durées-en-chaînes-lisibles)
    - [Analyser des chaînes en durées](#analyser-des-chaînes-en-durées)
12. [Utilitaires divers](#utilitaires-divers)
    - [Verbosité et journalisation](#verbosité-et-journalisation)
    - [Horodatages et tailles en octets](#horodatages-et-tailles-en-octets)
    - [Télécharger des fichiers](#télécharger-des-fichiers)
    - [Barres de progression pour des transferts personnalisés](#barres-de-progression-pour-des-transferts-personnalisés)
    - [Ouvrir des fichiers avec l'application par défaut](#ouvrir-des-fichiers-avec-lapplication-par-défaut)
13. [Utilitaires de profilage](#utilitaires-de-profilage)
    - [Chronomètre en temps réel](#chronomètre-en-temps-réel)
    - [Chronomètre CPU](#chronomètre-cpu)
    - [Chronomètre GPU](#chronomètre-gpu)
    - [tic / toc façon MATLAB](#tic--toc-façon-matlab)

---


## Installation et configuration

Installez le paquet depuis PyPI (ou directement depuis GitHub, voir le README) :

```bash
# Utilitaires principaux (bibliothèque + CLI argparse)
pip install os-helper

# Jumelle CLI click optionnelle
pip install "os-helper[cli]"
```

Puis importez la bibliothèque : les exemples ci-dessous utilisent l'alias conventionnel `osh`.

```python
import os_helper as osh
```

## Informations système

Utilisez les fonctions suivantes pour déterminer la plateforme sur laquelle votre script s'exécute. Elles sont particulièrement utiles pour écrire des scripts multiplateformes.

```python
from os_helper import windows, linux, macos, unix

# Vérifier si le système est Windows
if windows():
    print("Exécution sous Windows !")

# Vérifier si le système est Linux
if linux():
    print("Exécution sous Linux !")

# Vérifier si le système est macOS
if macos():
    print("Exécution sous macOS !")

# Vérifier si le système est de type Unix
if unix():
    print("Exécution sur un système de type Unix !")
```

### Résolution du nombre de workers

`get_nb_workers` suit la convention `n_jobs` de scikit-learn (`0` = pool
entier, positif = nombre exact, négatif = `taille_pool + n + 1`),
surchageable pour tout le processus via la variable d'environnement
`NB_WORKERS`, pratique dans les conteneurs où le nombre de CPU visibles
ne reflète pas le vrai quota.

```python
from os_helper import get_nb_workers, getpid

print(get_nb_workers())      # -1 (défaut) : tous les cœurs CPU disponibles
print(get_nb_workers(-2))    # tous les cœurs sauf un
print(get_nb_workers(4))     # positif : pris au pied de la lettre
print(get_nb_workers(0))     # 0 : la taille complète du pool

print(getpid())              # ID du processus courant, sous forme de chaîne
```

## Inspection matérielle

Faits matériels et métriques en direct, multiplateformes : aucune dépendance
système lourde au-delà de `psutil` (le socle) et des outils propres à
chaque plateforme (`system_profiler` / `nvidia-smi` / `rocm-smi` / `ioreg`,
appelés uniquement quand c'est pertinent).

### Instantané en un appel

`hardware_info()` agrège chaque sonde ci-dessous en un seul dict prêt pour
le JSON : la même charge utile que renvoient les surfaces CLI/API/MCP
`hardware info`.

```python
from os_helper import hardware_info

info = hardware_info()
print(info)
# {
#     'platform': 'darwin',
#     'cpu': {'physical_cores': 12, 'logical_cores': 12,
#             'model': 'Apple M2 Max', 'percent': 8.3},
#     'ram_gb': 96.0, 'available_ram_gb': 61.2,
#     'disk': {'free_gb': 512.3, 'used_gb': 487.7,
#              'total_gb': 1000.0, 'percent_used': 48.8},
#     'gpu_vendor': 'apple', 'gpus': [],
#     'gpu_utilization_percent': 14.0,
#     'apple_chip': 'Apple M2 Max', 'apple_unified_gb': 96.0,
# }
```

### Sondes individuelles

Chaque champ de l'instantané ci-dessus est aussi accessible comme fonction à
part entière, pour les appelants qui n'ont besoin que d'un seul fait (par
exemple choisir une taille de batch à partir de `ram_gb()` sans payer le
coût d'une sonde GPU).

```python
from os_helper import (
    platform_name, cpu_count_logical, cpu_count_physical, cpu_model,
    ram_gb, gpu_vendor, gpus, apple_chip_name, apple_unified_memory_gb,
)

print(platform_name())         # 'darwin' / 'linux' / 'windows'
print(cpu_count_logical())     # 12 (inclut l'hyperthreading/SMT)
print(cpu_count_physical())    # 12 ou None si psutil ne peut pas le dire
print(cpu_model())             # 'Apple M2 Max' ou None

print(ram_gb())                # 96.0 (RAM totale installée)
print(gpu_vendor())            # 'apple' / 'nvidia' / 'amd' / 'intel' / 'cpu'
print(gpus())                  # [] sur Apple (mémoire unifiée, pas de liste de
                                #  VRAM dédiée) ; [{'vendor': 'nvidia', 'name': ...,
                                #  'vram_gb': ...}, ...] sur les machines NVIDIA/AMD

# La mémoire d'Apple Silicon est unifiée (partagée avec le GPU), elle est donc
# rapportée séparément plutôt que noyée dans la liste de VRAM de `gpus()`.
if gpu_vendor() == "apple":
    print(apple_chip_name())          # 'Apple M2 Max'
    print(apple_unified_memory_gb())  # 96.0
```

### Métriques en direct

À distinguer des faits statiques ci-dessus : ces valeurs sont ré-échantillonnées
à chaque appel (adapté à un rapport de diagnostic ponctuel ou un print CLI ;
pas à une boucle chaude). `hardware_info()` les intègre déjà : n'y accédez
directement que si vous voulez une seule valeur sans payer pour tout un
instantané.

```python
from os_helper import cpu_percent, available_ram_gb, disk_usage_gb, gpu_utilization_percent

print(cpu_percent())            # 8.3  (charge CPU instantanée, 0-100)
print(available_ram_gb())       # 61.2 (RAM libre à cet instant, <= ram_gb())

usage = disk_usage_gb()         # par défaut, le système de fichiers du dossier personnel
print(usage)                    # {'free_gb': 512.3, 'used_gb': 487.7,
                                 #  'total_gb': 1000.0, 'percent_used': 48.8}
print(disk_usage_gb("/tmp"))    # ou vérifiez le système de fichiers d'un chemin précis

# Apple via IOKit (pas besoin de sudo/powermetrics), NVIDIA via nvidia-smi,
# AMD via rocm-smi. None si indisponible (mauvais fournisseur, outil absent du PATH).
print(gpu_utilization_percent())  # 14.0 ou None
```

## Chargement de configuration

`get_config` résout les réglages selon un ordre de repli fixe : un fichier
JSON/YAML explicite (ou le premier fichier correspondant dans un dossier),
puis les fichiers `.env` fusionnés dans `os.environ`, puis l'environnement
du processus. Elle ne lève une `RuntimeError` claire que si aucune source ne
satisfait toutes les clés requises.

```python
from os_helper import get_config

# 1) Un fichier de config (ou un dossier qui en contient un) l'emporte en premier,
#    s'il possède toutes les clés.
config = get_config(
    keys=["host", "port"],
    config_type="database",
    path="config.yaml",  # ou un dossier : le premier *.json/*.yaml/*.yml
                          # avec toutes les clés requises est choisi, trié par nom
)
print(config)  # {'host': 'localhost', 'port': 5432}

# 2) Pas de chemin (ou le fichier manque une clé) : repli sur les fichiers .env,
#    fusionnés dans os.environ (par défaut : [".env"] dans le dossier courant).
config = get_config(keys=["api_key"], config_type="API", env_files=[".env.local"])

# 3) Puis les simples variables d'environnement, essayées d'abord en UPPER_CASE
#    (l'orthographe conventionnelle), puis la clé exacte telle que donnée.
import os
os.environ["API_KEY"] = "sk-example"
config = get_config(keys=["api_key"], config_type="API", path=None, env_files=[])
print(config)  # {'api_key': 'sk-example'}
```

> Vous chargez de vrais secrets (clés API, credentials de base de
> données) de cette façon ? Voir
> [GESTION_DES_CREDENTIALS.md](GESTION_DES_CREDENTIALS.md) pour les
> précautions de sécurité et comment superposer un vault (HashiCorp Vault,
> gestionnaires de secrets AWS/GCP/Azure) par-dessus `get_config`.

## Utilitaires fichiers et dossiers

Les utilitaires suivants aident à travailler efficacement avec les fichiers et
dossiers : vérifier leur existence, gérer les chemins ou effectuer des
opérations comme zipper des dossiers ou décrire leur contenu.

### Vérifier l'existence d'un fichier ou d'un dossier


```python
from os_helper import file_exists, dir_exists

# Vérifier qu'un fichier existe
print(file_exists("example.txt"))  # True si le fichier existe, False sinon

# Vérifier qu'un dossier existe et n'est pas vide
print(dir_exists("/path/to/folder", check_empty=True))  # True si non vide, False sinon
```

### Gérer les dossiers

```python
from os_helper import make_directory, remove_directory

# Créer un dossier
make_directory("/path/to/new_folder")
print("Dossier créé !")

# Supprimer un dossier (et son contenu, s'il existe)
remove_directory("/path/to/new_folder")
print("Dossier supprimé !")
```

### Taille de fichier et opérations sur les chemins

```python
from os_helper import size_file, absolute2relative_path, relative2absolute_path

# Obtenir la taille d'un fichier en octets
print(size_file("example.txt"))  # Sortie : 1024 (si le fichier fait 1 Ko)

# Convertir un chemin absolu en chemin relatif
relative_path = absolute2relative_path("/home/user/project/file.txt", "/home/user")
print(relative_path)  # Sortie : 'project/file.txt'

# Convertir un chemin relatif en chemin absolu
absolute_path = relative2absolute_path("relative/path/to/file")
print(absolute_path)  # Sortie : '/home/user/relative/path/to/file'
```

### Copier, supprimer et localiser des fichiers

```python
from os_helper import checkfile, copyfile, remove_files, join, recursive_glob, path_without_home

# Vérifier qu'un fichier existe (et optionnellement qu'il n'est pas vide)
# et lever une exception avec un message clair sinon : pratique comme
# précondition en tête de fonction.
checkfile("example.txt", "Expected input file is missing", check_empty=True)

# Copier un fichier, en créant au passage les dossiers de destination manquants.
copyfile("example.txt", "backups/example.txt")

# Suppression par lot au mieux : chaque suppression est journalisée, les
# fichiers absents sont ignorés plutôt que de lever une exception.
remove_files(["backups/example.txt", "does-not-exist.txt"])

# join() est os.path.join avec normalisation, l'appelant obtient donc un
# séparateur cohérent quelle que soit la façon dont les morceaux ont été passés.
config_path = join("configs", "prod", "app.yaml")
print(config_path)  # 'configs/prod/app.yaml'

# Trouver récursivement toutes les correspondances d'un motif glob sous un
# dossier racine.
python_files = recursive_glob("src", "*.py")
print(python_files)  # ['src/main.py', 'src/utils/helpers.py', ...]

# Afficher un chemin relatif au dossier personnel, pour des lignes de log
# destinées à l'utilisateur qui ne doivent pas exposer le chemin absolu complet.
print(path_without_home("/Users/alice/projects/app/config.yaml"))
# '~/projects/app/config.yaml'
```

### Décrire le contenu d'un dossier

`folder_description` parcourt un dossier, retourne un dict
`{chemin_relatif: taille_en_octets}` et peut en option écrire un
`index.html` au style Bootstrap et un fichier compagnon `description.json`
à côté.

```python
from os_helper import folder_description

description = folder_description(
    "/path/to/folder",
    recursive=True,         # descendre dans les sous-dossiers
    index_html=True,        # écrire /path/to/folder/index.html
    with_size=True,         # inclure une colonne de taille dans l'index HTML
    description_json=True,  # écrire /path/to/folder/description.json
)

print(description)
# {
#     'file1.txt': 1024,
#     'subfolder/file2.txt': 2097152,
# }
```

### Décomposer un chemin fichier/dossier

`folder_name_ext` découpe sur le **dernier** point, si bien que les
extensions à plusieurs parties comme `.tar.gz` ne sont pas réduites à une
seule extension. Retrouvez le nom de fichier original avec
`"basename.extension"`.

```python
from os_helper import folder_name_ext

# Décomposer un chemin de fichier en dossier, nom de base et extension
folder, name, ext = folder_name_ext("/path/to/file.tar.gz")
print(folder, name, ext)  # Sortie : '/path/to', 'file.tar', 'gz'

# Gérer les dossiers
folder, name, ext = folder_name_ext("/path/to/folder")
print(folder, name, ext)  # Sortie : '/path/to', 'folder', ''

# Gérer les fichiers sans extension
folder, name, ext = folder_name_ext("/path/to/file")
print(folder, name, ext)  # Sortie : '/path/to', 'file', ''

```

### Compresser un dossier en fichier ZIP

```python
from os_helper import zip_folder

# Créer une archive ZIP d'un dossier et de son contenu
zip_folder("/path/to/folder", "/path/to/folder_archive.zip")
print("Dossier compressé avec succès en archive ZIP !")
```

## Utilitaires de chaînes

Les utilitaires de chaînes simplifient les tâches courantes de manipulation
de texte, comme garantir la compatibilité ASCII ou nettoyer des chaînes pour
un usage sûr dans des noms de fichiers ou des URLs.



### Détecter les chaînes vides

`emptystring` détecte `None`, `""` et les chaînes composées uniquement
d'espaces en un seul appel : utilisez-la plutôt que `not s` ou `s == ""`,
qui ratent toutes deux `"   "`.

```python
from os_helper import emptystring

print(emptystring(None))     # True
print(emptystring(""))       # True
print(emptystring("   "))    # True  (uniquement des espaces)
print(emptystring("hello"))  # False
```

### Conversion en chaîne ASCII

```python
from os_helper import asciistring

# Convertir une chaîne en une représentation ASCII sûre
safe_string = asciistring("Café-Con-Leche!", replacement_char="_")
print(safe_string)  # Sortie : 'cafe_con_leche'

# Autoriser les chiffres et préserver la casse
safe_string = asciistring("Special#File$2024", lower=False)
print(safe_string)  # Sortie : 'Special-File-2024'

# S'assurer que le résultat convient pour des noms de fichiers ou des URLs
safe_string = asciistring("Café@2024.txt")
print(safe_string)  # Sortie : 'cafe-2024-txt'
```

## Ressources temporaires

Les utilitaires de ressources temporaires permettent de créer des fichiers
ou des dossiers temporaires pour des tests ou du stockage intermédiaire. Ces
ressources sont nettoyées automatiquement à la fin du contexte.


### Créer un fichier temporaire

```python
from os_helper import temporary_filename

# Créer un fichier temporaire
with temporary_filename(suffix=".txt") as temp_file:
    print(f"Fichier temporaire créé : {temp_file}")
    # Effectuer des opérations sur le fichier temporaire
    with open(temp_file, "wt") as f:
        f.write("Contenu temporaire")
# Le fichier est supprimé automatiquement à la fin du contexte
```

### Créer un dossier temporaire

```python
from os_helper import temporary_folder

# Créer un dossier temporaire
with temporary_folder(prefix="tempdir") as temp_dir:
    print(f"Dossier temporaire créé : {temp_dir}")
    # Effectuer des opérations dans le dossier temporaire
    with open(f"{temp_dir}/tempfile.txt", "wt") as f:
        f.write("Contenu temporaire")
# Le dossier et son contenu sont supprimés automatiquement à la fin du contexte
```

### Créer un répertoire temporaire persistant (nettoyage à la charge de l'appelant)

`make_temporary_directory` est le pendant sans gestionnaire de contexte de
`temporary_folder` : utilisez-le quand le répertoire doit **survivre** à un
bloc `with` (un gestionnaire de requête qui nettoie après avoir diffusé une
réponse, un dossier de travail pour la durée de vie du processus…). Vous
êtes responsable du nettoyage.

```python
from os_helper import make_temporary_directory, remove_directory

work = make_temporary_directory(prefix="myjob-")
try:
    # ... écrire des artefacts intermédiaires dans `work`, faire circuler le chemin ...
    pass
finally:
    remove_directory(work)  # vous décidez quand il disparaît
```

Vous pouvez aussi épingler un `temporary_filename` à l'intérieur d'un dossier
choisi (par exemple pour qu'un outil qui résout des chemins relatifs au
fichier retrouve quand même ses voisins) :

```python
from os_helper import temporary_filename

with temporary_filename(suffix=".wav", directory=work) as tmp:
    # `tmp` se trouve dans `work`, à côté des éventuels fichiers d'entrée voisins
    ...
```

### Déposer un fichier sur un backend distant

`temporary_remote_file` téléverse un fichier local là où vous le pointez
(S3, GCS, SFTP, un point de terminaison HTTP, un dict en mémoire…) et
garantit que l'artefact distant est supprimé à la sortie du bloc `with` —
même si le corps lève une exception.

Fournissez deux fonctions pour votre backend : `upload(local_path) ->
remote_id` et `delete(remote_id) -> None`. Passez en option
`checkfile_function` pour valider le téléversement, ou
`from_local_file=<path>` pour téléverser un fichier existant plutôt que
d'en créer un nouveau.

```python
from os_helper import temporary_remote_file

storage = {}

def upload(local_path):
    with open(local_path, "rb") as f:
        storage[local_path] = f.read()
    return local_path  # utiliser le chemin local comme identifiant "distant"

def delete(remote_path):
    storage.pop(remote_path, None)

with temporary_remote_file(
    upload, delete,
    prefix="run", suffix=".bin",
    initial_content=b"hello world",
) as remote:
    assert storage[remote] == b"hello world"
# l'artefact distant a disparu après le bloc
```

## Commandes système

La fonction utilitaire `system` permet d'exécuter des commandes système et
d'en capturer la sortie et les messages d'erreur. Elle fournit une gestion
robuste des erreurs et des vérifications optionnelles pour les fichiers ou
dossiers de sortie attendus.



### Exécuter une commande système

```python
from os_helper import system

# Exécuter une commande système
output = system("echo 'Hello, World!'")
print(output["out"])  # Sortie de la commande : "Hello, World!"
print(output["err"])  # Erreur de la commande (le cas échéant)

# Exécuter une commande et vérifier la sortie attendue
output = system("touch example.txt", expected_output="example.txt")
assert output["out"] == ""  # Pas de sortie stdout pour la commande 'touch'
assert output["err"] == ""  # Pas de sortie stderr pour la commande 'touch'
```


## Réseau

Les utilitaires `Réseau` fournissent des moyens simples de vérifier des URLs
et de récupérer des adresses IP publiques.



### Vérifier qu'une URL est valide et accessible

```python
from os_helper import is_working_url

# Vérifier qu'une URL est valide et accessible
url = "https://www.google.com"
if is_working_url(url):
    print(f"L'URL {url} est accessible.")
else:
    print(f"L'URL {url} n'est pas accessible.")
```

### Récupérer les adresses IP publiques

```python
from os_helper import get_user_ip

# Obtenir les adresses IP publiques
ip_info = get_user_ip()
print(f"Adresse IPv4 : {ip_info['ipv4']}")
print(f"Adresse IPv6 : {ip_info['ipv6']}")
```

## Hachage

Les utilitaires `Hachage` permettent de générer des empreintes pour des
chaînes, des fichiers et des dossiers, avec diverses options de contenu et
de configuration.


### Générer un hachage pour une chaîne

```python
from os_helper import hash_string

# Générer un hachage pour une chaîne
input_string = "example"
hash_result = hash_string(input_string)
print(f"Hachage de '{input_string}' : {hash_result}")

# Générer un hachage tronqué
truncated_hash = hash_string(input_string, size=8)
print(f"Hachage tronqué : {truncated_hash}")
```

### Hacher un fichier

```python
from os_helper import hashfile

# Créer un fichier d'exemple à hacher
with open("example.txt", "w") as f:
    f.write("Hash this content")

# Générer un hachage pour le fichier
file_hash = hashfile("example.txt")
print(f"Hachage du fichier : {file_hash}")
```

### Hacher un dossier

```python
from os_helper import hashfolder

# Créer un dossier et des fichiers de test
import os
os.makedirs("test_folder", exist_ok=True)
with open("test_folder/file1.txt", "w") as f:
    f.write("File 1 content")
with open("test_folder/file2.txt", "w") as f:
    f.write("File 2 content")

# Générer un hachage pour le dossier basé sur le contenu
folder_hash = hashfolder("test_folder", hash_content=True)
print(f"Hachage du contenu du dossier : {folder_hash}")

# Générer un hachage pour le dossier basé uniquement sur le chemin
path_hash = hashfolder("test_folder", hash_content=False, hash_path=True)
print(f"Hachage du chemin du dossier : {path_hash}")

# Générer un hachage incluant la date courante
dated_hash = hashfolder("test_folder", date=True)
print(f"Hachage du dossier avec date : {dated_hash}")
```


## Utilitaires de durée

Utilitaires pour formater et analyser des durées lisibles par un humain.


### Formater des durées en chaînes lisibles

`time2str` formate un nombre de secondes en heures / minutes / secondes.

```python
from os_helper import time2str

duration = 3661  # 1 heure, 1 minute et 1 seconde

formatted_time = time2str(duration)
print(f"Temps formaté : {formatted_time}")           # "1 hr 1 min 1 sec"

compact_time = time2str(duration, no_space=True)
print(f"Temps compact : {compact_time}")              # "1hr 1min 1sec"
```

### Analyser des chaînes en durées

`str2time` analyse les formulations courantes de durées en secondes.

```python
from os_helper import str2time

print(str2time("1:30:00"))      # 5400.0  (HH:MM:SS)
print(str2time("1 hr 30 min"))  # 5400.0
print(str2time("90 minutes"))   # 5400.0
print(str2time("1.5 days"))     # 129600.0
```

## Utilitaires divers

La section `Utilitaires divers` contient des fonctions pour la
journalisation, le téléchargement de fichiers et la génération de messages
verbeux.


### Verbosité et journalisation

`verbosity(n)` fixe le niveau de log global sur le logger racine ; appelée
sans argument, elle retourne le niveau courant. La correspondance est
symétrique autour de zéro :

| niveau | nom du logger |
|------:|:-------------|
|  ``>= 2`` | DEBUG    |
|  ``1``    | INFO     |
|  ``0``    | WARNING  |
|  ``-1``   | ERROR    |
|  ``<= -2``| CRITICAL |

```python
from os_helper import verbosity, debug, info, error, critical, check

verbosity(2)  # afficher DEBUG + INFO + WARNING + ERROR + CRITICAL

debug("Visible uniquement si verbosity(2) ou plus est réglé.")
info("Le processus a démarré avec succès.")

# `error(...)` et `critical(...)` journalisent tous deux sans lever d'exception.
# Utilisez `check(cond, msg)` pour un échec façon assert ou levez explicitement.
error("Quelque chose s'est mal passé, mais l'exécution continue.")
critical("État irrécupérable atteint : journalisé, à l'appelant de décider la suite.")
check(1 + 1 == 2, "arithmetic is broken")
```

Pour une application de haut niveau, un script, un notebook ou une CLI,
`init_logging` connecte en un seul appel un gestionnaire console coloré (et
en option un fichier de log UTF-8). Les fonctions pratiques ci-dessus
(`info` / `warning` / …) journalisent via un logger dédié `"os_helper"`
dont les enregistrements remontent vers ce que configure `init_logging`.

```python
import logging
from os_helper import init_logging, info

# Logger racine : console colorée + un fichier de log, DEBUG et au-dessus.
init_logging(level=logging.DEBUG, filename="run.log")
info("la journalisation est configurée")

# Variante adaptée aux CLI : ne configure que l'arbre de logger de votre outil.
# Idempotente (un appel répété n'ajoute pas de handler en double), et
# propagate=True garde les enregistrements visibles pour les handlers racine
# d'un hôte ou de pytest (caplog).
init_logging(name="mytool", propagate=True, live_stream=True)
```

### Horodatages et tailles en octets

```python
from os_helper import now_string, format_size

# Horodatage courant, deux saveurs : "log" lisible par un humain ou compatible
# système de fichiers.
print(now_string())              # "2026/08/09-14:32:07"
print(now_string("filename"))    # "2026-08-09-14-32-07"

# Tailles en octets lisibles par un humain (unités décimales/SI, comme les
# fabricants de disques les affichent).
print(format_size(512))          # "512 B"
print(format_size(1_536))        # "1.50 KB"
print(format_size(1_536_000))    # "1.50 MB"
print(format_size(1_500_000_000))  # "1.50 GB"
```

### Télécharger des fichiers

La fonction download_file permet de télécharger des fichiers depuis une URL
vers un emplacement donné.

`download_file` est la primitive de transfert commune à toute la suite :
elle diffuse bloc par bloc (empreinte mémoire plate même pour un fichier de
plusieurs Go), affiche une barre de progression sur un terminal interactif
(désactivée automatiquement hors TTY) et par défaut est **reprenable**,
**réessayée**, **atomique** et **idempotente**. Elle retourne des métadonnées
permettant de choisir une extension de fichier à partir du type MIME du
serveur sans requête supplémentaire.

```python
from os_helper import download_file, file_exists

# Téléchargement de base. Les octets atterrissent dans un fichier compagnon
# "<file>.part" et sont renommés atomiquement vers la destination une fois
# complets, si bien que le chemin final n'existe jamais qu'en fichier complet,
# jamais tronqué.
url = "https://example.com/sample.pdf"  # mettez votre propre URL à la place de cet exemple fictif
file_path = "downloaded_sample.pdf"

meta = download_file(url, file_path)
print(meta)
# {'path': 'downloaded_sample.pdf', 'content_type': 'application/pdf',
#  'bytes': 12345, 'sha256': '', 'resumed': False}

# Idempotent par défaut : un second appel voit le fichier complet et court-circuite
# le réseau entièrement. Passez overwrite=True pour forcer un nouveau téléchargement.
download_file(url, file_path)  # pas de re-téléchargement, retourne immédiatement

# Intégrité vérifiée et reprenable : si un "<file>.part" partiel existe, le
# transfert continue avec une requête HTTP Range plutôt que de repartir de zéro ;
# le SHA-256 du fichier terminé est vérifié et une non-correspondance lève une
# ValueError. Les erreurs réseau transitoires sont réessayées avec un backoff
# exponentiel (retries=3 par défaut).
download_file(
    "https://example.com/model.bin",
    "model.bin",
    sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
)

# Certains serveurs/CDN rejettent la vérification préalable HEAD (405/403) même
# quand GET fonctionne : passez check_url=False pour la sauter et se fier au
# statut de GET à la place.
download_file(url, file_path, check_url=False, overwrite=True)

# Vérifier que le fichier existe
if file_exists(file_path):
    print(f"Fichier téléchargé avec succès vers {file_path}")
else:
    print("Le téléchargement du fichier a échoué.")
```



### Barres de progression pour des transferts personnalisés

`download_file` utilise `progress_bar` en interne ; utilisez-la directement
en enveloppant votre propre transfert (un callback S3/SFTP, un
téléversement par blocs personnalisé) pour que chaque opération de
déplacement d'octets de votre projet affiche la même interface : unités
mises à l'échelle en octets, désactivée automatiquement quand `stderr`
n'est pas un terminal interactif (logs CI, sortie redirigée).

```python
from os_helper import progress_bar

total_bytes = 10_485_760  # par ex. depuis un en-tête Content-Length
bar = progress_bar(total=total_bytes, desc="uploading")
for chunk in range(0, total_bytes, 1_048_576):
    # ... envoyer/recevoir un bloc ici ...
    bar.update(min(1_048_576, total_bytes - chunk))
bar.close()
```

### Ouvrir des fichiers avec l'application par défaut

La fonction openfile ouvre un fichier avec l'application par défaut pour
son type.

```python
from os_helper import openfile

# Ouvrir un fichier PDF avec le lecteur par défaut
openfile("example.pdf") # mettez votre propre fichier à ouvrir par votre propre OS à la place de cet exemple fictif
```

## Utilitaires de profilage

Trois gestionnaires de contexte et une paire façon MATLAB pour mesurer le
temps que prend du code. Choisissez le bon outil pour la question posée :

| Question | Utiliser |
|---|---|
| « Combien de temps réel cela a-t-il pris ? » (inclut sleeps, I/O, attentes GPU) | `wall_timer` |
| « Combien de travail CPU cela a-t-il fait ? » (exclut sleep / I/O / sous-processus) | `cpu_timer` |
| « Combien de temps le GPU y a-t-il passé ? » (événements CUDA ou synchro MPS) | `gpu_timer` |
| « Chronomètre rapide façon MATLAB » | `tic` / `toc` |

### Chronomètre en temps réel

```python
import time
from os_helper import wall_timer, time2str

with wall_timer() as t:
    time.sleep(0.05)
    # ... travail ...

print(f"Temps réel : {t['seconds']:.3f} s ({time2str(t['seconds'])})")
```

### Chronomètre CPU

`cpu_timer` rapporte le CPU consommé par ce processus (utilisateur + système,
sommé sur tous les threads) : les sleeps et les I/O ne comptent pas, il
isole donc le « vrai calcul ». N'inclut PAS les sous-processus (utilisez
`wall_timer` pour ceux-ci).

```python
from os_helper import cpu_timer

with cpu_timer() as t:
    total = sum(i * i for i in range(10_000_000))

print(f"Temps CPU : {t['seconds']:.3f} s")
```

### Chronomètre GPU

Import paresseux de `torch` : `os-helper` lui-même ne dépend PAS de
PyTorch. Si torch n'est pas installé ou qu'aucun GPU n'est disponible au
moment de l'appel, lève une `RuntimeError` claire (le helper existe ; il
refuse simplement de s'exécuter).

```python
from os_helper import gpu_timer
import torch

if torch.cuda.is_available():
    x = torch.randn(2048, 2048, device="cuda")
    with gpu_timer() as t:           # backend="auto" choisit cuda/mps/lève une exception
        y = x @ x
    print(f"Temps GPU : {t['milliseconds']:.2f} ms")
```

Apple Silicon : passez `backend="mps"` (ou fiez-vous à `auto`). Le chemin
MPS de PyTorch manque d'événements de chronométrage fin, le helper se
rabat donc sur `torch.mps.synchronize()` + une mesure en temps réel autour
du bloc synchronisé (précision ~1 ms).

### tic / toc façon MATLAB

Pour parsemer un script d'un chronomètre rapide. Chaque `tic()` écrase le
« dernier tic » implicite. Pour des chronométrages imbriqués, capturez le
handle.

```python
from os_helper import tic, toc

tic()
# ... travail ...
elapsed = toc()                  # secondes, ne réinitialise PAS
print(f"A pris {elapsed:.3f}s")

# Chronométrages imbriqués via des handles explicites :
t_outer = tic()
# ...
t_inner = tic()
# ...
print(toc(t_inner))              # bloc interne
print(toc(t_outer))              # bloc externe
```

Appelez `toc(log=True)` pour aussi émettre une ligne de log INFO.
