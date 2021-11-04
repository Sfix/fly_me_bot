"""Init the module that handles the data for training and testing."""

# Load the librairies
import os
import sys


# Add the module
path_libraries = os.path.join(os.getcwd(), "shared_code")
if path_libraries not in sys.path:
    sys.path.append(path_libraries)
path_libraries = os.path.join(os.getcwd(), "shared_code", "frames")
if path_libraries not in sys.path:
    sys.path.append(path_libraries)
