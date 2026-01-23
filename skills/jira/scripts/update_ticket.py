#!/usr/bin/env python3
"""
Update Jira Ticket

Updates an existing Jira issue with new field values.

Usage:
    python update_ticket.py --ticket <key> [options]

Arguments:
    --ticket        Ticket key (required, e.g., PROJ-123)
    --status        Transition to new status
    --assignee      New assignee
    --priority      New priority
    --summary       Updated summary
    --description   Updated description
    --labels        Replace labels (comma-separated)
    --add-labels    Add labels (comma-separated)
    --remove-labels Remove labels (comma-separated)
    --components    Replace components
    --custom-fields Custom fields as JSON

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
        description='Update a Jira ticket',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--ticket', required=True, help='Ticket key')
    parser.add_argument('--status', help='Transition to status')
    parser.add_argument('--assignee', help='New assignee')
    parser.add_argument('--priority', help='New priority')
    parser.add_argument('--summary', help='New summary')
    parser.add_argument('--description', help='New description')
    parser.add_argument('--labels', help='Replace all labels')
    parser.add_argument('--add-labels', help='Add labels')
    parser.add_argument('--remove-labels', help='Remove labels')
    parser.add_argument('--components', help='Replace components')
    parser.add_argument('--custom-fields', help='Custom fields as JSON')
    args = parser.parse_args()
    
    client = get_client()
    ticket = args.ticket.upper()
    
    print(f"🔧 Updating ticket {ticket}...", file=sys.stderr)
    
    # Verify ticket exists
    success, issue = client.get_issue(ticket)
    if not success:
        print(f"❌ Error: Could not find ticket {ticket}: {issue}", file=sys.stderr)
        sys.exit(2)
    
    # Handle status transition separately
    if args.status:
        transition_id = client.find_transition_by_name(ticket, args.status)
        if transition_id:
            success, result = client.transition_issue(ticket, transition_id)
            if success:
                print(f"   ✓ Transitioned to: {args.status}", file=sys.stderr)
            else:
                print(f"   ⚠️  Transition failed: {result}", file=sys.stderr)
        else:
            print(f"   ⚠️  Status '{args.status}' not available", file=sys.stderr)
            # Show available transitions
            success, transitions = client.get_transitions(ticket)
            if success:
                available = [t['to']['name'] for t in transitions.get('transitions', [])]
                print(f"   Available: {', '.join(available)}", file=sys.stderr)
    
    # Build update fields
    fields = {}
    update = {}
    
    if args.summary:
        fields['summary'] = args.summary
    
    if args.description:
        fields['description'] = client._format_body(args.description)
    
    if args.priority:
        fields['priority'] = {'name': args.priority}
    
    if args.assignee:
        if args.assignee.lower() == 'me':
            success, me = client.get_myself()
            if success:
                fields['assignee'] = {'accountId': me.get('accountId')}
        elif args.assignee.lower() in ['none', 'unassigned', '-']:
            fields['assignee'] = None
        else:
            success, users = client.search_users(args.assignee, max_results=1)
            if success and users:
                fields['assignee'] = {'accountId': users[0].get('accountId')}
            else:
                print(f"   ⚠️  Could not find user: {args.assignee}", file=sys.stderr)
    
    if args.labels:
        fields['labels'] = [l.strip() for l in args.labels.split(',') if l.strip()]
    
    # Label modifications using update syntax
    if args.add_labels:
        labels_to_add = [l.strip() for l in args.add_labels.split(',') if l.strip()]
        update['labels'] = [{'add': label} for label in labels_to_add]
    
    if args.remove_labels:
        labels_to_remove = [l.strip() for l in args.remove_labels.split(',') if l.strip()]
        if 'labels' not in update:
            update['labels'] = []
        update['labels'].extend([{'remove': label} for label in labels_to_remove])
    
    if args.components:
        fields['components'] = [{'name': c.strip()} for c in args.components.split(',')]
    
    if args.custom_fields:
        try:
            custom = json.loads(args.custom_fields)
            fields.update(custom)
        except json.JSONDecodeError as e:
            print(f"   ⚠️  Invalid custom-fields JSON: {e}", file=sys.stderr)
    
    # Apply updates if any fields changed
    if fields or update:
        success, result = client.update_issue(ticket, fields=fields if fields else None,
                                               update=update if update else None)
        if not success:
            print(f"❌ Error updating ticket: {result}", file=sys.stderr)
            sys.exit(3)
        
        print(f"   ✓ Fields updated", file=sys.stderr)
    
    # Output result
    output = {
        'success': True,
        'key': ticket,
        'url': f"{client.base_url}/browse/{ticket}",
        'updated_fields': list(fields.keys()) + (['labels'] if update else [])
    }
    print(json.dumps(output, indent=2))
    
    print(f"✅ Ticket {ticket} updated successfully", file=sys.stderr)
    sys.exit(0)


if __name__ == '__main__':
    main()
