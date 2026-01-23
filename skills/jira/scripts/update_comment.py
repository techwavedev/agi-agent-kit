#!/usr/bin/env python3
"""
Update Comment on Jira Ticket

Updates an existing comment on a Jira issue.

Usage:
    python update_comment.py --ticket <key> --comment-id <id> --text <text>

Arguments:
    --ticket        Ticket key (required)
    --comment-id    Comment ID to update (required)
    --text          New comment text (required)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Ticket not found
    3 - Update error
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jira_client import get_client


def main():
    parser = argparse.ArgumentParser(
        description='Update a comment on a Jira ticket',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--ticket', required=True, help='Ticket key')
    parser.add_argument('--comment-id', required=True, help='Comment ID')
    parser.add_argument('--text', required=True, help='New comment text')
    args = parser.parse_args()
    
    client = get_client()
    ticket = args.ticket.upper()
    
    print(f"✏️  Updating comment {args.comment_id} on {ticket}...", file=sys.stderr)
    
    # Update comment
    success, result = client.update_comment(ticket, args.comment_id, args.text)
    
    if not success:
        print(f"❌ Error updating comment: {result}", file=sys.stderr)
        sys.exit(3)
    
    output = {
        'success': True,
        'ticket': ticket,
        'comment_id': args.comment_id,
        'updated': True
    }
    print(json.dumps(output, indent=2))
    
    print(f"✅ Comment updated on {ticket}", file=sys.stderr)
    sys.exit(0)


if __name__ == '__main__':
    main()
