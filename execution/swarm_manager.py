#!/usr/bin/env python3
"""
Swarm Manager (MoE Dispatch Router)

Dynamically splits a complex master prompt into parallel sub-tasks, assigns them
to specialized local/cloud Expert sub-agents (via task_router), and synthesizes
the result. This implements the "Multi-Agent MoE Architecture" trend.
"""

import sys
import json
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_command(cmd_args):
    """Executes a command and returns the output."""
    try:
        # Check output to capture everything
        result = subprocess.run(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Return the error output if the command fails
        return f"ERROR: {e.stderr.strip()}"

def run_subtask(subtask):
    """Worker function to route and execute a specific subtask."""
    step = subtask.get("step", 0)
    task_text = subtask.get("task", "")
    route = subtask.get("route", "unknown")
    
    print(f"[{route.upper()}] 🐝 Expert #{step} spinning up for: '{task_text}'")
    
    # 🌟 Route and Execute! (task_router automatically executes local or delegates cloud)
    # Using --json output if it exists, otherwise parsing standard output
    output = run_command(["python3", "execution/task_router.py", "route", "--task", task_text])
    
    return {
        "step": step,
        "task": task_text,
        "route": route,
        "result": output
    }

def synthesize_results(master_task, completed_tasks):
    """Passes the raw reports to the Cloud Orchestrator (the IDE Agent) for synthesis."""
    print(f"\n🧠 Preparing synthesis payload from {len(completed_tasks)} Experts...")
    
    # Bundle the completed outputs into a format the IDE Agent can read
    context_blocks = []
    for ct in completed_tasks:
        context_blocks.append(f"--- EXPERT {ct['step']} ({ct['route'].upper()}) ---\nTask: {ct['task']}\nOutput: {ct['result']}\n")
    
    context_str = "\n".join(context_blocks)
    
    synthesis_payload = (
        f"==== ORCHESTRATOR SYNTHESIS REQUIRED ====\n"
        f"The Swarm has completed its parallel execution. Please read the following expert outputs "
        f"and provide the final synthesis to the user.\n\n"
        f"Master Task: '{master_task}'\n\n"
        f"{context_str}\n"
        f"=========================================\n"
    )
    
    # Output is consumed by the active AI Agent reading the terminal!
    return synthesis_payload

def main():
    parser = argparse.ArgumentParser(description="Swarm Manager - MoE Dispatch Router")
    parser.add_argument("--task", type=str, required=True, help="Master complex task to distribute")
    parser.add_argument("--max-workers", type=int, default=5, help="Max parallel expert agents")
    args = parser.parse_args()

    print(f"🚀 Master Task Received: '{args.task}'")
    
    # 0. MEMORY-FIRST PROTOCOL (Qdrant Cache)
    print("🔍 Checking Qdrant Hybrid Memory cache...")
    try:
        mem_output = run_command(["python3", "execution/memory_manager.py", "auto", "--query", args.task])
        if "{" in mem_output:
            mem_data = json.loads(mem_output[mem_output.find("{"):])
            
            # FAST-PATH: Exact cache hit
            if mem_data.get("cache_hit") and mem_data.get("cached_response"):
                print("⚡ QDRANT CACHE HIT: Master task was already solved! Bypassing Swarm.")
                print("\n" + "="*60)
                print("🐝 CACHED SWARM SYNTHESIS")
                print("="*60)
                print(mem_data["cached_response"])
                
                with open(".tmp/swarm_synthesis.md", "w") as f:
                    f.write("# MoE Swarm Execution Report (CACHED)\n\n")
                    f.write(f"**Master Task:** `{args.task}`\n\n")
                    f.write("## Synthesis (Retrieved from Qdrant Memory)\n")
                    f.write(mem_data["cached_response"])
                sys.exit(0)
                
    except Exception as e:
        print(f"⚠️ Memory lookup failed ({e}), continuing without cache.")

    print(f"🧩 Dynamically splitting Master Task...")
    
    # 1. Ask task_router to geometrically split the compound task
    split_output = run_command(["python3", "execution/task_router.py", "split", "--task", args.task])
    
    try:
        # Find the JSON block in the split output (in case there are other logs)
        if "{" in split_output:
            json_str = split_output[split_output.find("{"):]
            split_data = json.loads(json_str)
        else:
            raise ValueError("No JSON found in task_router split output")
    except Exception as e:
        print(f"❌ Failed to parse task split: {e}")
        print("Raw Output:", split_output)
        sys.exit(1)
        
    subtasks = split_data.get("subtasks", [])
    if not subtasks:
        print("⚠️ No subtasks discovered. Try a more complex prompt.")
        sys.exit(0)
        
    print(f"📊 Decomposed into {len(subtasks)} sub-tasks ({split_data.get('local_count', 0)} local, {split_data.get('cloud_count', 0)} cloud)")
    
    # 2. Dispatch the Swarm in Parallel
    completed_tasks = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        # submit all tasks
        futures = {executor.submit(run_subtask, t): t for t in subtasks}
        
        for future in as_completed(futures):
            subtask = futures[future]
            try:
                result = future.result()
                completed_tasks.append(result)
                print(f"✅ Expert #{result['step']} completed its objective!")
            except Exception as exc:
                print(f"❌ Expert #{subtask.get('step')} generated an exception: {exc}")
                completed_tasks.append({
                    "step": subtask.get("step"),
                    "task": subtask.get("task"),
                    "route": subtask.get("route"),
                    "result": f"ERROR: Thread crashed - {exc}"
                })
                
    # Sort completed tasks by original step order
    completed_tasks.sort(key=lambda x: x["step"])
    
    # 3. Synchronize and Synthesize
    final_report = synthesize_results(args.task, completed_tasks)
    
    print("\n" + "="*60)
    print("🐝 SWARM SYNTHESIS COMPLETE")
    print("="*60)
    print(final_report)
    
    # Write to a determinable output file
    with open(".tmp/swarm_synthesis.md", "w") as f:
        f.write("# MoE Swarm Execution Report\n\n")
        f.write(f"**Master Task:** `{args.task}`\n\n")
        f.write("## Synthesis\n")
        f.write(final_report)
        f.write("\n\n## Expert Raw Outputs\n")
        for ct in completed_tasks:
            f.write(f"### Expert #{ct['step']} ({ct['route']})\n")
            f.write(f"**Task:** {ct['task']}\n\n```\n{ct['result']}\n```\n\n")

if __name__ == "__main__":
    main()
