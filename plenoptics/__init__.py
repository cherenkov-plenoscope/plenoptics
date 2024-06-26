from .version import __version__
from . import default_config
from . import production
from . import sources
from . import analysis
from . import plot

import os
import numpy as np
import json_utils
import json_line_logger
import plenopy
from importlib import resources as importlib_resources
import subprocess


def init(work_dir, random_seed=42, minimal=False):
    cfg_dir = os.path.join(work_dir, "config")
    default_config.write_default_config(cfg_dir=cfg_dir, minimal=minimal)


def run(work_dir, pool, logger=None):
    logger = utils.LoggerStdout_if_None(logger=logger)
    logger.info("Start")

    logger.info("Make light-field-geometryies")
    production.light_field_geometry.run(
        work_dir=work_dir, pool=pool, logger=logger
    )
    logger.info("Light-field-geometryies done")

    logger.info("Make observations")
    production.observations.run(work_dir=work_dir, pool=pool, logger=logger)
    logger.info("Observations done")

    logger.info("Make Analysis")
    production.analysis.run(work_dir=work_dir, pool=pool, logger=logger)
    logger.info("Analysis done")

    logger.info("Make Plots")

    logger.info("Plot mirror deformations")
    pjobs = _plot_mirror_deformations_make_jobs(work_dir=work_dir)
    logger.info("{:d} jobs to do".format(len(pjobs)))
    pool.map(_run_script_job, pjobs)

    logger.info("Plot guide stars")
    plot_guide_stars(work_dir=work_dir, pool=pool, logger=logger)

    logger.info("Plot guide stars vs. offaxis")
    plot_guide_stars_vs_offaxis(work_dir=work_dir, logger=logger)

    logger.info("Plot depth")
    pjobs = _plot_depth_make_jobs(work_dir=work_dir)
    logger.info("{:d} jobs to do".format(len(pjobs)))
    pool.map(_run_script_job, pjobs)

    logger.info("Plot phantom")
    pjobs = _plot_phantom_source_make_jobs(work_dir=work_dir)
    logger.info("{:d} jobs to do".format(len(pjobs)))
    pool.map(_run_script_job, pjobs)

    logger.info("Plots done")
    logger.info("Done")


def _plot_mirror_deformations_make_jobs(work_dir):
    cfg_dir = os.path.join(work_dir, "config")
    config = json_utils.tree.read(cfg_dir)

    jobs = []

    # mirrors
    # -------
    for mirror_key in config["mirrors"]:
        mirror_dimensions_path = os.path.join(
            work_dir, "config", "mirrors", mirror_key + ".json"
        )
        for deformation_key in config["mirror_deformations"]:
            outpath = os.path.join(
                work_dir,
                "plots",
                "mirrors",
                mirror_key,
                deformation_key,
            )

            mirror_deformations_path = os.path.join(
                work_dir,
                "config",
                "mirror_deformations",
                deformation_key + ".json",
            )

            if not os.path.exists(outpath):
                job = {
                    "script": "plot_mirror_deformation",
                    "argv": [
                        mirror_dimensions_path,
                        mirror_deformations_path,
                        outpath,
                    ],
                }
                jobs.append(job)

    return jobs


def _plot_depth_make_jobs(work_dir):
    cfg_dir = os.path.join(work_dir, "config")
    config = json_utils.tree.read(cfg_dir)

    jobs = []
    for instrument_key in config["observations"]["instruments"]:
        if "point" in config["observations"]["instruments"][instrument_key]:
            depth_out_dir = os.path.join(
                work_dir, "plots", "depth", instrument_key
            )
            if not os.path.exists(depth_out_dir):
                job = {
                    "script": "plot_depth",
                    "argv": [
                        "--work_dir",
                        work_dir,
                        "--out_dir",
                        os.path.join(
                            work_dir, "plots", "depth", instrument_key
                        ),
                        "--instrument_key",
                        instrument_key,
                    ],
                }
                jobs.append(job)

            depth_refocus_out_dir = os.path.join(
                work_dir, "plots", "depth_refocus", instrument_key
            )
            if not os.path.exists(depth_refocus_out_dir):
                job = {
                    "script": "plot_depth_refocus",
                    "argv": [
                        "--work_dir",
                        work_dir,
                        "--out_dir",
                        depth_refocus_out_dir,
                        "--instrument_key",
                        instrument_key,
                    ],
                }
                jobs.append(job)
    return jobs


def _plot_phantom_source_make_jobs(work_dir):
    cfg_dir = os.path.join(work_dir, "config")
    config = json_utils.tree.read(cfg_dir)

    jobs = []
    for instrument_key in config["observations"]["instruments"]:
        if "phantom" in config["observations"]["instruments"][instrument_key]:
            out_dir = os.path.join(
                work_dir, "plots", "phantom", instrument_key
            )

            if not os.path.exists(out_dir):
                job = {
                    "script": "plot_phantom_source",
                    "argv": [
                        "--work_dir",
                        work_dir,
                        "--out_dir",
                        out_dir,
                        "--instrument_key",
                        instrument_key,
                    ],
                }
                jobs.append(job)
    return jobs


def _run_script_job(job):
    return _run_script(script=job["script"], argv=job["argv"])


def _run_script(script, argv):
    if not script.endswith(".py"):
        script += ".py"

    script_path = os.path.join(
        importlib_resources.files("plenoptics"), "scripts", script
    )

    args = []
    args.append("python")
    args.append(script_path)
    args += argv
    return subprocess.call(args)


def plot_guide_stars(work_dir, pool, logger=None):
    logger = utils.LoggerStdout_if_None(logger=logger)
    guide_stars_dir = os.path.join(work_dir, "plots", "guide_stars")

    if not os.path.exists(guide_stars_dir):
        logger.debug("run script 'plot_image_of_star_cmap'")
        _run_script(
            script="plot_image_of_star_cmap",
            argv=["--work_dir", work_dir, "--out_dir", guide_stars_dir],
        )

        table_vmax = analysis.guide_stars.table_vmax(work_dir=work_dir)
        vmax = analysis.guide_stars.table_vmax_max(table_vmax=table_vmax)

        jobs = []
        for instrument_key in table_vmax:
            out_dir = os.path.join(guide_stars_dir, instrument_key)
            if not os.path.exists(out_dir):
                logger.debug("missing '{:s}'".format(out_dir))
                for star_key in table_vmax[instrument_key]:
                    job = {"script": "plot_image_of_star"}
                    job["argv"] = [
                        "--work_dir",
                        work_dir,
                        "--out_dir",
                        out_dir,
                        "--instrument_key",
                        instrument_key,
                        "--star_key",
                        star_key,
                        "--vmax",
                        "{:e}".format(vmax),
                    ]
                    jobs.append(job)

        pool.map(_run_script_job, jobs)


def plot_guide_stars_vs_offaxis(work_dir, logger):
    out_dir = os.path.join(work_dir, "plots", "guide_stars_vs_offaxis")
    if not os.path.exists(out_dir):
        logger.info("Plot guide stars vs. offaxis")
        _run_script(
            script="plot_image_of_star_vs_offaxis",
            argv=[
                "--work_dir",
                work_dir,
                "--out_dir",
                out_dir,
            ],
        )


def mv_observation(work_dir, observation_key="phantom", postfix=".old"):
    config = json_utils.tree.read(os.path.join(work_dir, "config"))

    # responses
    for instrument_key in config["observations"]["instruments"]:
        if (
            observation_key
            in config["observations"]["instruments"][instrument_key]
        ):
            response_path = os.path.join(
                work_dir, "responses", instrument_key, observation_key
            )
            if os.path.exists(response_path):
                os.rename(response_path, response_path + postfix)

            analysis_path = os.path.join(
                work_dir, "analysis", instrument_key, observation_key
            )
            if os.path.exists(analysis_path):
                os.rename(analysis_path, analysis_path + postfix)
            if os.path.exists(analysis_path + ".json"):
                os.rename(
                    analysis_path + ".json", analysis_path + ".json" + postfix
                )
