import requests

from .const import Const


class AnkiConnectClient:
    """
    Client for interacting with Anki via AnkiConnect.
    """

    def __init__(self, url: str = Const.ANKI_URL):
        self.url = url

    def _invoke(self, action, **params):
        try:
            response = requests.post(
                self.url,
                json={"action": action, "version": 6, "params": params},
            )
            return response.json()
        except requests.exceptions.ConnectionError:
            return {
                "error": (
                    "Could not connect to Anki. "
                    "Is it running with AnkiConnect installed?"
                )
            }

    def add_note(
        self,
        lemma: str,
        context: str,
        deck: str = Const.ANKI_DEFAULT_DECK,
        model: str = Const.ANKI_DEFAULT_NOTE_TYPE,
    ):
        """
        Adds a note to Anki.
        """
        params = {
            "note": {
                "deckName": deck,
                "modelName": model,
                "fields": {"Front": lemma, "Back": context},
                "options": {"allowDuplicate": False},
                "tags": ["lex"],
            }
        }
        return self._invoke("addNote", **params)

    def create_deck(self, deck_name: str = Const.ANKI_DEFAULT_DECK):
        """
        Creates a deck if it doesn't exist.
        """
        return self._invoke("createDeck", deck=deck_name)
