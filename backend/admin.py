#!/usr/bin/env python
import sys
import os
import subprocess
import threading
import time
import logging
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    jsonify,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
)
from werkzeug.utils import secure_filename
from flask_cors import CORS

# Import Managers
try:
    from managers import update_manager
    from managers import background_manager
except ImportError:
    # Fallback for when running from root as module
    from backend.managers import update_manager
    from backend.managers import background_manager

print(f"[DEBUG] Running admin.py from {Path(__file__).resolve()}")

if getattr(sys, "_MEIPASS", None):
    # PyInstaller onefile puts extracted files here
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.secret_key = "replace-with-your-secure-secret-key"
app.config["APP_RUNNING"] = False
logger = app.logger
logger.setLevel(logging.INFO)
CORS(app)

# === Constants / paths ===
PYTHON_EXEC = sys.executable
PROJECT_ROOT = BASE_DIR.parent               
INSTALL_DIR = PROJECT_ROOT                   

# Frontend paths
UI_DIR = PROJECT_ROOT / "UI"
UI_DIST_DIR = UI_DIR / "dist"
ADMIN_FRONTEND_DIR = PROJECT_ROOT / "admin-frontend"
ADMIN_DIST_DIR = ADMIN_FRONTEND_DIR / "dist"
SPA_DIST = ADMIN_DIST_DIR

# Ensure static images dir exists
background_manager.STATIC_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

main_app_logs = []
app_process = None

def capture_app_logs(process):
    """Continuously read stdout from the main app process."""
    logger.info("Starting log capture thread...")
    try:
        while True:
            line = process.stdout.readline()
            
            # Check if process has ended
            if process.poll() is not None:
                # Process ended, read any remaining output
                remaining = process.stdout.read()
                if remaining:
                    main_app_logs.append(remaining)
                    logger.error(f"Process ended with remaining output: {remaining}")
                break
            
            # Log the line if we have one
            if line:
                main_app_logs.append(line.rstrip())
                logger.info(f"Main app output: {line.rstrip()}")
            else:
                # No line but process still running, just wait a bit
                time.sleep(0.1)
                
    except Exception as e:
        logger.error(f"Error in capture_app_logs: {e}")
    finally:
        app.config["APP_RUNNING"] = False
        exit_code = process.poll()
        logger.info(f"Main app process ended with exit code: {exit_code}")
        main_app_logs.append(f"{datetime.now()} - Process ended with exit code: {exit_code}")


# ----- Routes -----

@app.route("/admin/ping", methods=["GET"])
def ping():
    return jsonify({"pong": True}), 200

@app.route("/admin/backgrounds", methods=["GET"])
def api_get_backgrounds():
    slots = background_manager.parse_slots_from_css_json(background_manager.CSS_FILE_PATH)
    for s in slots:
        p = s.get("path")
        if p:
            fs = background_manager.path_url_to_fs(p)
            if not fs or not fs.exists():
                s["path"] = None
    return jsonify(slots), 200

@app.route("/admin/backgrounds", methods=["POST"])
def api_set_backgrounds():
    payload = request.get_json() or {}
    slots = payload.get("slots", [])
    background_manager.write_slots_to_css_json(background_manager.CSS_FILE_PATH, slots)
    return jsonify({"status": "success"}), 200

@app.route("/admin/backgrounds/images", methods=["GET"])
def api_list_images():
    return jsonify(background_manager.list_images()), 200

@app.route("/admin/update_background", methods=["POST"])
def update_background():
    slot_num = request.form.get("slot_number")
    start_str = request.form.get("startDate")
    end_str = request.form.get("endDate")
    file = request.files.get("bgFile")

    if not slot_num:
        flash("Aucun slot n'a été sélectionné", "warning")
        return redirect(url_for("serve_spa", path=""))

    try:
        idx = int(slot_num) - 1
        if idx not in range(4):
            raise ValueError()
    except:
        flash("Numéro de slot invalide", "danger")
        return redirect(url_for("serve_spa", path=""))

    slots = background_manager.parse_slots_from_css_json(background_manager.CSS_FILE_PATH)
    while len(slots) < 4:
        slots.append({"path": None, "start": None, "end": None})

    if file and file.filename:
        background_manager.STATIC_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        save_path = background_manager.STATIC_IMAGES_DIR / secure_filename(file.filename)
        file.save(save_path)
        new_path = url_for("static", filename=f"assets/images/{file.filename}")
        slots[idx]["path"] = new_path

    try:
        if start_str:
            slots[idx]["start"] = datetime.strptime(start_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    except:
        pass
    try:
        if end_str:
            slots[idx]["end"] = datetime.strptime(end_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    except:
        pass

    background_manager.write_slots_to_css_json(background_manager.CSS_FILE_PATH, slots)
    flash(f"Background du slot {idx+1} mis à jour avec succès !", "success")
    return redirect(url_for("serve_spa", path=""))

@app.route("/admin/backgrounds/import", methods=["POST"])
def api_import_background():
    if "image" not in request.files:
        return jsonify({"error": "no file part"}), 400
    f = request.files["image"]
    if f.filename == "":
        return jsonify({"error": "empty filename"}), 400

    filename = secure_filename(f.filename)
    dest = background_manager.STATIC_IMAGES_DIR / filename

    try:
        f.save(dest)
    except Exception as e:
        return jsonify({"error": f"could not save: {e}"}), 500

    url = f"/static/assets/images/{filename}"

    slots = background_manager.parse_slots_from_css_json(background_manager.CSS_FILE_PATH)
    new_slot = {
        "path": url,
        "start": datetime.now().strftime("%Y-%m-%d"),
        "end": None,
    }
    slots = [s for s in slots if s.get("path") != url]
    slots.insert(0, new_slot)
    if len(slots) > 4:
        slots = slots[:4]
    background_manager.write_slots_to_css_json(background_manager.CSS_FILE_PATH, slots)

    return jsonify({"status": "success", "url": url, "slots": slots}), 200

@app.route("/admin/check_update", methods=["GET"])
def admin_check_update():
    try:
        try:
            remote_sha = update_manager.get_remote_commit_sha()
        except Exception as e:
            return jsonify({"error": f"Could not get remote commit: {e}"}), 500
        local_sha = update_manager.get_local_commit_sha()
        
        if not local_sha:
            return jsonify({
                "error": "Could not determine local version",
                "up_to_date": False,
                "needs_update": True,
                "method": "api"
            }), 200
        
        up_to_date = local_sha == remote_sha
        
        return jsonify({
            "up_to_date": up_to_date,
            "local": local_sha[:8] if local_sha else "unknown",
            "remote": remote_sha[:8],
            "local_full": local_sha,
            "remote_full": remote_sha,
            "method": "api",
            "has_git": update_manager.find_git_executable() is not None
        }), 200
        
    except Exception as e:
        logger.error("Error checking update: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/admin/app_update", methods=["POST"])
def admin_app_update():
    try:
        update_manager.perform_app_update()
        message = f"Application mise à jour ! ({datetime.now():%Y-%m-%d %H:%M:%S})"
        
        # Return success with reload instruction
        return jsonify({
            "status": "success", 
            "message": message,
            "reload_required": True,
            "reload_delay": 3000  # 3 seconds delay
        }), 200
        
    except Exception as e:
        err_msg = f"Erreur lors de la mise à jour : {str(e)}"
        return jsonify({"status": "error", "message": err_msg}), 500

@app.route("/admin/debug/git_status", methods=["GET"])
def debug_git_status():
    """Debug route to check git repository status"""
    try:
        results = {}
        git_dir = PROJECT_ROOT / ".git"
        results["is_git_repo"] = git_dir.is_dir()
        results["project_root"] = str(PROJECT_ROOT)
        results["base_dir"] = str(BASE_DIR)
        results["git_dir_path"] = str(git_dir)
        
        if results["is_git_repo"]:
            git_exe = update_manager.find_git_executable()
            if git_exe:
                # Get current branch
                try:
                    branch_result = update_manager.run_git_command(
                        ["-C", str(PROJECT_ROOT), "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True, text=True
                    )
                    results["current_branch"] = branch_result.stdout.strip() if branch_result.returncode == 0 else f"ERROR: {branch_result.stderr}"
                except Exception as e:
                    results["current_branch"] = f"ERROR: {e}"
                
                # Get current commit
                try:
                    commit_result = update_manager.run_git_command(
                        ["-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
                        capture_output=True, text=True
                    )
                    results["current_commit"] = commit_result.stdout.strip() if commit_result.returncode == 0 else f"ERROR: {commit_result.stderr}"
                except Exception as e:
                    results["current_commit"] = f"ERROR: {e}"
                
                # Get repository status
                try:
                    status_result = update_manager.run_git_command(
                        ["-C", str(PROJECT_ROOT), "status", "--porcelain"],
                        capture_output=True, text=True
                    )
                    results["uncommitted_changes"] = status_result.stdout.strip() if status_result.returncode == 0 else f"ERROR: {status_result.stderr}"
                except Exception as e:
                    results["uncommitted_changes"] = f"ERROR: {e}"
                
                # Get remote URL
                try:
                    remote_result = update_manager.run_git_command(
                        ["-C", str(PROJECT_ROOT), "config", "--get", "remote.origin.url"],
                        capture_output=True, text=True
                    )
                    results["remote_url"] = remote_result.stdout.strip() if remote_result.returncode == 0 else f"ERROR: {remote_result.stderr}"
                except Exception as e:
                    results["remote_url"] = f"ERROR: {e}"
            else:
                results["git_available"] = False
                results["error"] = "Git executable not found"
        
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/debug/system_info", methods=["GET"])
def debug_system_info():
    try:
        info = {}
        
        # Check if git is in PATH
        git_exe = update_manager.find_git_executable()
        info["git_executable"] = git_exe if git_exe else "NOT FOUND"
        
        # Check Python info
        info["python_executable"] = PYTHON_EXEC
        info["python_version"] = sys.version
        
        # Check paths
        info["project_root"] = str(PROJECT_ROOT)
        info["base_dir"] = str(BASE_DIR)
        info["is_git_repo"] = (PROJECT_ROOT / ".git").exists()
        
        # Check PATH environment
        path_env = os.environ.get('PATH', '')
        git_in_path = any('git' in p.lower() for p in path_env.split(os.pathsep))
        info["git_in_path"] = git_in_path
        
        common_git_paths = [
            "C:/Program Files/Git/bin/git.exe",
            "C:/Program Files (x86)/Git/bin/git.exe",
        ]
        existing_git_paths = [p for p in common_git_paths if Path(p).exists()]
        info["existing_git_installations"] = existing_git_paths
        

        try:
            import requests
            info["requests_available"] = True
            info["requests_version"] = requests.__version__
        except ImportError:
            info["requests_available"] = False
        
        return jsonify(info), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/auto_update_settings", methods=["POST"])
def auto_update_settings():
    enabled = bool(request.form.get("enabled"))
    time_str = request.form.get("time", "20:00")
    cfg = {"enabled": enabled, "time": time_str}
    update_manager.save_auto_update_cfg(cfg)
    flash("Paramètres de mise à jour automatique enregistrés", "success")
    return redirect(url_for("serve_spa", path=""))

@app.route("/admin/update_gtfs", methods=["POST"])
def admin_update_gtfs():
    transport = request.form.get("transport", "").lower()
    z = request.files.get("gtfs_zip")

    if not z or z.filename == "":
        flash("Aucun fichier sélectionné.", "danger")
        return redirect(url_for("serve_spa", path=""))

    if not z.filename.lower().endswith(".zip"):
        flash("Merci de télécharger un fichier ZIP GTFS.", "warning")
        return redirect(url_for("serve_spa", path=""))

    GTFS_ROOT = PROJECT_ROOT / "backend" / "GTFS"
    stm_dir = GTFS_ROOT / "stm"

    if transport == "stm":
        target = stm_dir

    timestamp = int(time.time())
    tmp_zip = GTFS_ROOT / f"{transport}_uploaded_{timestamp}.zip"
    staging = GTFS_ROOT / f".tmp_extract_{transport}_{timestamp}"

    try:
        z.save(tmp_zip)

        with zipfile.ZipFile(tmp_zip, "r") as archive:
            archive.extractall(staging)

        entries = list(staging.iterdir())
        if len(entries) == 1 and entries[0].is_dir():
            extracted_root = entries[0]
        else:
            extracted_root = staging

        if target.exists():
            import shutil
            shutil.rmtree(target)
        import shutil
        shutil.move(str(extracted_root), str(target))

        if staging.exists():
            try:
                shutil.rmtree(staging)
            except:
                pass

        # Record update time
        info = update_manager.load_gtfs_update_info()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        info[transport] = now
        update_manager.save_gtfs_update_info(info)

        flash(f"Fichiers GTFS {transport.upper()} mis à jour avec succès ! ({now})", "success")
    except Exception as e:
        logger.exception("GTFS update failed")
        flash(f"Erreur d'extraction ou de mise à jour : {e}", "danger")
    finally:
        if tmp_zip.exists():
            try:
                tmp_zip.unlink()
            except:
                pass
        if staging.exists():
            try:
                import shutil
                shutil.rmtree(staging)
            except:
                pass

    return redirect(url_for("serve_spa", path=""))

@app.route("/admin/gtfs_update_info", methods=["GET"])
def get_gtfs_update_info():
    info = update_manager.load_gtfs_update_info()
    return jsonify(info), 200

@app.route("/admin/start", methods=["POST"])
def admin_start():
    global app_process
    if not app.config["APP_RUNNING"]:
        try:
            # Use the simple startup script instead
            cmd = [
                PYTHON_EXEC,
                "-u",
                str(PROJECT_ROOT / "run_main.py"),
            ]
            
            logger.info(f"Starting main app with command: {' '.join(cmd)}")
            
            app_process = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT), 
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
            app.config["APP_RUNNING"] = True
            main_app_logs.append(f"{datetime.now()} - Main app started.")
            
            threading.Thread(target=capture_app_logs, args=(app_process,), daemon=True).start()
            return jsonify({"status": "started"}), 200
        except Exception as e:
            logger.error("Error starting main app: %s", e)
            return jsonify({"status": "error", "error": str(e)}), 500
    return jsonify({"status": "already_running"}), 200

@app.route("/admin/stop", methods=["POST"])
def admin_stop():
    global app_process
    if app.config["APP_RUNNING"] and app_process:
        try:
            app_process.terminate()
            app_process.wait(timeout=10)
            app.config["APP_RUNNING"] = False
            main_app_logs.append(f"{datetime.now()} - Main app stopped.")
            return jsonify({"status": "stopped"}), 200
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 500
    return jsonify({"status": "not_running"}), 200

@app.route("/admin/status")
def admin_status():
    return jsonify({"running": app.config["APP_RUNNING"]})

@app.route("/admin/logs_data")
def logs_data():
    return "\n".join(main_app_logs)

# Start auto-update worker
threading.Thread(target=update_manager.auto_update_worker, daemon=True).start()

@app.route("/admin/", defaults={"path": ""})
@app.route("/admin/<path:path>")
def serve_spa(path):
    full_path = SPA_DIST / path
    if path and full_path.exists():
        return send_from_directory(str(SPA_DIST), path)
    return send_from_directory(str(SPA_DIST), "index.html")

def auto_start_main_app():
    """Auto-start the main app when admin server starts"""
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true' or os.getenv("FLASK_ENV") == "development":
        return
    def delayed_start():
        time.sleep(10)
        
        if app.config["APP_RUNNING"]:
            logger.info("Main application is already running, skipping auto-start")
            return
        try:
            logger.info("Auto-starting main application...")
            with app.app_context():
                result = admin_start()
                data, status_code = result
                if status_code == 200:
                    response_data = data.get_json()
                    if response_data.get("status") == "started":
                        logger.info("✅ ETS Flux has started successfully!")
                        time.sleep(3)
                    elif response_data.get("status") == "already_running":
                        logger.info("✅ ETS Flux was already running")
                else:
                    logger.error("❌ Failed to auto-start ETS Flux")
        except Exception as e:
            logger.error("❌ Error auto-starting ETS Flux: %s", e)
            main_app_logs.append(f"{datetime.now()} - Auto-start failed: {e}")
    
    threading.Thread(target=delayed_start, daemon=True).start()

auto_start_main_app()  

if __name__ == "__main__":
    if os.getenv("FLASK_DEV_MODE") == "true":
        print("[WARNING] Running in Flask development mode - not recommended for production")
        app.run(debug=True, use_reloader=True, host="127.0.0.1", port=5001)
    else:
        print("[INFO] Starting admin server with Waitress (production mode)")
        from waitress import serve
        serve(app, host="127.0.0.1", port=5001, threads=8)