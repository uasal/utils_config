import re
from pathlib import Path
from typing import Any, List, Union

import astropy.units as u
import toml


class ConfigLoader:
    """Class to load and process configuration files."""

    def __init__(self, base_dir: str, mode: str = "raw", recursive: bool = False):
        """
        :param base_dir: Directory to search for .toml config files.
        :param mode: One of ['raw', 'unitless', 'parsed'].
        :param recursive: If True, searches subdirectories for .toml files.
        """
        self.base_dir = Path(base_dir).resolve()
        self.mode = mode.lower()
        self.recursive = recursive
        self.config_data: dict[str, dict[str, Any]] = {}

        if self.mode not in {"raw", "unitless", "parsed"}:
            raise ValueError("Invalid mode. Choose from 'raw', 'unitless', or 'parsed'.")

    def load_configs(self):
        """Loads allaldsfkj;sdlk .toml files in the given directory and processes them accordingly."""
        search_pattern = "**/*.toml" if self.recursive else "*.toml"
        toml_files = list(self.base_dir.glob(search_pattern))

        if not toml_files:
            raise FileNotFoundError(f"No .toml files found in {self.base_dir}")

        for toml_file in toml_files:
            try:
                with open(toml_file, "r") as f:
                    config = toml.load(f)

                file_key = toml_file.stem  # Use filename (without extension) as key
                self.config_data[file_key] = self._process_config(config)

            except Exception as e:
                raise ValueError(f"Error parsing {toml_file}: {e}") from e

        return self.config_data

    def _process_config(self, config):
        """Processes the config data based on the selected mode."""
        if self.mode == "raw":
            return config
        elif self.mode == "parsed":
            return self._parse_units(config, values_only=False)
        elif self.mode == "unitless":
            return self._parse_units(config, values_only=True)

    def _parse_units(self, config, values_only: bool):
        """Recursively processes the configuration dictionary to parse units."""
        if isinstance(config, dict):
            return {key: self._parse_units(value, values_only) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._parse_units(item, values_only) for item in config]
        elif isinstance(config, str):
            return self._extract_value_and_unit(config, values_only)
        else:
            return config  # Keep numbers, booleans, datetime objects, etc. unchanged

    def _extract_value_and_unit(self, value, values_only: bool):
        """
        Extracts numerical value and unit from a string.
        Example:
          - '10e-3arcsecond' → {'value': 1.0e-2, 'unit': 'arcsecond'}
          - '0.024Kelvin/hour' → {'value': 0.024, 'unit': 'Kelvin/hour'}
        """
        match = re.match(r"([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)([a-zA-Z/%µ]+$)", value.strip())
        if match:
            num, unit = match.groups()
            return float(num) if values_only else {"value": float(num), "unit": unit} if unit else float(num)
        return value  # Return as-is if it doesn't match the expected format

    def validate_astropy(self) -> Union[bool, List[str]]:
        """
        Validates that every unit in the loaded configuration is a valid Astropy unit.

        This method walks through self.config_data and, for every dictionary that
        appears to represent a unitized value (i.e. contains both 'value' and 'unit'),
        it attempts to construct an Astropy Unit from the unit string.

        Any invalid units are recorded with a message indicating the file and the key path
        within that file.

        Returns:
            A list of error messages. An empty list indicates all units conform to Astropy.
        """
        errors = []

        def _check_units(data, path, file_key):
            if isinstance(data, dict):
                # Check if this dict looks like a unitized value.
                if "value" in data and "unit" in data:
                    unit_str = data["unit"]
                    try:
                        u.Unit(unit_str)
                    except Exception as e:
                        # Record error with file key and path within the configuration.
                        path_str = " -> ".join(str(p) for p in path)
                        errors.append(f"{file_key}.toml -> {path_str}: invalid unit '{unit_str}'")
                # Recurse into each key/value pair.
                for key, value in data.items():
                    _check_units(value, path + [key], file_key)
            elif isinstance(data, list):
                for idx, item in enumerate(data):
                    _check_units(item, path + [f"[{idx}]"], file_key)
            # Other data types are ignored.

        for file_key, config in self.config_data.items():
            _check_units(config, [], file_key)

        return True if not errors else errors
