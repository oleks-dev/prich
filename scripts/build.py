import subprocess
import tarfile
import zipfile
from pathlib import Path

def build():
    print("📦 Building sdist and wheel...")
    subprocess.run(["python", "-m", "build", "--sdist", "--wheel"], check=True)

def list_sdist_contents():
    sdist_path = next(Path("dist").glob("*.tar.gz"), None)
    if not sdist_path:
        print("❌ No sdist archive found.")
        return

    print(f"\n📦 sdist contents ({sdist_path}):")
    with tarfile.open(sdist_path, "r:gz") as tar:
        for member in tar.getmembers():
            print("  -", member.name)

def list_wheel_contents():
    wheel_path = next(Path("dist").glob("*.whl"), None)
    if not wheel_path:
        print("❌ No wheel archive found.")
        return

    print(f"\n📦 wheel contents ({wheel_path}):")
    with zipfile.ZipFile(wheel_path, "r") as zipf:
        for name in zipf.namelist():
            print("  -", name)

def main():
    build()
    list_sdist_contents()
    list_wheel_contents()

if __name__ == "__main__":
    main()
