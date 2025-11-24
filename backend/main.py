# app.py
import os, sys, logging
from flask_cors import CORS
from flask import Flask, jsonify

# ────── PACKAGE IMPORTS ───────────────────────────────────────
from .config            import BUS_ROUTES
from .utils             import is_service_unavailable

from .loaders.stm       import (
    fetch_stm_alerts,
    fetch_stm_realtime_data,
    fetch_stm_positions_dict,
    process_stm_trip_updates,
)

from .alerts import process_stm_alerts

# New Imports
from .loaders.gtfs_loader import download_gtfs_data, load_gtfs_data
from .managers.weather_manager import get_weather

# ────────────────────────────────────────────────────────────────

print("__name__:", __name__)
print("__package__:", __package__)
print("sys.path:", sys.path)

logger = logging.getLogger('BdeB-GTFS')
app = Flask(__name__)
CORS(app)
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
GTFS_BASE = os.path.join(PACKAGE_DIR, "GTFS")  # points to backend/GTFS
STM_DIR = os.path.join(GTFS_BASE, "stm")

os.makedirs(STM_DIR, exist_ok=True)

# ─── Download GTFS files from Supabase on startup (production only) ────────
download_gtfs_data(STM_DIR)

# ─── check for required GTFS files ────────────────────────────
routes_map, stm_trips, stm_stop_times = load_gtfs_data(STM_DIR)

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
            "data": "/api/data"
        }
    })

@app.route('/api/data', methods=['GET'])
def get_data():
    """
    Main API endpoint that returns all transit data
    """
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

            
            stm_trip_entities = fetch_stm_realtime_data()
            # FIX: Pass routes_map so vehicle positions can convert GTFS IDs to short names
            positions_dict = fetch_stm_positions_dict(BUS_ROUTES, stm_trips, routes_map)
            
            # Debug: Log how many vehicle positions we got
            logger.info(f"[OCCUPANCY] Fetched {len(positions_dict)} vehicle positions")
            if len(positions_dict) > 0:
                # Show first few for debugging
                for i, ((route, trip), pos_data) in enumerate(list(positions_dict.items())[:3]):
                    logger.info(f"  Position {i+1}: Route={route}, Trip={trip}, Occ={pos_data.get('occupancy')}")
            else:
                logger.warning("[OCCUPANCY] No vehicle positions found - occupancy will show as 'Unknown'")
            
            buses = process_stm_trip_updates(
                stm_trip_entities,
                stm_trips,
                stm_stop_times,
                positions_dict
            )

            # Enhanced debug logging for occupancy
            logger.info("----- DEBUG: Final Merged STM Buses with Occupancy -----")
            status_map = {0: "INCOMING_AT", 1: "STOPPED_AT", 2: "IN_TRANSIT_TO"}
            
            for b in buses:
                raw_stat = b.get("current_status")
                if isinstance(raw_stat, int):
                    stat_str = status_map.get(raw_stat, f"Unknown({raw_stat})")
                else:
                    stat_str = str(raw_stat)
                
                # Log occupancy information
                occupancy = b.get("occupancy", "Unknown")
                logger.info(
                    f"Route={b['route_id']}, Trip={b['trip_id']}, "
                    f"Stop={b['stop_id']}, ArrTime={b['arrival_time']}, "
                    f"Occupancy={occupancy}, AtStop={b['at_stop']}, "
                    f"Lat={b.get('lat')}, Lon={b.get('lon')}, Dist={b.get('distance_m')}m, "
                    f"currentStatus={stat_str}"
                )
            logger.info("-----------------------------------------")

            buses = merge_alerts_into_buses(buses, processed_stm if 'processed_stm' in locals() else [])
        except Exception as e:
            logger.error(f"ERROR processing buses: {e}")
            import traceback
            traceback.print_exc()

        # ========== WEATHER ==========
        weather = get_weather()

        # Build response
        response = {
            "buses": buses,
            "metro_lines": metro_lines,
            "weather": weather,
            "alerts": filtered_alerts,
            "debug": {
                "total_buses": len(buses),
                "total_metro_lines": len(metro_lines),
                "alerts_count": len(filtered_alerts)
            }
        }

        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in get_data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    from waitress import serve
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting ETS Flux on http://0.0.0.0:{port}")
    serve(app, host='0.0.0.0', port=port)