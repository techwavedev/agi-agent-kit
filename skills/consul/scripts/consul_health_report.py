#!/usr/bin/env python3
"""
Consul Health Report Generator

Generates a PDF health report for Consul clusters running on EKS.

Usage:
    python consul_health_report.py --environment nonprod --output ./reports/
    python consul_health_report.py --environment prod --output ./reports/ --format pdf
    python consul_health_report.py --environment nonprod --format markdown

Arguments:
    --environment, -e   Environment name (nonprod, prod, etc.)
    --output, -o        Output directory (default: current directory)
    --format, -f        Output format: pdf, markdown, or both (default: both)
    --namespace, -n     Consul namespace (default: consul)

Exit Codes:
    0 - Success
    1 - Invalid arguments
    2 - Kubectl not available or cluster access failed
    3 - Report generation failed
"""

import argparse
import json
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

# Environment to EKS cluster mapping
CLUSTER_MAP = {
    'nonprod': 'eks-nonprod',
    'prod': 'eks-prod',
}

def run_kubectl(cmd, namespace='consul'):
    """Execute kubectl command and return output."""
    full_cmd = f"kubectl {cmd}"
    try:
        result = subprocess.run(
            full_cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "Command timed out", 1
    except Exception as e:
        return str(e), 1

def run_consul_cmd(cmd, namespace='consul', token=None):
    """Execute command inside Consul server pod."""
    token_flag = f'-token="{token}"' if token else ''
    full_cmd = f'kubectl exec -n {namespace} consul-server-0 -- consul {cmd} {token_flag}'
    return run_kubectl(full_cmd.replace('kubectl ', ''))

def get_bootstrap_token(namespace='consul'):
    """Retrieve Consul bootstrap ACL token from Kubernetes secret."""
    cmd = f"get secret -n {namespace} consul-bootstrap-acl-token -o jsonpath='{{.data.token}}'"
    output, rc = run_kubectl(cmd)
    if rc == 0 and output:
        import base64
        try:
            return base64.b64decode(output).decode('utf-8')
        except:
            return None
    return None

def set_cluster_context(environment, region='eu-west-1'):
    """Set kubectl context to the target EKS cluster."""
    cluster_name = CLUSTER_MAP.get(environment, f'eks-{environment}')
    cmd = f"aws eks update-kubeconfig --name {cluster_name} --region {region}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0

def collect_health_data(namespace='consul'):
    """Collect all health data from Consul cluster."""
    data = {
        'timestamp': datetime.now().isoformat(),
        'pods': {},
        'helm': {},
        'members': [],
        'raft_peers': [],
        'autopilot': {},
        'services': [],
        'ca_config': {},
        'warnings': [],
    }
    
    # Get pods
    output, rc = run_kubectl(f'-n {namespace} get pods -o json')
    if rc == 0:
        try:
            pods_json = json.loads(output)
            data['pods'] = pods_json
        except:
            pass
    
    # Get helm release info
    output, rc = run_kubectl(f'-n {namespace} get pods -o wide'.replace('kubectl ', ''))
    result = subprocess.run(f'helm list -n {namespace} -o json', shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        try:
            data['helm'] = json.loads(result.stdout)
        except:
            pass
    
    # Get Consul members
    output, rc = run_consul_cmd('members')
    if rc == 0:
        lines = output.strip().split('\n')
        for line in lines[1:]:  # Skip header
            if line.strip():
                parts = line.split()
                if len(parts) >= 6:
                    data['members'].append({
                        'node': parts[0],
                        'address': parts[1],
                        'status': parts[2],
                        'type': parts[3],
                        'build': parts[4],
                        'dc': parts[6] if len(parts) > 6 else '',
                    })
    
    # Get bootstrap token for ACL-protected commands
    token = get_bootstrap_token(namespace)
    
    # Get Raft peers
    if token:
        output, rc = run_consul_cmd('operator raft list-peers', token=token)
        if rc == 0:
            lines = output.strip().split('\n')
            for line in lines[1:]:  # Skip header
                if line.strip() and 'Defaulted' not in line:
                    parts = line.split()
                    if len(parts) >= 6:
                        data['raft_peers'].append({
                            'node': parts[0],
                            'id': parts[1],
                            'address': parts[2],
                            'state': parts[3],
                            'voter': parts[4],
                            'commit_index': parts[6] if len(parts) > 6 else '',
                        })
        
        # Get autopilot state
        output, rc = run_consul_cmd('operator autopilot state', token=token)
        if rc == 0:
            data['autopilot']['raw'] = output
            data['autopilot']['healthy'] = 'Healthy:                      true' in output
        
        # Get CA config
        output, rc = run_consul_cmd('connect ca get-config', token=token)
        if rc == 0:
            try:
                # Find JSON in output
                json_start = output.find('{')
                if json_start >= 0:
                    data['ca_config'] = json.loads(output[json_start:])
            except:
                pass
    
    # Get registered services
    output, rc = run_consul_cmd('catalog services')
    if rc == 0:
        services = [s.strip() for s in output.split('\n') if s.strip() and 'Defaulted' not in s]
        data['services'] = services
    
    # Check for warnings in logs
    result = subprocess.run(
        f'kubectl logs -n {namespace} -l app=consul,component=server --tail=100 2>&1 | grep -iE "(error|warn|fail)" | tail -20',
        shell=True, capture_output=True, text=True
    )
    if result.returncode == 0 and result.stdout:
        for line in result.stdout.strip().split('\n'):
            if 'Check is now critical' in line:
                # Extract service name
                if 'check=service:' in line:
                    svc = line.split('check=service:')[1].strip()
                    data['warnings'].append({
                        'type': 'critical_check',
                        'service': svc,
                        'message': f'Health check failing for {svc}'
                    })
            elif 'deprecated' in line.lower():
                if not any(w['type'] == 'deprecated_token' for w in data['warnings']):
                    data['warnings'].append({
                        'type': 'deprecated_token',
                        'message': 'Deprecated token query parameter in use'
                    })
    
    return data

def generate_pdf_report(data, environment, output_path):
    """Generate PDF report from collected data."""
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
    except ImportError:
        print("Error: fpdf2 not installed. Install with: pip install fpdf2", file=sys.stderr)
        return False
    
    class ConsulHealthReport(FPDF):
        def __init__(self, env):
            super().__init__()
            self.env = env
            
        def header(self):
            self.set_font('Helvetica', 'B', 16)
            self.set_text_color(0, 102, 204)
            self.cell(0, 10, 'Consul Health Report', border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            self.set_font('Helvetica', '', 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 6, f'Environment: {self.env}', border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            self.cell(0, 6, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            self.ln(5)
            self.set_draw_color(0, 102, 204)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f'Page {self.page_no()}', align='C')

        def section_title(self, title):
            self.set_font('Helvetica', 'B', 14)
            self.set_text_color(0, 51, 102)
            self.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(2)

        def status_badge(self, status):
            if status.upper() in ['HEALTHY', 'ALIVE', 'RUNNING', 'LEADER', 'OK']:
                self.set_fill_color(40, 167, 69)
            elif status.upper() in ['WARNING', 'WARN', 'FOLLOWER']:
                self.set_fill_color(255, 193, 7)
            else:
                self.set_fill_color(220, 53, 69)
            self.set_text_color(255, 255, 255)
            self.set_font('Helvetica', 'B', 10)
            self.cell(25, 6, status.upper(), fill=True, align='C')
            self.set_text_color(0, 0, 0)

        def add_table(self, headers, rows, col_widths=None):
            self.set_font('Helvetica', 'B', 9)
            self.set_fill_color(240, 240, 240)
            self.set_text_color(0, 0, 0)
            if col_widths is None:
                col_widths = [190 / len(headers)] * len(headers)
            for i, header in enumerate(headers):
                self.cell(col_widths[i], 7, header, border=1, fill=True, align='C')
            self.ln()
            self.set_font('Helvetica', '', 8)
            for row in rows:
                for i, cell in enumerate(row):
                    self.cell(col_widths[i], 6, str(cell), border=1, align='C')
                self.ln()
            self.ln(3)

        def add_key_value(self, key, value, indent=0):
            self.set_font('Helvetica', 'B', 10)
            self.set_x(10 + indent)
            self.cell(50, 6, f'{key}:', new_x=XPos.RIGHT, new_y=YPos.TOP)
            self.set_font('Helvetica', '', 10)
            self.cell(0, 6, str(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf = ConsulHealthReport(environment)
    pdf.add_page()
    
    # Overall Status
    is_healthy = data.get('autopilot', {}).get('healthy', False) and len(data.get('members', [])) >= 3
    pdf.section_title('Overall Status')
    pdf.status_badge('HEALTHY' if is_healthy else 'UNHEALTHY')
    pdf.ln(10)
    
    # Cluster Summary
    pdf.section_title('Cluster Summary')
    pdf.add_key_value('Datacenter', CLUSTER_MAP.get(environment, environment))
    helm_info = data.get('helm', [{}])
    if helm_info and len(helm_info) > 0:
        h = helm_info[0]
        pdf.add_key_value('Chart Version', h.get('chart', 'N/A'))
        pdf.add_key_value('App Version', h.get('app_version', 'N/A'))
        pdf.add_key_value('Revision', h.get('revision', 'N/A'))
    pdf.add_key_value('Autopilot Health', 'Healthy' if data.get('autopilot', {}).get('healthy') else 'Unknown')
    pdf.ln(5)
    
    # Raft Consensus
    if data.get('raft_peers'):
        pdf.section_title('Raft Consensus (HA Health)')
        headers = ['Node', 'Address', 'State', 'Voter', 'Commit Index']
        rows = [[p['node'], p['address'], p['state'], p['voter'], p['commit_index']] for p in data['raft_peers']]
        pdf.add_table(headers, rows, [40, 45, 25, 20, 30])
    
    # Consul Members
    if data.get('members'):
        pdf.section_title('Consul Members')
        headers = ['Node', 'Address', 'Status', 'Type', 'Build']
        rows = [[m['node'], m['address'], m['status'], m['type'], m['build']] for m in data['members']]
        pdf.add_table(headers, rows, [40, 45, 25, 25, 25])
    
    # Services
    if data.get('services'):
        pdf.section_title(f'Registered Services ({len(data["services"])} total)')
        pdf.set_font('Helvetica', '', 9)
        for i, svc in enumerate(data['services']):
            if i % 3 == 0 and i > 0:
                pdf.ln()
            pdf.cell(60, 5, f'- {svc}', new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.ln(10)
    
    # CA Config
    if data.get('ca_config'):
        pdf.section_title('Connect CA (mTLS)')
        cfg = data['ca_config'].get('Config', {})
        pdf.add_key_value('Provider', data['ca_config'].get('Provider', 'N/A'))
        pdf.add_key_value('Root Cert TTL', cfg.get('RootCertTTL', 'N/A'))
        pdf.add_key_value('Intermediate TTL', cfg.get('IntermediateCertTTL', 'N/A'))
        pdf.add_key_value('Leaf Cert TTL', cfg.get('LeafCertTTL', 'N/A'))
        pdf.ln(5)
    
    # Warnings
    if data.get('warnings'):
        pdf.add_page()
        pdf.section_title('Warnings Detected')
        for w in data['warnings']:
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_fill_color(255, 243, 205)
            pdf.set_text_color(133, 100, 4)
            pdf.multi_cell(190, 6, f"WARNING: {w.get('message', w.get('type', 'Unknown'))}", fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Helvetica', '', 9)
            if w.get('service'):
                pdf.add_key_value('Service', w['service'], indent=5)
            pdf.ln(5)
    
    # Save
    pdf.output(output_path)
    return True

def generate_markdown_report(data, environment, output_path):
    """Generate Markdown report from collected data."""
    is_healthy = data.get('autopilot', {}).get('healthy', False) and len(data.get('members', [])) >= 3
    
    lines = [
        f"# Consul Health Report",
        "",
        f"**Environment:** {environment} ({CLUSTER_MAP.get(environment, environment)})",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## Overall Status",
        "",
        f"| Status | Result |",
        f"|--------|--------|",
        f"| **Cluster Health** | {'✅ **HEALTHY**' if is_healthy else '❌ **UNHEALTHY**'} |",
        "",
        "---",
        "",
        "## Cluster Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| **Datacenter** | `{CLUSTER_MAP.get(environment, environment)}` |",
    ]
    
    helm_info = data.get('helm', [{}])
    if helm_info and len(helm_info) > 0:
        h = helm_info[0]
        lines.append(f"| **Chart Version** | `{h.get('chart', 'N/A')}` |")
        lines.append(f"| **App Version** | `{h.get('app_version', 'N/A')}` |")
        lines.append(f"| **Revision** | {h.get('revision', 'N/A')} |")
    
    lines.append(f"| **Autopilot Health** | {'✅ Healthy' if data.get('autopilot', {}).get('healthy') else 'Unknown'} |")
    lines.extend(["", "---", ""])
    
    # Raft peers
    if data.get('raft_peers'):
        lines.extend([
            "## Raft Consensus (HA Health)",
            "",
            "| Node | Address | State | Voter | Commit Index |",
            "|------|---------|-------|-------|--------------|",
        ])
        for p in data['raft_peers']:
            state = f"**{p['state']}**" if p['state'].lower() == 'leader' else p['state']
            lines.append(f"| `{p['node']}` | {p['address']} | {state} | {p['voter']} | {p['commit_index']} |")
        lines.extend(["", "---", ""])
    
    # Members
    if data.get('members'):
        lines.extend([
            "## Consul Members",
            "",
            "| Node | Address | Status | Type | Build |",
            "|------|---------|--------|------|-------|",
        ])
        for m in data['members']:
            lines.append(f"| `{m['node']}` | {m['address']} | {m['status']} | {m['type']} | {m['build']} |")
        lines.extend(["", "---", ""])
    
    # Services
    if data.get('services'):
        lines.extend([
            f"## Registered Services ({len(data['services'])} total)",
            "",
        ])
        for svc in data['services']:
            lines.append(f"- `{svc}`")
        lines.extend(["", "---", ""])
    
    # CA Config
    if data.get('ca_config'):
        cfg = data['ca_config'].get('Config', {})
        lines.extend([
            "## Connect CA (mTLS)",
            "",
            "| Setting | Value |",
            "|---------|-------|",
            f"| **Provider** | {data['ca_config'].get('Provider', 'N/A')} |",
            f"| **Root Cert TTL** | {cfg.get('RootCertTTL', 'N/A')} |",
            f"| **Intermediate TTL** | {cfg.get('IntermediateCertTTL', 'N/A')} |",
            f"| **Leaf Cert TTL** | {cfg.get('LeafCertTTL', 'N/A')} |",
            "",
            "---",
            "",
        ])
    
    # Warnings
    if data.get('warnings'):
        lines.extend([
            "## Warnings Detected",
            "",
        ])
        for w in data['warnings']:
            lines.append(f"### ⚠️ {w.get('message', w.get('type', 'Unknown'))}")
            lines.append("")
            if w.get('service'):
                lines.append(f"- **Service:** `{w['service']}`")
            lines.append("")
        lines.extend(["---", ""])
    
    lines.extend([
        "",
        "*Report generated by Consul health monitoring skill*",
    ])
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Generate Consul health report for EKS clusters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('-e', '--environment', required=True, 
                        help='Environment name (nonprod, prod)')
    parser.add_argument('-o', '--output', default='.',
                        help='Output directory (default: current)')
    parser.add_argument('-f', '--format', choices=['pdf', 'markdown', 'both'], default='both',
                        help='Output format (default: both)')
    parser.add_argument('-n', '--namespace', default='consul',
                        help='Consul namespace (default: consul)')
    parser.add_argument('-r', '--region', default='eu-west-1',
                        help='AWS region (default: eu-west-1)')
    
    args = parser.parse_args()
    
    # Set cluster context
    print(f"Setting context to {args.environment} cluster...")
    if not set_cluster_context(args.environment, args.region):
        print(f"Error: Failed to set cluster context for {args.environment}", file=sys.stderr)
        sys.exit(2)
    
    # Collect health data
    print("Collecting health data...")
    data = collect_health_data(args.namespace)
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = f'consul_health_{args.environment}_{timestamp}'
    
    # Generate reports
    if args.format in ['pdf', 'both']:
        pdf_path = output_dir / f'{base_name}.pdf'
        print(f"Generating PDF report: {pdf_path}")
        if generate_pdf_report(data, args.environment, str(pdf_path)):
            print(f"  ✓ PDF saved: {pdf_path}")
        else:
            print(f"  ✗ PDF generation failed", file=sys.stderr)
    
    if args.format in ['markdown', 'both']:
        md_path = output_dir / f'{base_name}.md'
        print(f"Generating Markdown report: {md_path}")
        if generate_markdown_report(data, args.environment, str(md_path)):
            print(f"  ✓ Markdown saved: {md_path}")
        else:
            print(f"  ✗ Markdown generation failed", file=sys.stderr)
    
    # Also save raw data as JSON
    json_path = output_dir / f'{base_name}.json'
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  ✓ Raw data saved: {json_path}")
    
    print("\nDone!")
    
    # Print summary
    is_healthy = data.get('autopilot', {}).get('healthy', False)
    print(f"\n{'='*50}")
    print(f"Cluster Status: {'✓ HEALTHY' if is_healthy else '✗ ISSUES DETECTED'}")
    print(f"Members: {len(data.get('members', []))}")
    print(f"Services: {len(data.get('services', []))}")
    print(f"Warnings: {len(data.get('warnings', []))}")
    print(f"{'='*50}")
    
    sys.exit(0)


if __name__ == '__main__':
    main()
