from __future__ import annotations

from collections import OrderedDict
from typing import Callable

from app.modules.task_base import TaskBase
from app.modules.tasks import DEFAULT_TASKS


class TaskRegistry:
    def __init__(self) -> None:
        self._tasks: OrderedDict[str, TaskBase] = OrderedDict()

    def register_task(self, task: TaskBase) -> None:
        self._tasks[task.name] = task

    def get_task(self, name: str) -> TaskBase | None:
        return self._tasks.get(name)

    def list_tasks(self) -> list[str]:
        return list(self._tasks.keys())


REGISTRY = TaskRegistry()
for _task in DEFAULT_TASKS:
    REGISTRY.register_task(_task)


def register_task(task: TaskBase) -> None:
    REGISTRY.register_task(task)


def get_task(name: str) -> TaskBase | None:
    return REGISTRY.get_task(name)


def list_tasks() -> list[str]:
    return REGISTRY.list_tasks()


def get_available_tasks() -> list[str]:
    return list_tasks()


def get_task_function(task_id: str) -> Callable | None:
    task = get_task(task_id)
    if not task:
        return None

    def _runner(**context):
        return task.run(context)

    return _runner
