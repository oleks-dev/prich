from enum import Enum


class FileScope(str, Enum):
    LOCAL = "local"
    GLOBAL = "global"
    EXTERNAL = "external"  # neither local nor global roots
