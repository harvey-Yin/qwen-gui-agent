"""
GUI Agent Benchmark Runner.
Runs predefined tasks against one or more VLM providers and produces scores.
"""
import json
import time
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from llm import create_client
from llm.base_client import VLMClient
from agent.orchestrator import Orchestrator, TaskResult


# ── Data classes ──────────────────────────────────────────────────────

@dataclass
class TaskScore:
    """Score for a single benchmark task."""
    task_id: str
    description: str
    completed: bool
    steps_used: int
    max_steps: int
    response_time: float          # total seconds
    json_parse_success_rate: float  # 0-1
    verified: bool                 # passed verification check


@dataclass
class BenchmarkReport:
    """Full benchmark report for one model."""
    model_name: str
    provider: str
    scores: List[TaskScore] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def task_completion_rate(self) -> float:
        if not self.scores:
            return 0.0
        return sum(1 for s in self.scores if s.completed) / len(self.scores)

    @property
    def verification_rate(self) -> float:
        if not self.scores:
            return 0.0
        return sum(1 for s in self.scores if s.verified) / len(self.scores)

    @property
    def avg_steps(self) -> float:
        completed = [s for s in self.scores if s.completed]
        if not completed:
            return 0.0
        return sum(s.steps_used for s in completed) / len(completed)

    @property
    def avg_response_time(self) -> float:
        if not self.scores:
            return 0.0
        return sum(s.response_time for s in self.scores) / len(self.scores)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "provider": self.provider,
            "timestamp": self.timestamp,
            "summary": {
                "task_completion_rate": round(self.task_completion_rate, 4),
                "verification_rate": round(self.verification_rate, 4),
                "avg_steps": round(self.avg_steps, 2),
                "avg_response_time_s": round(self.avg_response_time, 2),
            },
            "scores": [
                {
                    "task_id": s.task_id,
                    "description": s.description,
                    "completed": s.completed,
                    "verified": s.verified,
                    "steps_used": s.steps_used,
                    "max_steps": s.max_steps,
                    "response_time": round(s.response_time, 2),
                    "json_parse_rate": round(s.json_parse_success_rate, 4),
                }
                for s in self.scores
            ],
        }


# ── Verification helpers ──────────────────────────────────────────────

def _check_process_running(process_name: str) -> bool:
    """Check if a process is running on Windows."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {process_name}"],
            capture_output=True, text=True, timeout=5,
        )
        return process_name.lower() in result.stdout.lower()
    except Exception:
        return False


def _check_process_running_any(processes: List[str]) -> bool:
    return any(_check_process_running(p) for p in processes)


def _check_window_exists(title: str) -> bool:
    """Check if a window with the given title exists (Windows only)."""
    try:
        import pyautogui
        windows = pyautogui.getWindowsWithTitle(title)
        return len(windows) > 0
    except Exception:
        return False


def verify_task(verify_spec: Dict[str, Any]) -> bool:
    """Run a verification check based on the task spec."""
    vtype = verify_spec.get("type", "")

    if vtype == "process_running":
        return _check_process_running(verify_spec["process"])
    elif vtype == "process_running_any":
        return _check_process_running_any(verify_spec["processes"])
    elif vtype == "window_exists":
        return _check_window_exists(verify_spec["window_title"])
    elif vtype == "window_contains_text":
        return _check_window_exists(verify_spec.get("window_title", ""))
    else:
        return False


# ── Benchmark runner ──────────────────────────────────────────────────

class GUIBenchmark:
    """Run benchmark tasks and produce scores."""

    def __init__(self, tasks_path: Optional[str] = None):
        if tasks_path is None:
            tasks_path = str(Path(__file__).parent / "tasks.json")
        with open(tasks_path, "r", encoding="utf-8") as f:
            self.tasks: List[Dict[str, Any]] = json.load(f)

    def run_task(
        self,
        task_def: Dict[str, Any],
        client: VLMClient,
    ) -> TaskScore:
        """Run a single benchmark task and score it."""
        task_id = task_def["id"]
        description = task_def["description"]
        max_steps = task_def.get("max_steps", 10)

        json_ok = 0
        json_total = 0

        def on_step(step):
            nonlocal json_ok, json_total
            json_total += 1
            if step.status != "failed":
                json_ok += 1

        orchestrator = Orchestrator(
            llm_client=client,
            max_steps=max_steps,
            on_step_callback=on_step,
        )

        start = time.time()
        result: TaskResult = orchestrator.run_task(description)
        elapsed = time.time() - start

        # Verification
        verified = False
        verify_spec = task_def.get("verify")
        if verify_spec and result.success:
            time.sleep(1)  # give the OS a moment
            verified = verify_task(verify_spec)

        return TaskScore(
            task_id=task_id,
            description=description,
            completed=result.success,
            steps_used=len(result.steps),
            max_steps=max_steps,
            response_time=elapsed,
            json_parse_success_rate=json_ok / json_total if json_total > 0 else 0.0,
            verified=verified,
        )

    def run_all(
        self,
        client: VLMClient,
        provider: str = "",
        task_ids: Optional[List[str]] = None,
    ) -> BenchmarkReport:
        """Run all (or selected) benchmark tasks."""
        report = BenchmarkReport(
            model_name=client.get_model_name(),
            provider=provider,
        )

        tasks_to_run = self.tasks
        if task_ids:
            tasks_to_run = [t for t in self.tasks if t["id"] in task_ids]

        for task_def in tasks_to_run:
            print(f"\n{'='*50}")
            print(f"Running: {task_def['id']} - {task_def['description']}")
            print(f"{'='*50}")
            score = self.run_task(task_def, client)
            report.scores.append(score)
            print(f"  Result: {'✅ PASS' if score.completed else '❌ FAIL'}"
                  f"  Verified: {'✅' if score.verified else '❌'}"
                  f"  Steps: {score.steps_used}/{score.max_steps}"
                  f"  Time: {score.response_time:.1f}s")

        return report

    def compare_models(
        self,
        clients: Dict[str, VLMClient],
        task_ids: Optional[List[str]] = None,
    ) -> List[BenchmarkReport]:
        """Run benchmark for multiple models and return reports."""
        reports = []
        for provider_name, client in clients.items():
            print(f"\n{'#'*60}")
            print(f"  Benchmarking: {provider_name} / {client.get_model_name()}")
            print(f"{'#'*60}")
            report = self.run_all(client, provider=provider_name, task_ids=task_ids)
            reports.append(report)
        return reports


# ── CLI entry point ──────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GUI Agent Benchmark")
    parser.add_argument("--provider", default=config.LLM_PROVIDER, help="LLM provider")
    parser.add_argument("--model", default=None, help="Model name override")
    parser.add_argument("--tasks", nargs="*", default=None, help="Task IDs to run (default: all)")
    parser.add_argument("--output", default=None, help="JSON output path")
    args = parser.parse_args()

    kwargs = {}
    if args.model:
        kwargs["model"] = args.model

    client = create_client(provider=args.provider, **kwargs)
    bench = GUIBenchmark()
    report = bench.run_all(client, provider=args.provider, task_ids=args.tasks)

    # Print summary
    print(f"\n{'='*60}")
    print(f"  BENCHMARK SUMMARY — {report.model_name}")
    print(f"{'='*60}")
    print(f"  Task Completion Rate : {report.task_completion_rate:.1%}")
    print(f"  Verification Rate    : {report.verification_rate:.1%}")
    print(f"  Average Steps        : {report.avg_steps:.1f}")
    print(f"  Average Response Time: {report.avg_response_time:.1f}s")

    # Save report
    if args.output:
        out_path = args.output
    else:
        out_path = str(Path(__file__).parent / f"report_{report.model_name.replace(':', '_')}.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    print(f"\n  Report saved to: {out_path}")
