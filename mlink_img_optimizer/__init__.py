import os
import logging
import pathlib
from shutil import copy2

try:
    from PIL import Image
    from PIL import ImageFile
    ImageFile.LOAD_TRUNCATED_IMAGES = True
except ImportError:
    logger.error('\n    This application requires Pillow to be installed. Please, install it first.\n')
    exit(1)

import optimize_images
from optimize_images.data_structures import Task, TaskResult
from optimize_images import constants
from optimize_images.img_optimize_png import optimize_png
from optimize_images.img_optimize_jpg import optimize_jpg
from optimize_images.reporting import human

logger = logging.getLogger(__name__)


def do_optimization(t: Task) -> TaskResult:
    """ Try to reduce file size of an image.
    Expects a Task object containing all the parameters for the image processing.
    The actual processing is done by the corresponding function,
    according to the detected image format.
    :param t: A Task object containing all the parameters for the image processing.
    :return: A TaskResult object containing information for single file report.
    """
    # TODO: Catch exceptions that may occur here.
    img = Image.open(t.src_path)

    # TODO: improve method of image format detection (what should happen if the
    #       file extension does not match the image content's format? Maybe we
    #       should skip unsupported formats?)
    if img.format.upper() == 'PNG':
        return optimize_png(t)
    elif (img.format.upper() == 'JPEG'):
        return optimize_jpg(t)
    else:
        pass


def json_report(r: TaskResult, f: pathlib.Path) -> dict:
    retval = {}
    if r.was_optimized:
        retval['percent'] = 100 - (r.final_size / r.orig_size * 100)
        retval['h_orig'] = human(r.orig_size)
        retval['h_final'] = human(r.final_size)
        retval['file'] = f
        return retval
    else:
        retval['file'] = f
        retval['percent'] = 0
        retval['h_orig'] = human(r.orig_size)
        retval['h_final'] = human(r.orig_size)

    return retval

def optimize(filepath):
    remove_transparency = True
    reduce_colors = False
    max_colors = 255
    max_w = 0
    max_h = 0
    keep_exif = True
    convert_all = False
    conv_big = False
    force_del = False
    bg_color = (255, 255, 255)  # By default, apply a white background
    grayscale = False
    ignore_size_comparison = False
    fast_mode = False

    task = Task(
        filepath, constants.DEFAULT_QUALITY, remove_transparency,
        reduce_colors, max_colors, max_w, max_h, keep_exif, convert_all,
        conv_big, force_del, bg_color, grayscale, ignore_size_comparison,
        fast_mode
    )

    r = do_optimization(task)
    total_src_size = r.orig_size
    report = json_report(r, filepath)
    print(report)
    return report
