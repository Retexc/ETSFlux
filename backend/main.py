"""
ETSignage : API de l'écran du salon (prochains passages STM, alertes, métro, météo).
Les annonces de l'écran se gèrent dans AMÉUX Flux ; ce serveur ne calcule que les données de transport.

GET /api/data   : tout (bus, métro, alertes, météo), gardé 20 secondes en mémoire
GET /api/meteo  : météo seulement (léger)
"""
import os, logging, threading, time
from flask_cors import CORS
from flask import Flask, jsonify

# ────── PACKAGE IMPORTS ───────────────────────────────────────
from .config            import BUS_ROUTES, BUS_STOP_IDS

from .loaders.stm       import (
    fetch_stm_alerts,
    fetch_stm_realtime_data,
    fetch_stm_positions_dict,
    process_stm_trip_updates,
)

from .alerts import process_stm_alerts

from .loaders.gtfs_loader import download_gtfs_data, load_gtfs_data
from .loaders.gtfs_update import telecharger_et_filtrer
from .loaders import exo
from .managers.weather_manager import get_weather

# ────────────────────────────────────────────────────────────────

logger = logging.getLogger('BdeB-GTFS')
app = Flask(__name__)
# Données publiques en lecture seule : tout site peut les lire, mais seulement en GET
CORS(app, methods=["GET"])
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
GTFS_BASE = os.path.join(PACKAGE_DIR, "GTFS")  # points to backend/GTFS
STM_DIR = os.path.join(GTFS_BASE, "stm")

os.makedirs(STM_DIR, exist_ok=True)

# ─── Horaires STM (GTFS) ──────────────────────────────────────
# 1. Au démarrage : fichiers déjà filtrés gardés dans Supabase (bucket gtfs-files), rapides à lire.
# 2. Absents : téléchargés directement de la STM et filtrés (loaders/gtfs_update.py).
# 3. À chaque démarrage (après 1 minute), puis chaque semaine : mis à jour depuis la STM, sans intervention
#    (GTFS_AUTO=non pour couper). Échec : anciens horaires gardés, nouvel essai 24 h plus tard.
download_gtfs_data(STM_DIR)
routes_map, stm_trips, stm_stop_times = load_gtfs_data(STM_DIR)

MAJ_GTFS_JOURS = 7
_verrou_gtfs = threading.Lock()


def mettre_a_jour_gtfs():
    """Télécharge le GTFS de la STM, filtre, puis recharge les horaires en mémoire. Faux si ça échoue."""
    global routes_map, stm_trips, stm_stop_times
    try:
        telecharger_et_filtrer(STM_DIR, BUS_ROUTES, BUS_STOP_IDS)
        nouveaux = load_gtfs_data(STM_DIR)
        with _verrou_gtfs:
            routes_map, stm_trips, stm_stop_times = nouveaux
        return True
    except Exception as e:
        # Anciens horaires gardés : mieux vaut des horaires un peu vieux que pas d'horaires
        logger.error(f"[GTFS] Mise à jour impossible, anciens horaires gardés : {e}")
        return False


DELAI_DEMARRAGE_S = 60      # laisse le serveur répondre d'abord (réveil de Render)
REESSAI_ECHEC_H = 24        # STM injoignable : on réessaie le lendemain, pas dans une semaine


def mettre_a_jour_exo():
    try:
        exo.telecharger()
        return True
    except Exception as e:
        logger.error(f"[exo] Horaires indisponibles, anciens gardés : {e}")
        return False


def boucle_exo():
    """Horaires exo (petit fichier) : tout de suite au démarrage, puis chaque semaine ; échec → réessai dans 1 h."""
    while True:
        ok = mettre_a_jour_exo()
        time.sleep(MAJ_GTFS_JOURS * 24 * 3600 if ok else 3600)


def boucle_gtfs():
    """
    Vérifie les horaires de la STM à CHAQUE démarrage, puis chaque semaine. Un serveur gratuit de Render
    redémarre souvent (mise en veille) : un simple compteur d'une semaine repartirait à zéro et la mise
    à jour n'arriverait jamais. En arrière-plan : les réponses de l'écran ne sont jamais retardées.
    """
    if stm_trips:
        time.sleep(DELAI_DEMARRAGE_S)
    while True:
        ok = mettre_a_jour_gtfs()
        time.sleep((MAJ_GTFS_JOURS * 24 if ok else REESSAI_ECHEC_H) * 3600)


if os.getenv("GTFS_AUTO", "oui").lower() not in ("non", "0", "false") and os.getenv("ENVIRONMENT") != "development":
    threading.Thread(target=boucle_gtfs, name="gtfs", daemon=True).start()
    threading.Thread(target=boucle_exo, name="exo", daemon=True).start()

# ====================================================================
# Metro Alerts Processing Functions
# ====================================================================
def process_metro_alerts():
    try:
        # Fetch all STM alerts
        alerts_data = fetch_stm_alerts()
        
        # Default status for all lines
        metro_status = {
            "1": {
                "name": "Ligne 1",
                "color": "Verte",
                "status": "Service normal",
                "statusColor": "text-green-400",
                "icon": "green-line",
                "is_normal": True,
                "alert_description": None
            },
            "2": {
                "name": "Ligne 2",
                "color": "Orange",
                "status": "Service normal",
                "statusColor": "text-green-400",
                "icon": "orange-line",
                "is_normal": True,
                "alert_description": None
            },
            "4": {
                "name": "Ligne 4",
                "color": "Jaune",
                "status": "Service normal",
                "statusColor": "text-green-400",
                "icon": "yellow-line",
                "is_normal": True,
                "alert_description": None
            },
            "5": {
                "name": "Ligne 5",
                "color": "Bleue",
                "status": "Service normal",
                "statusColor": "text-green-400",
                "icon": "blue-line",
                "is_normal": True,
                "alert_description": None
            }
        }
        
        # Process alerts to check for metro disruptions
        if alerts_data:
            import re
            for alert in alerts_data:
                try:
                    informed_entities = alert.get("informed_entities", [])
                    
                    # Get French header and description for this alert
                    header_texts = alert.get("header_texts", [])
                    description_texts = alert.get("description_texts", [])
                    
                    # Debug: Log what we're getting from the API
                    logger.debug(f"Alert header_texts: {header_texts}")
                    logger.debug(f"Alert description_texts: {description_texts}")
                    
                    header = ""
                    description = ""
                    for ht in header_texts:
                        if ht.get("language") == "fr":
                            header = ht.get("text", "")
                            break
                    
                    for dt in description_texts:
                        if dt.get("language") == "fr":
                            description = dt.get("text", "")
                            break
                    
                    # Remove HTML tags from description
                    if description:
                        description = re.sub(r'<[^>]+>', '', description).strip()
                    
                    # Debug: Log what we extracted
                    logger.debug(f"Extracted header: '{header}'")
                    logger.debug(f"Extracted description (cleaned): '{description}'")
                    
                    # Check if this is a network-wide alert (affects all metro)
                    is_network_wide = False
                    affected_metro_lines = []
                    
                    for entity in informed_entities:
                        # Check for agency-wide alert (like strikes)
                        if entity.get("agency_id") == "STM":
                            is_network_wide = True
                            logger.info(f"[ALERT] Detected network-wide STM alert: {header[:50]}...")
                        
                        # Check for specific metro line alerts using route_short_name
                        route_short_name = entity.get("route_short_name", "")
                        route_id = entity.get("route_id", "")
                        
                        # Metro routes can be in either field
                        metro_line = route_short_name if route_short_name in ["1", "2", "4", "5"] else (route_id if route_id in ["1", "2", "4", "5"] else None)
                        
                        if metro_line:
                            affected_metro_lines.append(metro_line)
                            logger.info(f"[ALERT] Detected alert for metro line {metro_line}: {header[:50]}...")
                    
                    # Use description first (it has the real message), fallback to header
                    alert_text = description or header
                    
                    # ← FIX: Skip messages that are NOT actual service disruptions
                    skip_keywords = [
                        "service normal",
                        "accès",  # Access closures (entrances closed)
                        "l'accès",
                        "access",
                        "entrance"
                    ]
                    
                    should_skip = any(keyword in alert_text.lower() for keyword in skip_keywords)
                    if should_skip:
                        logger.info(f"[INFO] Skipping non-service-disruption message: {alert_text[:50]}...")
                        continue
                    
                    # Apply the alert to affected lines
                    if is_network_wide:
                        # Network-wide alert affects all metro lines
                        logger.warning(f"[WARNING] APPLYING NETWORK-WIDE ALERT TO ALL METRO LINES")
                        logger.info(f"   Alert text: '{alert_text}'")
                        for line_id in metro_status.keys():
                            metro_status[line_id]["is_normal"] = False
                            metro_status[line_id]["status"] = "Service perturbé"
                            metro_status[line_id]["alert_description"] = alert_text
                            metro_status[line_id]["statusColor"] = "text-red-400"
                    elif affected_metro_lines:
                        # Apply alert to specific metro lines
                        logger.warning(f"[WARNING] APPLYING ALERT TO LINES: {', '.join(affected_metro_lines)}")
                        logger.info(f"   Alert text: '{alert_text}'")
                        for line_id in affected_metro_lines:
                            metro_status[line_id]["is_normal"] = False
                            metro_status[line_id]["status"] = "Service perturbé"
                            metro_status[line_id]["alert_description"] = alert_text
                            metro_status[line_id]["statusColor"] = "text-red-400"
                        
                except Exception as e:
                    logger.error(f"Error processing individual metro alert: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        # Convert to list format for frontend
        result = list(metro_status.values())
        logger.info(f"[STATUS] Final Metro Status:")
        for line in result:
            status_text = "NORMAL" if line["is_normal"] else "DISRUPTED"
            logger.info(f"  [{status_text}] {line['name']} ({line['color']}): {line['status']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in process_metro_alerts: {e}")
        import traceback
        traceback.print_exc()
        return get_default_metro_status()

def get_default_metro_status():
    """Return default metro status when API fails"""
    return [
        {
            "name": "Ligne 1",
            "color": "Verte",
            "status": "Service normal",
            "statusColor": "text-green-400",
            "icon": "green-line",
            "is_normal": True,
            "alert_description": None
        },
        {
            "name": "Ligne 2",
            "color": "Orange",
            "status": "Service normal",
            "statusColor": "text-green-400",
            "icon": "orange-line",
            "is_normal": True,
            "alert_description": None
        },
        {
            "name": "Ligne 4",
            "color": "Jaune",
            "status": "Service normal",
            "statusColor": "text-green-400",
            "icon": "yellow-line",
            "is_normal": True,
            "alert_description": None
        },
        {
            "name": "Ligne 5",
            "color": "Bleue",
            "status": "Service normal",
            "statusColor": "text-green-400",
            "icon": "blue-line",
            "is_normal": True,
            "alert_description": None
        }
    ]

def merge_alerts_into_buses(buses, processed_alerts):
    """
    Merge alert information into bus objects.
    """
    for bus in buses:
        route_id = bus.get("route_id")
        
        # Find matching alert
        for alert in processed_alerts:
            if route_id in alert.get("routes", []):
                if alert.get("effect") == "NO_SERVICE":
                    bus["cancelled"] = True
                    bus["delayed_text"] = None
                break
    
    return buses

# ====================== API Routes ======================
@app.route('/')
def index():
    return jsonify({
        "status": "ok",
        "message": "ETS Flux API is running",
        "endpoints": {
            "data": "/api/data",
            "meteo": "/api/meteo"
        }
    })

# Réponse gardée en mémoire : plusieurs écrans (et plus tard le Roku) ne relancent pas tout le calcul
CACHE_SECONDES = 20
_cache = {"ts": 0.0, "corps": None}
_verrou = threading.Lock()


@app.route('/api/data', methods=['GET'])
def get_data():
    with _verrou:
        if _cache["corps"] is not None and time.time() - _cache["ts"] < CACHE_SECONDES:
            return jsonify(_cache["corps"]), 200
        corps, code = calculer_donnees()
        if code == 200:
            _cache.update(ts=time.time(), corps=corps)
        return jsonify(corps), code


@app.route('/api/meteo', methods=['GET'])
def get_meteo():
    return jsonify(get_weather()), 200


def calculer_donnees():
    """Bus, métro, alertes et météo, calculés à partir du GTFS et des API de la STM."""
    try:
        # Process metro alerts first
        metro_lines = process_metro_alerts()
        
        # ========== STM ALERTS ==========
        filtered_alerts = []
        try:
            processed_stm = process_stm_alerts()
            logger.debug(f"Processed STM alerts: {processed_stm}")
            
            # Format alerts for frontend
            for alert in processed_stm:
                alert_obj = {
                    "header": alert.get("header", "Alerte"),
                    "description": alert.get("description", ""),
                    "alert_type": alert.get("alert_type", "info"),
                    "severity": alert.get("severity", "info")
                }
                
                # Add route information if it exists
                if alert.get("is_network_wide"):
                    alert_obj["routes"] = "Réseau STM"
                    alert_obj["stop"] = "Général"
                elif alert.get("routes"):
                    routes_str = ", ".join(alert["routes"])
                    alert_obj["routes"] = routes_str
                    alert_obj["stop"] = "Ligne spécifique"
                else:
                    alert_obj["routes"] = "N/A"
                    alert_obj["stop"] = "N/A"
                
                filtered_alerts.append(alert_obj)
            
            # ===== ADD METRO ALERTS TO THE BANNER =====
            logger.info("[METRO] Checking metro lines for alerts to add to banner...")
            for metro_line in metro_lines:
                if not metro_line.get("is_normal") and metro_line.get("alert_description"):
                    metro_alert = {
                        "header": f"Métro {metro_line['name']} - {metro_line['color']}",
                        "description": metro_line["alert_description"],
                        "routes": f"Métro {metro_line['color']}",
                        "stop": "Métro",
                        "alert_type": "metro",
                        "severity": "warning"
                    }
                    filtered_alerts.append(metro_alert)
                    logger.info(f"  [OK] Added metro alert to banner: {metro_alert['header']}")
                
        except Exception as e:
            logger.error(f"ERROR processing STM alerts: {e}")
            import traceback
            traceback.print_exc()

        # ========== STM BUSES WITH OCCUPANCY ==========
        buses = []
        try:
            # Horaires lus d'un coup (la mise à jour hebdomadaire peut les remplacer à tout moment)
            with _verrou_gtfs:
                g_routes, g_trips, g_stop_times = routes_map, stm_trips, stm_stop_times

            stm_trip_entities = fetch_stm_realtime_data()
            # routes_map : convertit les identifiants GTFS en numéros de ligne
            positions_dict = fetch_stm_positions_dict(BUS_ROUTES, g_trips, g_routes)
            
            # Debug: Log how many vehicle positions we got
            logger.debug(f"[OCCUPANCY] Fetched {len(positions_dict)} vehicle positions")
            if len(positions_dict) > 0:
                # Show first few for debugging
                for i, ((route, trip), pos_data) in enumerate(list(positions_dict.items())[:3]):
                    logger.debug(f"  Position {i+1}: Route={route}, Trip={trip}, Occ={pos_data.get('occupancy')}")
            else:
                logger.warning("[OCCUPANCY] No vehicle positions found - occupancy will show as 'Unknown'")
            
            buses = process_stm_trip_updates(
                stm_trip_entities,
                g_trips,
                g_stop_times,
                positions_dict
            )

            # Enhanced debug logging for occupancy
            logger.debug("----- DEBUG: Final Merged STM Buses with Occupancy -----")
            status_map = {0: "INCOMING_AT", 1: "STOPPED_AT", 2: "IN_TRANSIT_TO"}
            
            for b in buses:
                raw_stat = b.get("current_status")
                if isinstance(raw_stat, int):
                    stat_str = status_map.get(raw_stat, f"Unknown({raw_stat})")
                else:
                    stat_str = str(raw_stat)
                
                # Log occupancy information
                occupancy = b.get("occupancy", "Unknown")
                logger.debug(
                    f"Route={b['route_id']}, Trip={b['trip_id']}, "
                    f"Stop={b['stop_id']}, ArrTime={b['arrival_time']}, "
                    f"Occupancy={occupancy}, AtStop={b['at_stop']}, "
                    f"Lat={b.get('lat')}, Lon={b.get('lon')}, Dist={b.get('distance_m')}m, "
                    f"currentStatus={stat_str}"
                )
            logger.debug("-----------------------------------------")

            buses = merge_alerts_into_buses(buses, processed_stm if 'processed_stm' in locals() else [])
        except Exception as e:
            logger.error(f"ERROR processing buses: {e}")
            import traceback
            traceback.print_exc()

        # ========== WEATHER ==========
        weather = get_weather()

        # ========== EXO (trains au départ de Lucien-L'Allier) ==========
        try:
            trains_exo = exo.departs_exo()
        except Exception as e:
            logger.error(f"[exo] {e}")
            trains_exo = []

        # Build response
        response = {
            "buses": buses,
            "metro_lines": metro_lines,
            "exo": trains_exo,
            "weather": weather,
            "alerts": filtered_alerts,
            "debug": {
                "total_buses": len(buses),
                "total_metro_lines": len(metro_lines),
                "alerts_count": len(filtered_alerts)
            }
        }

        return response, 200

    except Exception as e:
        logger.error(f"Error in get_data: {e}")
        import traceback
        traceback.print_exc()
        return {"error": "Erreur du serveur"}, 500

if __name__ == '__main__':
    from waitress import serve
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting ETS Flux on http://0.0.0.0:{port}")
    serve(app, host='0.0.0.0', port=port)