
# utils_config

[![Read The Docs](https://img.shields.io/readthedocs/utils-config)](https://utils-config.readthedocs.io/)


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

loader = ConfigLoader("config_pearl/config_pearl/config","raw",recursive=True) #relative path from where you run the tool
config_parsed = loader.load_configs()
print(config_parsed["observatory"]["pointing"]["jitter_rms"])
```

## Troubleshooting
If you encounter issues, try the following:
- Ensure you are running Python 3.12
- Check that `pip list | grep utils_config` confirms the package is installed
- Uninstall and reinstall using:
  ```sh
  pip uninstall utils_config
  pip install .
  ```

If you'd like to print the whole dictionary in all 3 formats for a sanity check, you can borrow the following 
```python
from utils_config import ConfigLoader
import json

config_raw = ConfigLoader("config_pearl/config_pearl/config","raw").load_configs() 
config_parsed = ConfigLoader("config_pearl/config_pearl/config","parsed").load_configs()
config_unitless = ConfigLoader("config_pearl/config_pearl/config","unitless").load_configs()

def print_dict(title, data):
    """Print pearl dictionary for all 3 formats -- json formatted!"""
    print(json.dumps(data, indent=4, sort_keys=True))

if __name__ == "__main__":
    print("\n===========   {raw}   ===========")
    print_dict("Raw Astropy TOML Data", config_raw)
    print("\n===========  {parsed}  ===========")
    print_dict("Parsed TOML Data (Value + Unit)", config_parsed)
    print("\n=========== {unitless} ===========")
    print_dict("Values-Only TOML Data", config_unitless)
```



