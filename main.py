import asyncio
import enum
import logging
import shutil
import signal
import sys
from argparse import ArgumentParser
from enum import StrEnum
from pathlib import Path

import pyvts

# OBS WS 5
# from simpleobsws import IdentificationParameters, WebSocketClient
# OBS WS 4
import simpleobsws
import yaml
from pydantic import BaseModel, Field

OBS_EVENT_SCENES = 1 << 2
CONFIG_PATH = "config.yml"
DEFAULT_CONFIG_PATH = "config.default.yml"

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
        # by default, TriggerAnimation -> "triggeranimation"
        # change to TriggerAnimation -> "TriggerAnimation"
        def _generate_next_value_(name, start, count, last_values):
            return name

        TriggerAnimation = enum.auto()
        ToggleExpression = enum.auto()
        RemoveAllExpressions = enum.auto()
        MoveModel = enum.auto()

        def __repr__(self):
            return f"{self.__class__.__name__}.{self.name}"

    name: str
    type: Type
    description: str
    file: str
    id: str = Field(alias="hotkeyID")
    keys: list = Field(alias="keyCombination")
    button_id: int = Field(alias="onScreenButtonID")


class Config(BaseModel):
    class OBS(BaseModel):
        address: str = "localhost"
        port: int = 4444
        password: str | None = None

    class VTS(BaseModel):
        address: str = "localhost"
        port: int = 8001

    obs: OBS
    vts: VTS
    transition_delay_ms: int = 0
    transition_delay_half: bool = False
    scenes_to_hotkeys: dict[str, str]
    default_hotkey: str | None


async def get_hotkeys(vts_plugin: pyvts.vts) -> dict[str, HotKey]:
    response_data = await vts_plugin.request(
        vts_plugin.vts_request.requestHotKeyList()
    )
    hotkeys_by_name = {
        item.name: item
        for item in (
            HotKey(**item) for item in response_data["data"]["availableHotkeys"]
        )
    }
    return hotkeys_by_name


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
    await vts_plugin.connect()
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
    await obs_client.connect()
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
            await asyncio.sleep(delay / 1000)
            await trigger_hotkey(vts_plugin, hotkey)

        asyncio.create_task(exec_after_delay())

    return on_switchscenes


def get_config() -> Config:
    config_path = Path("config.yml")
    if not config_path.exists():
        logger.info("Config file not found, creating default config.yml")
        default_config_path = Path("config.default.yml")
        if not default_config_path.exists():
            raise FileNotFoundError(
                "Default config file not found. Please create config.yml manually."
            )
        shutil.copy(default_config_path, config_path)

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
        "Available Hotkeys: %s",
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
        loop.run_until_complete(main())
    finally:
        loop.close()
