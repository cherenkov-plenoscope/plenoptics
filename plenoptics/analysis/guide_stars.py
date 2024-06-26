import numpy as np
import json_utils
import os
from . import point_source_report
from .. import utils


def list_instruments_observing_guide_stars(config):
    out = []
    for instrument_key in config["observations"]["instruments"]:
        if "star" in config["observations"]["instruments"][instrument_key]:
            out.append(instrument_key)
    return out


def list_guide_star_indices(config):
    out = []
    for guide_star_idx in range(
        len(config["observations"]["star"]["guide_stars"])
    ):
        out.append(guide_star_idx)
    return out


def guide_star_idx_to_key(guide_star_idx):
    return "{:06d}".format(guide_star_idx)


def list_guide_star_keys(config):
    out = []
    for guide_star_idx in list_guide_star_indices(config=config):
        key = guide_star_idx_to_key(guide_star_idx=guide_star_idx)
        out.append(key)
    return out


def table_vmax(work_dir):
    config = json_utils.tree.read(os.path.join(work_dir, "config"))
    out = {}
    for instrument_key in list_instruments_observing_guide_stars(config):
        out[instrument_key] = {}

        reports_zip_path = os.path.join(
            work_dir,
            "analysis",
            instrument_key,
            "star.zip",
        )
        reports = utils.zipfile_json_read_to_dict(reports_zip_path)

        for guide_star_key in list_guide_star_keys(config):
            img = point_source_report.make_norm_image(
                point_source_report=reports[guide_star_key]
            )
            out[instrument_key][guide_star_key] = np.max(img)

    return out


def table_vmax_max(table_vmax):
    vmax = 0.0
    for instrument_key in table_vmax:
        for guide_star_key in table_vmax[instrument_key]:
            vmax = np.max([vmax, table_vmax[instrument_key][guide_star_key]])
    return vmax
