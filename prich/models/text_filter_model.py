import re
from typing import Optional, List, Tuple
from pydantic import BaseModel

class TextFilterModel(BaseModel):
    strip: Optional[bool] = True
    strip_prefix: Optional[str] = None
    slice_start: Optional[int] = None
    slice_end: Optional[int] = None
    regex_extract: Optional[str] = None
    regex_replace: Optional[List[Tuple[str, str]]] = None  # [(pattern, replacement), ...]

    def apply(self, text: str) -> str:
        out = text

        if self.strip:
            out = out.strip()

        if self.strip_prefix and out.startswith(self.strip_prefix):
            out = out[len(self.strip_prefix):]

        if self.slice_start is not None or self.slice_end is not None:
            out = out[self.slice_start:self.slice_end]

        if self.regex_extract:
            m = re.search(self.regex_extract, out)
            out = m.group(1) if (m and m.groups()) else (m.group(0) if m else "")

        if self.regex_replace:
            for pattern, repl in self.regex_replace:
                out = re.sub(pattern, repl, out)

        return out
