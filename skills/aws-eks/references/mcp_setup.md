# EKS MCP Server Setup

## Overview

The Amazon EKS MCP Server is part of AWS Labs MCP Servers, providing AI-assisted Kubernetes cluster management through the Model Context Protocol.

**Source:** [awslabs/mcp](https://github.com/awslabs/mcp)

## Installation Methods

### Method 1: uvx (Recommended)

```bash
# Install uvx if not present
pip install uvx

# Run server directly
uvx awslabs.eks-mcp-server@latest
```

### Method 2: pip install

```bash
pip install awslabs.eks-mcp-server
eks-mcp-server
```

## Client Configuration

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "eks": {
      "command": "uvx",
      "args": [
        "awslabs.eks-mcp-server@latest",
        "--allow-write",
        "--allow-sensitive-data-access"
      ],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

### Cursor IDE

Edit `.cursor/mcp.json` in your project or `~/.cursor/mcp.json` globally:

```json
{
  "mcpServers": {
    "eks": {
      "command": "uvx",
      "args": ["awslabs.eks-mcp-server@latest", "--allow-write"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

### VS Code with Continue

Edit `.continue/config.json`:

```json
{
  "mcpServers": [
    {
      "name": "eks",
      "command": "uvx",
      "args": ["awslabs.eks-mcp-server@latest", "--allow-write"]
    }
  ]
}
```

## Configuration Flags

| Flag                            | Description                               | Default         |
| ------------------------------- | ----------------------------------------- | --------------- |
| `--allow-write`                 | Enable create, update, delete operations  | Disabled        |
| `--allow-sensitive-data-access` | Allow access to logs, secrets, configmaps | Disabled        |
| `--region`                      | Override AWS region                       | From env/config |
| `--profile`                     | AWS profile to use                        | default         |

## Environment Variables

```bash
# Required: AWS credentials (via profile or env vars)
AWS_PROFILE=default
AWS_REGION=us-east-1

# Or explicit credentials
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

## Verifying Setup

Once configured, ask the AI assistant:

- "List my EKS clusters"
- "Describe cluster X"
- "What pods are running in namespace Y?"

If the server is connected properly, it will use MCP tools to fetch real data.

## Troubleshooting

### Server not starting

```bash
# Test manually
uvx awslabs.eks-mcp-server@latest --help
```

### Authentication errors

```bash
# Verify AWS credentials
aws sts get-caller-identity
aws eks list-clusters --region <region>
```

### Permission denied

- Ensure IAM user/role has EKS permissions
- Check `--allow-write` flag is set for write operations

## Related MCP Servers

For comprehensive AWS management, consider adding:

```json
{
  "mcpServers": {
    "eks": { "...": "..." },
    "aws-api": {
      "command": "uvx",
      "args": ["awslabs.aws-api-mcp-server@latest"]
    },
    "cloudformation": {
      "command": "uvx",
      "args": ["awslabs.cfn-mcp-server@latest"]
    }
  }
}
```
