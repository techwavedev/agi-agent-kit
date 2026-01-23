#!/usr/bin/env python3
"""
Add Comment to Jira Ticket

Adds a comment to an existing Jira issue.

Usage:
    python add_comment.py --ticket <key> --comment <text> [options]

Arguments:
    --ticket        Ticket key (required)
    --comment       Comment text (required)
    --visibility    Restrict to group (optional)
    --mention       Mention users (comma-separated)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Ticket not found
    3 - Comment error
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jira_client import get_client


def main():
    parser = argparse.ArgumentParser(
        description='Add a comment to a Jira ticket',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--ticket', required=True, help='Ticket key')
    parser.add_argument('--comment', required=True, help='Comment text')
    parser.add_argument('--visibility', help='Restrict to group')
    parser.add_argument('--mention', help='Mention users (comma-separated)')
    args = parser.parse_args()
    
    client = get_client()
    ticket = args.ticket.upper()
    
    print(f"💬 Adding comment to {ticket}...", file=sys.stderr)
    
    # Verify ticket exists
    success, issue = client.get_issue(ticket)
    if not success:
        print(f"❌ Error: Could not find ticket {ticket}: {issue}", file=sys.stderr)
        sys.exit(2)
    
    # Build comment text with mentions
    comment_text = args.comment
    if args.mention:
        mentions = [f"[~{u.strip()}]" for u in args.mention.split(',')]
        comment_text = f"{' '.join(mentions)} {comment_text}"
    
    # Build visibility if specified
    visibility = None
    if args.visibility:
        visibility = {
            'type': 'group',
            'value': args.visibility
        }
    
    # Add comment
    success, result = client.add_comment(ticket, comment_text, visibility)
    
    if not success:
        print(f"❌ Error adding comment: {result}", file=sys.stderr)
        sys.exit(3)
    
    comment_id = result.get('id', 'Unknown')
    
    output = {
        'success': True,
        'ticket': ticket,
        'comment_id': comment_id,
        'url': f"{client.base_url}/browse/{ticket}?focusedCommentId={comment_id}"
    }
    print(json.dumps(output, indent=2))
    
    print(f"✅ Comment added to {ticket}", file=sys.stderr)
    sys.exit(0)


if __name__ == '__main__':
    main()
