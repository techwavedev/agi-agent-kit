#!/usr/bin/env python3
import os
import sys
import fnmatch

FORBIDDEN_TERMS = [
    "EC (European Commission)",
    "Jira",
    "GitLab",
    "AWS EKS",
    "Consul",
    "private branch",
    "ec branch"
]

def load_npmignore():
    """Load patterns from .npmignore"""
    ignore_patterns = []
    if os.path.exists(".npmignore"):
        with open(".npmignore", 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Normalize directory patterns
                    if line.endswith('/'):
                        line = line.rstrip('/')
                    ignore_patterns.append(line)
    return ignore_patterns

def is_ignored(path, ignore_patterns):
    """Check if path matches any ignore pattern"""
    # Check against each pattern
    for pattern in ignore_patterns:
        # Match against relative path from cwd
        rel_path = os.path.relpath(path, os.getcwd())
        
        # Check if the path starts with the pattern (directory exclusion)
        if rel_path.startswith(pattern) or fnmatch.fnmatch(rel_path, pattern):
            return True
            
        # Also check just the filename for simple patterns
        if fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
            
    return False

def scan_files(directory, ignore_patterns):
    print(f"🔍 Scanning {directory} for forbidden terms (respecting .npmignore)...")
    violation_found = False
    
    for root, dirs, files in os.walk(directory):
        # Filter directories based on ignore patterns
        dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d), ignore_patterns)]
        
        if ".git" in root or "node_modules" in root:
            continue
            
        for file in files:
            path = os.path.join(root, file)
            
            # Skip ignored files
            if is_ignored(path, ignore_patterns):
                continue
                
            if file.endswith(('.js', '.md', '.json', '.txt')):
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
    ignore_patterns = load_npmignore()
    print(f"ℹ️  Loaded {len(ignore_patterns)} ignore patterns")
    
    # Check bin/init.js and templates specifically
    violation = False
    if scan_files("bin", ignore_patterns): violation = True
    if scan_files("templates", ignore_patterns): violation = True

    if violation:
        print("\n⛔ SECURITY CHECK FAILED: Private terms found in public code.")
        sys.exit(1)
    
    print("\n✅ Security Check PASSED. Safe to publish.")
    sys.exit(0)
