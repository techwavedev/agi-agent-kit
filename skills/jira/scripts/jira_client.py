#!/usr/bin/env python3
"""
Jira API Client Utility

Provides a reusable client for Jira REST API operations.
Handles authentication, error handling, and common operations.

This module is used by all other Jira scripts.

Usage:
    from jira_client import JiraClient
    
    client = JiraClient()
    issue = client.get_issue("PROJ-123")

Environment Variables Required:
    JIRA_URL - Base URL (e.g., https://company.atlassian.net)
    JIRA_EMAIL - User email
    JIRA_API_TOKEN - API token
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("❌ Error: requests library required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    # Look for .env in common locations
    for env_path in ['.env', '../.env', '../../.env', Path.home() / '.env']:
        if Path(env_path).exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass


class JiraClient:
    """
    Jira REST API client with authentication and error handling.
    """
    
    def __init__(self, url: str = None, email: str = None, token: str = None):
        """
        Initialize the Jira client.
        
        Args:
            url: Jira instance URL (or JIRA_URL env var)
            email: User email (or JIRA_EMAIL env var)
            token: API token (or JIRA_API_TOKEN env var)
        """
        self.base_url = (url or os.getenv('JIRA_URL', '')).rstrip('/')
        self.email = email or os.getenv('JIRA_EMAIL', '')
        self.token = token or os.getenv('JIRA_API_TOKEN', '')
        
        if not all([self.base_url, self.email, self.token]):
            missing = []
            if not self.base_url:
                missing.append('JIRA_URL')
            if not self.email:
                missing.append('JIRA_EMAIL')
            if not self.token:
                missing.append('JIRA_API_TOKEN')
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        self.api_url = f"{self.base_url}/rest/api/3"
        self.session = requests.Session()
        self.session.auth = (self.email, self.token)
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Tuple[bool, Any]:
        """
        Make an API request.
        
        Returns:
            (success, data_or_error)
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 204:
                return True, None
            
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_msg = self._parse_error(error_data, response.status_code)
                return False, error_msg
            
            return True, response.json() if response.content else None
            
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"
        except json.JSONDecodeError:
            return False, f"Invalid JSON response: {response.text[:200]}"
    
    def _parse_error(self, error_data: Dict, status_code: int) -> str:
        """Parse Jira error response into readable message."""
        if 'errorMessages' in error_data and error_data['errorMessages']:
            return '; '.join(error_data['errorMessages'])
        if 'errors' in error_data:
            return '; '.join(f"{k}: {v}" for k, v in error_data['errors'].items())
        return f"HTTP {status_code} error"
    
    # ========== Issue Operations ==========
    
    def get_issue(self, key: str, fields: List[str] = None, expand: List[str] = None) -> Tuple[bool, Any]:
        """Get issue by key."""
        params = {}
        if fields:
            params['fields'] = ','.join(fields)
        if expand:
            params['expand'] = ','.join(expand)
        
        return self._request('GET', f'issue/{key}', params=params)
    
    def create_issue(self, fields: Dict) -> Tuple[bool, Any]:
        """Create a new issue."""
        return self._request('POST', 'issue', json={'fields': fields})
    
    def update_issue(self, key: str, fields: Dict = None, update: Dict = None) -> Tuple[bool, Any]:
        """Update an existing issue."""
        data = {}
        if fields:
            data['fields'] = fields
        if update:
            data['update'] = update
        
        return self._request('PUT', f'issue/{key}', json=data)
    
    def delete_issue(self, key: str) -> Tuple[bool, Any]:
        """Delete an issue."""
        return self._request('DELETE', f'issue/{key}')
    
    def search_issues(self, jql: str, fields: List[str] = None, 
                      max_results: int = 50, start_at: int = 0) -> Tuple[bool, Any]:
        """Search issues using JQL."""
        data = {
            'jql': jql,
            'maxResults': max_results,
            'startAt': start_at
        }
        if fields:
            data['fields'] = fields
        
        return self._request('POST', 'search', json=data)
    
    # ========== Transitions ==========
    
    def get_transitions(self, key: str) -> Tuple[bool, Any]:
        """Get available transitions for an issue."""
        return self._request('GET', f'issue/{key}/transitions')
    
    def transition_issue(self, key: str, transition_id: str, 
                         fields: Dict = None, comment: str = None) -> Tuple[bool, Any]:
        """Transition an issue to a new status."""
        data = {
            'transition': {'id': transition_id}
        }
        if fields:
            data['fields'] = fields
        if comment:
            data['update'] = {
                'comment': [{
                    'add': {'body': self._format_adf(comment)}
                }]
            }
        
        return self._request('POST', f'issue/{key}/transitions', json=data)
    
    def find_transition_by_name(self, key: str, status_name: str) -> Optional[str]:
        """Find transition ID by target status name."""
        success, transitions = self.get_transitions(key)
        if not success:
            return None
        
        status_lower = status_name.lower()
        for t in transitions.get('transitions', []):
            if t.get('to', {}).get('name', '').lower() == status_lower:
                return t['id']
            if t.get('name', '').lower() == status_lower:
                return t['id']
        
        return None
    
    # ========== Comments ==========
    
    def get_comments(self, key: str) -> Tuple[bool, Any]:
        """Get all comments for an issue."""
        return self._request('GET', f'issue/{key}/comment')
    
    def add_comment(self, key: str, body: str, visibility: Dict = None) -> Tuple[bool, Any]:
        """Add a comment to an issue."""
        data = {
            'body': self._format_adf(body)
        }
        if visibility:
            data['visibility'] = visibility
        
        return self._request('POST', f'issue/{key}/comment', json=data)
    
    def update_comment(self, key: str, comment_id: str, body: str) -> Tuple[bool, Any]:
        """Update an existing comment."""
        data = {
            'body': self._format_adf(body)
        }
        return self._request('PUT', f'issue/{key}/comment/{comment_id}', json=data)
    
    def delete_comment(self, key: str, comment_id: str) -> Tuple[bool, Any]:
        """Delete a comment."""
        return self._request('DELETE', f'issue/{key}/comment/{comment_id}')
    
    # ========== Worklog ==========
    
    def get_worklogs(self, key: str) -> Tuple[bool, Any]:
        """Get all worklogs for an issue."""
        return self._request('GET', f'issue/{key}/worklog')
    
    def add_worklog(self, key: str, time_spent: str, 
                    comment: str = None, started: str = None,
                    adjust_estimate: str = None, new_estimate: str = None) -> Tuple[bool, Any]:
        """
        Add a worklog entry.
        
        Args:
            key: Issue key
            time_spent: Time in Jira format (e.g., "2h", "1d", "30m")
            comment: Work description
            started: Start datetime in ISO format
            adjust_estimate: How to adjust estimate (new, manual, leave, auto)
            new_estimate: New estimate if adjust_estimate is 'new'
        """
        data = {
            'timeSpent': time_spent
        }
        if comment:
            data['comment'] = self._format_adf(comment)
        if started:
            data['started'] = started
        
        params = {}
        if adjust_estimate:
            params['adjustEstimate'] = adjust_estimate
        if new_estimate:
            params['newEstimate'] = new_estimate
        
        return self._request('POST', f'issue/{key}/worklog', json=data, params=params)
    
    # ========== Projects ==========
    
    def get_projects(self) -> Tuple[bool, Any]:
        """Get all accessible projects."""
        return self._request('GET', 'project')
    
    def get_project(self, key: str) -> Tuple[bool, Any]:
        """Get project details."""
        return self._request('GET', f'project/{key}')
    
    # ========== Users ==========
    
    def search_users(self, query: str, max_results: int = 50) -> Tuple[bool, Any]:
        """Search for users."""
        return self._request('GET', 'user/search', params={
            'query': query,
            'maxResults': max_results
        })
    
    def get_myself(self) -> Tuple[bool, Any]:
        """Get current user info."""
        return self._request('GET', 'myself')
    
    # ========== Helpers ==========
    
    def _format_adf(self, text: str) -> Dict:
        """
        Convert plain text to Atlassian Document Format (ADF).
        
        Simple implementation - converts text to paragraphs.
        """
        paragraphs = []
        for para in text.split('\n\n'):
            if para.strip():
                paragraphs.append({
                    'type': 'paragraph',
                    'content': [{'type': 'text', 'text': para.strip()}]
                })
        
        return {
            'type': 'doc',
            'version': 1,
            'content': paragraphs if paragraphs else [
                {'type': 'paragraph', 'content': [{'type': 'text', 'text': text}]}
            ]
        }
    
    def parse_time_to_seconds(self, time_str: str) -> int:
        """
        Parse Jira time format to seconds.
        
        Supports: 1w, 2d, 3h, 30m (and combinations like "2h 30m")
        """
        total = 0
        patterns = {
            'w': 5 * 8 * 60 * 60,  # 1 week = 5 days
            'd': 8 * 60 * 60,      # 1 day = 8 hours
            'h': 60 * 60,
            'm': 60,
            's': 1
        }
        
        for match in re.finditer(r'(\d+)\s*([wdhms])', time_str.lower()):
            value, unit = int(match.group(1)), match.group(2)
            total += value * patterns.get(unit, 0)
        
        return total


def get_client() -> JiraClient:
    """Get a configured Jira client instance."""
    try:
        return JiraClient()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}", file=sys.stderr)
        print("\nEnsure these environment variables are set:", file=sys.stderr)
        print("  JIRA_URL=https://your-domain.atlassian.net", file=sys.stderr)
        print("  JIRA_EMAIL=your-email@example.com", file=sys.stderr)
        print("  JIRA_API_TOKEN=your-api-token", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    # Test connection when run directly
    print("Testing Jira connection...")
    client = get_client()
    
    success, result = client.get_myself()
    if success:
        print(f"✅ Connected as: {result.get('displayName', 'Unknown')}")
        print(f"   Email: {result.get('emailAddress', 'N/A')}")
    else:
        print(f"❌ Connection failed: {result}")
        sys.exit(1)
