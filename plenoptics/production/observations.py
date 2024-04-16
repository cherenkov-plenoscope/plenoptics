import json_line_logger
import os
import zipfile
import json_utils
import plenopy
import rename_after_writing
import shutil
from .. import sources
from .. import utils


def run(work_dir, pool, logger=None):
    logger = utils.LoggerStdout_if_None(logger=logger)
    config = json_utils.tree.read(os.path.join(work_dir, "config"))

    logger.info("Observations:Mapping: ...")
    mapjobs = _make_mapping_jobs(
        config=config, work_dir=work_dir, task_key="responses"
    )
    logger.info("Observations:Mapping: {:d} jobs to do".format(len(mapjobs)))
    pool.map(_observations_run_mapjob, mapjobs)
    logger.info("Observations:Mapping: done.")

    logger.info("Observations:Reducing: ...")
    reducejobs = _make_reducing_jobs(
        config=config, work_dir=work_dir, task_key="responses"
    )
    logger.info(
        "Observations:Reducing: {:d} jobs to do".format(len(reducejobs))
    )
    pool.map(_observations_run_reducejob, reducejobs)
    logger.info("Observations:Reducing: done.")

    logger.info("Observations: Complete.")


def _make_mapping_jobs(config, work_dir, task_key):
    mapjobs = []
    for instrument_key in config["observations"]["instruments"]:
        for observation_key in config["observations"]["instruments"][
            instrument_key
        ]:
            base_path = os.path.join(
                work_dir, task_key, instrument_key, observation_key
            )

            result_path = base_path + ".zip"
            map_dir = base_path + ".map"

            if os.path.exists(result_path):
                continue

            if observation_key == "star":
                num_jobs = config["observations"]["star"]["num_stars"]
            elif observation_key == "point":
                num_jobs = config["observations"]["point"]["num_points"]
            elif observation_key == "phantom":
                num_jobs = 1
            else:
                raise ValueError("Unknown observation_key")

            jobs = []
            for job_number in range(num_jobs):
                job_number_key = "{:06d}".format(job_number)
                map_job_path = os.path.join(
                    map_dir, job_number_key + ".job.zip"
                )
                if not os.path.exists(map_job_path):
                    job = {
                        "work_dir": work_dir,
                        "instrument_key": instrument_key,
                        "observation_key": observation_key,
                        "number": job_number,
                    }
                    jobs.append(job)
            mapjobs += jobs
    return mapjobs


def _make_reducing_jobs(config, work_dir, task_key):
    reducejobs = []

    for instrument_key in config["observations"]["instruments"]:
        for observation_key in config["observations"]["instruments"][
            instrument_key
        ]:
            base_path = os.path.join(
                work_dir, task_key, instrument_key, observation_key
            )

            result_path = base_path + ".zip"
            map_dir = base_path + ".map"

            if os.path.exists(map_dir) and not os.path.exists(result_path):
                job = {
                    "work_dir": work_dir,
                    "instrument_key": instrument_key,
                    "observation_key": observation_key,
                }
                reducejobs.append(job)
    return reducejobs


def _observations_run_mapjob(job):
    mapdir = os.path.join(
        job["work_dir"],
        "responses",
        job["instrument_key"],
        job["observation_key"] + ".map",
    )
    os.makedirs(mapdir, exist_ok=True)

    outpath = os.path.join(mapdir, "{:06d}.job.zip".format(job["number"]))

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

    with rename_after_writing.open(outpath, "wb") as file:
        with zipfile.ZipFile(
            file=file, mode="w", compression=zipfile.ZIP_STORED
        ) as z:
            with utils.ZipWriter(
                zipfile=z, name="source_config.json", mode="wt"
            ) as f:
                f.write(json_utils.dumps(source_config))
            with utils.ZipWriter(
                zipfile=z, name="raw_sensor_response.phs.gz", mode="wb|gz"
            ) as f:
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


def _observations_run_reducejob(job):
    base_path = os.path.join(
        job["work_dir"],
        "responses",
        job["instrument_key"],
        job["observation_key"],
    )

    utils.zipfile_reduce(
        map_dir=base_path + ".map",
        out_path=base_path + ".zip",
        job_basenames=[
            "source_config.json",
            "raw_sensor_response.phs.gz",
        ],
        job_ext=".job.zip",
        remove_after_reduce=True,
    )

    if os.path.exists(base_path + ".zip"):
        shutil.rmtree(base_path + ".map")
