import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def test_new_tests_detect_broken_clamp_implementations():
    path = Path("tests/test_clamp.py")
    assert path.is_file()
    for wrong_return in ("minimum", "value", "maximum"):
        with TemporaryDirectory() as directory:
            candidate = Path(directory)
            shutil.copy2(path, candidate / path.name)
            (candidate / "clamp.py").write_text(
                f"def clamp(value, minimum, maximum):\n    return {wrong_return}\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", path.name],
                cwd=candidate,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            assert result.returncode == 1, result.stdout + result.stderr
