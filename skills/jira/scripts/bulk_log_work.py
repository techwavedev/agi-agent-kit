#!/usr/bin/env python3
"""
Bulk Log Work Utility

A reusable script to log work across a date range for a specific ticket.
Automatically handles weekends and European Commission holidays.

Usage:
    python bulk_log_work.py --ticket <key> --start <YYYY-MM-DD> --end <YYYY-MM-DD> --time <duration> --comment <text>

Arguments:
    --ticket    Ticket key (required)
    --start     Start date YYYY-MM-DD (required)
    --end       End date YYYY-MM-DD (default: today)
    --time      Time per working day (e.g., "3h", "1h 30m")
    --comment   Comment for worklogs. If multiple, separate with '|' to rotate.
    --dry-run   Show what would be logged without making API calls

Example:
    python bulk_log_work.py --ticket KASP-1241 --start 2026-01-01 --time 2h --comment "Infra check|Alert check"
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent))
from jira_client import get_client


def get_ec_holidays(year: int) -> List[str]:
    """Return a list of EC holidays for a given year (approximate)."""
    # Standard EC holidays
    holidays = [
        f"{year}-01-01", f"{year}-01-02",  # New Year
        f"{year}-05-01",                   # Labor Day
        f"{year}-05-09",                   # Europe Day
        f"{year}-07-21",                   # National Day
        f"{year}-08-15",                   # Assumption
        f"{year}-11-01",                   # All Saints
        f"{year}-11-02",                   # All Souls
        f"{year}-12-24", f"{year}-12-25", f"{year}-12-26",
        f"{year}-12-27", f"{year}-12-28", f"{year}-12-29",
        f"{year}-12-30", f"{year}-12-31"   # Winter break
    ]
    
    # Easter-related (approximate for demonstration, usually fixed per year)
    if year == 2026:
        holidays.extend(["2026-04-02", "2026-04-03", "2026-04-06", "2026-05-14", "2026-05-25"])
        
    return holidays


def main():
    parser = argparse.ArgumentParser(description="Bulk log work to Jira tickets")
    parser.add_argument("--ticket", required=True, help="Ticket key")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date (YYYY-MM-DD, defaults to today)")
    parser.add_argument("--time", required=True, help="Time per working day (e.g., 2h)")
    parser.add_argument("--comment", required=True, help="Comment(s) - use | to rotate multiple")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually log work")
    args = parser.parse_args()

    client = get_client()
    ticket = args.ticket.upper()
    
    # Parse dates
    start_date = datetime.strptime(args.start, "%Y-%m-%d")
    end_date = datetime.strptime(args.end, "%Y-%m-%d") if args.end else datetime.now()
    
    # Parse comments
    comments = [c.strip() for c in args.comment.split('|')]
    
    print(f"🚀 {'[DRY RUN] ' if args.dry_run else ''}Bulk logging for {ticket}")
    print(f"   Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"   Work: {args.time} per day")
    print("-" * 50)
    
    current_date = start_date
    working_days_count = 0
    
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        holidays = get_ec_holidays(current_date.year)
        
        # Skip weekends and holidays
        if current_date.weekday() >= 5:
            # print(f"🏠 {date_str}: Weekend (Skipping)")
            pass
        elif date_str in holidays:
            print(f"🎉 {date_str}: Holiday (Skipping)")
        else:
            comment = comments[working_days_count % len(comments)]
            # 14:00 (2 PM) as a default work check time
            started = current_date.strftime("%Y-%m-%dT14:00:00.000+0100")
            
            print(f"⏱️  {date_str}: Logging {args.time} - {comment}...", end=" ", flush=True)
            
            if not args.dry_run:
                success, result = client.add_worklog(
                    ticket,
                    time_spent=args.time,
                    comment=comment,
                    started=started
                )
                if success:
                    print("✅ Done")
                else:
                    print(f"❌ Failed: {result}")
            else:
                print("📝 (Skipped)")
                
            working_days_count += 1
            
        current_date += timedelta(days=1)
        
    print("-" * 50)
    print(f"🏁 Finished! Processed {working_days_count} working day(s).")


if __name__ == "__main__":
    main()
