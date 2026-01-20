#!/usr/bin/env python3
"""
Confluent Kafka Upgrade Pre-flight Check Script

Validates cluster readiness for upgrade from 7.x to 8.x versions:
- Version compatibility check
- Cluster health verification
- Deprecated configuration detection
- Java version validation
- ZooKeeper/KRaft mode assessment
- Backup recommendations

Usage:
    python upgrade_preflight.py --current-version 7.6 --target-version 8.0 --bootstrap-servers kafka-01:9092
    python upgrade_preflight.py -c 7.5 -t 8.0 -b localhost:9092 --config /opt/confluent/etc/kafka/server.properties

Arguments:
    --current-version, -c    Current Confluent Platform version (required)
    --target-version, -t     Target Confluent Platform version (required)
    --bootstrap-servers, -b  Bootstrap servers for cluster checks (required)
    --config                 Path to server.properties for config validation
    --skip-cluster           Skip cluster health checks (offline validation only)
    --json                   Output results as JSON

Exit Codes:
    0 - Ready for upgrade
    1 - Invalid arguments
    2 - Connection failed
    3 - Pre-flight checks failed (blockers found)
    4 - Critical issues (do not proceed)
"""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class PreflightResult:
    """Pre-flight check result."""
    name: str
    status: str  # "pass", "fail", "warn", "skip"
    message: str
    details: Optional[str] = None


@dataclass
class PreflightReport:
    """Complete pre-flight report."""
    current_version: str
    target_version: str
    overall_status: str = "unknown"
    blockers: List[PreflightResult] = field(default_factory=list)
    warnings: List[PreflightResult] = field(default_factory=list)
    passed: List[PreflightResult] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class UpgradePreflight:
    """Confluent Kafka upgrade pre-flight checker."""

    # Upgrade paths matrix
    UPGRADE_PATHS = {
        ("7.3", "8.0"): {"direct": False, "via": "7.6"},
        ("7.4", "8.0"): {"direct": True},
        ("7.5", "8.0"): {"direct": True},
        ("7.6", "8.0"): {"direct": True},
        ("7.6", "8.1"): {"direct": True},
        ("8.0", "8.1"): {"direct": True},
    }

    def __init__(
        self,
        current_version: str,
        target_version: str,
        bootstrap_servers: Optional[str] = None,
        config_path: Optional[str] = None,
    ):
        self.current_version = current_version
        self.target_version = target_version
        self.bootstrap_servers = bootstrap_servers
        self.config_path = Path(config_path) if config_path else None
        self.report = PreflightReport(current_version, target_version)
        self.kafka_bin = self._find_kafka_bin()

    def _find_kafka_bin(self) -> str:
        """Find Kafka binary directory."""
        paths = [
            "/opt/confluent/bin",
            "/opt/kafka/bin",
            os.path.expanduser("~/confluent/bin"),
        ]
        for path in paths:
            if os.path.exists(os.path.join(path, "kafka-topics")):
                return path
        return "/opt/confluent/bin"

    def _run_cmd(self, cmd: List[str], timeout: int = 30) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    def check_upgrade_path(self) -> PreflightResult:
        """Verify upgrade path is supported."""
        key = (self.current_version, self.target_version)
        
        if key in self.UPGRADE_PATHS:
            path_info = self.UPGRADE_PATHS[key]
            if path_info["direct"]:
                return PreflightResult(
                    name="Upgrade Path",
                    status="pass",
                    message=f"Direct upgrade from {self.current_version} to {self.target_version} is supported",
                )
            else:
                return PreflightResult(
                    name="Upgrade Path",
                    status="fail",
                    message=f"Direct upgrade not supported. Upgrade to {path_info['via']} first.",
                    details=f"Required path: {self.current_version} → {path_info['via']} → {self.target_version}",
                )
        else:
            # Check if it's a minor version difference
            current_major = self.current_version.split(".")[0]
            target_major = self.target_version.split(".")[0]
            
            if current_major == target_major:
                return PreflightResult(
                    name="Upgrade Path",
                    status="pass",
                    message=f"Minor version upgrade within {current_major}.x is supported",
                )
            else:
                return PreflightResult(
                    name="Upgrade Path",
                    status="warn",
                    message=f"Upgrade path {self.current_version} → {self.target_version} not in known matrix",
                    details="Consult Confluent documentation for compatibility",
                )

    def check_java_version(self) -> PreflightResult:
        """Check Java version compatibility."""
        code, stdout, stderr = self._run_cmd(["java", "-version"])
        
        if code != 0:
            return PreflightResult(
                name="Java Version",
                status="fail",
                message="Cannot determine Java version",
                details=stderr,
            )
        
        # Parse Java version from stderr (Java outputs version to stderr)
        version_output = stderr.lower()
        
        # Extract version number
        java_version = None
        if "version" in version_output:
            import re
            match = re.search(r'version ["\']?(\d+)', version_output)
            if match:
                java_version = int(match.group(1))
        
        if java_version is None:
            return PreflightResult(
                name="Java Version",
                status="warn",
                message="Could not parse Java version",
                details=version_output[:200],
            )
        
        # Check requirements for target version
        if self.target_version.startswith("8."):
            if java_version >= 17:
                return PreflightResult(
                    name="Java Version",
                    status="pass",
                    message=f"Java {java_version} meets requirement (Java 17+ required for 8.x)",
                )
            else:
                return PreflightResult(
                    name="Java Version",
                    status="fail",
                    message=f"Java {java_version} is below requirement. Java 17+ required for version 8.x",
                    details="Install Amazon Corretto 17 or OpenJDK 17+",
                )
        else:
            if java_version >= 11:
                return PreflightResult(
                    name="Java Version",
                    status="pass",
                    message=f"Java {java_version} meets requirement for 7.x",
                )
            else:
                return PreflightResult(
                    name="Java Version",
                    status="fail",
                    message=f"Java {java_version} is below requirement. Java 11+ required.",
                )

    def check_cluster_health(self) -> List[PreflightResult]:
        """Check cluster health indicators."""
        results = []
        
        if not self.bootstrap_servers:
            results.append(PreflightResult(
                name="Cluster Health",
                status="skip",
                message="Bootstrap servers not provided, skipping cluster checks",
            ))
            return results
        
        # Check connectivity
        cmd = [
            f"{self.kafka_bin}/kafka-broker-api-versions",
            "--bootstrap-server", self.bootstrap_servers,
        ]
        code, stdout, stderr = self._run_cmd(cmd)
        
        if code != 0:
            results.append(PreflightResult(
                name="Broker Connectivity",
                status="fail",
                message="Cannot connect to Kafka brokers",
                details=stderr[:200],
            ))
            return results
        
        results.append(PreflightResult(
            name="Broker Connectivity",
            status="pass",
            message="Successfully connected to Kafka cluster",
        ))
        
        # Check under-replicated partitions
        cmd = [
            f"{self.kafka_bin}/kafka-topics",
            "--bootstrap-server", self.bootstrap_servers,
            "--describe", "--under-replicated-partitions",
        ]
        code, stdout, stderr = self._run_cmd(cmd)
        
        if code == 0:
            urp_lines = [l for l in stdout.strip().split("\n") if l.strip()]
            if urp_lines:
                results.append(PreflightResult(
                    name="Under-replicated Partitions",
                    status="fail",
                    message=f"{len(urp_lines)} under-replicated partitions found",
                    details="Resolve URP before upgrade to ensure data safety",
                ))
            else:
                results.append(PreflightResult(
                    name="Under-replicated Partitions",
                    status="pass",
                    message="No under-replicated partitions",
                ))
        
        # Check offline partitions
        cmd = [
            f"{self.kafka_bin}/kafka-topics",
            "--bootstrap-server", self.bootstrap_servers,
            "--describe", "--unavailable-partitions",
        ]
        code, stdout, stderr = self._run_cmd(cmd)
        
        if code == 0:
            offline_lines = [l for l in stdout.strip().split("\n") if l.strip()]
            if offline_lines:
                results.append(PreflightResult(
                    name="Offline Partitions",
                    status="fail",
                    message=f"CRITICAL: {len(offline_lines)} offline partitions found",
                    details="DO NOT PROCEED. Resolve offline partitions first.",
                ))
            else:
                results.append(PreflightResult(
                    name="Offline Partitions",
                    status="pass",
                    message="No offline partitions",
                ))
        
        return results

    def check_config_compatibility(self) -> List[PreflightResult]:
        """Check configuration for deprecated settings."""
        results = []
        
        if not self.config_path:
            results.append(PreflightResult(
                name="Configuration Check",
                status="skip",
                message="No config file provided, skipping config validation",
            ))
            return results
        
        if not self.config_path.exists():
            results.append(PreflightResult(
                name="Configuration Check",
                status="fail",
                message=f"Config file not found: {self.config_path}",
            ))
            return results
        
        # Parse config
        config = {}
        try:
            with open(self.config_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip()
        except Exception as e:
            results.append(PreflightResult(
                name="Configuration Check",
                status="fail",
                message=f"Cannot parse config: {e}",
            ))
            return results
        
        # Check deprecated settings for 8.x
        if self.target_version.startswith("8."):
            deprecated = ["log.message.format.version", "inter.broker.protocol.version"]
            found_deprecated = [d for d in deprecated if d in config]
            
            if found_deprecated:
                results.append(PreflightResult(
                    name="Deprecated Settings",
                    status="warn",
                    message=f"Deprecated settings found: {', '.join(found_deprecated)}",
                    details="These should be removed before or during upgrade",
                ))
            else:
                results.append(PreflightResult(
                    name="Deprecated Settings",
                    status="pass",
                    message="No deprecated settings found",
                ))
        
        # Check ZooKeeper vs KRaft
        has_zk = "zookeeper.connect" in config
        has_kraft = "process.roles" in config
        has_migration = "zookeeper.metadata.migration.enable" in config
        
        if has_zk and not has_kraft and not has_migration:
            results.append(PreflightResult(
                name="Metadata Mode",
                status="warn",
                message="ZooKeeper mode detected. Consider migrating to KRaft.",
                details="ZooKeeper is deprecated in 8.x. Plan KRaft migration.",
            ))
        elif has_zk and has_kraft and has_migration:
            results.append(PreflightResult(
                name="Metadata Mode",
                status="pass",
                message="Migration mode configured (ZK → KRaft)",
            ))
        elif has_kraft and not has_zk:
            results.append(PreflightResult(
                name="Metadata Mode",
                status="pass",
                message="KRaft mode active",
            ))
        
        return results

    def generate_recommendations(self) -> List[str]:
        """Generate upgrade recommendations."""
        recs = []
        
        # Always recommend backup
        recs.append("Create full backup of configurations and ZooKeeper/KRaft data before upgrade")
        
        # Version-specific recommendations
        if self.target_version.startswith("8."):
            recs.append("Verify Java 17+ is installed on all nodes")
            recs.append("Review Confluent 8.x release notes for breaking changes")
            recs.append("Plan for ZooKeeper to KRaft migration if not already using KRaft")
            recs.append("Remove 'log.message.format.version' and 'inter.broker.protocol.version' settings")
        
        # General recommendations
        recs.append("Test upgrade in non-production environment first")
        recs.append("Schedule upgrade during low-traffic period")
        recs.append("Prepare rollback plan and verify backup restorability")
        recs.append("Monitor cluster metrics during and after upgrade")
        
        return recs

    def run_checks(self, skip_cluster: bool = False) -> PreflightReport:
        """Run all pre-flight checks."""
        print("🔍 Running upgrade pre-flight checks...")
        print(f"   Current: {self.current_version} → Target: {self.target_version}")
        print()
        
        # Upgrade path
        print("  ├── Checking upgrade path...")
        path_result = self.check_upgrade_path()
        self._categorize_result(path_result)
        
        # Java version
        print("  ├── Checking Java version...")
        java_result = self.check_java_version()
        self._categorize_result(java_result)
        
        # Configuration
        print("  ├── Checking configuration...")
        config_results = self.check_config_compatibility()
        for result in config_results:
            self._categorize_result(result)
        
        # Cluster health
        if not skip_cluster:
            print("  ├── Checking cluster health...")
            health_results = self.check_cluster_health()
            for result in health_results:
                self._categorize_result(result)
        
        # Generate recommendations
        print("  └── Generating recommendations...")
        self.report.recommendations = self.generate_recommendations()
        
        # Determine overall status
        if self.report.blockers:
            self.report.overall_status = "blocked"
        elif self.report.warnings:
            self.report.overall_status = "warnings"
        else:
            self.report.overall_status = "ready"
        
        return self.report

    def _categorize_result(self, result: PreflightResult) -> None:
        """Categorize result into blockers, warnings, or passed."""
        if result.status == "fail":
            self.report.blockers.append(result)
        elif result.status == "warn":
            self.report.warnings.append(result)
        elif result.status == "pass":
            self.report.passed.append(result)


def print_report(report: PreflightReport, as_json: bool = False) -> None:
    """Print the pre-flight report."""
    if as_json:
        output = {
            "current_version": report.current_version,
            "target_version": report.target_version,
            "overall_status": report.overall_status,
            "blockers": [{"name": r.name, "message": r.message, "details": r.details} for r in report.blockers],
            "warnings": [{"name": r.name, "message": r.message, "details": r.details} for r in report.warnings],
            "passed": [{"name": r.name, "message": r.message} for r in report.passed],
            "recommendations": report.recommendations,
        }
        print(json.dumps(output, indent=2))
        return
    
    print("\n" + "=" * 60)
    print("📋 UPGRADE PRE-FLIGHT REPORT")
    print("=" * 60)
    print(f"   From: Confluent {report.current_version}")
    print(f"   To:   Confluent {report.target_version}")
    print(f"   Status: {'🟢 READY' if report.overall_status == 'ready' else '🟡 WARNINGS' if report.overall_status == 'warnings' else '🔴 BLOCKED'}")
    print()
    
    if report.blockers:
        print("❌ BLOCKERS (must resolve before upgrade):")
        for r in report.blockers:
            print(f"   • {r.name}: {r.message}")
            if r.details:
                print(f"     → {r.details}")
        print()
    
    if report.warnings:
        print("⚠️ WARNINGS (review before upgrade):")
        for r in report.warnings:
            print(f"   • {r.name}: {r.message}")
            if r.details:
                print(f"     → {r.details}")
        print()
    
    if report.passed:
        print("✅ PASSED:")
        for r in report.passed:
            print(f"   • {r.name}: {r.message}")
        print()
    
    print("📝 RECOMMENDATIONS:")
    for i, rec in enumerate(report.recommendations, 1):
        print(f"   {i}. {rec}")
    print()
    
    print("=" * 60)
    if report.overall_status == "ready":
        print("✅ Cluster is ready for upgrade. Proceed with caution.")
    elif report.overall_status == "warnings":
        print("⚠️ Cluster can be upgraded, but review warnings first.")
    else:
        print("🛑 DO NOT PROCEED. Resolve blockers before upgrade.")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Confluent Kafka Upgrade Pre-flight Check",
    )
    parser.add_argument(
        "--current-version", "-c",
        required=True,
        help="Current Confluent Platform version (e.g., 7.6)",
    )
    parser.add_argument(
        "--target-version", "-t",
        required=True,
        help="Target Confluent Platform version (e.g., 8.0)",
    )
    parser.add_argument(
        "--bootstrap-servers", "-b",
        help="Bootstrap servers for cluster checks",
    )
    parser.add_argument(
        "--config",
        help="Path to server.properties for config validation",
    )
    parser.add_argument(
        "--skip-cluster",
        action="store_true",
        help="Skip cluster health checks",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    
    args = parser.parse_args()
    
    checker = UpgradePreflight(
        current_version=args.current_version,
        target_version=args.target_version,
        bootstrap_servers=args.bootstrap_servers,
        config_path=args.config,
    )
    
    report = checker.run_checks(skip_cluster=args.skip_cluster)
    print_report(report, args.json)
    
    # Exit codes
    if report.overall_status == "blocked":
        sys.exit(4)
    elif report.overall_status == "warnings":
        sys.exit(3)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
