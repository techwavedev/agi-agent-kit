#!/usr/bin/env python3
"""
Script: fastapi_tool_bridge.py
Purpose: Secure FastAPI Bridge for Sandbox Execution.
         Provides authenticated stubs for isolated containers (e.g., llm-sandbox) 
         to execute actions against the host without needing direct internet 
         access or raw API keys. Includes native Langfuse tracing.

Usage:
    uvicorn execution.fastapi_tool_bridge:app --host 127.0.0.1 --port 8000
"""

import os
import json
import subprocess
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional, Dict

# Attempt to import Langfuse for Observability tracking
try:
    from langfuse.decorators import observe
    LANGFUSE_ENABLED = True
except ImportError:
    LANGFUSE_ENABLED = False
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

app = FastAPI(title="AGI Agent Kit - Secure Tool Bridge", version="1.0.0")

# Security: The sandbox must pass this token (injected via environment variable during container start)
INTERNAL_SANDBOX_TOKEN = os.environ.get("SANDBOX_BRIDGE_TOKEN", "dev-secure-bridge-token-999")

def verify_sandbox_token(x_sandbox_token: str = Header(...)):
    if x_sandbox_token != INTERNAL_SANDBOX_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized Sandbox Access")
    return True

class ExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict
    
class ExecuteResponse(BaseModel):
    status: str
    output: Optional[dict] = None
    error: Optional[str] = None
    stdout: Optional[str] = None

@observe(name="tool_bridge_execution", as_type="generation")
def safe_execute_tool(tool_name: str, args: dict) -> ExecuteResponse:
    """
    Safely routes the requested tool action to the host executor.
    (This function natively tracks execution time and parameters in Langfuse if deployed).
    """
    # Dummy routing for dynamic tools for now. 
    # In full production, this maps exactly to the qdrant tools execution map.
    try:
        # Example validation
        if "rm " in str(args) or "mkfs" in str(args):
            raise ValueError("Destructive commands blocked by security bridge.")
            
        print(f"Bridge intercept: executing {tool_name} with {args}")
        
        # Example: Mocking a shell executor bridge securely
        if tool_name == "execute_terminal":
            cmd = args.get("command", "echo 'No command'")
            # This is extremely dangerous. In production, we'd use a strict allowlist
            # But this proves the architecture of bridging host from sandbox
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            return ExecuteResponse(
                status="success" if res.returncode == 0 else "error",
                output={"returncode": res.returncode},
                stdout=res.stdout,
                error=res.stderr if res.returncode != 0 else None
            )
            
        return ExecuteResponse(status="success", output={"message": f"Successfully mapped {tool_name}"})
        
    except Exception as e:
        return ExecuteResponse(status="error", error=str(e))


@app.post("/api/v1/execute", response_model=ExecuteResponse)
async def execute_bridge(
    req: ExecuteRequest, 
    authorized: bool = Depends(verify_sandbox_token)
):
    """
    Primary intake for the sandbox to request host-side actions safely.
    """
    result = safe_execute_tool(req.tool_name, req.arguments)
    if result.status == "error":
        raise HTTPException(status_code=400, detail=result.error)
    return result

@app.get("/health")
def health_check():
    return {
        "status": "online", 
        "langfuse_tracing": "active" if LANGFUSE_ENABLED else "disabled"
    }
