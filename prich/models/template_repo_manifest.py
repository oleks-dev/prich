from pydantic import BaseModel
from typing import List, Literal


class TemplateRepoItem(BaseModel):
    id: str
    name: str
    version: str
    schema_version: str
    author: str
    description: str
    files: list
    folder_checksum: str
    tags: list[str]


class TemplatesRepoManifest(BaseModel):
    name: str
    description: str
    repository: str
    schema_version: Literal["1.0"]
    templates: List[TemplateRepoItem]
    templates_path: str
    templates_download_path: str
