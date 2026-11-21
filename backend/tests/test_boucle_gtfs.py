"""Horaires STM : vérifiés à chaque démarrage (Render redémarre souvent), puis chaque semaine."""
import os

import pytest

os.environ.setdefault("STM_API_KEY", "test")
os.environ.setdefault("WEATHER_API_KEY", "test")
os.environ["ENVIRONMENT"] = "development"   # ni téléchargement Supabase ni boucle au chargement

import backend.main as M  # noqa: E402


class Fin(Exception):
    pass


def lancer(monkeypatch, resultats, horaires_deja_la=True):
    pauses, appels = [], []
    suite = iter(resultats)
    monkeypatch.setattr(M, "stm_trips", {"t": 1} if horaires_deja_la else {})
    monkeypatch.setattr(M, "mettre_a_jour_gtfs", lambda: appels.append(1) or next(suite))

    def pause(s):
        pauses.append(s)
        if len(appels) >= len(resultats):
            raise Fin

    monkeypatch.setattr(M.time, "sleep", pause)
    with pytest.raises(Fin):
        M.boucle_gtfs()
    return pauses, appels


def test_verifie_au_demarrage_puis_chaque_semaine(monkeypatch):
    pauses, appels = lancer(monkeypatch, [True, True])
    assert pauses[0] == M.DELAI_DEMARRAGE_S          # d'abord laisser le serveur répondre
    assert pauses[1] == 7 * 24 * 3600                # puis une semaine
    assert len(appels) == 2


def test_sans_horaires_tout_de_suite(monkeypatch):
    pauses, appels = lancer(monkeypatch, [True], horaires_deja_la=False)
    assert appels == [1]
    assert pauses == [7 * 24 * 3600]


def test_echec_reessaie_le_lendemain(monkeypatch):
    pauses, _ = lancer(monkeypatch, [False, True])
    assert pauses[1] == 24 * 3600
