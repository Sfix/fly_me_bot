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
