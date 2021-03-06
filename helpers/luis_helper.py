# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# Transform by Serge Neuman pf the P of OC

import logging
logger = logging.getLogger("Luis Helper")
logger.setLevel(level= logging.INFO)
logger.info("Je suis on...")


from enum import Enum
from typing import (Dict, Tuple)
from botbuilder.ai.luis import LuisRecognizer
from botbuilder.core import IntentScore, TopIntent, TurnContext

from journey_details import Journey_details

from shared_code.constants.luis_app import LUIS_APPS
from datetime import datetime as dt


def top_intent(intents: Dict[LUIS_APPS, dict]) -> TopIntent:
    """Return the top intent.

    Args:
        intents (Dict[Intent, dict]): the intents discovered by Luis

    Returns:
        TopIntent: The top intent found.
    """
    max_intent = LUIS_APPS.NONE_INTENT
    max_value = 0.0

    for intent, value in intents:
        intent_score = IntentScore(value)
        if intent_score.score > max_value:
            max_intent, max_value = intent, intent_score.score

    return TopIntent(max_intent, max_value)


class LuisHelper:
    """Handle the communication with Luis."""

    @staticmethod
    async def execute_luis_query(
        luis_recognizer: LuisRecognizer, turn_context: TurnContext
    ) -> Tuple[LUIS_APPS, object]:
        """Return an object with preformatted LUIS results for the bot's dialogs to consume."""
        result = None
        intent = None

        try:
            recognizer_result = await luis_recognizer.recognize(turn_context)

        except Exception as exception:
            logger.info(f"Pb: {exception}")
            print(exception)


        intent = (
                    sorted(
                            recognizer_result.intents,
                            key=recognizer_result.intents.get,
                            reverse=True,
                    )[:1][0]
                    if recognizer_result.intents
                    else None
        )

        # Check that Luis has found something with enough confidence.
        if recognizer_result.intents[intent].score < LUIS_APPS.THREESHOLD_FOR_VALID_INTENT:
            return None, recognizer_result.entities

        if intent is None:
            return None, None

        # Check if we have a greeting and if yes, which one
        if intent == LUIS_APPS.INTENTS[LUIS_APPS.INTENT_GREETINGS_NAME]:
            result = "Hey"
            return intent, result

        # Check if we have a request for Help
        if intent == LUIS_APPS.INTENTS[LUIS_APPS.INTENT_HELP_NAME]:
            return intent, None

        # We have to decode the journey now
        if intent != LUIS_APPS.INTENTS[LUIS_APPS.INTENT_SPECIFY_JOURNEY_NAME]:
            return None, None
        # logger.info("Need to decode the intent.")
# TODO SERGE : Retrouver les donnees deja trouvees
        result = Journey_details()

        found_cities = recognizer_result.entities.get(
                                                        'geographyV2_city',
                                                        None
        )
        to_place = recognizer_result.entities.get(
                        LUIS_APPS.ENTITIES["To place name"].replace(' ', '_'),
                        None
        )
        from_place = recognizer_result.entities.get(
                    LUIS_APPS.ENTITIES["From place name"].replace(' ', '_'),
                    None
        )
        if to_place is not None:
            for city in found_cities:
                if city in to_place[0]:
                    result.destination = city
                    break
        elif from_place is not None:
            if from_place[0].lower() == turn_context.activity.text.lower():
                result.destination = from_place[0]


        if from_place is not None:
            for city in found_cities:
                if city in from_place[0]:
                    result.origin = city
                    break
        elif to_place is not None:
            if to_place[0].lower() == turn_context.activity.text.lower():
                result.origin = to_place[0]


        # This value will be a TIMEX. And we are only interested in a Date
        #  so grab the first result and drop the Time part. TIMEX is a
        # format that represents DateTime expressions that include some ambiguity.
        # e.g. missing a Year.
        date_entities = recognizer_result.entities.get("datetime", [])
        from_date = recognizer_result.entities.get(
                        LUIS_APPS.ENTITIES["From date name"].replace(' ', '_'),
                        None
        )
        to_date = recognizer_result.entities.get(
                    LUIS_APPS.ENTITIES["To date name"].replace(' ', '_'),
                    None
        )
        if len(date_entities) == 1:
            if date_entities[0]['type'] == 'date':
                timex = date_entities[0]['timex']
                if from_date is not None:
                    result.departure_date = timex[0].split("T")[0]
                if to_date is not None:
                    result.return_date = timex[0].split("T")[0]
        elif len(date_entities) == 2:
            try:
                if date_entities[0]['type'] == 'date':
                    result.departure_date = date_entities[0]['timex'][0].split("T")[0]
                if date_entities[1]['type'] == 'date':
                    result.return_date = date_entities[1]['timex'][0].split("T")[0]
                    if (
                        dt.strptime(result.return_date, '%Y-%m-%d')
                            - dt.strptime(result.departure_date, '%Y-%m-%d')
                    ).days < 0:
                        tmp = result.return_date
                        result.return_date = result.departure_date
                        result.departure_date =  tmp
            except:
                if "XX" in result.return_date:
                    result.return_date = None
                if "XX" in result.departure_date:
                    result.departure_date = None

        budget_entity = recognizer_result.entities.get(
                                                        "money",
                                                        None
        )
        if budget_entity is not None:
            result.max_budget = budget_entity[0]

        return intent, result
