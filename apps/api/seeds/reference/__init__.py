# seeds/reference package — ordered reference-data seed modules.
#
# Order is explicit, not alphabetical, because downstream domains depend on
# earlier ones being seeded first:
#   keyword_sets     — no dependencies
#   item_categories  — no dependencies
#   irdai_exclusions — validated against item_categories
#   diagnosis        — validated against item_categories
#   room_rent        — resolves keyword_set FK at write time
#   billing_mode     — resolves keyword_set FK + item_category codes at write time

import importlib

_LOAD_ORDER = [
    "keyword_sets",
    "item_categories",
    "irdai_exclusions",
    "diagnosis",
    "room_rent",
    "billing_mode",
]

REFERENCE_MODULES = [
    importlib.import_module(f"seeds.reference.{name}")
    for name in _LOAD_ORDER
]
