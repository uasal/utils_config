import os
import tempfile

import pytest
import toml

from utils_config import ConfigLoader


@pytest.fixture
def sample_toml_file():
    """Create a temporary TOML file for testing"""
    toml_content = {"section": {"param1": "value1", "param2": 1234567890, "param3": 3.14}}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".toml") as tmp_file:
        tmp_file.write(toml.dumps(toml_content).encode("utf-8"))
        tmp_file_path = tmp_file.name

    yield tmp_file_path

    # Cleanup after test
    os.remove(tmp_file_path)


def test_config_loader(sample_toml_file):
    """Test that ConfigLoader correctly loads a TOML file"""
    loader = ConfigLoader(directory=os.path.dirname(sample_toml_file), mode="raw")
    config_data = loader.load()

    # Extract file name to match expected structure
    filename = os.path.basename(sample_toml_file)

    assert filename in config_data, f"Expected {filename} in loaded config"
    assert config_data[filename]["section"]["param1"] == "value1"
    assert config_data[filename]["section"]["param2"] == 1234567890
    assert config_data[filename]["section"]["param3"] == 3.14
