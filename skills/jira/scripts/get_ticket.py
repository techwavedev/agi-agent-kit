#!/usr/bin/env python3
"""
Get Jira Ticket Details

Retrieve full details for a specific Jira issue.

Usage:
    python get_ticket.py --ticket <key> [options]

Arguments:
    --ticket            Ticket key (required)
    --include-comments  Include comments
    --include-worklog   Include work logs
    --include-transitions  Show available transitions
    --output            Output format: json, summary (default: summary)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Ticket not found
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jira_client import get_client


def format_summary(issue: dict, transitions: list = None, comments: list = None, 
                   worklogs: list = None, base_url: str = '') -> str:
    """Format issue as human-readable summary."""
    key = issue.get('key', 'Unknown')
    fields = issue.get('fields', {})
    
    lines = [
        f"# {key}: {fields.get('summary', 'No summary')}",
        "",
        f"**URL:** {base_url}/browse/{key}",
        "",
        "## Details",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Type | {fields.get('issuetype', {}).get('name', '-')} |",
        f"| Status | {fields.get('status', {}).get('name', '-')} |",
        f"| Priority | {fields.get('priority', {}).get('name', '-') if fields.get('priority') else '-'} |",
    ]
    
    assignee = fields.get('assignee')
    lines.append(f"| Assignee | {assignee.get('displayName', '-') if assignee else 'Unassigned'} |")
    
    reporter = fields.get('reporter')
    lines.append(f"| Reporter | {reporter.get('displayName', '-') if reporter else '-'} |")
    
    lines.append(f"| Created | {fields.get('created', '-')[:10] if fields.get('created') else '-'} |")
    lines.append(f"| Updated | {fields.get('updated', '-')[:10] if fields.get('updated') else '-'} |")
    
    if fields.get('labels'):
        lines.append(f"| Labels | {', '.join(fields['labels'])} |")
    
    lines.append("")
    
    # Description
    description = fields.get('description')
    if description:
        lines.append("## Description")
        lines.append("")
        if isinstance(description, dict):
            # ADF format - extract text
            content = description.get('content', [])
            for block in content:
                if block.get('type') == 'paragraph':
                    text_parts = [c.get('text', '') for c in block.get('content', [])]
                    lines.append(''.join(text_parts))
        else:
            lines.append(str(description))
        lines.append("")
    
    # Transitions
    if transitions:
        lines.append("## Available Transitions")
        lines.append("")
        for t in transitions:
            lines.append(f"- {t.get('name')} → {t.get('to', {}).get('name', '?')}")
        lines.append("")
    
    # Comments
    if comments:
        lines.append(f"## Comments ({len(comments)})")
        lines.append("")
        for c in comments[-5:]:  # Last 5 comments
            author = c.get('author', {}).get('displayName', 'Unknown')
            created = c.get('created', '')[:10]
            body = c.get('body', '')
            if isinstance(body, dict):
                # ADF format
                text_parts = []
                for block in body.get('content', []):
                    if block.get('type') == 'paragraph':
                        text_parts.extend([p.get('text', '') for p in block.get('content', [])])
                body = ' '.join(text_parts)
            lines.append(f"**{author}** ({created}):")
            lines.append(f"> {body[:200]}...")
            lines.append("")
    
    # Worklogs
    if worklogs:
        lines.append(f"## Work Logs ({len(worklogs)})")
        lines.append("")
        total_seconds = sum(w.get('timeSpentSeconds', 0) for w in worklogs)
        total_hours = total_seconds / 3600
        lines.append(f"**Total Time Logged:** {total_hours:.1f}h")
        lines.append("")
        for w in worklogs[-5:]:  # Last 5 entries
            author = w.get('author', {}).get('displayName', 'Unknown')
            time_spent = w.get('timeSpent', '?')
            lines.append(f"- {author}: {time_spent}")
        lines.append("")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Get Jira ticket details',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--ticket', required=True, help='Ticket key')
    parser.add_argument('--include-comments', action='store_true', help='Include comments')
    parser.add_argument('--include-worklog', action='store_true', help='Include work logs')
    parser.add_argument('--include-transitions', action='store_true', help='Show transitions')
    parser.add_argument('--output', choices=['json', 'summary'], default='summary',
                        help='Output format')
    args = parser.parse_args()
    
    client = get_client()
    ticket = args.ticket.upper()
    
    print(f"📋 Getting details for {ticket}...", file=sys.stderr)
    
    # Get issue
    expand = []
    if args.include_comments:
        expand.append('renderedFields')
    
    success, issue = client.get_issue(ticket, expand=expand if expand else None)
    if not success:
        print(f"❌ Error: Could not find ticket {ticket}: {issue}", file=sys.stderr)
        sys.exit(2)
    
    # Get optional data
    transitions = None
    comments = None
    worklogs = None
    
    if args.include_transitions:
        success, trans_data = client.get_transitions(ticket)
        if success:
            transitions = trans_data.get('transitions', [])
    
    if args.include_comments:
        success, comment_data = client.get_comments(ticket)
        if success:
            comments = comment_data.get('comments', [])
    
    if args.include_worklog:
        success, worklog_data = client.get_worklogs(ticket)
        if success:
            worklogs = worklog_data.get('worklogs', [])
    
    # Output
    if args.output == 'json':
        output = {
            'issue': issue,
            'transitions': transitions,
            'comments': comments,
            'worklogs': worklogs
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_summary(issue, transitions, comments, worklogs, client.base_url))
    
    sys.exit(0)


if __name__ == '__main__':
    main()
