from __future__ import unicode_literals

from msme_logistics.patches.insert_demo_data.execute import execute

# This patch exists solely as a fresh module path so Frappe's patch system
# detects it as "new" and runs it on bench migrate — even though the old
# insert_demo_data patch was already logged as executed in tabPatch Log.
#
# The actual logic lives in insert_demo_data/execute.py.
