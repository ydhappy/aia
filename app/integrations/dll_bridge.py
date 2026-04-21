from __future__ import annotations

import ctypes
from pathlib import Path
from typing import Any


class DLLBridge:
    def __init__(self, dll_path: str | None = None) -> None:
        self.dll_path = Path(dll_path).expanduser().resolve() if dll_path else None
        self.lib = None
        if self.dll_path and self.dll_path.exists():
            self.lib = ctypes.WinDLL(str(self.dll_path))

    def is_loaded(self) -> bool:
        return self.lib is not None

    def call_bool(self, func_name: str, *args: Any) -> bool:
        if self.lib is None:
            return False
        func = getattr(self.lib, func_name)
        func.restype = ctypes.c_int
        converted = [self._convert_arg(arg) for arg in args]
        return bool(func(*converted))

    def call_int(self, func_name: str, *args: Any) -> int:
        if self.lib is None:
            return -1
        func = getattr(self.lib, func_name)
        func.restype = ctypes.c_int
        converted = [self._convert_arg(arg) for arg in args]
        return int(func(*converted))

    def call_str(self, func_name: str, *args: Any) -> str:
        if self.lib is None:
            return ""
        func = getattr(self.lib, func_name)
        func.restype = ctypes.c_char_p
        converted = [self._convert_arg(arg) for arg in args]
        result = func(*converted)
        return result.decode("utf-8", errors="ignore") if result else ""

    def _convert_arg(self, value: Any) -> Any:
        if isinstance(value, str):
            return ctypes.c_char_p(value.encode("utf-8"))
        if isinstance(value, bool):
            return ctypes.c_int(1 if value else 0)
        if isinstance(value, int):
            return ctypes.c_int(value)
        return value


dll_bridge = DLLBridge()
