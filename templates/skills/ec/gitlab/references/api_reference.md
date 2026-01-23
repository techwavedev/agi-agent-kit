# GitLab API Reference

API endpoints for managing GitLab Kubernetes agents, tokens, and projects. All operations can be performed by project owners/maintainers — no GitLab admin access required.

---

## Authentication

All API requests require a Personal Access Token or Project Access Token:

```bash
export GITLAB_HOST="gitlab.example.com"
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"

# Include in requests
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/..."
```

### Required Token Scopes

| Operation              | Required Scopes     |
| ---------------------- | ------------------- |
| List/view agents       | `api` or `read_api` |
| Register/delete agents | `api`               |
| Manage tokens          | `api`               |
| Project management     | `api`               |
| GitOps (Flux access)   | `read_repository`   |

---

## Kubernetes Agent API

### List Agents for a Project

List all agents registered in a project.

**Minimum Role:** Developer

```bash
GET /projects/:id/cluster_agents
```

**Example:**

```bash
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents" | jq
```

**Response:**

```json
[
  {
    "id": 1,
    "name": "eks-nonprod-agent",
    "config_project": {
      "id": 20,
      "name": "kubernetes-agents",
      "path_with_namespace": "infrastructure/kubernetes-agents"
    },
    "created_at": "2026-01-15T10:00:00.000Z",
    "created_by_user_id": 42
  }
]
```

---

### Get Agent Details

Get details of a specific agent.

**Minimum Role:** Developer

```bash
GET /projects/:id/cluster_agents/:agent_id
```

**Example:**

```bash
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}" | jq
```

---

### Register an Agent

Register a new agent with the project.

**Minimum Role:** Maintainer

```bash
POST /projects/:id/cluster_agents
```

**Body:**

```json
{
  "name": "eks-nonprod-agent"
}
```

**Example:**

```bash
curl --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --url "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents" \
  --data '{"name":"eks-nonprod-agent"}' | jq
```

**Response:**

```json
{
  "id": 1,
  "name": "eks-nonprod-agent",
  "config_project": {
    "id": 20,
    "name": "kubernetes-agents",
    "path_with_namespace": "infrastructure/kubernetes-agents"
  },
  "created_at": "2026-01-21T12:00:00.000Z",
  "created_by_user_id": 42
}
```

**Next Step:** Create a token for the agent to actually connect.

---

### Delete an Agent

Delete an agent registration. This does NOT uninstall the agent from the cluster.

**Minimum Role:** Maintainer

```bash
DELETE /projects/:id/cluster_agents/:agent_id
```

**Example:**

```bash
curl --request DELETE \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}"
```

**Important:** After deleting from GitLab, also uninstall from cluster:

```bash
helm uninstall gitlab-agent --namespace gitlab-agent
```

---

## Agent Token API

### List Tokens for an Agent

List all active tokens for an agent. Maximum 2 active tokens allowed.

**Minimum Role:** Developer

```bash
GET /projects/:id/cluster_agents/:agent_id/tokens
```

**Example:**

```bash
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens" | jq
```

**Response:**

```json
[
  {
    "id": 1,
    "name": "initial-token",
    "description": "Initial installation token",
    "agent_id": 1,
    "status": "active",
    "created_at": "2026-01-21T12:00:00.000Z",
    "created_by_user_id": 42
  }
]
```

---

### Get Single Token

Get details of a specific token, including last used time.

**Minimum Role:** Developer

```bash
GET /projects/:id/cluster_agents/:agent_id/tokens/:token_id
```

**Example:**

```bash
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens/1" | jq
```

**Response includes `last_used_at`:**

```json
{
  "id": 1,
  "name": "initial-token",
  "status": "active",
  "last_used_at": "2026-01-21T12:30:00.000Z",
  "created_at": "2026-01-21T12:00:00.000Z"
}
```

---

### Create Agent Token

Create a new token for agent authentication. **The token value is only returned once — save it immediately!**

**Minimum Role:** Maintainer

**Limit:** Maximum 2 active tokens per agent.

```bash
POST /projects/:id/cluster_agents/:agent_id/tokens
```

**Body:**

```json
{
  "name": "token-name",
  "description": "optional description"
}
```

**Example:**

```bash
TOKEN_RESPONSE=$(curl --silent --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --url "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens" \
  --data '{"name":"install-token","description":"EKS installation"}')

echo $TOKEN_RESPONSE | jq

# Extract token value (SAVE THIS!)
AGENT_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.token')
echo "Agent Token: ${AGENT_TOKEN}"
```

**Response:**

```json
{
  "id": 2,
  "name": "install-token",
  "description": "EKS installation",
  "agent_id": 1,
  "status": "active",
  "created_at": "2026-01-21T12:00:00.000Z",
  "created_by_user_id": 42,
  "last_used_at": null,
  "token": "glagent-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

---

### Revoke Token

Revoke (delete) a token. The agent will disconnect if this was its active token.

**Minimum Role:** Maintainer

```bash
DELETE /projects/:id/cluster_agents/:agent_id/tokens/:token_id
```

**Example:**

```bash
curl --request DELETE \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens/1"
```

---

## Project API

### Get Project ID

Find project ID by path.

```bash
# URL-encode the path (replace / with %2F)
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/infrastructure%2Fkubernetes-agents" | jq '.id'
```

Or search by name:

```bash
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects?search=kubernetes-agents" | jq '.[].id'
```

---

### List Projects

List projects you have access to.

```bash
GET /projects
```

**Useful parameters:**

| Parameter    | Description                            |
| ------------ | -------------------------------------- |
| `search`     | Search by name                         |
| `owned`      | Only your projects                     |
| `membership` | Projects you're a member of            |
| `per_page`   | Results per page (default 20, max 100) |

**Example:**

```bash
# List projects you own
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects?owned=true" | jq '.[].path_with_namespace'
```

---

### Get Project Details

```bash
GET /projects/:id
```

**Example:**

```bash
curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://${GITLAB_HOST}/api/v4/projects/${PROJECT_ID}" | jq
```

---

## Helper Scripts

### Full Agent Setup Script

Complete script based on API (project owner perspective):

```bash
#!/bin/bash
# gitlab-agent-setup.sh - Register agent and create token via API

set -e

# Configuration
GITLAB_HOST="${GITLAB_HOST:-gitlab.example.com}"
PROJECT_ID="${PROJECT_ID:-}"
AGENT_NAME="${AGENT_NAME:-eks-agent}"

# Validate inputs
if [ -z "$GITLAB_TOKEN" ]; then
  echo "Error: GITLAB_TOKEN must be set"
  exit 1
fi

if [ -z "$PROJECT_ID" ]; then
  echo "Error: PROJECT_ID must be set"
  exit 1
fi

API_URL="https://${GITLAB_HOST}/api/v4"

echo "=== Registering agent '${AGENT_NAME}' ==="

# Register agent
AGENT_RESPONSE=$(curl --silent --fail \
  --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --url "${API_URL}/projects/${PROJECT_ID}/cluster_agents" \
  --data "{\"name\":\"${AGENT_NAME}\"}")

AGENT_ID=$(echo $AGENT_RESPONSE | jq -r '.id')
echo "Agent ID: ${AGENT_ID}"

echo "=== Creating agent token ==="

# Create token
TOKEN_RESPONSE=$(curl --silent --fail \
  --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --url "${API_URL}/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens" \
  --data '{"name":"install-token","description":"Installation token"}')

AGENT_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.token')
echo "Agent Token: ${AGENT_TOKEN}"

echo ""
echo "=== Next Steps ==="
echo "1. Save this token securely (it cannot be retrieved again)"
echo "2. Install agent on EKS cluster:"
echo ""
echo "helm repo add gitlab https://charts.gitlab.io"
echo "helm repo update"
echo "helm upgrade --install gitlab-agent gitlab/gitlab-agent \\"
echo "  --namespace gitlab-agent \\"
echo "  --create-namespace \\"
echo "  --set config.token=\"${AGENT_TOKEN}\" \\"
echo "  --set config.kasAddress=\"wss://${GITLAB_HOST}/-/kubernetes-agent/\""
```

### Token Rotation Script

```bash
#!/bin/bash
# rotate-agent-token.sh - Rotate agent token with zero downtime

set -e

# Configuration
GITLAB_HOST="${GITLAB_HOST:-gitlab.example.com}"
PROJECT_ID="${PROJECT_ID:-}"
AGENT_ID="${AGENT_ID:-}"

API_URL="https://${GITLAB_HOST}/api/v4"

echo "=== Creating new token ==="
TOKEN_RESPONSE=$(curl --silent --fail \
  --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --url "${API_URL}/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens" \
  --data "{\"name\":\"rotation-$(date +%Y%m%d)\",\"description\":\"Token rotation\"}")

NEW_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.token')
echo "New token created"

echo "=== Updating agent deployment ==="
helm upgrade gitlab-agent gitlab/gitlab-agent \
  --namespace gitlab-agent \
  --reuse-values \
  --set config.token="${NEW_TOKEN}"

echo "=== Waiting for rollout ==="
kubectl rollout status deployment/gitlab-agent -n gitlab-agent

echo "=== Listing old tokens ==="
curl --silent \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "${API_URL}/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens" | \
  jq '.[] | select(.name != "rotation-'$(date +%Y%m%d)'") | {id, name}'

echo ""
echo "Manually revoke old tokens with:"
echo "curl --request DELETE --header \"PRIVATE-TOKEN: \${GITLAB_TOKEN}\" \\"
echo "  \"${API_URL}/projects/${PROJECT_ID}/cluster_agents/${AGENT_ID}/tokens/OLD_TOKEN_ID\""
```

---

## Error Handling

### Common API Errors

| HTTP Code | Meaning           | Solution                               |
| --------- | ----------------- | -------------------------------------- |
| 401       | Unauthorized      | Check token is valid and not expired   |
| 403       | Forbidden         | Need higher role (e.g., Maintainer)    |
| 404       | Not found         | Check project/agent ID exists          |
| 422       | Validation failed | Check request body (e.g., token limit) |

### Token Limit Error

```json
{
  "message": "An agent can have at most 2 active tokens"
}
```

**Solution:** Revoke an existing token before creating a new one.
