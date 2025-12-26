import os
import logging
from .stm import (
    load_stm_routes,
    load_stm_gtfs_trips,
    load_stm_stop_times
)

try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

logger = logging.getLogger('BdeB-GTFS')

def download_gtfs_data(stm_dir):
    """Download GTFS files from Supabase if configured."""
    if os.environ.get('ENVIRONMENT') == 'development':
        return

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    if not (SUPABASE_URL and SUPABASE_KEY):
        print("⚠️  Supabase credentials not set, skipping cloud download")
        return

    if not SUPABASE_AVAILABLE:
        print("⚠️  Supabase module not installed")
        return

    try:
        print("📥 Downloading GTFS files from Supabase...")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # List files in the stm folder
        result = supabase.storage.from_("gtfs-files").list("stm")
        
        if result:
            files_to_download = ["routes.txt", "trips.txt", "stop_times.txt"]
            
            for filename in files_to_download:
                # Find the most recent version of this file
                matching_files = [f for f in result if f["name"].endswith(filename)]
                
                if matching_files:
                    # Sort by created_at to get most recent
                    matching_files.sort(key=lambda x: x["created_at"], reverse=True)
                    latest_file = matching_files[0]
                    
                    # Download the file
                    file_path_in_bucket = f"stm/{latest_file['name']}"
                    local_file_path = os.path.join(stm_dir, filename)
                    
                    print(f"   Downloading {filename}...")
                    data = supabase.storage.from_("gtfs-files").download(file_path_in_bucket)
                    
                    with open(local_file_path, "wb") as f:
                        f.write(data)
                    
                    file_size = len(data) / 1024
                    print(f"   ✅ {filename} downloaded ({file_size:.1f} KB)")
            
            print("✅ GTFS files downloaded from Supabase!")
        else:
            print("⚠️  No GTFS files found in Supabase")
            
    except Exception as e:
        print(f"⚠️  Error downloading GTFS from Supabase: {e}")
        print("   Continuing with local files if available...")

def load_gtfs_data(stm_dir):
    """Load GTFS data from local files."""
    required_stm = ["routes.txt", "trips.txt", "stop_times.txt"]
    missing = []
    
    for fname in required_stm:
        fpath = os.path.join(stm_dir, fname)
        if not os.path.isfile(fpath):
            missing.append(f"stm/{fname}")
        else:
            fsize = os.path.getsize(fpath) / 1024
            print(f"✓ Found {fname} ({fsize:.1f} KB)")

    if missing:
        print("⚠️  Fichiers GTFS manquants:")
        for m in missing:
            print(f"   • {m}")
        print("\nL'application démarre quand même. Téléchargez les fichiers GTFS via l'interface admin.")
        return {}, {}, {}
    else:
        print("📂 Loading GTFS files...")
        stm_routes_fp = os.path.join(stm_dir, "routes.txt")
        stm_trips_fp = os.path.join(stm_dir, "trips.txt")
        stm_stop_times_fp = os.path.join(stm_dir, "stop_times.txt")
        
        routes_map = load_stm_routes(stm_routes_fp)
        stm_trips = load_stm_gtfs_trips(stm_trips_fp, routes_map)
        stm_stop_times = load_stm_stop_times(stm_stop_times_fp)
        
        print(f"✅ Loaded {len(stm_trips)} trips")
        print(f"✅ Loaded {len(routes_map)} routes")
        
        return routes_map, stm_trips, stm_stop_times
