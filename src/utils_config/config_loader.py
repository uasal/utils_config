import os
import re
import warnings
from pathlib import Path
from typing import Any, List, Optional, Union

import astropy.units as u
import toml


class ConfigLoader:
    """Class to load and process .toml configuration files.

    Supports raw loading, parsing unit-bearing values, or stripping units
    entirely. Also expands environment variables in string paths.
    """

    def __init__(self, base_dir: str, mode: str = "raw", recursive: bool = False):
        """Initializes the ConfigLoader.

        Parameters
        ----------
        base_dir : str
            Directory to search for .toml config files.
        mode : str
            One of ['raw', 'unitless', 'parsed'].
        recursive : bool
            If True, searches subdirectories for .toml files.

        Raises
        ------
        ValueError
            If mode is not one of the allowed values.
        """
        self.base_dir = Path(base_dir).resolve()
        self.mode = mode.lower()
        self.recursive = recursive
        self.config_data: dict[str, dict[str, Any]] = {}

        if self.mode not in {"raw", "unitless", "parsed"}:
            raise ValueError("Invalid mode. Choose from 'raw', 'unitless', or 'parsed'.")

    def load_configs(self) -> dict[str, dict[str, Any]]:
        """Loads all .toml files in the given directory and processes them.

        Environment variables in string values are automatically expanded.

        Returns
        -------
        dict[str, dict[str, Any]]
            Dictionary of processed config data keyed by filename.

        Raises
        ------
        FileNotFoundError
            If no .toml files are found.
        ValueError
            If any file fails to parse.
        """
        search_pattern = "**/*.toml" if self.recursive else "*.toml"
        toml_files = list(self.base_dir.glob(search_pattern))

        if not toml_files:
            raise FileNotFoundError(f"No .toml files found in {self.base_dir}")

        for toml_file in toml_files:
            try:
                with open(toml_file, "r") as f:
                    config = toml.load(f)

                # Expand env vars like $SERVER in config values
                config = self._expand_env_vars(config)

                # Use filename (without extension) as dictionary key
                file_key = toml_file.stem
                self.config_data[file_key] = self._process_config(config)

            except Exception as e:
                raise ValueError(f"Error parsing {toml_file}: {e}") from e

        return self.config_data

    def _expand_env_vars(self, config: Any, path: Optional[list[str]] = None) -> Any:
        """Recursively expands environment variables in all string values.
        Produces warning if env variable not defined in user's environment.

        Parameters
        ----------
        config : Any
            The loaded config subtree.
        path : Optional[list[str]])
            Internal path tracker for nested keys.

        Returns
        -------
        Any
            Same structure with all string values processed via os.path.expandvars.
        """
        if path is None:
            path = []

        if isinstance(config, dict):
            return {k: self._expand_env_vars(v, path + [k]) for k, v in config.items()}

        elif isinstance(config, list):
            return [self._expand_env_vars(v, path + [f"[{i}]"]) for i, v in enumerate(config)]

        elif isinstance(config, str):
            unresolved = re.findall(r"\$(\w+)|\$\{(\w+)\}", config)
            for match in unresolved:
                var_name = match[0] or match[1]
                if var_name and var_name not in os.environ:
                    location = " -> ".join(path)
                    warnings.warn(
                        f"Environment variable '${var_name}' referenced by '{location}' is not set so '{config}' will not expand. "
                        f"If using '{location}' please set '${var_name}' and call this method again.  "
                        f"Reference the README for instructions on setting up an environment variable.",
                        stacklevel=3,
                    )
            return os.path.expandvars(config)
        return config

    def _process_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Processes the config data based on the selected mode.

        Parameters
        ----------
        config : dict
            Raw config data.

        Returns
        -------
        dict
            Processed config data (parsed, unitless, or raw).
        """
        if self.mode == "raw":
            return config
        elif self.mode == "parsed":
            return self._parse_units(config, values_only=False)
        elif self.mode == "unitless":
            return self._parse_units(config, values_only=True)
        return config  # default to raw

    def _parse_units(self, config: Any, values_only: bool) -> Any:
        """Recursively processes the configuration to parse or remove units.

        Parameters
        ----------
        config : Any
            Config subtree to process.
        values_only : bool
            If True, return only the numerical value without units.

        Returns
        -------
        Any
            Transformed config subtree.
        """
        if isinstance(config, dict):
            return {key: self._parse_units(value, values_only) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._parse_units(item, values_only) for item in config]
        elif isinstance(config, str):
            return self._extract_value_and_unit(config, values_only)
        else:
            return config  # Leave non-string values unchanged

    def _extract_value_and_unit(self, value: str, values_only: bool) -> Union[str, float, dict[str, Any]]:
        """Extracts a numerical value and unit from a string.

        Recognizes values like '10e-3arcsecond' or '0.024Kelvin/hour'.

        Parameters
        ----------
        value : str
            Input string to parse.
        values_only : bool
            If True, return only float; otherwise return dict with 'value' and 'unit'.

        Returns
        -------
        Union[str, float, dict]
            Parsed result or original string if no match.
        """
        match = re.match(r"([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)([a-zA-Z/%µ]+$)", value.strip())
        if match:
            num, unit = match.groups()
            return float(num) if values_only else {"value": float(num), "unit": unit} if unit else float(num)
        return value  # Return as-is if no match

    def validate_astropy(self) -> Union[bool, List[str]]:
        """Validates that all parsed units are compatible with Astropy.

        Walks through self.config_data and checks if every unit string is valid.

        Returns
        -------
        bool | List[str]
            True if all units are valid; otherwise a list of error messages.
        """
        errors = []

        def _check_units(data: Any, path: List[str], file_key: str):
            if isinstance(data, dict):
                # Check if this dict looks like a unitized value.
                if "value" in data and "unit" in data:
                    unit_str = data["unit"]
                    try:
                        u.Unit(unit_str)
                    except Exception:
                        path_str = " -> ".join(str(p) for p in path)
                        errors.append(f"{file_key}.toml -> {path_str}: invalid unit '{unit_str}'")
                # Recurse into nested keys
                for key, value in data.items():
                    _check_units(value, path + [key], file_key)
            elif isinstance(data, list):
                for idx, item in enumerate(data):
                    _check_units(item, path + [f"[{idx}]"], file_key)
            # Other data types (e.g., str, int) are ignored

        for file_key, config in self.config_data.items():
            _check_units(config, [], file_key)

        return True if not errors else errors
