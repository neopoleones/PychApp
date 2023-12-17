import os
import yaml
from cryptography.fernet import Fernet

ENV_PATH = "CFG_PATH"
DEFAULT_PATH = "etc/default.yml"


class Config:
    def __init__(self, path: str):
        # Sets the default values for configuration options
        self.env = 'dev'
        self.secret = Fernet.generate_key()

        self.rest = {
            'host': 'localhost',
            'port': 8080
        }

        self.mongo = {
            'con_link': 'mongodb://mongo:27017/',
            'db': 'pychapp'
        }

        self.__load_configuration(path)

    def __load_configuration(self, path: str):
        with open(path, 'r') as raw:
            cfg = yaml.load(raw, yaml.Loader)
            if 'pychapp' not in cfg:
                raise Exception("Incorrect configuration file provided")

            for k, v in cfg['pychapp'].items():
                if hasattr(self, k):
                    setattr(self, k, v)


def get_configuration() -> Config:
    path = os.environ.get(ENV_PATH)
    if not path:
        path = DEFAULT_PATH
    print(f"Loading the configuration: {path=}")

    return Config(path)
