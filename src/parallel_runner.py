"""多 Agent 并行执行框架 v5.0 — 并发采集 + 纠错验证"""
import concurrent.futures
import traceback
from datetime import datetime
from typing import Callable, Any


class AgentTask:
    """单个 Agent 任务定义"""

    def __init__(self, name: str, func: Callable, args: tuple = (), kwargs: dict = None,
                 timeout: int = 120, retries: int = 1, critical: bool = False):
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.timeout = timeout
        self.retries = retries
        self.critical = critical  # 关键任务失败则整体失败
        self.result = None
        self.error = None
        self.elapsed = 0
        self.attempts = 0


class ParallelRunner:
    """多 Agent 并行调度器"""

    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.tasks: list[AgentTask] = []
        self.results: dict[str, Any] = {}
        self.errors: dict[str, str] = {}
        self.start_time = None

    def add_task(self, task: AgentTask):
        self.tasks.append(task)
        return self

    def add(self, name: str, func: Callable, *args, timeout=120, retries=1, critical=False, **kwargs):
        """快捷添加任务"""
        self.tasks.append(AgentTask(name, func, args, kwargs, timeout, retries, critical))
        return self

    def _execute_task(self, task: AgentTask) -> AgentTask:
        """执行单个任务（含重试）"""
        task.attempts += 0
        for attempt in range(task.retries):
            task.attempts += 1
            try:
                start = datetime.now()
                if task.args and task.kwargs:
                    task.result = task.func(*task.args, **task.kwargs)
                elif task.args:
                    task.result = task.func(*task.args)
                elif task.kwargs:
                    task.result = task.func(**task.kwargs)
                else:
                    task.result = task.func()
                task.elapsed = (datetime.now() - start).total_seconds()
                return task
            except Exception as e:
                task.error = f"[尝试 {attempt+1}/{task.retries}] {e}"
                if attempt < task.retries - 1:
                    print(f"  [重试] {task.name} 失败，重试中...")
        return task

    def run_all(self) -> dict:
        """并行执行所有任务"""
        self.start_time = datetime.now()
        print(f"\n{'='*60}")
        print(f"[{self.start_time.strftime('%H:%M:%S')}] 启动 {len(self.tasks)} 个 Agent 并行任务")
        print(f"{'='*60}")

        completed = 0
        failed = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self._execute_task, task): task
                for task in self.tasks
            }

            for future in concurrent.futures.as_completed(future_to_task):
                task = future.result()
                if task.error:
                    failed += 1
                    status = "FAIL"
                    self.errors[task.name] = task.error
                    if task.critical:
                        print(f"  [{status}] {task.name} - 关键任务失败: {task.error}")
                    else:
                        print(f"  [{status}] {task.name} - {task.error}")
                else:
                    completed += 1
                    status = "OK"
                    self.results[task.name] = task.result
                    print(f"  [{status}] {task.name} ({task.elapsed:.1f}s)")

        total_time = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{'='*60}")
        print(f"完成: {completed}/{len(self.tasks)} | 失败: {failed} | 总耗时: {total_time:.1f}s")
        print(f"{'='*60}\n")

        return self.results

    def get(self, name: str, default=None):
        """获取指定任务结果"""
        return self.results.get(name, default)

    def has_critical_failure(self) -> bool:
        """检查是否有关键任务失败"""
        for task in self.tasks:
            if task.critical and task.error:
                return True
        return False

    def get_summary(self) -> str:
        """获取执行摘要"""
        lines = ["## Agent 执行摘要\n"]
        for task in self.tasks:
            if task.error:
                lines.append(f"- **{task.name}**: 失败 — {task.error}")
            else:
                lines.append(f"- **{task.name}**: 成功 ({task.elapsed:.1f}s)")
        return "\n".join(lines)
