# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Handle cancel and help intents."""

from botbuilder.core import BotTelemetryClient, NullTelemetryClient
from botbuilder.dialogs import (
    ComponentDialog,
    DialogContext,
    DialogTurnResult,
    DialogTurnStatus,
)
from botbuilder.schema import ActivityTypes

from dotenv import load_dotenv
import os
load_dotenv(dotenv_path= 'C:\\Users\\serge\\OneDrive\\Data Sciences\\Data Sciences - Ingenieur IA\\10e projet\\Deliverables')

import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
logger = logging.getLogger(__name__)
logger.addHandler(
                    AzureLogHandler(
                                    connection_string= "InstrumentationKey=" \
                    + f"{os.getenv('AppInsightsInstrumentationKey', '')};"   \
                    +                               "IngestionEndpoint="     \
                    + f"{os.getenv('AppInsightsIngestionEndpoint', '')}"
                    )
)


logger.setLevel(level= logging.INFO)
properties = {'custom_dimensions': {'module': 'cancel_and_help_dialog'}}


class CancelAndHelpDialog(ComponentDialog):
    """Implementation of handling cancel and help."""

    def __init__(
        self,
        dialog_id: str,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
    ):
        super(CancelAndHelpDialog, self).__init__(dialog_id)
        self.telemetry_client = telemetry_client

    async def on_begin_dialog(
        self, inner_dc: DialogContext, options: object
    ) -> DialogTurnResult:
        result = await self.interrupt(inner_dc)
        if result is not None:
            return result

        return await super(CancelAndHelpDialog, self).on_begin_dialog(inner_dc, options)

    async def on_continue_dialog(self, inner_dc: DialogContext) -> DialogTurnResult:
        result = await self.interrupt(inner_dc)
        if result is not None:
            return result

        return await super(CancelAndHelpDialog, self).on_continue_dialog(inner_dc)

    async def interrupt(self, inner_dc: DialogContext) -> DialogTurnResult:
        """Detect obvious interruptions before wasting a request on LUIS."""
        if inner_dc.context.activity.type == ActivityTypes.message:
            text = inner_dc.context.activity.text.lower()

            if text in ("help", "?", "sos"):
                # Log the request
                dialogs = inner_dc.stack[-1].state['options'].log_utterances.utterance_list
                dialogs.append(text)
                properties["custom_dimensions"]['messages'] = "\t".join(dialogs)
                logger.info("Help", extra= properties)
                await inner_dc.context.send_activity("I will ask you the questions, just answer or say 'Bye'")
                return DialogTurnResult(DialogTurnStatus.Waiting)

            if text in ("cancel", "quit", "bye"):
                # Log the cancel
                try:
                    # Look for the dialog as it is saved somewhere else
                    def find_utterances(dialog_stack):
                        if 'options' in dialog_stack:
                            return dialog_stack['options'].log_utterances.utterance_list
                        if 'state' in dialog_stack:
                            if 'dialogs' in dialog_stack['state']:
                                return find_utterances(dialog_stack['state']['dialogs'].state.dialogs)
                        return None
                    utterances = find_utterances(inner_dc.stack[-1].state)
                except:
                    utterances = ['Dialog not retrieved.']

                utterances.append(text)
                properties["custom_dimensions"]['messages'] = "\t".join(utterances)
                logger.info("Cancel", extra= properties)
                await inner_dc.context.send_activity("Ok, I let you go. See you soon.")
                return await inner_dc.cancel_all_dialogs()

        return None
