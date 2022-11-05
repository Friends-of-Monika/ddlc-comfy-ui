# Building ComfyUI

## Prerequisites

For building ComfyUI you'll need:
* Inkscape installed and available at PATH; to check if it is installed
  correctly, open your terminal on Linux/MacOS or cmd.exe/PowerShell on Windows
  and type:

  ```shell
  inkscape --version
  ```

  If you didn't get 'command not found' sort of error but some meaningful
  output, you have it installed right.
* Python 3 and PIP installed; similarly to Inkscape, to check if it is installed
  type the following in command line:

  ```shell
  python3 -m pip --version
  ```

### Setting up environment

Before you proceed to installing dependencies, create and enter Python virtual
environment:

```shell
python3 -m venv venv
source venv/bin/activate
```

### Installing dependencies

Install Python dependencies with `pip`:

```shell
python3 -m pip install -r requirements.txt
```

## Building submod

Once everything is set, run the following command to build submod:

```shell
python3 Make.py -t mas
```