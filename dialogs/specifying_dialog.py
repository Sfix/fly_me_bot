# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Flight booking dialog."""

from datatypes_date_time.timex import Timex

from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.dialogs.prompts import (
                                        TextPrompt,
                                        DateTimePrompt,
                                        ConfirmPrompt,
                                        PromptOptions,
                                        PromptValidatorContext,
)
from botbuilder.core import MessageFactory, BotTelemetryClient, NullTelemetryClient
from sample_21.journey_details import Journey_details

from shared_code.constants.luis_app import LUIS_APPS
from .cancel_and_help_dialog import CancelAndHelpDialog
# from .date_resolver_dialog import DateResolverDialog
from journey_specifier_recognizer import Journey_specifier_recognizer


from helpers.luis_helper import LuisHelper


class Specifying_dialog(CancelAndHelpDialog):
    """Journey specification implementation."""

    def __init__(
        self,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient()
    ):
        """Init the class.

        Args:
            dialog_id (str, optional): Defaults to None.
            telemetry_client (BotTelemetryClient, optional): Insight. Defaults to NullTelemetryClient().
        """
        super(Specifying_dialog, self).__init__(
            dialog_id or Specifying_dialog.__name__, telemetry_client
        )
        self.telemetry_client = telemetry_client

        text_prompt = TextPrompt(TextPrompt.__name__)
        text_prompt.telemetry_client = telemetry_client

        date_time_prompt = DateTimePrompt(
            DateTimePrompt.__name__, Specifying_dialog.datetime_prompt_validator
        )
        date_time_prompt.telemetry_client = telemetry_client

        waterfall_dialog = WaterfallDialog(
            WaterfallDialog.__name__,
            [
                self.init_step,
                self.destination_step,
                self.origin_step,
                self.departure_date_step,
                self.return_date_step,
                self.budget_step,
                self.confirm_step,
                self.final_step,
            ],
        )
        waterfall_dialog.telemetry_client = telemetry_client

        self.add_dialog(text_prompt)
        self.add_dialog(date_time_prompt)
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        # self.add_dialog(
        #     DateResolverDialog(DateResolverDialog.__name__, self.telemetry_client)
        # )
        self.add_dialog(waterfall_dialog)

        self.initial_dialog_id = WaterfallDialog.__name__


    async def init_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Handle the entry to the dialog."""
        Journey_details = step_context.options

        # Test if we enter from reload
        if step_context.options.destination is None:
            return await step_context.prompt(
                                                TextPrompt.__name__,
                                                PromptOptions(
                    prompt=MessageFactory.text(
                            "To which city would you like to travel?"
                            ),
                    retry_prompt= MessageFactory.text(
                            "I do need to know where you want to go."
                    )

                                                )
            )

        return await step_context.next(step_context.options.destination)


    async def destination_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for destination."""
        journey_details = step_context.options

        if journey_details.destination is None:
            # Ask Luis what it thinks about it.
            intent, luis_result = await LuisHelper.execute_luis_query(
                self.luis_recognizer, step_context.context
            )
            journey_details.merge(luis_result, replace_when_exist= False)
            if luis_result.destination is None:
                return await step_context.replace_dialog(
                                        dialog_id= Specifying_dialog.__name__,
                                        options= journey_details
                )
            # define intent and luis_result without luis
#            journey_details.destination = luis_result.destination

        return await step_context.next(journey_details.destination)

    async def origin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for origin city."""
        journey_details = step_context.options

        # Check the number of words to guess if it worth asking
        # to decode the answer.
        if len(step_context.result.split(" ")) > 1:
        # Ask Luis what it thinks about it.
            intent, luis_result = await LuisHelper.execute_luis_query(
                self.luis_recognizer, step_context.context
            )
            journey_details.merge(luis_result, replace_when_exist= False)
            result = luis_result.destination
            if result is None:
                return await step_context.replace_dialog(
                                        dialog_id= Specifying_dialog.__name__,
                                        options= journey_details
                )
        else:
            # define intent and luis_result without luis
            intent = LUIS_APPS.INTENTS[LUIS_APPS.INTENT_SPECIFY_JOURNEY_NAME]
            result = step_context.result

        # Capture the response to the previous step's prompt
        journey_details.destination = result
        # Ask for the next
        if journey_details.origin is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("From which city will you be travelling?")
                ),
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(journey_details.origin)

    async def departure_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Handle waterfall at origin is returned and departure date is checked."""
        # Handle the previous question...
        journey_details = step_context.options

        # Check the number of words to guess if it worth asking LUIS
        # to decode the answer.
        if len(step_context.result.split(" ")) > 1:
        # Ask Luis what it thinks about it.
            intent, luis_result = await LuisHelper.execute_luis_query(
                self.luis_recognizer, step_context.context
            )
            journey_details.merge(luis_result, replace_when_exist= False)
            result = luis_result.origin
            if result is None:
                return await step_context.replace_dialog(
                                        dialog_id= Specifying_dialog.__name__,
                                        options= journey_details
                )
        else:
            # define intent and luis_result without luis
            intent = LUIS_APPS.INTENTS[LUIS_APPS.INTENT_SPECIFY_JOURNEY_NAME]
            result = step_context.result
        # If we are here, we consider that the origin point is legit
        journey_details.origin = result

        # Check if we need to display the request for the date before going
        # down to the next step of the waterfall
        if (
            not journey_details.departure_date
            or
            self.is_ambiguous(journey_details.departure_date)
        ):
            return await step_context.prompt(
                DateTimePrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("When do you want to leave?"),
                    retry_prompt= MessageFactory.text("Please be more precise.")
                ),
            )  # pylint: disable=line-too-long,bad-continuation
        return await step_context.next(journey_details.departure_date)

    async def return_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Handle waterfall at origin is returned and departure date is checked"""
        # Handle the previous question...
        journey_details = step_context.options

        # Check the number of words to guess if it worth asking LUIS to decode
        # the answer.
        # if "definite" not in Timex(step_context.result[0].timex.split("T")[0]).types:
        # # Ask Luis what it thinks about it.
        #     intent, luis_result = await LuisHelper.execute_luis_query(
        #         self.luis_recognizer, step_context.context
        #     )
        #     result = luis_result.departure_date
        #     if result is None or self.is_ambiguous(result):
        #         return await step_context.replace_dialog(
        #                                 dialog_id= Specifying_dialog.__name__,
        #                                 options= journey_details
        #         )
        # else:
        #     # define intent and luis_result without luis
        #     intent = LUIS_APPS.INTENTS[LUIS_APPS.INTENT_SPECIFY_JOURNEY_NAME]
        #     result = Timex(step_context.result)
        # # If we are here, we consider that the origin point is legit
        # journey_details.departure_date = result
        # Due to the validation we have a date
        if journey_details.departure_date is None:
            journey_details.departure_date = step_context.result[0].timex

        # Check if we need to display the request for the budget before going
        # down to the next step of the waterfall
        if journey_details.return_date is None:
            return await step_context.prompt(
                DateTimePrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("When do you want to come back?"),
                    retry_prompt= MessageFactory.text("I need you to be more precise.")
                ),
            )  # pylint: disable=line-too-long,bad-continuation
        return await step_context.next(journey_details.return_date)

    async def budget_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for the max budget."""
        journey_details = step_context.options

        # # Check the number of words to guess if it worth asking LUIS to decode
        # # the answer.
        # if "definite" not in Timex(step_context.result).types:
        # # Ask Luis what it thinks about it.
        #     intent, luis_result = await LuisHelper.execute_luis_query(
        #         self.luis_recognizer, step_context.context
        #     )
        #     result = luis_result.return_date
        #     if result is None or self.is_ambiguous(result):
        #         return await step_context.replace_dialog(
        #                                 dialog_id= Specifying_dialog.__name__,
        #                                 options= journey_details
        #         )
        # else:
        #     # define intent and luis_result without luis
        #     intent = LUIS_APPS.INTENTS[LUIS_APPS.INTENT_SPECIFY_JOURNEY_NAME]
        #     result = Timex(step_context.result)
        # # Capture the value.
        # journey_details.departure_date = result
        # Thanks to the validation we have a right format
        if journey_details.return_date is None:
            journey_details.return_date = step_context.result[0].timex

        if journey_details.max_budget is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("Up to how much are you ready to spend?")
                ),
            )  # pylint: disable=line-too-long,bad-continuation
        return await step_context.next(journey_details.max_budget)


    async def confirm_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Confirm the information the user has provided."""
        journey_details = step_context.options

        # Check the number of words to guess if it worth asking LUIS
        # to decode the answer.
        if journey_details.max_budget is None:
            if not step_context.result.replace('.', '').isdigit():
                # Ask Luis what it thinks about it.
                intent, luis_result = await LuisHelper.execute_luis_query(
                    self.luis_recognizer, step_context.context
                )
                result = luis_result.max_budget
                if result is None:
                    return await step_context.replace_dialog(
                                            dialog_id= Specifying_dialog.__name__,
                                            options= journey_details
                    )
            else:
                # define intent and luis_result without luis
                intent = LUIS_APPS.INTENTS[LUIS_APPS.INTENT_SPECIFY_JOURNEY_NAME]
                result = step_context.result
            # If we are here, we consider that the origin point is legit
            journey_details.max_budget = result

        await step_context.context.send_activity(activity_or_text= "Please confirm the following:")
        await step_context.context.send_activity(
                                activity_or_text= f"You want to travel "
                                        + f"to {journey_details.destination} "
                                        + f"from {journey_details.origin}"
        )
        await step_context.context.send_activity(
                                activity_or_text= f"You would leave on "
                                        + f"{journey_details.departure_date}"
                                        + f" and be back "
                                        + f"for {journey_details.return_date}."
        )
        msg = f"Your budget is {journey_details.max_budget['number']} "       \
                            + f"{journey_details.max_budget['units']} top."

        # Offer a YES/NO prompt.
        return await step_context.prompt(
            ConfirmPrompt.__name__, PromptOptions(prompt=MessageFactory.text(msg))
        )

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Complete the interaction and end the dialog."""
        if step_context.result:
            journey_details = step_context.options
            journey_details.confirm_step = step_context.result

            return await step_context.end_dialog(journey_details)

        return await step_context.end_dialog()



    @staticmethod
    async def datetime_prompt_validator(prompt_context: PromptValidatorContext) -> bool:
        """Validate the date provided is in proper form."""
        if prompt_context.recognized.succeeded:
            timex = Timex(prompt_context.recognized.value[0].timex.split("T")[0])
            if "definite" in timex.types:
                return True
            msg = "Please be more precise. I miss "
            if timex.day_of_month is None:
                msg += "the day, "
            if timex.month is None:
                msg += "the month, "
            if timex.year is None:
                msg += "the year, "
            split_msg = msg.split(',')
            if len(split_msg) == 2:
                msg = split_msg[0] + "."
            else:
                msg = ', '.join(split_msg[:-2]) + " and" + split_msg[-2] + "."
            await prompt_context.context.send_activity(msg)
        await prompt_context.context.send_activity('You can use the format YYYY-MM-DD')
        return False


    def is_ambiguous(self, timex: str) -> bool:
        """Ensure time is correct."""
        timex_property = Timex(timex)
        return "definite" not in timex_property.types
