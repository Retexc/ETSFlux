"""Filtrage automatique du GTFS de la STM (loaders/gtfs_update.py). Lancé par `python -m pytest -q`."""
import csv
import io
import os
import zipfile

import pytest

from backend.loaders.gtfs_update import GtfsInvalide, filtrer_gtfs


def faux_gtfs(chemin, routes, trips, stop_times):
    def texte(lignes):
        b = io.StringIO()
        csv.writer(b).writerows(lignes)
        return "﻿" + b.getvalue()   # BOM, comme certains exports
    with zipfile.ZipFile(chemin, "w") as z:
        z.writestr("routes.txt", texte(routes))
        z.writestr("trips.txt", texte(trips))
        z.writestr("stop_times.txt", texte(stop_times))
        z.writestr("stops.txt", "stop_id\n1\n")


def lire(dossier, nom):
    with open(os.path.join(dossier, nom), encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.fixture
def gtfs(tmp_path):
    chemin = tmp_path / "stm.zip"
    faux_gtfs(
        chemin,
        [["route_id", "route_short_name", "route_long_name"], ["61", "61", "Wellington"], ["36", "36", "Monk"], ["24", "24", "Sherbrooke"]],
        [["route_id", "service_id", "trip_id"], ["61", "S", "t61"], ["36", "S", "t36"], ["24", "S", "t24"]],
        [["trip_id", "arrival_time", "stop_id"], ["t61", "08:00:00", "52743"], ["t61", "08:05:00", "99999"], ["t36", "09:00:00", "62248"], ["t24", "10:00:00", "52743"]],
    )
    return chemin


def test_garde_seulement_nos_lignes_et_nos_arrets(gtfs, tmp_path):
    dossier = tmp_path / "stm"
    comptes = filtrer_gtfs(gtfs, dossier, ["61", "36"], ["52743", "62248"])
    assert comptes == {"routes": 2, "trips": 2, "stop_times": 2}
    assert [r["route_short_name"] for r in lire(dossier, "routes.txt")] == ["61", "36"]
    assert {r["trip_id"] for r in lire(dossier, "trips.txt")} == {"t61", "t36"}
    assert [(r["trip_id"], r["stop_id"]) for r in lire(dossier, "stop_times.txt")] == [("t61", "52743"), ("t36", "62248")]
    # Aucun fichier temporaire laissé derrière
    assert sorted(os.listdir(dossier)) == ["routes.txt", "stop_times.txt", "trips.txt"]


def test_gtfs_sans_nos_lignes_garde_les_anciens_fichiers(gtfs, tmp_path):
    dossier = tmp_path / "stm"
    filtrer_gtfs(gtfs, dossier, ["61", "36"], ["52743", "62248"])
    avant = lire(dossier, "stop_times.txt")
    with pytest.raises(GtfsInvalide):
        filtrer_gtfs(gtfs, dossier, ["747"], ["52743"])
    assert lire(dossier, "stop_times.txt") == avant


def test_fichier_manquant(tmp_path):
    chemin = tmp_path / "incomplet.zip"
    with zipfile.ZipFile(chemin, "w") as z:
        z.writestr("routes.txt", "route_id,route_short_name\n61,61\n")
    with pytest.raises(GtfsInvalide, match="trips.txt"):
        filtrer_gtfs(chemin, tmp_path / "stm", ["61"], ["1"])
