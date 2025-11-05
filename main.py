import asyncio
import contextlib
import enum
import io
import logging
import signal
import sys
from argparse import ArgumentParser
from enum import StrEnum
from pathlib import Path

import pyvts
import yaml
from pydantic import BaseModel, Field

""
# OBS WS 5
# from simpleobsws import IdentificationParameters, WebSocketClient
# OBS WS 4
import simpleobsws

OBS_EVENT_SCENES = 1 << 2
CONFIG_PATH = "config.yml"

pyvts.config.plugin_default["plugin_name"] = "OBS-to-VTS"
pyvts.config.plugin_default["developer"] = "Tina"

API_CONNECTION_INFO = pyvts.config.vts_api.copy()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("log.txt")
file_handler.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
for handler in (file_handler, console_handler):
    logger.addHandler(handler)


class HotKey(BaseModel):
    class Type(StrEnum):
        def _generate_next_value_(name, start, count, last_values):
            return name

        TriggerAnimation = enum.auto()
        ToggleExpression = enum.auto()
        RemoveAllExpressions = enum.auto()
        MoveModel = enum.auto()

        def __repr__(self):
            return f"{self.__class__.__name__}.{self.name}"

    name: str
    # my Type enum is probably not complete, let's not risk a crash
    # for people with more esoteric hotkeys or if VTS ever add more
    # in the future
    # type: Type
    type: str
    description: str
    file: str
    id: str = Field(alias="hotkeyID")
    keys: list = Field(alias="keyCombination")
    button_id: int = Field(alias="onScreenButtonID")


class Config(BaseModel):
    class OBS(BaseModel):
        address: str = "localhost"
        port: int = 4444
        password: str | None = Field(coerce_numbers_to_str=True, default=None)

    class VTS(BaseModel):
        address: str = "localhost"
        port: int = 8001

    obs: OBS = OBS()
    vts: VTS = VTS()
    transition_delay_ms: int = 0
    transition_delay_half: bool = False
    scenes_to_hotkeys: dict[str, str] = {
        "Scene": "My Animation 1",
        "Scene 2": "My Animation 2",
        "Scene 3": "My Animation 3",
    }
    default_hotkey: str | None = "My Animation 1"


async def get_hotkeys(vts_plugin: pyvts.vts) -> dict[str, HotKey]:
    response_data = await vts_plugin.request(
        vts_plugin.vts_request.requestHotKeyList()
    )
    return {
        item.name: item
        for item in (
            HotKey(**item) for item in response_data["data"]["availableHotkeys"]
        )
    }


async def trigger_hotkey(vts_plugin: pyvts.vts, hotkey_name: str):
    hotkeys_by_name = await get_hotkeys(vts_plugin)
    hotkey = hotkeys_by_name.get(hotkey_name)
    if not hotkey:
        logger.warning(f"Hotkey '{hotkey_name}' not found.")
        return
    logger.info(f"Triggering hotkey: {hotkey.name}")
    await vts_plugin.request(
        vts_plugin.vts_request.requestTriggerHotKey(hotkeyID=hotkey.id)
    )


async def init_vts(host: str, port: int) -> pyvts.vts:
    vts_plugin = pyvts.vts()
    pyvts.config.vts_api["host"] = host
    pyvts.config.vts_api["port"] = port
    logger.info(f"Connecting to VTS at {host}:{port}...")
    try:
        await vts_plugin.connect()
    except Exception as e:
        logger.error(
            "Failed to connect to VTube Studio API. Is VTS running and the"
            " plugin API enabled?"
        )
        raise e
    logger.info(
        "Authenticating with VTS... If this is the first time, you may need to"
        " accept the application from VTube Studio's window."
    )
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            await vts_plugin.request_authenticate_token()
        tried_resetting_token = False
        while not (await vts_plugin.request_authenticate()):
            if tried_resetting_token:
                logger.error("Failed to authenticate with VTube Studio API.")
                sys.exit(1)
            logger.warning(
                "Authentication with VTube Studio API failed, resetting token and"
                " retrying..."
            )
            await vts_plugin.request_authenticate_token(force=True)
            tried_resetting_token = True
    except Exception as e:
        logger.error("Failed to authenticate with VTube Studio API.")
        raise e
    logger.info("Successfully connected to VTS.")
    return vts_plugin


# OBS WS 5
# async def init_obs(host: str, port: int, password: str) -> WebSocketClient:
#     obs_client = WebSocketClient(
#         url=f"ws://{host}:{port}",
#         password=password,
#         identification_parameters=IdentificationParameters(
#             eventSubscriptions=OBS_EVENT_SCENES
#         ),
#     )
#     await obs_client.connect()
#     await obs_client.wait_until_identified()
#     return obs_client


# OBS WS 4
async def init_obs(host: str, port: int, password: str):
    obs_client = simpleobsws.obsws(host=host, port=port, password=password)
    logger.info(
        f"Connecting to OBS at {host}:{port} (password={bool(password)})..."
    )
    try:
        await obs_client.connect()
    except Exception as e:
        logger.error(
            "Failed to connect to OBS. Is OBS running and WebSocket 4.x"
            " enabled?"
        )
        raise e
    logger.info("Successfully connected to OBS.")
    return obs_client


def create_switchscenes_handler(vts_plugin: pyvts.vts, config: Config):
    # OBS WS 5
    # async def on_switchscenes(event):
    #     if event["eventType"] != "CurrentProgramSceneChanged":
    #         return
    #     scene_name = event["eventData"]["sceneName"]
    #     logger.info(f"OBS switched to scene: {scene_name}")
    #     hotkey = config.scenes_to_hotkeys.get(scene_name, config.default_hotkey)
    #     if not hotkey:
    #         logger.info(f"No hotkey mapped for scene '{scene_name}', skipping.")
    #         return
    #     await trigger_hotkey(vts_plugin, hotkey)

    # OBS WS 4 SwitchScenes
    # async def on_switchscenes(event):
    #     print(event)
    #     scene_name = event["scene-name"]
    #     logger.info(f"OBS switched to scene: {scene_name}")
    #     hotkey = config.scenes_to_hotkeys.get(scene_name, config.default_hotkey)
    #     if not hotkey:
    #         logger.info(f"No hotkey mapped for scene '{scene_name}', skipping.")
    #         return
    #     await trigger_hotkey(vts_plugin, hotkey)

    # OBS WS 4 TransitionBegin
    async def on_switchscenes(event):
        logger.info(f"Received OBS event: {event}")
        scene_name = event["to-scene"]
        logger.info(f"OBS switched to scene: {scene_name}")
        hotkey = config.scenes_to_hotkeys.get(scene_name, config.default_hotkey)
        if not hotkey:
            logger.info(f"No hotkey mapped for scene '{scene_name}', skipping.")
            return

        async def exec_after_delay():
            if config.transition_delay_half:
                delay = event["duration"] / 2
            else:
                delay = config.transition_delay_ms
            if delay:
                logging.info(f"Waiting {delay}ms before firing hotkey...")
                await asyncio.sleep(delay / 1000)
            await trigger_hotkey(vts_plugin, hotkey)

        asyncio.create_task(exec_after_delay())

    return on_switchscenes


def generate_default_config() -> str:
    default_config = Config()
    dump = yaml.safe_dump(default_config.model_dump(), sort_keys=False)
    comments = {
        "default_hotkey": [
            "Hotkey to trigger when no scene match is found",
            "Set to null to disable changing the animation in that case",
            "Not recommended, it's best to have a default animation.",
        ],
        "transition_delay_ms": [
            "Delay in milliseconds before triggering the hotkey after a"
            " scene change",
            "Useful if you want to hide the transition behind a stinger video,"
            " in this",
            "case, you probably want to match the value of the"
            " Transition Point in OBS",
            "Set to 0 to disable",
        ],
        "transition_delay_half": [
            "Set to true to wait half of the transition delay before triggering"
            " the hotkey",
            "This bypasses the transition_delay_ms setting entirely",
        ],
    }
    result = ""
    for line in dump.splitlines():
        # Add newline between sections
        if result and not line.startswith(" "):
            result += "\n"

        # Add comments if any
        key = line.split(":", 1)[0]
        if key in comments:
            for comment in comments[key]:
                result += f"# {comment}\n"
        spaces = line[: len(line) - len(line.lstrip())]

        # Reformat key and value to quote strings with spaces when they span
        # multiple words
        pair = line.split(":", 1)
        for x in (0, 1):
            pair[x] = pair[x].strip()
            if " " in pair[x]:
                pair[x] = f'"{pair[x]}"'
        key, value = pair
        result += f"{spaces}{key}: {value}\n"

    return result


def get_config() -> Config:
    config_path = Path("config.yml")
    if not config_path.exists():
        logger.info("Config file not found, creating default config.yml")
        default_config = generate_default_config()
        with config_path.open("w") as f:
            f.write(default_config)

    with config_path.open("r") as f:
        data = yaml.safe_load(f)
    return Config(**data)


async def main():
    config = get_config()
    parser = ArgumentParser()
    parser.add_argument(
        "--vts-host",
        type=str,
        default=config.vts.address or API_CONNECTION_INFO["host"],
        help="VTube Studio host",
    )
    parser.add_argument(
        "--vts-port",
        type=int,
        default=config.vts.port or API_CONNECTION_INFO["port"],
        help="VTube Studio port",
    )
    parser.add_argument(
        "--obs-host",
        type=str,
        default=config.obs.address or "localhost",
        help="OBS WebSocket host",
    )
    parser.add_argument(
        "--obs-port",
        type=int,
        default=config.obs.port or 4455,
        help="OBS WebSocket port",
    )
    parser.add_argument(
        "--obs-password",
        type=str,
        default=config.obs.password or None,
        help="OBS WebSocket password",
    )
    args = parser.parse_args()

    vts_plugin = await init_vts(args.vts_host, args.vts_port)
    obs_client = await init_obs(args.obs_host, args.obs_port, args.obs_password)
    logger.info(
        "Available VTS Hotkeys: %s",
        [x.name for x in (await get_hotkeys(vts_plugin)).values()],
    )
    logger.info("Triggering default hotkey")
    await trigger_hotkey(vts_plugin, config.default_hotkey)
    on_switchscenes = create_switchscenes_handler(vts_plugin, config)
    # OBS WS 5
    # obs_client.register_event_callback(on_switchscenes)
    # OBS WS 4 SwitchScenes
    # obs_client.register(on_switchscenes, "SwitchScenes")
    # OBS WS 4 TransitionBegin
    obs_client.register(on_switchscenes, "TransitionBegin")

    async def shutdown():
        await vts_plugin.close()
        await obs_client.disconnect()
        loop.stop()

    loop = asyncio.get_running_loop()
    if sys.platform != "win32":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig, lambda: asyncio.create_task(shutdown())
            )

    await asyncio.Future()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        try:
            loop.run_until_complete(main())
        except Exception as e:
            logger.error("Unhandled exception: %s", e)
            logger.debug("Exception details:", exc_info=True)
            input("Press Enter to exit...")
    except KeyboardInterrupt:
        pass
