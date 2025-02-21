import re
from pathlib import Path
from typing import Any

import toml
import astropy.units as u  

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
        """Loads all .toml files in the given directory and processes them accordingly."""
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

    def infer_unit_type(self) -> str:
        """
        Infers the unit type in the loaded configuration.

        This method walks through self.config_data and checks each dictionary
        that appears to be a unitized value (i.e. contains both 'value' and 'unit').
        It tries to construct an astropy Unit from the unit string.
        
        Returns:
            "astropy" if at least one unit is found and all such units are valid Astropy units.
            "unknown" if any unit is invalid or if no unit entries are found.
        """
        unit_valid = True
        found_units = False

        def _check_units(data):
            nonlocal unit_valid, found_units
            if isinstance(data, dict):
                if "value" in data and "unit" in data:
                    found_units = True
                    unit_str = data["unit"]
                    try:
                        u.Unit(unit_str)
                    except Exception:
                        unit_valid = False
                for value in data.values():
                    _check_units(value)
            elif isinstance(data, list):
                for item in data:
                    _check_units(item)

        for config in self.config_data.values():
            _check_units(config)

        # If at least one unit was found and all were valid, return "astropy".
        # Otherwise, return "unknown".
        return "astropy" if found_units and unit_valid else "unknown"

