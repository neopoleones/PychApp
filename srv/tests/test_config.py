import yaml
import pytest
from srv.app.cfg.loader import Config
from cryptography.fernet import Fernet
from unittest.mock import mock_open, patch


class TestConfig:

    @patch("builtins.open", new_callable=mock_open,
           read_data="pychapp:\n  env: 'prod'\n  secret: 'abcdef'\n")
    def test_init_loads_config(self, mock_file):
        config = Config("path/to/config")

        assert config.env == 'prod'
        assert config.secret == 'abcdef'

    @patch("builtins.open", new_callable=mock_open,
           read_data="pychapp:\n  env: 'prod'\n")
    def test_init_sets_default_values(self, mock_file):
        config = Config("path/to/config")

        assert config.env == 'prod'
        assert isinstance(config.secret, bytes)
        assert config.rsa_secret == "superSe-cure"

    @patch("builtins.open", new_callable=mock_open,
           read_data="invalid:\n  data: 'data'\n")
    def test_init_raises_exception_for_invalid_config(self, mock_file):
        with pytest.raises(Exception):
            Config("path/to/config")

    @patch("builtins.open", new_callable=mock_open,
           read_data="pychapp:\n  rest:\n    host: '127.1'\n    port: 9090")
    def test_init_loads_nested_config(self, mock_file):
        config = Config("path/to/config")

        assert config.rest['host'] == '127.1'
        assert config.rest['port'] == 9090
