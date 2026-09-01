import time
import json
import requests
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.core.config import settings

BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

def fetch_cves(pub_start: str, pub_end: str, severity: str = "CRITICAL") -> list:
    all_cves = []
    start_index = 0
    results_per_page = 2000
    
    headers = {}
    if settings.nvd_api_key:
        headers["apiKey"] = settings.nvd_api_key
        sleep_delay = 0.6
        print("[INFO] Using NVD API key.")
    else:
        sleep_delay = 6.5
        print("[WARNING] No NVD_API_KEY found. Defaulting to 5 requests per 30s rate limit.")

    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    while True:
        params = {
            "cvssV3Severity": severity,
            "pubStartDate": pub_start,
            "pubEndDate": pub_end,
            "resultsPerPage": results_per_page,
            "startIndex": start_index,
        }
        
        print(f"Fetching startIndex: {start_index}...")
        try:
            response = requests.get(BASE_URL, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"[ERROR] HTTP connection failed: {e}")
            sys.exit(1)
            
        data = response.json()
        vulns = data.get("vulnerabilities", [])
        all_cves.extend(vulns)
        
        total = data.get("totalResults", 0)
        start_index += results_per_page
        
        print(f"Accumulated {len(all_cves)} / {total} records.")
        
        if start_index >= total:
            break
            
        time.sleep(sleep_delay)

    return all_cves

if __name__ == "__main__":
    cves = fetch_cves("2025-08-27T00:00:00.000", "2025-12-25T00:00:00.000")
    
    output_file = settings.raw_data_dir / "cves_raw.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cves, f, indent=2)
        
    print(f"Successfully saved {len(cves)} CVEs to {output_file.resolve()}")
