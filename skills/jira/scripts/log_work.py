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
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jira_client import get_client


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
    
    print(f"⏱️  Logging {args.time} to {ticket}...", file=sys.stderr)
    
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
    
    # Add worklog
    success, result = client.add_worklog(
        ticket,
        time_spent=args.time,
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
