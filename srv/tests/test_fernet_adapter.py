import pytest
import cryptography.exceptions
from srv.app.storage.provider import FernetAdapter


def get_adapter(secret):
    return FernetAdapter(secret=secret)


def test_bad_secret():
    with pytest.raises(ValueError):
        _ = get_adapter(b"Secret is not 32 url-safe base64-encoded bytes ")
        pytest.fail("Should fail")


def test_encode_decode_good_secret():
    test_message = b"hello world"
    sa = get_adapter(b"Pls68m35-oXRfEo1HAPKPyjI3SPiC-3UP140vn1xisU=")

    assert test_message == sa.decrypt(sa.encrypt(test_message))


def test_encode_decode_bad_secret():
    test_message = b"hello world"
    sa = get_adapter(b"Pls68m35-oXRfEo1HAPKPyjI3SPiC-3UP140vn1xisU=")

    enc_message = sa.encrypt(test_message)
    sa = get_adapter(b"rvurXglBtj93e3jp9ByXHAp9p-PKYMLzqX997EqaGjM=")

    with pytest.raises(cryptography.fernet.InvalidToken):
        sa.decrypt(enc_message)
