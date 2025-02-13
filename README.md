# utils_config

## Overview
`utils_config` is a Python package that provides a utility for parsing TOML files. Currently there are 3 data formats this package makes available, "raw" which returns a dictionary of strings as whatever format they're stored in, "parsed" which reads .toml files and separates out 'value' and 'unit', and "unitless" which parses the input string and removes any units. See examples below for how to grab each format. 

## Installation

### **1. Clone the Repoistory**
To get started, clone this repository using:
```sh
git clone git@github.com:uasal/utils_config.git
cd utils_config
```

### **2. Install the Package**
Once inside the project directory, install the package using:
```sh
pip install .
```

### **For Pip-only installation**
For those who simply want to use the tool and not clone the repository:
```sh
pip install git+ssh://git@github.com/uasal/utils_config.git
```

## Usage and Verifying the Installation
To verify the installed version matches the latest release: 
```sh
pip show utils_config
```

If you have cloned the repo and your version is out of date, make sure you are on the `develop` branch and pulled prior to reinstalling via pip. You may have to do this command at the root of the utils_config repo: 
```sh
pip install --no-cache-dir --force-reinstall .
```
For pip-only installations simply run the install command again. Once installed, your python code should use an import `ConfigLoader` and then be able to use the 3 input arguments as shown below. Keep in mind your path will be relative to where you're running the script. Below is an example of using this tool to parse a toml config inside config_pearl.

### Raw
```python
from utils_config import ConfigLoader

loader = ConfigLoader("config_pearl/configs","raw",recursive=True) #relative path from where you run the tool
config_parsed = loader.load_configs()
print(config_parsed["observatory"]["pointing"]["jitter_rms"])
```

From the above example, adjusting the second argument should result in the following data formats returned:
- `ConfigLoader("config_pearl/configs","unitless")` -> `0.01`
- `ConfigLoader("config_pearl/configs","parsed")` -> `{'value': 0.01, 'unit': 'arcsecond'}`
- `ConfigLoader("config_pearl/configs","raw")` -> `10e-3arcsecond`

## For Developers
This package is based off the LINCC framework which utilizes Ruff for linting, pytest for unit tests and coverage, and sphinx for auto doc generation. If planning on making a commit, there are a few packages you need to install first:

```
pip install mypy sphinx pytest types-toml sphinx-autoapi sphinx-copybutton sphinx-rtd-theme pytest-cov
```
