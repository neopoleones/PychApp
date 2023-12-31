import os
import yaml
from cryptography.fernet import Fernet

ENV_PATH = "CFG_PATH"
DEFAULT_PATH = "etc/default.yml"


class Config:
    """
    A class to manage configuration settings from a YAML file.

    Attributes:
        env: Environment setting, defaults to 'dev'.
        secret: Secret key for encryption, generated using Fernet.
        rsa_secret: RSA secret key.
        rest: Configuration for REST API including host and port.
        mongo: MongoDB connection settings including connection
            link and database name.
    """

    def __init__(self, path: str):
        """
        Initializes the configuration class

        Args:
            path: The file path to the YAML configuration file.

        Raises:
            Exception: If the configuration file is incorrect or missing
                required sections.
        """

        self.env = 'dev'
        self.secret = Fernet.generate_key()
        self.rsa_secret = "superSe-cure"

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
        """
        Private method to load values from yaml using builtin python functions

        Args:
            path: The file path to the YAML configuration file.
        """

        with open(path, 'r') as raw:
            cfg = yaml.load(raw, yaml.Loader)
            if 'pychapp' not in cfg:
                raise Exception("Incorrect configuration file provided")

            for k, v in cfg['pychapp'].items():
                if hasattr(self, k):
                    setattr(self, k, v)


def get_configuration() -> Config:
    """
    Loads and returns a Config object based on the environment
    configuration file.

    Returns:
        Config: The configuration object initialized
        with settings from the file.

    Notes:
        The file path is determined by the environment variable
        ENV_PATH, with a default fallback.
    """

    path = os.environ.get(ENV_PATH)
    if not path:
        path = DEFAULT_PATH
    print(f"Loading the configuration: {path=}")

    return Config(path)
