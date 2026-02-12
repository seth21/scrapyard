# model/nodes/__init__.py

# 1. Expose the registry getter so engine.py can find it easily
from .registry import get_node_class

# 2. FORCE IMPORT all your node files.
# This runs the code in those files, triggering the @register_node decorators.
from . import click
from . import extract
from . import loop
from . import repeat
from . import scroll
from . import visit
