import importlib

from opensafely._vendor.jobrunner import config
from opensafely._vendor.jobrunner.executors.logging import LoggingExecutor


def get_executor_api():
    module_name, cls = config.EXECUTOR.split(":", 1)
    module = importlib.import_module(module_name)
    return LoggingExecutor(getattr(module, cls)())
