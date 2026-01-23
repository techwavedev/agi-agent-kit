#!/usr/bin/env python3
import os
import sys

FORBIDDEN_TERMS = [
    "EC (European Commission)",
    "Jira",
    "GitLab",
    "AWS EKS",
    "Consul",
    "private branch",
    "ec branch"
]

def scan_files(directory):
    print(f"🔍 Scanning {directory} for forbidden terms...")
    violation_found = False
    
    for root, dirs, files in os.walk(directory):
        if ".git" in root or "node_modules" in root:
            continue
            
        for file in files:
            if file.endswith(('.js', '.md', '.json', '.txt')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for term in FORBIDDEN_TERMS:
                            if term in content:
                                print(f"❌ VIOLATION in {path}: Found '{term}'")
                                violation_found = True
                except:
                    pass
    
    return violation_found

if __name__ == "__main__":
    print("🛡️  Running Pre-Flight Security Check...")
    
    # Check bin/init.js specifically
    if scan_files("bin") or scan_files("templates"):
        print("\n⛔ SECURITY CHECK FAILED: Private terms found in public code.")
        sys.exit(1)
    
    print("\n✅ Security Check PASSED. Safe to publish.")
    sys.exit(0)
