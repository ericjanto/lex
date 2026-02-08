import pytest
import responses

from .anki import AnkiConnectClient
from .const import Const


@pytest.fixture
def anki_client():
    return AnkiConnectClient()


@responses.activate
def test_add_note_success(anki_client):
    responses.add(
        responses.POST,
        Const.ANKI_URL,
        json={"result": 12345, "error": None},
        status=200,
    )

    result = anki_client.add_note("test_lemma", "test_context")
    assert result["result"] == 12345
    assert result["error"] is None


@responses.activate
def test_add_note_error(anki_client):
    responses.add(
        responses.POST,
        Const.ANKI_URL,
        json={"result": None, "error": "deck not found"},
        status=200,
    )

    result = anki_client.add_note("test_lemma", "test_context")
    assert result["error"] == "deck not found"


@responses.activate
def test_anki_connection_error(anki_client):
    # No response added, will trigger connection error
    result = anki_client.add_note("test_lemma", "test_context")
    assert "error" in result
    assert "Could not connect" in result["error"]
