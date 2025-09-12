from dataclasses import dataclass
from pathlib import Path


@dataclass
class PrichFolder:
    global_dir: Path
    local_dir: Path
    global_templates: Path
    local_templates: Path


@dataclass
class MainFolder:
    home_dir: Path
    cwd_dir: Path
    prich: PrichFolder


def mock_paths_create_prich_global_folders(main_folder: MainFolder):
    main_folder.prich.global_dir.mkdir(exist_ok=True)
    main_folder.prich.global_templates.mkdir(exist_ok=True)

def mock_paths_create_prich_local_folders(main_folder: MainFolder):
    main_folder.prich.local_dir.mkdir(exist_ok=True)
    main_folder.prich.local_templates.mkdir(exist_ok=True)

