#!/usr/bin/env python3
"""
Confluent Kafka Configuration Validator

Validates Kafka broker server.properties for:
- Required settings presence
- Deprecated configuration detection
- Version-specific compatibility
- Security best practices
- Performance recommendations

Usage:
    python validate_config.py --config /opt/confluent/etc/kafka/server.properties --version 8.0
    python validate_config.py --compare broker-01:config1.properties broker-02:config2.properties

Arguments:
    --config, -c         Path to server.properties file to validate
    --version, -v        Target Confluent version (7.x, 8.x) for compatibility checks
    --compare            Compare configurations between brokers
    --strict             Enable strict mode (fail on warnings)
    --json               Output results as JSON

Exit Codes:
    0 - Valid configuration
    1 - Invalid arguments
    2 - Configuration file not found
    3 - Validation errors found
    4 - Critical errors (deprecated or incompatible settings)
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Deprecated settings by version
DEPRECATED_SETTINGS = {
    "8.0": [
        "log.message.format.version",
        "inter.broker.protocol.version",
        "kafka.metrics.reporters",  # Renamed
        "broker.id.generation.enable",  # KRaft handles this
    ],
    "7.6": [
        "kafka.metrics.reporters",
    ],
}

# Required settings for KRaft mode
KRAFT_REQUIRED = [
    "process.roles",
    "node.id",
    "controller.quorum.voters",
    "controller.listener.names",
]

# Required settings for any production broker
PRODUCTION_REQUIRED = [
    "log.dirs",
    "listeners",
    "advertised.listeners",
]

# Security best practices
SECURITY_RECOMMENDED = {
    "authorizer.class.name": "kafka.security.authorizer.AclAuthorizer",
    "ssl.keystore.location": None,  # Just check existence
    "ssl.truststore.location": None,
    "sasl.enabled.mechanisms": None,
}

# Performance recommendations
PERFORMANCE_DEFAULTS = {
    "num.network.threads": ("8", "Should be at least 8 for production"),
    "num.io.threads": ("16", "Should be 2x network threads or more"),
    "socket.send.buffer.bytes": ("102400", "Increase for high throughput"),
    "socket.receive.buffer.bytes": ("102400", "Increase for high throughput"),
    "num.replica.fetchers": ("4", "Increase for faster replication"),
}


class ConfigValidator:
    """Validates Kafka broker configuration."""

    def __init__(self, config_path: str, version: str = "8.0"):
        self.config_path = Path(config_path)
        self.version = version
        self.config: Dict[str, str] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def load_config(self) -> bool:
        """Load and parse the configuration file."""
        if not self.config_path.exists():
            self.errors.append(f"Configuration file not found: {self.config_path}")
            return False

        try:
            with open(self.config_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue
                    # Parse key=value
                    if "=" in line:
                        key, value = line.split("=", 1)
                        self.config[key.strip()] = value.strip()
            return True
        except Exception as e:
            self.errors.append(f"Failed to parse config: {e}")
            return False

    def check_deprecated(self) -> None:
        """Check for deprecated settings."""
        deprecated = DEPRECATED_SETTINGS.get(self.version, [])
        for setting in deprecated:
            if setting in self.config:
                self.errors.append(
                    f"DEPRECATED: '{setting}' is deprecated in version {self.version}. "
                    f"Current value: {self.config[setting]}"
                )

    def check_kraft_mode(self) -> None:
        """Check KRaft mode configuration."""
        # Check if using KRaft
        if "process.roles" in self.config:
            self.info.append("KRaft mode detected")
            
            # Verify required KRaft settings
            for setting in KRAFT_REQUIRED:
                if setting not in self.config:
                    self.errors.append(f"MISSING: Required KRaft setting '{setting}'")
            
            # Check for conflicting ZooKeeper settings
            if "zookeeper.connect" in self.config and "zookeeper.metadata.migration.enable" not in self.config:
                self.errors.append(
                    "CONFLICT: 'zookeeper.connect' present without 'zookeeper.metadata.migration.enable'. "
                    "Either remove ZK config or enable migration mode."
                )
            
            # Validate process.roles
            roles = self.config.get("process.roles", "")
            valid_roles = {"broker", "controller", "broker,controller", "controller,broker"}
            if roles not in valid_roles:
                self.errors.append(f"INVALID: 'process.roles' must be one of {valid_roles}")
        else:
            # ZooKeeper mode
            if "zookeeper.connect" in self.config:
                self.warnings.append(
                    "ZooKeeper mode detected. Consider migrating to KRaft for version 8.x+"
                )
            else:
                self.errors.append(
                    "MISSING: Neither 'process.roles' (KRaft) nor 'zookeeper.connect' (ZK) found"
                )

    def check_required(self) -> None:
        """Check for required production settings."""
        for setting in PRODUCTION_REQUIRED:
            if setting not in self.config:
                self.errors.append(f"MISSING: Required setting '{setting}'")

    def check_security(self) -> None:
        """Check security best practices."""
        # Check for authentication
        if "sasl.enabled.mechanisms" not in self.config and "ssl.keystore.location" not in self.config:
            self.warnings.append(
                "SECURITY: No authentication configured (SASL or SSL client auth)"
            )
        
        # Check for authorization
        if "authorizer.class.name" not in self.config:
            self.warnings.append(
                "SECURITY: No authorizer configured. Consider enabling ACLs."
            )
        
        # Check for TLS
        if "ssl.keystore.location" not in self.config:
            self.warnings.append(
                "SECURITY: SSL/TLS not configured for broker"
            )
        
        # Check super.users
        if "super.users" not in self.config and "authorizer.class.name" in self.config:
            self.warnings.append(
                "SECURITY: 'super.users' not set while ACLs enabled. "
                "Ensure admin access is configured."
            )

    def check_performance(self) -> None:
        """Check performance recommendations."""
        for setting, (recommended, reason) in PERFORMANCE_DEFAULTS.items():
            if setting in self.config:
                try:
                    current = int(self.config[setting])
                    rec = int(recommended)
                    if current < rec:
                        self.info.append(
                            f"PERF: '{setting}' is {current}, recommended: {rec}. {reason}"
                        )
                except ValueError:
                    pass
            else:
                self.info.append(f"PERF: '{setting}' not set. Default may be suboptimal.")

    def check_listeners(self) -> None:
        """Validate listener configuration."""
        listeners = self.config.get("listeners", "")
        advertised = self.config.get("advertised.listeners", "")
        security_map = self.config.get("listener.security.protocol.map", "")
        
        # Parse listeners
        listener_names = set()
        for listener in listeners.split(","):
            if "://" in listener:
                name = listener.split("://")[0]
                listener_names.add(name)
        
        # Check advertised.listeners matches
        if advertised:
            for listener in advertised.split(","):
                if "://" in listener:
                    name = listener.split("://")[0]
                    if name not in listener_names:
                        self.errors.append(
                            f"MISMATCH: Advertised listener '{name}' not in listeners"
                        )
        
        # Check security protocol map
        if listener_names and security_map:
            mapped_names = set()
            for mapping in security_map.split(","):
                if ":" in mapping:
                    name = mapping.split(":")[0]
                    mapped_names.add(name)
            
            unmapped = listener_names - mapped_names
            if unmapped:
                self.errors.append(
                    f"MISMATCH: Listeners {unmapped} not in security protocol map"
                )

    def check_replication(self) -> None:
        """Check replication settings."""
        rf = self.config.get("default.replication.factor", "1")
        min_isr = self.config.get("min.insync.replicas", "1")
        
        try:
            if int(rf) < 3:
                self.warnings.append(
                    f"DURABILITY: 'default.replication.factor' is {rf}. "
                    f"Recommended: 3 for production."
                )
            
            if int(min_isr) < 2:
                self.warnings.append(
                    f"DURABILITY: 'min.insync.replicas' is {min_isr}. "
                    f"Recommended: 2 for production with RF>=3."
                )
        except ValueError:
            pass

    def validate(self) -> Dict:
        """Run all validation checks."""
        if not self.load_config():
            return self.get_results()
        
        self.check_deprecated()
        self.check_kraft_mode()
        self.check_required()
        self.check_listeners()
        self.check_security()
        self.check_replication()
        self.check_performance()
        
        return self.get_results()

    def get_results(self) -> Dict:
        """Get validation results."""
        status = "valid"
        if self.errors:
            status = "invalid"
        elif self.warnings:
            status = "warnings"
        
        return {
            "config_path": str(self.config_path),
            "version": self.version,
            "status": status,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "settings_count": len(self.config),
        }


def compare_configs(configs: List[str]) -> Dict:
    """Compare configurations between multiple brokers."""
    parsed = {}
    differences = []
    
    for config_spec in configs:
        if ":" in config_spec:
            name, path = config_spec.split(":", 1)
        else:
            name = Path(config_spec).stem
            path = config_spec
        
        validator = ConfigValidator(path)
        if validator.load_config():
            parsed[name] = validator.config
    
    if len(parsed) < 2:
        return {"error": "Need at least 2 valid configs to compare"}
    
    # Find all unique keys
    all_keys = set()
    for config in parsed.values():
        all_keys.update(config.keys())
    
    # Compare each key
    for key in sorted(all_keys):
        values = {}
        for name, config in parsed.items():
            values[name] = config.get(key, "<not set>")
        
        unique_values = set(values.values())
        if len(unique_values) > 1:
            differences.append({
                "setting": key,
                "values": values,
            })
    
    return {
        "configs": list(parsed.keys()),
        "differences": differences,
        "identical_settings": len(all_keys) - len(differences),
    }


def print_results(results: Dict, as_json: bool = False) -> None:
    """Print validation results."""
    if as_json:
        print(json.dumps(results, indent=2))
        return
    
    print(f"\n📋 Configuration Validation: {results['config_path']}")
    print(f"   Target Version: {results['version']}")
    print(f"   Settings Count: {results['settings_count']}")
    print(f"   Status: {'✅ ' + results['status'].upper() if results['status'] == 'valid' else '⚠️ ' + results['status'].upper() if results['status'] == 'warnings' else '❌ ' + results['status'].upper()}")
    print()
    
    if results["errors"]:
        print("❌ Errors:")
        for error in results["errors"]:
            print(f"   • {error}")
        print()
    
    if results["warnings"]:
        print("⚠️ Warnings:")
        for warning in results["warnings"]:
            print(f"   • {warning}")
        print()
    
    if results["info"]:
        print("ℹ️ Recommendations:")
        for info in results["info"]:
            print(f"   • {info}")
        print()


def print_comparison(results: Dict, as_json: bool = False) -> None:
    """Print comparison results."""
    if as_json:
        print(json.dumps(results, indent=2))
        return
    
    if "error" in results:
        print(f"❌ {results['error']}")
        return
    
    print(f"\n📋 Configuration Comparison")
    print(f"   Brokers: {', '.join(results['configs'])}")
    print(f"   Identical Settings: {results['identical_settings']}")
    print(f"   Differences: {len(results['differences'])}")
    print()
    
    if results["differences"]:
        print("🔍 Differences:")
        for diff in results["differences"]:
            print(f"\n   {diff['setting']}:")
            for broker, value in diff["values"].items():
                print(f"      {broker}: {value}")


def main():
    parser = argparse.ArgumentParser(
        description="Confluent Kafka Configuration Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to server.properties file to validate",
    )
    parser.add_argument(
        "--version", "-v",
        default="8.0",
        help="Target Confluent version (default: 8.0)",
    )
    parser.add_argument(
        "--compare",
        nargs="+",
        help="Compare configurations (format: name:path or just path)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings (exit code 3)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    
    args = parser.parse_args()
    
    if args.compare:
        results = compare_configs(args.compare)
        print_comparison(results, args.json)
        sys.exit(0 if not results.get("differences") else 3)
    
    if not args.config:
        parser.error("--config is required when not using --compare")
    
    validator = ConfigValidator(args.config, args.version)
    results = validator.validate()
    print_results(results, args.json)
    
    # Exit codes
    if results["status"] == "invalid":
        sys.exit(4 if any("DEPRECATED" in e for e in results["errors"]) else 3)
    elif results["status"] == "warnings" and args.strict:
        sys.exit(3)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
