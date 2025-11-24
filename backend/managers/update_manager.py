import sys
import os
import subprocess
import shutil
import time
import json
import zipfile
import tempfile
import logging
import requests
from datetime import datetime
from pathlib import Path

logger = logging.getLogger('BdeB-GTFS')

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent  # /backend/
PROJECT_ROOT = BASE_DIR.parent
INSTALL_DIR = PROJECT_ROOT
PYTHON_EXEC = sys.executable

GITHUB_API_REPO = "Retexc/BdeB-Go"
UPDATE_INFO_FILE = PROJECT_ROOT / "gtfs_update_info.json"
AUTO_UPDATE_CFG = INSTALL_DIR / "auto_update_config.json"

# === Git utilities ===

def find_git_executable():
    """Find git executable on the system"""
    git_paths = [
        "git",  # If git is in PATH
        "C:/Program Files/Git/bin/git.exe",
        "C:/Program Files (x86)/Git/bin/git.exe", 
        "C:/Users/{}/AppData/Local/Programs/Git/bin/git.exe".format(os.getenv('USERNAME', '')),
        "C:/Git/bin/git.exe",
    ]
    
    for git_path in git_paths:
        if shutil.which(git_path) or (Path(git_path).exists() if git_path.endswith('.exe') else False):
            return git_path
    
    return None

def run_git_command(args, **kwargs):
    """Run a git command with proper error handling"""
    git_exe = find_git_executable()
    if not git_exe:
        raise Exception("Git not found. Please install Git and add it to your PATH.")
    
    cmd = [git_exe] + args
    return subprocess.run(cmd, **kwargs)

# === Update system functions ===

def get_remote_commit_sha():
    """Get the latest commit SHA from GitHub API"""
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_API_REPO}/commits/main"
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        return response.json()["sha"]
    except Exception as e:
        logger.error(f"Failed to get remote commit: {e}")
        raise

def get_local_commit_sha():
    git_exe = find_git_executable()
    if git_exe:
        try:
            result = run_git_command(
                ["-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
    
    try:
        git_head = PROJECT_ROOT / ".git" / "HEAD"
        if git_head.exists():
            head_content = git_head.read_text().strip()
            if head_content.startswith("ref: "):
                # Read the ref file
                ref_path = PROJECT_ROOT / ".git" / head_content[5:]
                if ref_path.exists():
                    return ref_path.read_text().strip()
            else:
                # Direct SHA
                return head_content
    except:
        pass
    
    return None

def safe_extract(zipf: zipfile.ZipFile, dest: Path):
    dest = dest.resolve()
    for member in zipf.namelist():
        member_path = dest / member
        resolved = member_path.resolve()
        if not str(resolved).startswith(str(dest)):
            raise RuntimeError("Unsafe path in zip file")
    zipf.extractall(dest)

def copy_directory_contents(src, dst):
    preserve_files = {
        "gtfs_update_info.json",
        "auto_update_config.json", 
        "backend/static/assets/images",  # User uploaded images
    }
    
    for src_file in src.rglob("*"):
        if src_file.is_file():
            rel_path = src_file.relative_to(src)
            dst_file = dst / rel_path
            should_preserve = any(str(rel_path).startswith(preserve) for preserve in preserve_files)  
            if should_preserve and dst_file.exists():
                logger.info(f"Preserving existing file: {rel_path}")
                continue
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)

def download_and_extract_update():
    try:
        zip_url = f"https://github.com/{GITHUB_API_REPO}/archive/refs/heads/main.zip"
        logger.info(f"Downloading update from {zip_url}")
        
        response = requests.get(zip_url, timeout=300)  # 5 minute timeout
        response.raise_for_status()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "update.zip"      
            zip_path.write_bytes(response.content)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                safe_extract(zip_file, temp_path)
            
            extracted_dirs = [d for d in temp_path.iterdir() if d.is_dir() and d.name != "__pycache__"]
            if not extracted_dirs:
                raise Exception("No directories found in downloaded ZIP")        
            source_dir = extracted_dirs[0]
            backup_dir = PROJECT_ROOT.parent / f"ETS-Flux-backup-{int(time.time())}"
            logger.info(f"Creating backup at {backup_dir}")
            try:
                shutil.copytree(PROJECT_ROOT, backup_dir, ignore=shutil.ignore_patterns("*.pyc", "__pycache__"))
            except Exception as e:
                logger.warning(f"Could not create backup: {e}")
            logger.info("Copying new files...")
            copy_directory_contents(source_dir, PROJECT_ROOT)
            
            logger.info("Update completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"Download and extract failed: {e}")
        raise

def perform_app_update_git():
    try:
        git_exe = find_git_executable()
        if not git_exe:
            raise Exception("Git not found. Please install Git and add it to your PATH.")
        git_dir = PROJECT_ROOT / ".git"
        if not git_dir.is_dir():
            logger.error(f"No git repository found at {PROJECT_ROOT}")
            raise Exception(f"Not a git repository: {PROJECT_ROOT}")        
        logger.info(f"Git repository found at {PROJECT_ROOT}, using git: {git_exe}")
        status_result = run_git_command(
            ["-C", str(PROJECT_ROOT), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if status_result.returncode != 0:
            raise Exception(f"Git status failed: {status_result.stderr}")
        
        if status_result.stdout.strip():
            logger.warning("Uncommitted changes detected, stashing them...")
            stash_result = run_git_command(
                ["-C", str(PROJECT_ROOT), "stash", "push", "-m", f"Auto-stash before update {datetime.now()}"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if stash_result.returncode != 0:
                logger.warning(f"Stash failed: {stash_result.stderr}")
        reset_result = run_git_command(
            ["-C", str(PROJECT_ROOT), "reset", "--hard", "HEAD"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if reset_result.returncode != 0:
            logger.warning(f"Reset failed: {reset_result.stderr}")
        logger.info("Fetching latest changes...")
        fetch_result = run_git_command(
            ["-C", str(PROJECT_ROOT), "fetch", "origin"],
            capture_output=True,
            text=True,
            timeout=300
        )
        if fetch_result.returncode != 0:
            raise Exception(f"Git fetch failed: {fetch_result.stderr}")

        logger.info("Pulling changes...")
        pull_result = run_git_command(
            ["-C", str(PROJECT_ROOT), "pull", "origin", "main"],
            capture_output=True,
            text=True,
            timeout=300
        )
        if pull_result.returncode != 0:
            logger.info("Main branch failed, trying master...")
            pull_result = run_git_command(
                ["-C", str(PROJECT_ROOT), "pull", "origin", "master"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if pull_result.returncode != 0:
                raise Exception(f"Git pull failed: {pull_result.stderr}")
        
        logger.info(f"Git pull successful: {pull_result.stdout}")
        return True
        
    except Exception as e:
        logger.error(f"Git update failed: {e}")
        raise

def perform_app_update_http():
    try:
        logger.info("Starting app update (Git-free method)")
        download_and_extract_update()
        return True
        
    except Exception as e:
        logger.error(f"HTTP update failed: {e}")
        raise

def perform_app_update():
    git_exe = find_git_executable()
    git_dir = PROJECT_ROOT / ".git"
    
    update_successful = False
    
    if git_exe and git_dir.exists():
        logger.info("Git available, using Git-based update")
        try:
            perform_app_update_git()
            update_successful = True
        except Exception as e:
            logger.warning(f"Git update failed: {e}, falling back to HTTP download")
    
    if not update_successful:
        logger.info("Using HTTP-based update (no Git required)")
        perform_app_update_http()
    
    try:
        # Update pip
        logger.info("Updating pip...")
        pip_result = subprocess.run(
            [PYTHON_EXEC, "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True, text=True, timeout=300
        )
        if pip_result.returncode != 0:
            logger.warning(f"Pip upgrade failed: {pip_result.stderr}")

        # Install requirements 
        req = PROJECT_ROOT / "requirements.txt"
        if req.exists():
            logger.info("Installing requirements...")
            req_result = subprocess.run(
                [PYTHON_EXEC, "-m", "pip", "install", "-r", str(req)],
                capture_output=True, text=True, timeout=600
            )
            if req_result.returncode != 0:
                logger.warning(f"Requirements installation had issues: {req_result.stderr}")
        
        # Run install.bat 
        install_bat = PROJECT_ROOT / "install.bat"
        if install_bat.exists():
            logger.info("Running install.bat in silent mode to rebuild frontend...")
            try:
                install_result = subprocess.run(
                    [str(install_bat), "silent"], 
                    cwd=str(PROJECT_ROOT),
                    capture_output=True, text=True,
                    timeout=900, shell=True
                )
                
                if install_result.returncode == 0:
                    logger.info("install.bat completed successfully")
                else:
                    logger.warning(f"install.bat returned code {install_result.returncode}")
                    logger.warning(f"install.bat stderr: {install_result.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.error("install.bat timed out after 15 minutes")
                raise Exception("Frontend rebuild timed out")
            except Exception as e:
                logger.error(f"Error running install.bat: {e}")
                raise Exception(f"Frontend rebuild failed: {e}")
        else:
            logger.warning("install.bat not found, skipping frontend rebuild")
        
    except Exception as e:
        logger.error(f"Post-update steps failed: {e}")
        raise

def load_auto_update_cfg():
    default = {"enabled": True, "time": "20:00"}
    if AUTO_UPDATE_CFG.exists():
        try:
            with open(AUTO_UPDATE_CFG, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                default.update(cfg)
        except:
            pass
    return default

def save_auto_update_cfg(cfg):
    with open(AUTO_UPDATE_CFG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def load_gtfs_update_info():
    if UPDATE_INFO_FILE.exists():
        try:
            with open(UPDATE_INFO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"stm": None, "exo": None}

def save_gtfs_update_info(info):
    try:
        with open(UPDATE_INFO_FILE, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2)
    except Exception as e:
        logger.error("Error saving GTFS info: %s", e)

def auto_update_worker():
    while True:
        cfg = load_auto_update_cfg()
        if cfg.get("enabled"):
            now = datetime.now()
            cutoff = datetime.strptime(cfg["time"], "%H:%M").time()
            if now.time() >= cutoff:
                try:
                    local_sha = get_local_commit_sha()
                    remote_sha = get_remote_commit_sha()
                    
                    if local_sha and remote_sha and local_sha != remote_sha:
                        logger.info("Auto-update: new commit detected, updating...")
                        perform_app_update()
                    elif not local_sha:
                        logger.warning("Auto-update: Could not determine local version")
                except Exception as e:
                    logger.error("Auto-update error: %s", e)
        time.sleep(3600)
