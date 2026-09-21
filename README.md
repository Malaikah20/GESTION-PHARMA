# Gestion Pharmacie

Application web Django pour gerer les produits, le stock, les clients, les fournisseurs, les ventes, les factures, les statistiques et les notifications d'une pharmacie.

## Prerequis

- Python 3.14 ou une version compatible
- Windows PowerShell
- Un environnement virtuel Python

## Installation

Depuis le dossier du projet :

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requerements.txt
```

Si PowerShell bloque l'activation de l'environnement :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

## Configuration de la base de donnees

Appliquer les migrations :

```powershell
python manage.py migrate
```

Creer un compte administrateur :

```powershell
python manage.py createsuperuser
```

## Lancer l'application

```powershell
python manage.py runserver
```

Ouvrir ensuite : http://127.0.0.1:8000/

Interface d'administration : http://127.0.0.1:8000/admin/

## Commandes utiles

Verifier la configuration Django :

```powershell
python manage.py check
```

Lancer les tests :

```powershell
python manage.py test
```

Creer de nouvelles migrations apres une modification de modele :

```powershell
python manage.py makemigrations
python manage.py migrate
```

## Fonctionnalites

- Gestion des produits, categories et fournisseurs
- Suivi du stock et des seuils d'alerte
- Suivi des dates de peremption
- Gestion des clients
- Creation de ventes avec plusieurs lignes de produits
- Verification du stock lors d'une vente
- Decrement automatique du stock apres encaissement
- Generation des factures
- Statistiques basees sur les ventes reelles
- Notifications basees sur les ruptures, les stocks faibles et les peremptions
- Authentification des utilisateurs

## Structure principale

```text
Gestion_pharma/
|-- manage.py
|-- Gestion_pharma/       Configuration Django
|-- Produits/              Application principale
|-- media/                 Fichiers envoyes par les utilisateurs
|-- db.sqlite3             Base de donnees SQLite locale
|-- requerements.txt       Dependances Python
```

## Remarques

Le projet utilise SQLite en environnement local. Le fichier `db.sqlite3` contient les donnees locales de l'application.

Pour un environnement de production, definir une nouvelle cle secrete, des hotes autorises et des parametres de securite adaptes.
