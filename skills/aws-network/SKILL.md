---
name: aws-network
description: AWS network troubleshooting and analysis via MCP. Use for path tracing, flow log analysis, Transit Gateway/Cloud WAN routing, VPC connectivity issues, Network Firewall rules, and VPN connections. Read-only operations for safe troubleshooting.
---

# AWS Network Skill

> Part of the [AWS skill family](../aws/SKILL.md). For resource management, see [aws-ccapi](../aws-ccapi/SKILL.md).

AWS network troubleshooting and analysis — VPC, Transit Gateway, Cloud WAN.

## MCP Server Setup

```json
{
  "mcpServers": {
    "network": {
      "command": "uvx",
      "args": ["awslabs.aws-network-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "eu-west-1"
      }
    }
  }
}
```

## Features

- **Path Tracing** — Systematic network troubleshooting methodology
- **Flow Log Analysis** — Query VPC, TGW, Network Firewall logs
- **Multi-Region Search** — Find resources across all regions
- **Inspection Detection** — Identify firewalls in traffic paths
- **Read-Only** — Safe troubleshooting, no config changes

## MCP Tools

### General Tools

| Tool                         | Description                               |
| ---------------------------- | ----------------------------------------- |
| `get_path_trace_methodology` | Troubleshooting methodology (call first!) |
| `find_ip_address`            | Locate ENI by IP across regions           |
| `get_eni_details`            | ENI details with SGs, NACLs, routing      |

### VPC Tools

| Tool                      | Description              |
| ------------------------- | ------------------------ |
| `list_vpcs`               | List all VPCs in region  |
| `get_vpc_network_details` | Comprehensive VPC config |
| `get_vpc_flow_logs`       | Query VPC flow logs      |

### Transit Gateway Tools

| Tool                    | Description                |
| ----------------------- | -------------------------- |
| `list_transit_gateways` | List all TGWs              |
| `get_tgw_details`       | TGW configuration          |
| `get_tgw_routes`        | Routes from specific table |
| `get_all_tgw_routes`    | All route tables           |
| `get_tgw_flow_logs`     | TGW flow logs              |
| `detect_tgw_inspection` | Find firewalls on TGW      |

### Cloud WAN Tools

| Tool                              | Description              |
| --------------------------------- | ------------------------ |
| `list_core_networks`              | List Cloud WAN networks  |
| `get_cloudwan_details`            | Core network config      |
| `get_cloudwan_routes`             | Routes by segment/region |
| `detect_cloudwan_inspection`      | Find NFG inspections     |
| `simulate_cloud_wan_route_change` | Simulate changes         |

### Network Firewall Tools

| Tool                             | Description              |
| -------------------------------- | ------------------------ |
| `list_network_firewalls`         | List all firewalls       |
| `get_firewall_rules`             | Stateless/stateful rules |
| `get_network_firewall_flow_logs` | Firewall logs            |

### VPN Tools

| Tool                   | Description                  |
| ---------------------- | ---------------------------- |
| `list_vpn_connections` | Site-to-Site VPN connections |

## Workflows

### 1. Troubleshoot Connectivity

```
Always start with:
→ get_path_trace_methodology
→ Follow systematic approach
→ Use find_ip_address to locate ENIs
→ get_eni_details for security analysis
```

### 2. Analyze Traffic

```
Ask: "Why can't EC2 reach the database?"
→ get_path_trace_methodology
→ find_ip_address for both endpoints
→ get_vpc_flow_logs to check traffic
→ Analyze SGs, NACLs, routes
```

### 3. TGW Routing Issues

```
Ask: "Check Transit Gateway routing"
→ get_all_tgw_routes
→ detect_tgw_inspection
→ get_tgw_flow_logs
```

## Scripts

| Script                     | Purpose                   |
| -------------------------- | ------------------------- |
| `scripts/configure_mcp.py` | Auto-configure MCP client |

## References

- [AWS Network MCP Server](https://awslabs.github.io/mcp/servers/aws-network-mcp-server)
