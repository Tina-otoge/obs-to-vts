# OBS to VTS

Maps OBS Studio scenes to VTube Studio hotkeys.

## Requirements

- Python

  Tested with Python 3.14.0, some older versions may work, please raise an Issue
  if your version is not supported.

## Usage

On Windows, you can use the provided `run.bat`.

If you are not on Windows or wish to install dependencies your own way, use your
preferred method to install dependencies from the `requirements.txt` file, and
run `main.py`.

Example:
1. `python -m venv .venv`
2. (Windows) `.\venv\Scripts\activate.bat`
3. (MacOS / Linux) `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python main.py`

Then, create or modify the `config.yml` file with your specific setup. When you
run the script for the first time, this file will be created for you.

The main things you want to look for in this file are the `scenes_to_hotkeys`
and `default_hotkey` settings. Names are self-explanatory. If your values have
spaces or special characters, you MUST enclose them between quote characters, as
in the provided example.

OBS and VTS connection settings can also be configured from this file.

You can also overwrite the connection settings using the following command-line
parameters: `--obs-host`, `--obs-port`, `--obs-password`, `--vts-host`, and
`--vts-port`.

## License

MIT.
