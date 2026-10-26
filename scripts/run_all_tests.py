"""
Automated Test Runner for the BDA Project.
Runs pytest and prints a clean evaluation summary.
"""

import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 70)
    print("RUNNING ALL AUTOMATED TESTS")
    print("=" * 70)
    
    venv_pytest = Path(__file__).resolve().parent.parent / ".venv" / "Scripts" / "pytest.exe"
    cmd = [str(venv_pytest) if venv_pytest.exists() else "pytest", "-v"]
    
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("[SUCCESS] ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print(f"[FAILURE] Tests exited with code {result.returncode}")
        print("=" * 70)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
