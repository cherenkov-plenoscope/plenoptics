import json_line_logger
import os
import zipfile
import sequential_tar
import gzip
import io
import json_utils
import plenopy
from .. import sources
from .. import utils


def run(work_dir, pool, logger=json_line_logger.LoggerStdout()):
    config = json_utils.tree.read(os.path.join(work_dir, "config"))

    mapjobs = []

    logger.info("Obs:Map: Making observations in map dir...")
    mapjobs = _observations_make_jobs(work_dir=work_dir)
    logger.info("Obs:Map: {:d} jobs to do".format(len(mapjobs)))
    pool.map(_observations_run_job, mapjobs)
    logger.info("Obs:Map: Making observations in map dir done.")

    logger.info("Obs:Reduce: Reducing observations from map dir...")
    logger.info("Obs:Reduce: {:d} jobs to do".format(len(ojobs)))
    logger.info("Obs:Reduce: Reducing observations from map dir dine.")

    logger.info("Obs: Complete.")


def _observations_make_jobs(work_dir):
    return _tasks_make_jobs(work_dir=work_dir, task_key="responses", suffix="")


def make_mapdir_name(work_dir, task_key, instrument_key, observation_key):
    return os.path.join(
        work_dir, task_key, instrument_key, observation_key + ".map"
    )


def _observation_star_make_jobs(
    work_dir, config, task_key, instrument_key, suffix
):
    jobs = []
    mapdir = make_mapdir_name(
        work_dir=work_dir,
        task_key=task_key,
        instrument_key=instrument_key,
        observation_key="star",
    )
    for n in range(config["observations"]["star"]["num_stars"]):
        nkey = "{:06d}".format(n)
        outpath = os.path.join(mapdir, nkey + suffix)
        if not os.path.exists(outpath):
            job = {
                "work_dir": work_dir,
                "instrument_key": instrument_key,
                "observation_key": "star",
                "number": n,
            }
            jobs.append(job)
    return jobs


def _observations_point_make_jobs(work_dir, config, instrument_key, suffix):
    jobs = []
    for n in range(config["observations"]["point"]["num_points"]):
        nkey = "{:06d}".format(n)
        outpath = os.path.join(
            work_dir,
            task_key,
            instrument_key,
            "point",
            nkey + suffix,
        )
        if not os.path.exists(outpath):
            job = {
                "work_dir": work_dir,
                "instrument_key": instrument_key,
                "observation_key": "point",
                "number": n,
            }
            jobs.append(job)
    return jobs


def _observations_phantom_make_jobs(work_dir, config, instrument_key, suffix):
    jobs = []
    n = 0
    nkey = "{:06d}".format(n)
    outpath = os.path.join(
        work_dir,
        task_key,
        instrument_key,
        "phantom",
        nkey + suffix,
    )
    if not os.path.exists(outpath):
        job = {
            "work_dir": work_dir,
            "instrument_key": instrument_key,
            "observation_key": "phantom",
            "number": n,
        }
        jobs.append(job)
    return jobs


def _tasks_make_jobs(work_dir, task_key, suffix):
    cfg_dir = os.path.join(work_dir, "config")
    config = json_utils.tree.read(cfg_dir)

    jobs = []

    for instrument_key in config["observations"]["instruments"]:
        if instrument_key not in config["instruments"]:
            continue

        for observation_key in config["observations"]["instruments"][
            instrument_key
        ]:
            if observation_key == "star":
                jobs += _observation_star_make_jobs(
                    work_dir=work_dir,
                    config=config,
                    instrument_key=instrument_key,
                    suffix=suffix,
                )
            elif observation_key == "point":
                jobs += _observations_point_make_jobs(
                    work_dir=work_dir,
                    config=config,
                    instrument_key=instrument_key,
                    suffix=suffix,
                )
            elif observation_key == "phantom":
                jobs = _observations_phantom_make_jobs(
                    work_dir=work_dir,
                    config=config,
                    instrument_key=instrument_key,
                    suffix=suffix,
                )
    return jobs


def _observations_run_job(job):
    mapdir = os.path.join(
        job["work_dir"],
        "responses",
        job["instrument_key"],
        job["observation_key"] + ".map",
    )
    os.makedirs(mapdir, exist_ok=True)

    outpath = os.path.join(mapdir, "{:06d}.tar".format(job["number"]))

    light_field_geometry_path = os.path.join(
        job["work_dir"],
        "instruments",
        job["instrument_key"],
        "light_field_geometry",
    )

    merlict_config = json_utils.tree.read(
        os.path.join(job["work_dir"], "config", "merlict")
    )

    if job["observation_key"] == "star":
        source_config = sources.star.make_source_config_from_job(job=job)
    elif job["observation_key"] == "point":
        source_config = sources.point.make_source_config_from_job(job=job)
    elif job["observation_key"] == "phantom":
        source_config = sources.mesh.make_source_config_from_job(job=job)
    else:
        raise AssertionError("Bad observation_key")

    raw_sensor_response = make_response_to_source(
        source_config=source_config,
        light_field_geometry_path=light_field_geometry_path,
        merlict_config=merlict_config,
    )

    with sequential_tar.open(outpath, "w") as tar:
        with tar.open("truth.json", "wt") as f:
            f.write(json_utils.dumps(source_config))
        with tar.open("raw_sensor_response.phs", "wb|gz") as f:
            plenopy.raw_light_field_sensor_response.write(
                f=f, raw_sensor_response=raw_sensor_response
            )


def make_response_to_source(
    source_config,
    light_field_geometry_path,
    merlict_config,
):
    if source_config["type"] == "star":
        return sources.star.make_response_to_star(
            star_config=source_config,
            light_field_geometry_path=light_field_geometry_path,
            merlict_config=merlict_config,
        )
    elif source_config["type"] == "mesh":
        return sources.mesh.make_response_to_mesh(
            mesh_config=source_config,
            light_field_geometry_path=light_field_geometry_path,
            merlict_config=merlict_config,
        )
    elif source_config["type"] == "point":
        return sources.point.make_response_to_point(
            point_config=source_config,
            light_field_geometry_path=light_field_geometry_path,
            merlict_config=merlict_config,
        )
    else:
        raise AssertionError("Type of source is not known")


def response_star_map_dir(work_dir, instrument_key):
    return os.path.join(work_dir, "responses", instrument_key, "star.map")


def response_star_map_make_jobs(work_dir, instrument_key, config):
    jobs = []
    mapdir = response_star_map_dir(
        work_dir=work_dir,
        instrument_key=instrument_key,
    )
    for n in range(config["observations"]["star"]["num_stars"]):
        nkey = "{:06d}".format(n)
        outpath = os.path.join(mapdir, nkey + ".tar")
        if not os.path.exists(outpath):
            job = {
                "work_dir": work_dir,
                "instrument_key": instrument_key,
                "observation_key": "star",
                "number": n,
            }
            jobs.append(job)
    return jobs
