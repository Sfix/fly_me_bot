"""Init the module for the constants."""

# Load the librairies
import os
import sys


# Add the module
path_libraries = os.path.join(os.getcwd(), "shared_code", "constants")
if path_libraries not in sys.path:
    sys.path.append(path_libraries)
