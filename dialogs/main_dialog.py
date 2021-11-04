# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
logger = logging.getLogger(name= "Specify Dialog")
logger.setLevel(level= logging.INFO)

from botbuilder.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions
from botbuilder.core import (
    MessageFactory,
    TurnContext,
    BotTelemetryClient,
    NullTelemetryClient,
)
from botbuilder.schema import InputHints

from journey_details import Journey_details
from journey_specifier_recognizer import Journey_specifier_recognizer
from helpers.luis_helper import LuisHelper

from .specifying_dialog import Specifying_dialog

from shared_code.constants.luis_app import LUIS_APPS


class MainDialog(ComponentDialog):
    def __init__(
        self,
        luis_recognizer: Journey_specifier_recognizer,
        specifying_dialog: Specifying_dialog,
        telemetry_client: BotTelemetryClient = None,
    ):
        super(MainDialog, self).__init__(MainDialog.__name__)
        self.telemetry_client = telemetry_client or NullTelemetryClient()

        text_prompt = TextPrompt(TextPrompt.__name__)
        text_prompt.telemetry_client = self.telemetry_client

        specifying_dialog.luis_recognizer = luis_recognizer
        specifying_dialog.telemetry_client = self.telemetry_client

        wf_dialog = WaterfallDialog(
            "WFDialog", [self.intro_step, self.act_step, self.final_step]
        )
        wf_dialog.telemetry_client = self.telemetry_client

        self._luis_recognizer = luis_recognizer
        self._specifying_dialog_id = specifying_dialog.id

        self.add_dialog(text_prompt)
        self.add_dialog(specifying_dialog)
        self.add_dialog(wf_dialog)

        self.initial_dialog_id = "WFDialog"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self._luis_recognizer.is_configured:
            await step_context.context.send_activity(
                MessageFactory.text(
                    "NOTE: LUIS is not configured. To enable all capabilities, add 'LuisAppId', 'LuisAPIKey' and "
                    "'LuisAPIHostName' to the appsettings.json file.",
                    input_hint=InputHints.ignoring_input,
                )
            )

            return await step_context.next(None)

        # Check if this is not the first entry
        if step_context.options:
            message_text = MessageFactory.text(
                                                str(step_context.options),
                                                str(step_context.options),
                                                InputHints.expecting_input
            )
            return await step_context.prompt(
                            dialog_id= TextPrompt.__name__,
                            options= PromptOptions(prompt= message_text)
            )

        # Check what LUIS is thinking about the message received
        intent, luis_result = await LuisHelper.execute_luis_query(
            self._luis_recognizer, step_context.context
        )

        if intent == LUIS_APPS.INTENTS[LUIS_APPS.INTENT_HELP_NAME]:
            help_text = "Let's go through the process, step by step.\nFirst I need your destination."
            get_help_message = MessageFactory.text(
                help_text, help_text, InputHints.ignoring_input
            )
            return await step_context.prompt(
                            dialog_id= TextPrompt.__name__,
                            options= PromptOptions(prompt= get_help_message)
            )

        if intent == LUIS_APPS.INTENTS[LUIS_APPS.INTENT_GREETINGS_NAME]:
            greeting_text = f"{luis_result}! Let's specify your journey \U0001F60E"
            greeting_message = MessageFactory.text(
                                                    greeting_text,
                                                    greeting_text,
                                                    InputHints.expecting_input
            )
            return await step_context.prompt(
                            dialog_id= TextPrompt.__name__,
                            options= PromptOptions(prompt= greeting_message)
            )

        if intent == LUIS_APPS.INTENTS[LUIS_APPS.INTENT_SPECIFY_JOURNEY_NAME]:
            return await step_context.begin_dialog(self._specifying_dialog_id, luis_result)

        message_text = "Hello! Please to help you. Where do you want to go?"
        prompt_message = MessageFactory.text(
                                                message_text,
                                                message_text,
                                                InputHints.expecting_input
        )
        return await step_context.prompt(
                                dialog_id= TextPrompt.__name__,
                                options= PromptOptions(prompt= prompt_message)
        )

    async def act_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Act accordingly to the intent found.

        Args:
            step_context (WaterfallStepContext): Waterfall of the Bot.

        Returns:
            DialogTurnResult: Next step according to the context.
        """
        # We must have Luis configured. So we do not check it and do not go
        # for a solution without Luis.
        # if not self._luis_recognizer.is_configured:
        #     # LUIS is not configured, we just run the Specifey_dialog path with an empty Journey_detailsInstance.
        #     return await step_context.begin_dialog(
        #         self._specifying_dialog_id, Journey_details()
        #     )
        # But we alert there is something wrong
        if not self._luis_recognizer.is_configured:
            logger.info("Luis is not configured...")

        # Call LUIS and gather any potential journey details. (Note the TurnContext has the response to the prompt.)
        intent, luis_result = await LuisHelper.execute_luis_query(
            self._luis_recognizer, step_context.context
        )
        if intent == LUIS_APPS.INTENTS[LUIS_APPS.INTENT_SPECIFY_JOURNEY_NAME] and luis_result:
            # TODO SERGE - Regarder les erreurs pouvant sortir de la lecture
            # TODO - Pour les traiter ici.
            # # Show a warning for Origin and Destination if we can't resolve them.
            # await MainDialog._show_warning_for_unsupported_cities(
            #     step_context.context, luis_result
            # )
            # Run the Journey Specify giving it whatever details we have from the LUIS call.
            return await step_context.begin_dialog(self._specifying_dialog_id, luis_result)

        elif intent == LUIS_APPS.INTENTS[LUIS_APPS.INTENT_GREETINGS_NAME]:
            greeting_text = "Hello to you too. Can I know where you want to go?"
            return await step_context.replace_dialog(
                                                        dialog_id= self.id,
                                                        options= greeting_text
            )

        elif intent == LUIS_APPS.INTENTS[LUIS_APPS.INTENT_HELP_NAME]:
            help_text = "I am expecting you to disclose your journey."
            return await step_context.replace_dialog(
                                                        dialog_id= self.id,
                                                        options= help_text
            )

        else:
            didnt_understand_text = "Sorry, I didn't get that. I wish to know " \
                                        + "where you want to go?"
            return await step_context.replace_dialog(
                                                dialog_id= self.id,
                                                options= didnt_understand_text
            )


    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Handle the final message.

        Args:
            step_context (WaterfallStepContext): Waterfall of the bot.

        Returns:
            DialogTurnResult: Next turn of the dialog.
        """
        # If the child dialog ("BookingDialog") was cancelled or the user failed to confirm,
        # the Result here will be null.
        if step_context.result is not None:
            result = step_context.result

            # Now we have all the booking details call the booking service.

            # If the call to the booking service was successful tell the user.
            # time_property = Timex(result.travel_date)
            # travel_date_msg = time_property.to_natural_language(datetime.now())
            msg_txt  = f"You have confirmed that you want to "
            msg_txt += f"go to {result.destination} from {result.origin}"
            msg_txt += f" on {result.departure_date} to {result.return_date}."
            msg_txt += f" Your best budget is {result.max_budget['number']}"
            msg_txt += f" {result.max_budget['units']}."
            message = MessageFactory.text(msg_txt, msg_txt, InputHints.ignoring_input)
            await step_context.context.send_activity(message)

        prompt_message = "Thsnk you. Have a good day."
        return await step_context.replace_dialog(self.id, prompt_message)

    # We do not handle this kind of error.
    # TODO SERGE - Regarder les autres erreurs
    #
    #  @staticmethod
    # async def _show_warning_for_unsupported_cities(
    #     context: TurnContext, luis_result: Journey_details
    # ) -> None:
    #     """
    #     Show a warning if the requested From or To cities are recognized as entities but they are not in the Airport entity list.

    #     In some cases LUIS will recognize the From and To composite entities as a valid cities but the From and To Airport values
    #     will be empty if those entity values can't be mapped to a canonical item in the Airport.
    #     """
    #     if luis_result.unsupported_airports:
    #         message_text = (
    #             f"Sorry but the following airports are not supported:"
    #             f" {', '.join(luis_result.unsupported_airports)}"
    #         )
    #         message = MessageFactory.text(
    #             message_text, message_text, InputHints.ignoring_input
    #         )
    #         await context.send_activity(message)
