#!/usr/bin/env python3
"""
Log Work Time to Jira Ticket

Logs work time against an existing Jira issue.

Usage:
    python log_work.py --ticket <key> --time <duration> [options]

Arguments:
    --ticket        Ticket key (required)
    --time          Time spent: "2h", "30m", "1d", "2h 30m" (required)
    --comment       Work description (optional)
    --started       Start time in ISO format (optional)
    --remaining     New remaining estimate (optional)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Ticket not found
    3 - Worklog error
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jira_client import get_client


def round_to_15min_blocks(time_str: str) -> str:
    """
    Round time to 15-minute blocks (EC Jira requirement).
    
    Args:
        time_str: Time string like "2h", "25m", "1h 20m"
    
    Returns:
        Rounded time string using 15m/30m/45m/1h increments
    """
    # Parse time to total minutes
    total_minutes = 0
    patterns = {
        'w': 5 * 8 * 60,  # 1 week = 5 days = 40 hours
        'd': 8 * 60,      # 1 day = 8 hours
        'h': 60,
        'm': 1
    }
    
    for match in re.finditer(r'(\d+)\s*([wdhm])', time_str.lower()):
        value, unit = int(match.group(1)), match.group(2)
        total_minutes += value * patterns.get(unit, 0)
    
    if total_minutes == 0:
        return time_str  # Return original if parsing failed
    
    # Round to nearest 15 minutes (minimum 15 min)
    rounded_minutes = max(15, round(total_minutes / 15) * 15)
    
    # Convert back to Jira format
    hours = rounded_minutes // 60
    mins = rounded_minutes % 60
    
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{mins}m"


def main():
    parser = argparse.ArgumentParser(
        description='Log work time to a Jira ticket',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--ticket', required=True, help='Ticket key')
    parser.add_argument('--time', required=True, help='Time spent (e.g., "2h", "1d")')
    parser.add_argument('--comment', help='Work description')
    parser.add_argument('--started', help='Start time (ISO format)')
    parser.add_argument('--remaining', help='New remaining estimate')
    args = parser.parse_args()
    
    client = get_client()
    ticket = args.ticket.upper()
    
    # Round to 15-minute blocks (EC requirement)
    original_time = args.time
    rounded_time = round_to_15min_blocks(original_time)
    
    if original_time != rounded_time:
        print(f"⏱️  Rounding {original_time} → {rounded_time} (15-min blocks)", file=sys.stderr)
    
    print(f"⏱️  Logging {rounded_time} to {ticket}...", file=sys.stderr)
    
    # Verify ticket exists
    success, issue = client.get_issue(ticket)
    if not success:
        print(f"❌ Error: Could not find ticket {ticket}: {issue}", file=sys.stderr)
        sys.exit(2)
    
    # Parse started time or use now
    started = args.started
    if not started:
        # Jira expects format: 2026-01-23T14:00:00.000+0100
        started = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000%z')
        if not started.endswith('+') and len(started) < 30:
            # Add timezone if missing
            started = datetime.now().astimezone().strftime('%Y-%m-%dT%H:%M:%S.000%z')
    
    # Determine estimate adjustment
    adjust_estimate = None
    new_estimate = None
    if args.remaining:
        adjust_estimate = 'new'
        new_estimate = args.remaining
    
    # Add worklog with rounded time
    success, result = client.add_worklog(
        ticket,
        time_spent=rounded_time,
        comment=args.comment,
        started=started,
        adjust_estimate=adjust_estimate,
        new_estimate=new_estimate
    )
    
    if not success:
        print(f"❌ Error logging work: {result}", file=sys.stderr)
        sys.exit(3)
    
    worklog_id = result.get('id', 'Unknown')
    time_logged = result.get('timeSpent', args.time)
    
    output = {
        'success': True,
        'ticket': ticket,
        'worklog_id': worklog_id,
        'time_logged': time_logged,
        'started': started
    }
    print(json.dumps(output, indent=2))
    
    print(f"✅ Logged {time_logged} to {ticket}", file=sys.stderr)
    sys.exit(0)


if __name__ == '__main__':
    main()
