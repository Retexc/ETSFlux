"""
Mise à jour automatique des horaires STM (GTFS), sans intervention.

Remplace la page « Réglages → GTFS » de l'ancien éditeur : le serveur télécharge lui-même le fichier
public de la STM, garde seulement nos lignes et nos arrêts (config.py), puis remplace les fichiers locaux.
Même filtrage que l'ancienne page : routes.txt par numéro de ligne, trips.txt par route_id,
stop_times.txt par trip_id ET stop_id.

Le fichier de la STM est gros (stop_times.txt fait plusieurs centaines de Mo une fois décompressé) :
tout est lu ligne par ligne, sans jamais le charger en mémoire (Render gratuit = 512 Mo).
"""
import csv
import io
import logging
import os
import shutil
import tempfile
import zipfile

import requests

logger = logging.getLogger('BdeB-GTFS')

GTFS_STM_URL = os.getenv("GTFS_STM_URL", "https://www.stm.info/sites/default/files/gtfs/gtfs_stm.zip")
FICHIERS = ("routes.txt", "trips.txt", "stop_times.txt")


class GtfsInvalide(Exception):
    """Le fichier reçu ne contient pas nos lignes ou nos arrêts : on garde les anciens fichiers."""


def _lire(zf, nom):
    # utf-8-sig : enlève le BOM éventuel au début du fichier
    return csv.DictReader(io.TextIOWrapper(zf.open(nom), encoding="utf-8-sig", newline=""))


def _ecrire(chemin, colonnes):
    f = open(chemin, "w", encoding="utf-8", newline="")
    w = csv.DictWriter(f, fieldnames=colonnes)
    w.writeheader()
    return f, w


def filtrer_gtfs(zip_path, dossier, lignes, arrets):
    """
    Lit le GTFS complet `zip_path` et écrit dans `dossier` les 3 fichiers filtrés.
    Les fichiers ne sont remplacés qu'à la fin, et seulement si tout est bon.
    Renvoie le nombre de lignes gardées par fichier.
    """
    lignes = {str(x) for x in lignes}
    arrets = {str(x) for x in arrets}
    os.makedirs(dossier, exist_ok=True)
    temp = tempfile.mkdtemp(dir=dossier)
    try:
        with zipfile.ZipFile(zip_path) as zf:
            manquants = [n for n in FICHIERS if n not in zf.namelist()]
            if manquants:
                raise GtfsInvalide(f"Fichiers absents du GTFS : {', '.join(manquants)}")

            route_ids = set()
            r = _lire(zf, "routes.txt")
            f, w = _ecrire(os.path.join(temp, "routes.txt"), r.fieldnames)
            with f:
                for row in r:
                    if (row.get("route_short_name") or "").strip() in lignes:
                        w.writerow(row)
                        route_ids.add(row["route_id"].strip())
            if not route_ids:
                raise GtfsInvalide(f"Aucune des lignes {', '.join(sorted(lignes))} dans le GTFS")

            trip_ids = set()
            r = _lire(zf, "trips.txt")
            f, w = _ecrire(os.path.join(temp, "trips.txt"), r.fieldnames)
            with f:
                for row in r:
                    if (row.get("route_id") or "").strip() in route_ids:
                        w.writerow(row)
                        trip_ids.add(row["trip_id"].strip())
            if not trip_ids:
                raise GtfsInvalide("Aucun trajet pour nos lignes dans le GTFS")

            n_stop_times = 0
            r = _lire(zf, "stop_times.txt")
            f, w = _ecrire(os.path.join(temp, "stop_times.txt"), r.fieldnames)
            with f:
                for row in r:
                    if (row.get("stop_id") or "").strip() in arrets and (row.get("trip_id") or "").strip() in trip_ids:
                        w.writerow(row)
                        n_stop_times += 1
            if not n_stop_times:
                raise GtfsInvalide("Aucun passage à nos arrêts dans le GTFS")

        for nom in FICHIERS:
            os.replace(os.path.join(temp, nom), os.path.join(dossier, nom))
        return {"routes": len(route_ids), "trips": len(trip_ids), "stop_times": n_stop_times}
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def telecharger_et_filtrer(dossier, lignes, arrets, url=GTFS_STM_URL):
    """Télécharge le GTFS de la STM dans un fichier temporaire, puis le filtre. Renvoie les comptes."""
    fd, zip_path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    try:
        logger.info(f"[GTFS] Téléchargement de {url}…")
        with requests.get(url, stream=True, timeout=(15, 120)) as r:
            r.raise_for_status()
            with open(zip_path, "wb") as f:
                for morceau in r.iter_content(chunk_size=1024 * 1024):
                    f.write(morceau)
        comptes = filtrer_gtfs(zip_path, dossier, lignes, arrets)
        logger.info(f"[GTFS] Mis à jour : {comptes}")
        return comptes
    finally:
        os.remove(zip_path)
