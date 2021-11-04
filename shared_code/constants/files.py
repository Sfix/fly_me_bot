"""Define the constants for the files."""

# Import the libraries.
import os
from typing import Final
from dataclasses import dataclass


@dataclass(frozen=True)
class FILES:  # pylint: disable=C0103
    """Handles the constants for the files."""

    PATH_TO_DATA: Final = os.path.join(
        "C:",
        os.sep,
        "Users",
        "serge",
        "OneDrive",
        "Data Sciences",
        "Data Sciences - Ingenieur IA",
        "10e projet",
        "Deliverables",
        "data",
    )

    FRAME_RAW_DATA: Final = os.path.join(PATH_TO_DATA, "frames", "frames.json")

    SAVED_UTTERANCES_TRAIN_TEST_SETS = os.path.join(
        PATH_TO_DATA, "df_utterances Train Test Sets.pkl"
    )

    WORDS_MAKING_DESTINATION = os.path.join(
        PATH_TO_DATA, "words making Destination.json"
    )
    WORDS_MAKING_END = os.path.join(PATH_TO_DATA, "words making End.json")
    WORDS_MAKING_ORIGIN = os.path.join(PATH_TO_DATA, "words making Origin.json")
    WORDS_MAKING_START = os.path.join(PATH_TO_DATA, "words making Start.json")

    UTTERANCES_GREETINGS = os.path.join(PATH_TO_DATA, "utterances Greetings.json")
    UTTERANCES_HELP = os.path.join(PATH_TO_DATA, "utterances Help.json")

    TRAIN_JSON = os.path.join(PATH_TO_DATA, "json_train.json")

    TEST_JSON = os.path.join(PATH_TO_DATA, "json_test.json")
