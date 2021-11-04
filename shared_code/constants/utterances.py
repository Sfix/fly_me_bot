"""Define the constants for the utterances."""

# Import the libraries.
import os
from typing import Final
from dataclasses import dataclass


@dataclass(frozen=True)
class UTTERANCES:  # pylint: disable=C0103
    """Handles the constants for the Utterances."""

    ENTITY_FROM_PLACE: Final = "From place"
    ENTITY_TO_PLACE: Final = "To place"
    ENTITY_FROM_DATE: Final = "From date"
    ENTITY_TO_DATE: Final = "To date"
    ENTITY_MAX_BUDGET: Final = "Max budget"

    ENTITY_FROM_PLACE_IN_FRAMES: Final = "or_city"
    ENTITY_TO_PLACE_IN_FRAMES: Final = "dst_city"
    ENTITY_FROM_DATE_IN_FRAMES: Final = "str_date"
    ENTITY_TO_DATE_IN_FRAMES: Final = "end_date"
    ENTITY_MAX_BUDGET_IN_FRAMES: Final = "budget"
