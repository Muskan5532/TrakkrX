
import json
from pathlib import Path

# Find the data folder inside the project
DATA_FOLDER = Path(__file__).parent / "data"


def load_data(filename):
    file_path = DATA_FOLDER / filename

    if not file_path.exists():
        return []

    with open(file_path, "r") as file:
        return json.load(file)


def save_data(filename, data):
    file_path = DATA_FOLDER / filename

    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
