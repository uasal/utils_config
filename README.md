# utils_config

## Overview
`utils_config` is a Python package that provides a utility for parsing TOML files. Currently there are 3 data formats this package makes available, "raw" which returns a dictionary of strings as whatever format they're stored in, "parsed" which reads .toml files and separates out 'value' and 'unit', and "unitless" which parses the input string and removes any units. See examples below for how to grab each format. 

## Installation Instructions

### **1. Clone the Repository**
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

## Usage and Verifying the Installation
Once installed, you can import `ConfigLoader` and use the 3 input arguments of the class as shown below. Keep in mind your path will be relative to where you're running the script. Below is an example of using this tool to parse a toml config found inside config_pearl.

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

