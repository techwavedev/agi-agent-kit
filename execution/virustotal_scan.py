#!/usr/bin/env python3
"""
Script: virustotal_scan.py
Purpose: Uploads a file to VirusTotal for scanning and retrieves the report.

Usage:
    python execution/virustotal_scan.py --file <path_to_file> --api-key <vt_api_key>

Arguments:
    --file      Path to the file to scan (required)
    --api-key   VirusTotal API Key (required)

Exit Codes:
    0 - Clean (0 detection)
    1 - Malicious (1+ detections)
    2 - Error in scanning/uploading
"""

import argparse
import time
import sys
import os
import requests
import hashlib

# VirusTotal API V3 endpoints
VT_URL = "https://www.virustotal.com/api/v3"

def get_file_hash(filepath):
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_file(filepath, api_key):
    """
    Uploads file to VirusTotal or checks if hash exists.
    Returns the analysis results.
    """
    headers = {"x-apikey": api_key}
    file_hash = get_file_hash(filepath)
    file_size = os.path.getsize(filepath)

    print(f"[*] File: {os.path.basename(filepath)}")
    print(f"[*] Size: {file_size} bytes")
    print(f"[*] Hash: {file_hash}")

    # 1. Check if file is already analyzed
    print("[*] Checking for existing report...")
    report_url = f"{VT_URL}/files/{file_hash}"
    response = requests.get(report_url, headers=headers)
    
    analysis_id = None
    
    if response.status_code == 200:
        print("[*] Existing report found.")
        data = response.json().get("data", {}).get("attributes", {})
        return data.get("last_analysis_stats", {}), data.get("last_analysis_results", {})
    elif response.status_code == 404:
        print("[*] No existing report. Uploading file...")
    else:
        print(f"[!] API Error (Check): {response.status_code} - {response.text}")
        sys.exit(2)

    # 2. Get Upload URL (for files > 32MB) or just use /files
    if file_size > 32 * 1024 * 1024:
        upload_url_endpoint = f"{VT_URL}/files/upload_url"
        resp = requests.get(upload_url_endpoint, headers=headers)
        if resp.status_code != 200:
            print(f"[!] Failed to get upload URL: {resp.text}")
            sys.exit(2)
        upload_url = resp.json()['data']
    else:
        upload_url = f"{VT_URL}/files"

    # 3. Upload File
    with open(filepath, "rb") as f:
        files = {"file": (os.path.basename(filepath), f)}
        resp = requests.post(upload_url, headers=headers, files=files)
        
    if resp.status_code != 200:
        print(f"[!] Upload failed: {resp.status_code} - {resp.text}")
        sys.exit(2)
        
    analysis_id = resp.json()["data"]["id"]
    print(f"[*] File uploaded. Analysis ID: {analysis_id}")
    
    # 4. Poll for results
    print("[*] Waiting for analysis to complete...")
    analysis_url = f"{VT_URL}/analyses/{analysis_id}"
    
    while True:
        resp = requests.get(analysis_url, headers=headers)
        if resp.status_code != 200:
            print(f"[!] Failed to get analysis status: {resp.text}")
            sys.exit(2)
            
        status = resp.json()["data"]["attributes"]["status"]
        if status == "completed":
            stats = resp.json()["data"]["attributes"]["stats"]
            results = resp.json()["data"]["attributes"].get("results", {})
            return stats, results
        
        print(f"[*] Status: {status}... waiting 10s")
        time.sleep(10)

def main():
    parser = argparse.ArgumentParser(description="VirusTotal File Scanner")
    parser.add_argument("--file", required=True, help="File to scan")
    parser.add_argument("--api-key", required=True, help="VirusTotal API Key")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"[!] File not found: {args.file}")
        sys.exit(2)

    try:
        stats, _ = scan_file(args.file, args.api_key)
        
        print("\n" + "="*40)
        print("SCAN RESULTS")
        print("="*40)
        print(f"Malicious: {stats.get('malicious', 0)}")
        print(f"Suspicious: {stats.get('suspicious', 0)}")
        print(f"Undetected: {stats.get('undetected', 0)}")
        print(f"Harmless: {stats.get('harmless', 0)}")
        
        if stats.get('malicious', 0) > 0:
            print("\n[!] THREAT DETECTED!")
            sys.exit(1)
        else:
            print("\n[+] Clean.")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n[!] Aborted by user.")
        sys.exit(2)
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
