from abc import ABC
from prich.core.optional_imports import ensure_optional_dep

class LazyOptionalProvider(ABC):
    def __init__(self):
        self._loaded_modules = {}

    def _lazy_import(self, module_name: str, pip_name: str = None):
        if module_name in self._loaded_modules:
            return self._loaded_modules[module_name]

        ensure_optional_dep(module_name, pip_name or module_name)
        module = __import__(module_name)
        self._loaded_modules[module_name] = module
        return module

    def _lazy_import_from(self, module_name: str, symbol: str, pip_name: str = None):
        if f"{module_name}:{symbol}" in self._loaded_modules:
            return self._loaded_modules[f"{module_name}:{symbol}"]

        ensure_optional_dep(module_name, pip_name or module_name)
        module = __import__(module_name, fromlist=[symbol])
        value = getattr(module, symbol)
        self._loaded_modules[f"{module_name}:{symbol}"] = value
        return value
