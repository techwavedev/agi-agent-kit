#!/usr/bin/env python3
"""
Bulk Log Maintenance Work

Automates work logging for KASP-1241 for every working day of the current month.
Excludes weekends and EC holidays (Jan 1, Jan 2).

Usage:
    python bulk_log_maintenance.py --ticket KASP-1241
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from jira_client import get_client


def log_bulk_work():
    client = get_client()
    ticket = "KASP-1241"
    
    # Configuration
    time_spent = "2h" # User mentioned 2 hours for the ticket
    comment_text = "Infra was checked, alerts was checked, and maintenance calendar checked"
    
    # EC Holidays for Jan 2026
    ec_holidays = [
        "2026-01-01", # New Year's Day
        "2026-01-02", # Day after New Year's Day
    ]
    
    # Current date is 2026-01-23
    today = datetime(2026, 1, 23)
    start_date = datetime(2026, 1, 1)
    
    current_date = start_date
    total_logged = 0
    
    print(f"🚀 Starting bulk work log for {ticket}")
    print(f"   Period: {start_date.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}")
    print(f"   Time unit: {time_spent} per working day")
    print("-" * 50)
    
    while current_date <= today:
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Check if weekend (Saturday=5, Sunday=6)
        if current_date.weekday() >= 5:
            print(f"🏠 {date_str}: Weekend (Skipping)")
        # Check if holiday
        elif date_str in ec_holidays:
            print(f"🎉 {date_str}: EC Holiday (Skipping)")
        else:
            # Format start time for Jira (afternoon checkup)
            # Jira expects: 2026-01-23T14:32:00.000+0100
            started = current_date.strftime("%Y-%m-%dT15:00:00.000+0100")
            
            print(f"⏱️  {date_str}: Logging {time_spent}...", end=" ", flush=True)
            
            success, result = client.add_worklog(
                ticket,
                time_spent=time_spent,
                comment=comment_text,
                started=started
            )
            
            if success:
                print("✅ Done")
                total_logged += 1
            else:
                print(f"❌ Failed: {result}")
        
        current_date += timedelta(days=1)
    
    print("-" * 50)
    print(f"🏁 Finished! Logged {total_logged} working day(s).")
    print(f"   Total hours: {total_logged * 2}h")


if __name__ == "__main__":
    log_bulk_work()
