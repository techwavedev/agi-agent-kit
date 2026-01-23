#!/usr/bin/env python3
"""
Search Jira Tickets

Search and filter Jira issues using JQL.

Usage:
    python search_tickets.py --jql <query> [options]

Arguments:
    --jql           JQL query string (required)
    --fields        Comma-separated fields to return
    --max-results   Maximum results (default: 50)
    --output        Output format: json, table, keys (default: table)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Search error
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jira_client import get_client


def format_table(issues: list) -> str:
    """Format issues as a simple table."""
    if not issues:
        return "No issues found."
    
    lines = []
    lines.append(f"{'Key':<12} {'Type':<10} {'Priority':<10} {'Status':<15} {'Summary'}")
    lines.append("-" * 80)
    
    for issue in issues:
        key = issue.get('key', '')
        fields = issue.get('fields', {})
        
        issue_type = fields.get('issuetype', {}).get('name', '-')[:10]
        priority = fields.get('priority', {}).get('name', '-')[:10] if fields.get('priority') else '-'
        status = fields.get('status', {}).get('name', '-')[:15]
        summary = fields.get('summary', '')[:50]
        
        lines.append(f"{key:<12} {issue_type:<10} {priority:<10} {status:<15} {summary}")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Search Jira tickets with JQL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--jql', required=True, help='JQL query')
    parser.add_argument('--fields', help='Comma-separated fields')
    parser.add_argument('--max-results', type=int, default=50, help='Max results')
    parser.add_argument('--output', choices=['json', 'table', 'keys'], default='table',
                        help='Output format')
    args = parser.parse_args()
    
    client = get_client()
    
    print(f"🔍 Searching: {args.jql}", file=sys.stderr)
    
    # Parse fields
    fields = None
    if args.fields:
        fields = [f.strip() for f in args.fields.split(',')]
    else:
        # Default useful fields
        fields = ['summary', 'status', 'priority', 'issuetype', 'assignee', 'created', 'updated']
    
    # Search
    success, result = client.search_issues(args.jql, fields=fields, max_results=args.max_results)
    
    if not success:
        print(f"❌ Search error: {result}", file=sys.stderr)
        sys.exit(2)
    
    issues = result.get('issues', [])
    total = result.get('total', len(issues))
    
    print(f"   Found {total} issue(s) (showing {len(issues)})", file=sys.stderr)
    
    # Output based on format
    if args.output == 'keys':
        for issue in issues:
            print(issue.get('key'))
    elif args.output == 'json':
        print(json.dumps(issues, indent=2))
    else:
        print(format_table(issues))
    
    sys.exit(0)


if __name__ == '__main__':
    main()
