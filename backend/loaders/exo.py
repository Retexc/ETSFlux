"""
Trains exo au départ de la gare Lucien-L'Allier (la plus proche de l'ÉTS) : lignes Vaudreuil–Hudson (VH),
Saint-Jérôme (SJ) et Candiac (CA).

- Horaires prévus : fichier GTFS public d'exo (petit : ~250 Ko), téléchargé au démarrage puis chaque semaine.
- Temps réel (retards, annulations) : seulement si la variable CHRONO_TOKEN existe (clé de l'API Chrono
  d'exo, demandée sur exo.quebec). Sans clé, les heures prévues sont affichées, sans l'icône « en direct ».

Tout le calcul (`prochains_departs`) est sans réseau : testé avec un faux GTFS (backend/tests/test_exo.py).
"""
import csv
import io
import logging
import os
import threading
import zipfile
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests

logger = logging.getLogger('BdeB-GTFS')

TZ = ZoneInfo("America/Toronto")
EXO_GTFS_URL = os.getenv(
    "EXO_GTFS_URL",
    "https://exo.quebec/uploads/ressources-telechargeables/a-propos/donnees-ouvertes/trains/google_transit.zip",
)
CHRONO_TRIPUPDATE_URL = "https://exo.chrono-saeiv.com/api/opendata/v1/TRAINS/tripupdate"

# Gare Lucien-L'Allier (deux quais dans le GTFS) et lignes qui en partent, dans l'ordre d'affichage
ARRETS = {"MTL3A", "MTL3C"}
NOM_ARRET = "Gare Lucien-L'Allier"
LIGNES = ["CA", "SJ", "VH"]
JOURS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class Horaires:
    """Horaires exo en mémoire (remplacés d'un coup à chaque mise à jour)."""

    def __init__(self):
        self.verrou = threading.Lock()
        self.routes = {}       # route_id -> {nom, couleur, texte}
        self.departs = []      # [(service_id, secondes depuis minuit, trip)]
        self.calendrier = {}   # service_id -> {jours, debut, fin}
        self.exceptions = {}   # (service_id, AAAAMMJJ) -> 1 ajouté / 2 retiré

    def charger_zip(self, contenu: bytes):
        with zipfile.ZipFile(io.BytesIO(contenu)) as z:
            lire = lambda n: list(csv.DictReader(io.TextIOWrapper(z.open(n), encoding="utf-8-sig")))
            routes = {
                r["route_id"]: {
                    "nom": r["route_short_name"].strip(),
                    "couleur": "#" + (r.get("route_color") or "999999").strip(),
                    "texte": "#" + (r.get("route_text_color") or "000000").strip(),
                }
                for r in lire("routes.txt") if r["route_short_name"].strip() in LIGNES
            }
            trips = {t["trip_id"]: t for t in lire("trips.txt") if t["route_id"] in routes}
            departs = []
            for st in lire("stop_times.txt"):
                t = trips.get(st["trip_id"])
                # Départ de la gare : 1er arrêt du trajet (les trajets qui y arrivent sont ignorés)
                if t and st["stop_id"] in ARRETS and st["stop_sequence"].strip() == "1":
                    departs.append((t["service_id"], secondes(st["departure_time"]), {
                        "trip_id": t["trip_id"], "route_id": t["route_id"], "direction": t.get("trip_headsign", ""),
                        "accessible": t.get("wheelchair_accessible") == "1", "velo": t.get("bikes_allowed") == "1",
                    }))
            calendrier = {
                c["service_id"]: {"jours": {j for j in JOURS if c[j] == "1"}, "debut": c["start_date"], "fin": c["end_date"]}
                for c in (lire("calendar.txt") if "calendar.txt" in z.namelist() else [])
            }
            exceptions = {
                (e["service_id"], e["date"]): int(e["exception_type"])
                for e in (lire("calendar_dates.txt") if "calendar_dates.txt" in z.namelist() else [])
            }
        if not departs:
            raise ValueError("Aucun départ de Lucien-L'Allier dans le GTFS d'exo")
        with self.verrou:
            self.routes, self.departs, self.calendrier, self.exceptions = routes, departs, calendrier, exceptions
        return len(departs)

    def actif(self, service_id: str, jour: date) -> bool:
        cle = jour.strftime("%Y%m%d")
        exc = self.exceptions.get((service_id, cle))
        if exc is not None:
            return exc == 1
        c = self.calendrier.get(service_id)
        return bool(c) and c["debut"] <= cle <= c["fin"] and JOURS[jour.weekday()] in c["jours"]


NOMS_JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def nom_jour(jour: date, aujourdhui: date) -> str:
    """« » aujourd'hui, « demain », sinon le nom du jour (« lundi »)."""
    ecart = (jour - aujourdhui).days
    return "" if ecart <= 0 else "demain" if ecart == 1 else NOMS_JOURS[jour.weekday()]


def secondes(hhmmss: str) -> int:
    """« 25:10:00 » → secondes depuis minuit (le GTFS dépasse 24 h pour les trajets après minuit)."""
    h, m, s = (int(x) for x in hhmmss.strip().split(":"))
    return h * 3600 + m * 60 + s


def prochains_departs(h: Horaires, maintenant: datetime, temps_reel: dict | None = None) -> list[dict]:
    """
    Prochain départ de chaque ligne (CA, SJ, VH) à partir de `maintenant` (avec fuseau), en cherchant
    jusqu'à 3 jours plus loin (fin de semaine : pas de train sur certaines lignes). `temps_reel` : {trip_id: {"retard": secondes, "annule": bool}} (API Chrono), ou None.
    """
    temps_reel = temps_reel or {}
    with h.verrou:
        routes, departs = h.routes, h.departs
    maintenant = maintenant.astimezone(TZ)
    meilleurs = {}
    # La veille aussi : un trajet « 24:30 » de la veille part à 0 h 30 aujourd'hui
    for decalage in range(-1, 4):
        jour = maintenant.date() + timedelta(days=decalage)
        minuit = datetime(jour.year, jour.month, jour.day, tzinfo=TZ)
        for service, sec, trip in departs:
            if not h.actif(service, jour):
                continue
            rt = temps_reel.get(trip["trip_id"], {})
            prevu = minuit + timedelta(seconds=sec)
            reel = prevu + timedelta(seconds=rt.get("retard", 0))
            if reel < maintenant - timedelta(seconds=30):
                continue
            actuel = meilleurs.get(trip["route_id"])
            if actuel is None or reel < actuel["_quand"]:
                meilleurs[trip["route_id"]] = {"_quand": reel, "trip": trip, "rt": rt, "prevu": prevu}
    resultat = []
    for route_id, m in meilleurs.items():
        r = routes[route_id]
        minutes = max(0, int((m["_quand"] - maintenant).total_seconds() // 60))
        resultat.append({
            "ligne": r["nom"], "couleur": r["couleur"], "texte": r["texte"],
            "direction": m["trip"]["direction"], "arret": NOM_ARRET,
            "depart": m["_quand"].isoformat(), "minutes": minutes,
            "heure": f"{m['_quand'].hour} h {m['_quand'].minute:02d}",
            "jour": nom_jour(m["_quand"].date(), maintenant.date()),
            "temps_reel": bool(m["rt"]), "annule": bool(m["rt"].get("annule")),
            "accessible": m["trip"]["accessible"], "velo": m["trip"]["velo"],
        })
    return sorted(resultat, key=lambda d: LIGNES.index(d["ligne"]) if d["ligne"] in LIGNES else 99)


HORAIRES = Horaires()


def telecharger(url: str = EXO_GTFS_URL) -> int:
    r = requests.get(url, timeout=(15, 60))
    r.raise_for_status()
    n = HORAIRES.charger_zip(r.content)
    logger.info(f"[exo] {n} départs de Lucien-L'Allier chargés")
    return n


def lire_temps_reel() -> dict:
    """Retards et annulations de l'API Chrono d'exo. {} sans clé ou en cas d'erreur (heures prévues gardées)."""
    jeton = os.getenv("CHRONO_TOKEN")
    if not jeton:
        return {}
    try:
        from google.transit import gtfs_realtime_pb2
        r = requests.get(CHRONO_TRIPUPDATE_URL, params={"token": jeton}, timeout=10)
        r.raise_for_status()
        flux = gtfs_realtime_pb2.FeedMessage()
        flux.ParseFromString(r.content)
        res = {}
        for e in flux.entity:
            if not e.HasField("trip_update"):
                continue
            tu = e.trip_update
            annule = tu.trip.schedule_relationship == gtfs_realtime_pb2.TripDescriptor.CANCELED
            retard = 0
            for stu in tu.stop_time_update:
                if stu.stop_id in ARRETS and stu.HasField("departure") and stu.departure.HasField("delay"):
                    retard = stu.departure.delay
                    break
            res[tu.trip.trip_id] = {"retard": retard, "annule": annule}
        return res
    except Exception as e:
        logger.warning(f"[exo] Temps réel indisponible : {e}")
        return {}


def departs_exo() -> list[dict]:
    if not HORAIRES.departs:
        return []
    return prochains_departs(HORAIRES, datetime.now(TZ), lire_temps_reel())
