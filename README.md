# OBS to VTS

Maps OBS Studio scenes to VTube Studio hotkeys.

https://github.com/user-attachments/assets/56b0d6f5-cd87-416e-b2fb-0e8799dc6adb

## Motivation

Playing around with VTube Studio, I wanted different zoom levels on my model
depending on the OBS scene I'm using. If you simply change your character's zoom
from OBS directly, the resolution will be very bad. It's better to zoom in VTube
Studio instead. Using this script, you can automate hotkeys when you change OBS
scenes, and thus automatically changing zoom levels in VTube Studio is now easy.

Of course, you can also use this to trigger any kind of VTS hotkey, the only
limit is your own imagination!

## Requirements

- Windows or Linux, untested on MacOS, but might work. Raise an issue if you
  need MacOS support.

- OBS Websockets 4.x.x-compat plugin

  https://github.com/obsproject/obs-websocket/releases

  This plugin relies on the `TransitionBegin` event from OBS WebSocket protocol
  4, which allows us to know what scene we are changing into as soon as you
  click on it. WebSocket protocol 5 has `CurrentProgramSceneChanged` which only
  triggers AFTER the transition, and `SceneTransitionStarted` which does not
  give any info about the next scene.

  See https://github.com/obsproject/obs-websocket/issues/983 and
  https://github.com/obsproject/obs-websocket/pull/1229 for more details.

## Download

Windows: [obs-to-vts.exe][direct-dl]

The program will generate config files in its directory, so ideally you'll want
to create a folder and put the exe inside it before running it.

<details>
  <summary>Others</summary>

  1. Install Python (tested with Python 3.12 and 3.14 only)
  2. `python -m venv venv`
  3. (Windows) `.\venv\Scripts\activate.bat`
  3. (MacOS / Linux) `source venv/bin/activate`
  4. `pip install -r requirements.txt`

  Run with: `python main.py`

</details>

## Usage

Make sure VTube Studio is open and that the "*Start API (allow plugins)*" option
in Settings > General > VTube Studio Plugins is ON.

Make sure OBS Studio is open and that the "*Enable WebSockets server*" in Tools
\> WebSockets Server Settings (4.x Compat) is ON.

Edit `config.yml` file to your convenience. When you run the tool for the first
time, this file will be created for you.

The main things you want to look for in this file are the `scenes_to_hotkeys`
and `default_hotkey` settings. Names are self-explanatory. If your scenes or
hotkeys have spaces or special characters, you MUST enclose them between quote
characters, as in the provided example.

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

## Updating

There are no automated updates. Please compare the modification date of the file
on your computer with [the date of the latest
commit](https://github.com/Tina-otoge/obs-to-vts/commits/master/). If they
differ, download the latest and release and overwrite your local files. Your
config file will NOT be deleted by this operation.


## License

MIT.

[direct-dl]: https://github.com/Tina-otoge/obs-to-vts/releases/latest/download/obs-to-vts.exe
