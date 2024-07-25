# Redpanda Property Extractor

CLI tool to extract all properties from the Redpanda's source code and generate a JSON output with their definitions.


## Dependencies

- Python 3
- A C++ compiler (tested with `gcc`)

## Installation

1. After cloning the project, initialize and update the C++ tree-sitter submodule:

```bash
git submodule init
git submodule update
```


2. Install the `tree_sitter` dependency for Python:
```bash
pip install -r requirements.txt
```

Optionally, you can use `venv` to avoid installing this dependency globally:

```bash
python -m venv /path/to/your/venv
source /path/to/your/vm/bin/activate
pip install -r requirements.txt
```

3. You will also need to download Redpanda's source code:

```bash
git clone https://github.com/redpanda-data/redpanda.git <dir>
```

Alternatively, you can run `make` to generate the file. It will be stored at `./gen/properties-output.json`.

## Usage

```
./property_extractor.py [-h] --path PATH [--recursive] [--output OUTPUT] --definitions DEFINITIONS [-v]

options:
  -h, --help            show this help message and exit
  --path PATH           Path to the Redpanda's source dir to extract the properties
  --recursive           Scan the path recursively
  --output OUTPUT       File to store the JSON output. If no file is provided, the JSON will be printed to the standard output
  --definitions DEFINITIONS
                        JSON file with extra type definitions to be used during the output generation
  -v, --verbose
```

Example usage:

```
./property_extractor.py --recursive --path /path/to/redpanda --definitions definitions.json --output my-output.json
```


## Transformers

A transformer is an object used to add, remove, or modify the fields of a property.
To create a new transformer, you need to create a class with the following methods:

- `accepts(self, info, file_pair) -> bool` where:
  - `info`: Information about the property extracted from the source code. This dictionary contains the following fields:
    - `name_in_file`: name of the property as declared in the header file
    - `declaration`: the whole line of the property declaration in the header file. This is useful because it contains the C++ type of the property
    - `params`: list of the params used in the constructor's initializer list to create the property in the implementation file (in that order):
        - The name of the property
        - The description of the property
        - The metadata object
        - The default value
  - `file_pair`: object with two properties `header` and `implementation` containing the path (as string) of the files that the property being processed belongs to
- `parse(self, property, info, file_pair) -> void` where:
    - `info` and `file_pair` are the same as in the `accepts` method
    - `property` is a dictionary where you can operate to modify the fields in the JSON output

To use your new transformer, add it to the list of [enabled transformers](property_extractor.py#L70). To see the existing transformers, check the [transformers.py](transformers.py) file.

## Definitions

The [definitions.json](definitions.json) file is merged in the output under the `definitions` field. Those definitions are used to change the types of the properties in the last stage of the generation. To change the types used in the generation, modify the file or provide another one using the `--definitions` option.
