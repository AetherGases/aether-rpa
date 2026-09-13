import importlib.util
import os

_spec = importlib.util.spec_from_file_location(
    "_stdlib_cmd",
    os.path.join(os.path.dirname(os.__file__), "cmd.py"),
)
_stdlib_cmd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_stdlib_cmd)

Cmd = _stdlib_cmd.Cmd


def __getattr__(name):
    return getattr(_stdlib_cmd, name)
