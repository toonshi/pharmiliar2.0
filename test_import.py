import sys
from pathlib import Path

# Absolute path to the src directory
src_path = Path("C:/Users/Roy Agoya/Desktop/pharmiliar/src")
sys.path.append(str(src_path))

# Check the sys.path after modification
print("sys.path:", sys.path)

# Try importing the medical_advisor module
try:
    import medical_advisor
    print("medical_advisor module imported successfully.")
except ModuleNotFoundError as e:
    print(f"Error importing medical_advisor: {e}")
