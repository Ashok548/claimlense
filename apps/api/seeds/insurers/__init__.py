# seeds/insurers package — auto-discovers insurer seed modules.
#
# Any .py file in this directory (except __init__.py and _*.py files) that
# exposes a PLANS_DATA attribute is automatically included in INSURER_MODULES.
# Adding a new insurer requires only creating seeds/insurers/my_insurer.py with
# a PLANS_DATA list — no manual registration here needed.

import importlib
import os
import pathlib

_HERE = pathlib.Path(__file__).parent

INSURER_MODULES = []

for _path in sorted(_HERE.glob("*.py")):
    _name = _path.stem
    if _name.startswith("_"):
        continue
    _module = importlib.import_module(f"seeds.insurers.{_name}")
    if hasattr(_module, "INSURER"):
        INSURER_MODULES.append(_module)

