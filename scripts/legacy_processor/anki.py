import requests

try:
    from .const import Const
except ImportError:
    from const import Const


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
                json={"action": action, "version": 6},
                timeout=2,
            )
            response.raise_for_status()
            res_json = response.json()
            if len(params) > 0:
                # Re-send with params if needed, but AnkiConnect usually takes action + params in one go?
                # The original code did: json={"action": action, "version": 6, "params": params}
                pass
            
            # Correction: The original code logic was:
            payload = {"action": action, "version": 6}
            if params:
                payload["params"] = params
            
            response = requests.post(self.url, json=payload, timeout=2)
            return response.json()

        except requests.exceptions.RequestException:
             # Return a dict structure similar to AnkiConnect error
            return {
                "error": (
                    "Could not connect to Anki. "
                    "Is it running with AnkiConnect installed?"
                ),
                "result": None
            }

    def add_note(
        self,
        front: str,
        back: str,
        deck: str = Const.ANKI_DEFAULT_DECK,
        model: str = Const.ANKI_DEFAULT_NOTE_TYPE,
        tags: list[str] = [],
    ):
        """
        Adds a note to Anki.
        """
        params = {
            "note": {
                "deckName": deck,
                "modelName": model,
                "fields": {"Front": front, "Back": back},
                "options": {"allowDuplicate": False},
                "tags": tags or ["lex"],
            }
        }
        return self._invoke("addNote", **params)

    def create_deck(self, deck_name: str = Const.ANKI_DEFAULT_DECK):
        """
        Creates a deck if it doesn't exist.
        """
        return self._invoke("createDeck", deck=deck_name)

    def sync(self):
        """
        Trigger a sync with AnkiWeb.
        """
        return self._invoke("sync")
