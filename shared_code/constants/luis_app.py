"""Define the constants for the files."""

# Import the libraries.
import os
from typing import Final
from typing import Dict
from dataclasses import dataclass
from dataclasses import field

from shared_code.constants.utterances import UTTERANCES
from shared_code.constants.files import FILES


class LUIS_APPS:  # pylint: disable=C0103
    """Handles the constants for the LUIS App."""

    VERSION_ID: Final = "0.1"
    NAME: Final = "Fly me"
    DESCRIPTION: Final = "LUIS App for Fly me"

    INTENT_SPECIFY_JOURNEY_NAME: Final[str] = "Specify journey name"
    INTENT_GREETINGS_NAME: Final[str] = "Greetings name"
    INTENT_HELP_NAME: Final[str] = "Help name"
    INTENTS: Final[Dict[str, str]] = {
        INTENT_SPECIFY_JOURNEY_NAME: "Specify_journey",
        INTENT_GREETINGS_NAME: "Greetings",
        INTENT_HELP_NAME: "Help",
    }
    NONE_INTENT = "NoneIntent"
    THREESHOLD_FOR_VALID_INTENT = 0.20

    ENTITIES: Final[Dict[str, str]] = {
        "From place name": UTTERANCES.ENTITY_FROM_PLACE,
        "To place name": UTTERANCES.ENTITY_TO_PLACE,
        "From date name": UTTERANCES.ENTITY_FROM_DATE,
        "To date name": UTTERANCES.ENTITY_TO_DATE,
        "Max budget": UTTERANCES.ENTITY_MAX_BUDGET,
    }

    FEATURES: Final[Dict[str, Dict[str, str]]] = {
        "origin phrases list": {
            "name": "Origin words",
            "file": FILES.WORDS_MAKING_ORIGIN,
        },
        "destination phrases list": {
            "name": "Destination words",
            "file": FILES.WORDS_MAKING_DESTINATION,
        },
        "starting phrases list": {
            "name": "Starting words",
            "file": FILES.WORDS_MAKING_START,
        },
        "ending phrases list": {
            "name": "Ending words",
            "file": FILES.WORDS_MAKING_END,
        },
    }
