# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Dialogs module."""
import os
import sys

path_to_dialogs = os.path.join(
                                os.getcwd(),
                                "fly_me_bot"
)
if path_to_dialogs not in sys.path:
    sys.path.append(path_to_dialogs)

from dialogs.specifying_dialog import Specifying_dialog
from dialogs.cancel_and_help_dialog import CancelAndHelpDialog
from dialogs.date_resolver_dialog import DateResolverDialog
from dialogs.main_dialog import MainDialog

__all__ = ["Specifying_dialog", "CancelAndHelpDialog", "DateResolverDialog", "MainDialog"]
