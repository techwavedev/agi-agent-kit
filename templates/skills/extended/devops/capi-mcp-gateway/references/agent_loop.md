# LLM Agent Loop with CAPI MCP Gateway

Pattern for building an LLM agent that discovers and invokes tools via CAPI's MCP endpoint.

---

## Full Python Implementation

```python
import requests
import json

BASE = "http://localhost:8383/mcp"
HEADERS = {"Content-Type": "application/json"}

class CapiMcpClient:
    """Client for CAPI MCP Gateway (JSON-RPC 2.0 over Streamable HTTP)."""

    def __init__(self, base_url=BASE, auth_token=None):
        self.base_url = base_url
        self.session_id = None
        self._req_id = 0
        self._extra = {}
        if auth_token:
            self._extra["Authorization"] = f"Bearer {auth_token}"

    def _next_id(self):
        self._req_id += 1
        return self._req_id

    def _call(self, method, params=None):
        body = {"jsonrpc": "2.0", "method": method, "id": self._next_id()}
        if params:
            body["params"] = params
        headers = {**HEADERS, **self._extra}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        resp = requests.post(self.base_url, json=body, headers=headers)
        resp.raise_for_status()
        if "Mcp-Session-Id" in resp.headers:
            self.session_id = resp.headers["Mcp-Session-Id"]
        data = resp.json()
        if "error" in data:
            raise McpError(data["error"]["code"], data["error"]["message"])
        return data["result"]

    def initialize(self):
        """Start session. Must be called first."""
        return self._call("initialize")

    def list_tools(self):
        """Return aggregated tool catalog."""
        return self._call("tools/list")["tools"]

    def call_tool(self, name, arguments):
        """Invoke a tool by name with arguments dict."""
        result = self._call("tools/call", {"name": name, "arguments": arguments})
        return result["content"][0]["text"]

    def ping(self):
        return self._call("ping")


class McpError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"MCP Error {code}: {message}")
```

---

## Agent Loop Pattern

Bridge LLM function-calling with CAPI MCP tool invocation:

```python
def agent_loop(user_message, mcp_client, llm):
    """
    1. Discover tools from CAPI
    2. Present as LLM function definitions
    3. Forward tool calls back to CAPI
    4. Feed results to LLM for final answer
    """
    # 1. Discover tools
    tools = mcp_client.list_tools()

    # 2. Present to LLM as function definitions
    llm_response = llm.chat(
        messages=[{"role": "user", "content": user_message}],
        tools=[{
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["inputSchema"]
            }
        } for t in tools]
    )

    # 3. If no tool call, return direct answer
    if not llm_response.tool_calls:
        return llm_response.content

    # 4. Execute tool calls via CAPI
    messages = [
        {"role": "user", "content": user_message},
        {"role": "assistant", "tool_calls": llm_response.tool_calls}
    ]
    for call in llm_response.tool_calls:
        result = mcp_client.call_tool(call.function.name,
                                       json.loads(call.function.arguments))
        messages.append({
            "role": "tool",
            "content": result,
            "tool_call_id": call.id
        })

    # 5. Final LLM response with tool results
    return llm.chat(messages=messages).content
```

### Usage

```python
from openai import OpenAI

llm = OpenAI()
mcp = CapiMcpClient(auth_token="<your-token>")
mcp.initialize()

answer = agent_loop("What is the status of order 12345?", mcp, llm)
print(answer)
```

---

## Multi-Turn Agent

For multi-turn conversations, cache the tool list and reuse the session:

```python
class CapiAgent:
    def __init__(self, mcp_url, auth_token, llm):
        self.mcp = CapiMcpClient(mcp_url, auth_token)
        self.mcp.initialize()
        self.tools = self.mcp.list_tools()
        self.llm = llm
        self.history = []

    def chat(self, user_message):
        self.history.append({"role": "user", "content": user_message})
        response = self.llm.chat(
            messages=self.history,
            tools=[{
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["inputSchema"]
                }
            } for t in self.tools]
        )

        while response.tool_calls:
            self.history.append({"role": "assistant", "tool_calls": response.tool_calls})
            for call in response.tool_calls:
                result = self.mcp.call_tool(
                    call.function.name,
                    json.loads(call.function.arguments)
                )
                self.history.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": call.id
                })
            response = self.llm.chat(messages=self.history, tools=[...])

        self.history.append({"role": "assistant", "content": response.content})
        return response.content
```

---

## SSE Streaming

For tools that declare streaming (via `mcp-streaming` metadata):

```python
import sseclient

def call_streaming_tool(mcp_client, tool_name, arguments):
    """Invoke a streaming tool and yield SSE events."""
    body = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": mcp_client._next_id(),
        "params": {"name": tool_name, "arguments": arguments}
    }
    headers = {
        **HEADERS,
        "Accept": "text/event-stream",
        "Mcp-Session-Id": mcp_client.session_id
    }
    resp = requests.post(mcp_client.base_url, json=body,
                         headers=headers, stream=True)
    client = sseclient.SSEClient(resp)
    for event in client.events():
        yield json.loads(event.data)
```

---

## Error Handling

```python
try:
    result = mcp.call_tool("orders.get", {"orderId": "123"})
except McpError as e:
    if e.code == -32602:
        print(f"Tool not found: {e.message}")
    elif e.code == -32000:
        print(f"Auth error: {e.message}")
    elif e.code == -32603:
        print(f"Backend error: {e.message}")
    else:
        print(f"MCP error ({e.code}): {e.message}")
```

| Code | Meaning | Recovery |
|------|---------|----------|
| `-32700` | Parse error | Fix JSON body |
| `-32600` | Invalid request | Check `jsonrpc` and `method` fields |
| `-32601` | Method not found | Use `initialize`, `tools/list`, `tools/call`, or `ping` |
| `-32602` | Invalid params | Verify tool name exists in `tools/list` |
| `-32603` | Internal error | Backend timeout — retry or increase `mcp-timeout` |
| `-32000` | Auth error | Refresh token or check OPA policy |
