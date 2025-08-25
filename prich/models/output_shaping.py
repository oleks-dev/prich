from typing import Optional
from pydantic import BaseModel


class BaseOutputShapingModel(BaseModel):

    # output shaping
    strip_output: Optional[bool] = True
    strip_output_prefix: Optional[str] = None

    slice_output_start: Optional[int] = None
    slice_output_end: Optional[int] = None

    # regex
    output_regex: Optional[str] = None                    # transforms main output

    def postprocess_output(self, output: str):
        """PostProcess output - Transform string text"""
        import re
        out = output
        if self.strip_output:
            out = out.strip()

        if self.strip_output_prefix and out.startswith(self.strip_output_prefix):
            out = out[len(self.strip_output_prefix):]

        if self.slice_output_start or self.slice_output_end:
            out = out[self.slice_output_start:self.slice_output_end]

        if self.output_regex:
            m = re.search(self.output_regex, out)
            if m:
                out = m.group(1) if m.groups() else m.group(0)

        return out
