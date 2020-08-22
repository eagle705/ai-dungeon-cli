import os
from typing import Dict
import argparse
import yaml


# -------------------------------------------------------------------------
# UTILS: DICT

def exists(cfg: Dict[str, str], key: str) -> str:
    return key in cfg and cfg[key]


# -------------------------------------------------------------------------
# CONF OBJECT

class Config:
    def __init__(self):
        self.prompt: str = "> "
        # self.user_name: str = None

        self.slow_typing_effect: bool = False

        self.debug: bool = False

        self.auth_token: str = None
        self.email: str = None
        self.scene: str = None
        self.voice: str = None
        self.tts: str = None
        self.asr: str = None
        self.linebot: str = None
        self.gpt: int = None
        self.mt: str = None
        self.temperature: float = 0.5
        self.locale: str = None
        self.password: str = None

    @staticmethod
    def merged(confs):
        default_conf = Config()
        conf = Config()
        for c in confs:
            for a in ['prompt', 'scene', 'debug', 'locale', 'voice', 'tts', 'asr', 'mt', 'temperature', 'gpt','linebot',
                      'auth_token']:
                v = getattr(c, a)
                if getattr(default_conf, a) != v:
                    setattr(conf, a, v)
        return conf


    @staticmethod
    def loaded_from_cli_args():
        conf = Config()
        conf.load_from_cli_args()
        return conf

    def load_from_cli_args(self):
        parsed = Config.parse_cli_args()
        if hasattr(parsed, "debug"):
            self.debug = parsed.debug
        if hasattr(parsed, "prompt"):
            self.prompt = parsed.prompt
        if hasattr(parsed, "scene"):
            self.scene = parsed.scene
        if hasattr(parsed, "tts"):
            self.tts = parsed.tts
        if hasattr(parsed, "asr"):
            self.asr = parsed.asr
        if hasattr(parsed, "linebot"):
            self.linebot = parsed.linebot
        if hasattr(parsed, "mt"):
            self.mt = parsed.mt
        if hasattr(parsed, "gpt"):
            self.gpt = parsed.gpt
        if hasattr(parsed, "temperature"):
            self.temperature = parsed.temperature
        if hasattr(parsed, "voice"):
            self.voice = parsed.voice
        if hasattr(parsed, "locale"):
            self.locale = parsed.locale
        if hasattr(parsed, "auth_token"):
            self.auth_token = parsed.auth_token
            # if exists(cfg, "user_name"):
            #     self.user_name = cfg["user_name"]

    @staticmethod
    def parse_cli_args():
        parser = argparse.ArgumentParser(description='ai-dungeon-cli is a command-line client to play.aidungeon.io')
        parser.add_argument("--debug", action='store_const', const=True,
                            help="enable debug")
        parser.add_argument("--prompt", type=str, required=False, default="> ",
                            help="text for user prompt")

        parser.add_argument("--auth-token", type=str, required=True,
                            help="authentication token")

        parser.add_argument("--scene", type=str, required=True,
                            help="scene file. (scenes/qa),(scenes/restaurant),...")

        parser.add_argument("--voice", type=str, required=False,
                            help="voice actor for 'say'")

        parser.add_argument("--tts", type=str, required=False, default="say",
                            help="text-to-speech driver. say/nes,[url]")

        parser.add_argument("--asr", type=str, required=False, default="google",
                            help="speech recognition driver google/nest,[url]")

        parser.add_argument("--gpt", type=int, required=False, default=3,
                            help="gpt version to use. 2/3")

        parser.add_argument("--linebot", type=str, required=False, default="",
                            help="line bot [channel],[secret]")

        parser.add_argument("--mt", type=str, required=False, default="google",
                            help="machine translation driver google/papago,[id],[secret]")
                            
        parser.add_argument("--temperature", type=float, required=False, default=1.0,
                            help="temperature for generation (recommended range: 0.5 ~ 2)")

        parser.add_argument("--locale", type=str, default="ko-KR",
                            help="locale")

        return parser.parse_args()


    @staticmethod
    def loaded_from_file():
        conf = Config()
        conf.load_from_file()
        return conf

    def load_from_file(self):
        cfg_file = "/config.yml"
        cfg_file_paths = [
            os.path.dirname(os.path.realpath(__file__)) + cfg_file,
            os.path.expanduser("~") + "/.config/ai-dungeon-cli" + cfg_file,
        ]

        did_read_cfg_file = False

        cfg = {}
        for file in cfg_file_paths:
            try:
                with open(file, "r") as cfg_raw:
                    cfg = yaml.load(cfg_raw, Loader=yaml.FullLoader)
                    did_read_cfg_file = True
            except IOError:
                pass

        if exists(cfg, "prompt"):
            self.prompt = cfg["prompt"]
        if exists(cfg, "auth_token"):
            self.auth_token = cfg["auth_token"]
        
