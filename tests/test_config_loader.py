import os
import tempfile
from pathlib import Path

import pytest
import toml
from utils_config.config_loader import ConfigLoader


@pytest.fixture
def sample_toml_file():
    """Create a temporary TOML file for testing"""
    toml_content = {"section": {"param1": "value1", "param2": 42, "param3": 3.14}}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".toml") as tmp_file:
        tmp_file.write(toml.dumps(toml_content).encode("utf-8"))
        tmp_file_path = tmp_file.name

    yield tmp_file_path

    # Cleanup after test
    os.remove(tmp_file_path)


def test_config_loader(sample_toml_file):
    """Test that ConfigLoader correctly loads a TOML file"""
    base_dir = os.path.dirname(sample_toml_file)
    loader = ConfigLoader(base_dir=base_dir, mode="raw")
    config_data = loader.load_configs()

    # Extract file name to match expected structure
    filename = Path(sample_toml_file).stem

    assert filename in config_data, f"Expected {filename} in loaded config"
    assert config_data[filename]["section"]["param1"] == "value1"
    assert config_data[filename]["section"]["param2"] == 42
    assert config_data[filename]["section"]["param3"] == 3.14
