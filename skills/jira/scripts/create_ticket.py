#!/usr/bin/env python3
"""
Create Jira Ticket

Creates a new issue in Jira with specified fields.

Usage:
    python create_ticket.py --project <key> --summary <text> [options]

Arguments:
    --project       Project key (required)
    --summary       Issue summary (required)
    --type          Issue type: Bug, Task, Story, Epic (default: Task)
    --priority      Priority: Highest, High, Medium, Low, Lowest
    --description   Description text
    --assignee      Assignee username or email
    --labels        Comma-separated labels
    --components    Comma-separated component names
    --epic          Epic link key
    --custom-fields Custom fields as JSON string
    --output        Output format: json, key, url (default: json)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - API error
"""

import argparse
import json
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from jira_client import get_client


def parse_labels(labels_str: str) -> list:
    """Parse comma-separated labels."""
    if not labels_str:
        return []
    return [l.strip() for l in labels_str.split(',') if l.strip()]


def build_fields(args, client) -> dict:
    """Build the fields dictionary for issue creation."""
    fields = {
        'project': {'key': args.project},
        'summary': args.summary,
        'issuetype': {'name': args.type}
    }
    
    if args.priority:
        fields['priority'] = {'name': args.priority}
    
    if args.description:
        fields['description'] = client._format_adf(args.description)
    
    if args.assignee:
        # Try to resolve assignee
        if args.assignee.lower() == 'me':
            success, me = client.get_myself()
            if success:
                fields['assignee'] = {'accountId': me.get('accountId')}
        else:
            # Search for user
            success, users = client.search_users(args.assignee, max_results=1)
            if success and users:
                fields['assignee'] = {'accountId': users[0].get('accountId')}
            else:
                print(f"⚠️  Warning: Could not find user '{args.assignee}'", file=sys.stderr)
    
    if args.labels:
        fields['labels'] = parse_labels(args.labels)
    
    if args.components:
        fields['components'] = [{'name': c.strip()} for c in args.components.split(',')]
    
    # Custom fields
    if args.custom_fields:
        try:
            custom = json.loads(args.custom_fields)
            fields.update(custom)
        except json.JSONDecodeError as e:
            print(f"⚠️  Warning: Invalid custom-fields JSON: {e}", file=sys.stderr)
    
    return fields


def main():
    parser = argparse.ArgumentParser(
        description='Create a Jira ticket',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--project', required=True, help='Project key')
    parser.add_argument('--summary', required=True, help='Issue summary')
    parser.add_argument('--type', default='Task', help='Issue type')
    parser.add_argument('--priority', help='Priority level')
    parser.add_argument('--description', help='Description text')
    parser.add_argument('--assignee', help='Assignee username/email')
    parser.add_argument('--labels', help='Comma-separated labels')
    parser.add_argument('--components', help='Comma-separated components')
    parser.add_argument('--epic', help='Epic link key')
    parser.add_argument('--custom-fields', help='Custom fields as JSON')
    parser.add_argument('--output', choices=['json', 'key', 'url'], default='json',
                        help='Output format')
    args = parser.parse_args()
    
    client = get_client()
    
    print(f"📝 Creating ticket in project {args.project}...", file=sys.stderr)
    
    # Build fields
    fields = build_fields(args, client)
    
    # Create issue
    success, result = client.create_issue(fields)
    
    if not success:
        print(f"❌ Error creating ticket: {result}", file=sys.stderr)
        sys.exit(2)
    
    issue_key = result.get('key', 'Unknown')
    issue_url = f"{client.base_url}/browse/{issue_key}"
    
    # Output based on format
    if args.output == 'key':
        print(issue_key)
    elif args.output == 'url':
        print(issue_url)
    else:
        output = {
            'success': True,
            'key': issue_key,
            'id': result.get('id'),
            'url': issue_url,
            'self': result.get('self')
        }
        print(json.dumps(output, indent=2))
    
    print(f"✅ Created ticket: {issue_key}", file=sys.stderr)
    print(f"   URL: {issue_url}", file=sys.stderr)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
