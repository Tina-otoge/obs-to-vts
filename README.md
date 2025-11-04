# OBS to VTS

Maps OBS Studio scenes to VTube Studio hotkeys.

## Motivation

Playing around with VTube Studio, I wanted different zoom levels on my model
depending on the OBS scene I'm using. If you simply change your character's zoom
from OBS directly, the resolution will be very bad. It's better to zoom in VTube
Studio instead. Using this script, you can automate hotkeys when you change OBS
scenes, and thus automatically changing zoom levels in VTube Studio for example.

Of course, you can also use this to trigger any kind of hotkey, the only limit
is your own imagination!

## Requirements

- Windows or Linux, untested on MacOS, but might work. Raise an issue if you
  need MacOS support.

- Python

  Tested with Python 3.12 and 3.14, some older versions may work, please raise
  an issue if your version is not supported.

- OBS Websockets 4.x.x-compat plugin

  https://github.com/obsproject/obs-websocket/releases

  This plugin relays on the `TransitionBegin` event from OBS WebSocket protocol
  4, which allows us to know what scene we are changing into as soon as you
  click on it. WebSocket protocol 5 has `CurrentProgramSceneChanged` which only
  triggers AFTER the transition, and `SceneTransitionStarted` which does not
  give any info about the next scene.

## Usage

Make sure VTube Studio is open and that the "*Start API (allow plugins)*" option
in Settings > General > VTube Studio Plugins is ON.

Make sure OBS Studio is open and that the "*Enable WebSockets server*" in Tools
\> WebSockets Server Settings (4.x Compat) is ON.

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

Setting a default hotkey is highly recommended. Imagine you have Scene A bound
to hotkey ZoomX2, and Scene B bound to ZoomX5, if you click on Scene C and it is
not bound to any hotkey, your character will be using a different zoom level
depending on if you were using Scene A or Scene B before!

You can add a custom delay before firing the hotkey using `transition_delay_ms`.

When `transition_delay_half` is set to `true`, it will trigger the hotkey at
exactly half of the current transition, no matter the value you have set for
`transition_delay_ms`.

OBS and VTS connection settings can also be configured from this file.

You can also overwrite the connection settings using the following command-line
parameters: `--obs-host`, `--obs-port`, `--obs-password`, `--vts-host`, and
`--vts-port`.

## License

MIT.
