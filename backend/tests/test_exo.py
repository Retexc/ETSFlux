"""Trains exo au départ de Lucien-L'Allier : prochains départs, demain, temps réel (faux GTFS, aucun réseau)."""
import csv
import io
import zipfile
from datetime import datetime

from backend.loaders.exo import TZ, Horaires, prochains_departs


def faux_zip():
    def t(lignes):
        b = io.StringIO()
        csv.writer(b).writerows(lignes)
        return b.getvalue()
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("routes.txt", t([["route_id", "route_short_name", "route_color", "route_text_color"],
                                    ["5", "CA", "5AB6B2", "000000"], ["1", "VH", "F16179", "000000"], ["6", "MA", "CA5898", "000000"]]))
        z.writestr("trips.txt", t([["route_id", "service_id", "trip_id", "trip_headsign", "wheelchair_accessible", "bikes_allowed"],
                                   ["5", "SEM", "ca1", "Candiac", "1", "1"], ["5", "SEM", "ca2", "Candiac", "1", "1"],
                                   ["1", "SEM", "vh1", "Vaudreuil", "0", "1"], ["1", "SEM", "vh-arrivee", "Lucien-L'Allier", "0", "0"],
                                   ["6", "SEM", "ma1", "Mascouche", "1", "1"]]))
        z.writestr("stop_times.txt", t([["trip_id", "departure_time", "stop_id", "stop_sequence"],
                                        ["ca1", "08:30:00", "MTL3C", "1"], ["ca2", "17:10:00", "MTL3A", "1"],
                                        ["vh1", "24:15:00", "MTL3A", "1"],
                                        ["vh-arrivee", "09:00:00", "MTL3A", "12"],   # arrivée à la gare : ignorée
                                        ["ma1", "08:00:00", "MTL3A", "1"]]))         # ligne non affichée
        z.writestr("calendar.txt", t([["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "start_date", "end_date"],
                                      ["SEM", "1", "1", "1", "1", "1", "0", "0", "20261101", "20261231"]]))
        z.writestr("calendar_dates.txt", t([["service_id", "date", "exception_type"], ["SEM", "20261125", "2"]]))
    return out.getvalue()


def h():
    x = Horaires()
    x.charger_zip(faux_zip())
    return x


def at(s):
    return datetime.fromisoformat(s).replace(tzinfo=TZ)


def test_prochain_depart_par_ligne_dans_l_ordre():
    d = prochains_departs(h(), at("2026-11-23T08:00"))   # lundi
    assert [x["ligne"] for x in d] == ["CA", "VH"]       # Mascouche jamais affichée
    ca = d[0]
    assert (ca["direction"], ca["heure"], ca["minutes"], ca["arret"]) == ("Candiac", "8 h 30", 30, "Gare Lucien-L'Allier")
    assert ca["couleur"] == "#5AB6B2" and ca["accessible"] and not ca["temps_reel"] and ca["jour"] == ""


def test_trajet_apres_minuit_et_lendemain():
    d = {x["ligne"]: x for x in prochains_departs(h(), at("2026-11-23T23:50"))}
    assert d["VH"]["heure"] == "0 h 15" and d["VH"]["jour"] == "demain"   # « 24:15 » du lundi
    assert d["CA"]["heure"] == "8 h 30" and d["CA"]["jour"] == "demain"


def test_fin_de_semaine_jusqu_a_lundi():
    d = {x["ligne"]: x for x in prochains_departs(h(), at("2026-11-21T12:00"))}   # samedi
    assert d["CA"]["jour"] == "lundi" and d["CA"]["heure"] == "8 h 30"


def test_jour_sans_service():
    # Mercredi 25 retiré (calendar_dates) : prochain Candiac le jeudi
    d = {x["ligne"]: x for x in prochains_departs(h(), at("2026-11-25T07:00"))}
    assert d["CA"]["depart"].startswith("2026-11-26T08:30")


def test_temps_reel_retard_et_annulation():
    d = prochains_departs(h(), at("2026-11-23T08:00"), {"ca1": {"retard": 300, "annule": False}})
    assert d[0]["heure"] == "8 h 35" and d[0]["temps_reel"]
    d = prochains_departs(h(), at("2026-11-23T08:00"), {"ca1": {"retard": 0, "annule": True}})
    assert d[0]["annule"]
