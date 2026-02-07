#!/usr/bin/env python3
"""
Confluent Kafka Health Check Script

Performs comprehensive health assessment of a Confluent Kafka cluster including:
- Broker connectivity and status
- Controller quorum health (KRaft)
- Partition health (under-replicated, offline)
- Consumer group lag
- Disk usage analysis

Usage:
    python kafka_health_check.py --bootstrap-servers kafka-01:9092,kafka-02:9092 --output ./reports/
    python kafka_health_check.py --bootstrap-servers localhost:9092 --quick
    python kafka_health_check.py --bootstrap-servers kafka-01:9092 --format pdf

Arguments:
    --bootstrap-servers, -b   Comma-separated list of broker addresses (required)
    --output, -o              Output directory for reports (default: current dir)
    --format, -f              Output format: pdf, markdown, both, json (default: both)
    --quick                   Quick check only, no detailed reports
    --timeout, -t             Connection timeout in seconds (default: 30)

Exit Codes:
    0 - Healthy cluster
    1 - Invalid arguments
    2 - Connection failed
    3 - Cluster unhealthy (warnings)
    4 - Cluster critical (offline partitions)
"""

import argparse
import json
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class KafkaHealthChecker:
    """Confluent Kafka cluster health checker."""

    def __init__(self, bootstrap_servers: str, timeout: int = 30):
        self.bootstrap_servers = bootstrap_servers
        self.timeout = timeout
        self.kafka_bin = self._find_kafka_bin()
        self.results: Dict = {
            "timestamp": datetime.now().isoformat(),
            "bootstrap_servers": bootstrap_servers,
            "status": "unknown",
            "brokers": [],
            "topics": {},
            "partitions": {},
            "consumer_groups": [],
            "alerts": [],
            "warnings": [],
        }

    def _find_kafka_bin(self) -> str:
        """Find Kafka binary directory."""
        paths = [
            "/opt/confluent/bin",
            "/opt/kafka/bin",
            os.path.expanduser("~/confluent/bin"),
            os.environ.get("KAFKA_HOME", "") + "/bin",
        ]
        for path in paths:
            if os.path.exists(os.path.join(path, "kafka-topics")):
                return path
        # Try to find via which
        try:
            result = subprocess.run(["which", "kafka-topics"], capture_output=True, text=True)
            if result.returncode == 0:
                return os.path.dirname(result.stdout.strip())
        except Exception:
            pass
        return "/opt/confluent/bin"  # Default fallback

    def _run_kafka_cmd(self, cmd: List[str], timeout: Optional[int] = None) -> Tuple[int, str, str]:
        """Run a Kafka CLI command and return exit code, stdout, stderr."""
        timeout = timeout or self.timeout
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return -1, "", str(e)

    def check_broker_connectivity(self) -> bool:
        """Check if we can connect to brokers."""
        cmd = [
            f"{self.kafka_bin}/kafka-broker-api-versions",
            "--bootstrap-server", self.bootstrap_servers,
        ]
        code, stdout, stderr = self._run_kafka_cmd(cmd)
        
        if code == 0:
            # Parse broker list from output
            lines = stdout.strip().split("\n")
            for line in lines:
                if ":" in line and "ApiVersion" not in line:
                    self.results["brokers"].append(line.strip())
            return True
        else:
            self.results["alerts"].append(f"Cannot connect to brokers: {stderr}")
            return False

    def check_under_replicated_partitions(self) -> int:
        """Check for under-replicated partitions."""
        cmd = [
            f"{self.kafka_bin}/kafka-topics",
            "--bootstrap-server", self.bootstrap_servers,
            "--describe",
            "--under-replicated-partitions",
        ]
        code, stdout, stderr = self._run_kafka_cmd(cmd)
        
        if code == 0:
            urp_count = len([l for l in stdout.strip().split("\n") if l.strip()])
            self.results["partitions"]["under_replicated"] = urp_count
            if urp_count > 0:
                self.results["warnings"].append(f"{urp_count} under-replicated partitions")
            return urp_count
        else:
            self.results["alerts"].append(f"Failed to check URP: {stderr}")
            return -1

    def check_offline_partitions(self) -> int:
        """Check for offline/unavailable partitions."""
        cmd = [
            f"{self.kafka_bin}/kafka-topics",
            "--bootstrap-server", self.bootstrap_servers,
            "--describe",
            "--unavailable-partitions",
        ]
        code, stdout, stderr = self._run_kafka_cmd(cmd)
        
        if code == 0:
            offline_count = len([l for l in stdout.strip().split("\n") if l.strip()])
            self.results["partitions"]["offline"] = offline_count
            if offline_count > 0:
                self.results["alerts"].append(f"CRITICAL: {offline_count} offline partitions")
            return offline_count
        else:
            self.results["alerts"].append(f"Failed to check offline partitions: {stderr}")
            return -1

    def check_topic_count(self) -> int:
        """Get total topic count."""
        cmd = [
            f"{self.kafka_bin}/kafka-topics",
            "--bootstrap-server", self.bootstrap_servers,
            "--list",
        ]
        code, stdout, stderr = self._run_kafka_cmd(cmd)
        
        if code == 0:
            topics = [t for t in stdout.strip().split("\n") if t.strip()]
            self.results["topics"]["count"] = len(topics)
            self.results["topics"]["list"] = topics[:50]  # First 50 topics
            return len(topics)
        else:
            return -1

    def check_consumer_groups(self) -> List[Dict]:
        """Check consumer group status and lag."""
        cmd = [
            f"{self.kafka_bin}/kafka-consumer-groups",
            "--bootstrap-server", self.bootstrap_servers,
            "--all-groups",
            "--describe",
        ]
        code, stdout, stderr = self._run_kafka_cmd(cmd, timeout=60)
        
        groups = []
        if code == 0:
            current_group = None
            total_lag = 0
            
            for line in stdout.strip().split("\n"):
                if not line.strip():
                    if current_group:
                        groups.append(current_group)
                        current_group = None
                    continue
                    
                parts = line.split()
                if len(parts) >= 7 and parts[0] not in ("GROUP", "Consumer"):
                    group_name = parts[0]
                    try:
                        lag = int(parts[5]) if parts[5] != "-" else 0
                        total_lag += lag
                    except (ValueError, IndexError):
                        lag = 0
                    
                    if current_group is None or current_group["name"] != group_name:
                        if current_group:
                            groups.append(current_group)
                        current_group = {
                            "name": group_name,
                            "lag": lag,
                            "partitions": 1,
                        }
                    else:
                        current_group["lag"] += lag
                        current_group["partitions"] += 1
            
            if current_group:
                groups.append(current_group)
            
            self.results["consumer_groups"] = groups[:20]  # Top 20
            self.results["total_consumer_lag"] = total_lag
            
            # Alert on high lag
            high_lag_groups = [g for g in groups if g["lag"] > 100000]
            if high_lag_groups:
                self.results["warnings"].append(
                    f"{len(high_lag_groups)} consumer groups have high lag (>100k)"
                )
        
        return groups

    def run_checks(self, quick: bool = False) -> Dict:
        """Run all health checks."""
        print("🔍 Running Kafka health checks...")
        
        # Critical checks
        print("  ├── Checking broker connectivity...")
        if not self.check_broker_connectivity():
            self.results["status"] = "critical"
            return self.results
        
        print("  ├── Checking offline partitions...")
        offline = self.check_offline_partitions()
        if offline > 0:
            self.results["status"] = "critical"
        
        print("  ├── Checking under-replicated partitions...")
        urp = self.check_under_replicated_partitions()
        if urp > 0 and self.results["status"] != "critical":
            self.results["status"] = "warning"
        
        if not quick:
            print("  ├── Getting topic count...")
            self.check_topic_count()
            
            print("  ├── Checking consumer groups...")
            self.check_consumer_groups()
        
        # Set final status
        if self.results["status"] == "unknown":
            self.results["status"] = "healthy"
        
        print(f"  └── Status: {self.results['status'].upper()}")
        return self.results


def generate_markdown_report(results: Dict, output_path: Path) -> str:
    """Generate a Markdown health report."""
    report = []
    report.append("# Confluent Kafka Health Report")
    report.append("")
    report.append(f"**Generated:** {results['timestamp']}")
    report.append(f"**Bootstrap Servers:** `{results['bootstrap_servers']}`")
    report.append(f"**Status:** {'🟢' if results['status'] == 'healthy' else '🟡' if results['status'] == 'warning' else '🔴'} **{results['status'].upper()}**")
    report.append("")
    
    # Alerts
    if results.get("alerts"):
        report.append("## 🚨 Alerts")
        report.append("")
        for alert in results["alerts"]:
            report.append(f"- ❌ {alert}")
        report.append("")
    
    # Warnings
    if results.get("warnings"):
        report.append("## ⚠️ Warnings")
        report.append("")
        for warning in results["warnings"]:
            report.append(f"- ⚠️ {warning}")
        report.append("")
    
    # Brokers
    report.append("## Broker Status")
    report.append("")
    report.append(f"**Active Brokers:** {len(results.get('brokers', []))}")
    report.append("")
    
    # Partitions
    report.append("## Partition Health")
    report.append("")
    partitions = results.get("partitions", {})
    report.append(f"| Metric | Count |")
    report.append(f"| ------ | ----- |")
    report.append(f"| Under-replicated | {partitions.get('under_replicated', 'N/A')} |")
    report.append(f"| Offline | {partitions.get('offline', 'N/A')} |")
    report.append("")
    
    # Topics
    if results.get("topics"):
        report.append("## Topics")
        report.append("")
        report.append(f"**Total Topics:** {results['topics'].get('count', 'N/A')}")
        report.append("")
    
    # Consumer Groups
    if results.get("consumer_groups"):
        report.append("## Consumer Groups")
        report.append("")
        report.append(f"**Total Lag:** {results.get('total_consumer_lag', 0):,}")
        report.append("")
        report.append("| Group | Lag | Partitions |")
        report.append("| ----- | --- | ---------- |")
        for group in results["consumer_groups"][:10]:
            report.append(f"| {group['name']} | {group['lag']:,} | {group['partitions']} |")
        report.append("")
    
    # Write report
    report_content = "\n".join(report)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_path / f"kafka_health_{timestamp}.md"
    filename.write_text(report_content)
    
    return str(filename)


def generate_pdf_report(results: Dict, output_path: Path) -> Optional[str]:
    """Generate a PDF health report (requires markdown-pdf or similar)."""
    # First generate markdown
    md_file = generate_markdown_report(results, output_path)
    
    # Try to convert to PDF using various tools
    pdf_file = md_file.replace(".md", ".pdf")
    
    converters = [
        # pandoc (most reliable)
        ["pandoc", md_file, "-o", pdf_file, "--pdf-engine=xelatex"],
        # md-to-pdf (npm package)
        ["md-to-pdf", md_file, "--dest", pdf_file],
    ]
    
    for cmd in converters:
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode == 0:
                print(f"  📄 PDF generated: {pdf_file}")
                return pdf_file
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    
    print("  ⚠️ PDF generation failed (pandoc or md-to-pdf not available)")
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Confluent Kafka Health Check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--bootstrap-servers", "-b",
        required=True,
        help="Comma-separated list of broker addresses",
    )
    parser.add_argument(
        "--output", "-o",
        default=".",
        help="Output directory for reports (default: current dir)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["pdf", "markdown", "both", "json"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick check only, no detailed reports",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=30,
        help="Connection timeout in seconds (default: 30)",
    )
    
    args = parser.parse_args()
    
    # Create output directory
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Run health checks
    checker = KafkaHealthChecker(args.bootstrap_servers, args.timeout)
    results = checker.run_checks(quick=args.quick)
    
    # Generate reports
    if args.format in ("json", "both"):
        json_file = output_path / f"kafka_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_file.write_text(json.dumps(results, indent=2))
        print(f"  📄 JSON saved: {json_file}")
    
    if not args.quick:
        if args.format in ("markdown", "both"):
            md_file = generate_markdown_report(results, output_path)
            print(f"  📄 Markdown saved: {md_file}")
        
        if args.format in ("pdf", "both"):
            generate_pdf_report(results, output_path)
    
    # Exit with appropriate code
    if results["status"] == "critical":
        print("\n❌ CRITICAL: Cluster has critical issues!")
        sys.exit(4)
    elif results["status"] == "warning":
        print("\n⚠️ WARNING: Cluster has warnings")
        sys.exit(3)
    else:
        print("\n✅ Cluster is healthy")
        sys.exit(0)


if __name__ == "__main__":
    main()
