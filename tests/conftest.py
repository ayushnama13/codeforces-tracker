import json
from pathlib import Path
import pytest
ROOT=Path(__file__).parent/'fixtures'
@pytest.fixture
def subs(): return json.loads((ROOT/'user_status.json').read_text())
@pytest.fixture
def rating(): return json.loads((ROOT/'user_rating.json').read_text())
@pytest.fixture
def info(): return json.loads((ROOT/'user_info.json').read_text())
@pytest.fixture
def problems_path(): return ROOT/'problems.csv'
