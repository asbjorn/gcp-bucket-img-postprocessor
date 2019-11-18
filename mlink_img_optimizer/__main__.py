import os
import logging
import pathlib

import mlink_img_optimizer
logger = logging.getLogger(__name__)


filepath = pathlib.Path('./tmp/')
f = filepath / 'original.jpg'
print(f.absolute())
print(f"Running locally (debugging): {f}")
report = mlink_img_optimizer.optimize(f)

from pprint import pprint
pprint(report)
