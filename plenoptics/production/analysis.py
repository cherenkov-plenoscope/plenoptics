import json_line_logger
import os
import zipfile
import glob
import json_utils
import rename_after_writing
import plenopy
import shutil
from . import observations
from .. import sources
from .. import utils


def run(work_dir, pool, logger=None):
    logger = utils.LoggerStdout_if_None(logger=logger)
    config = json_utils.tree.read(os.path.join(work_dir, "config"))

    logger.info("Analysis:Mapping: ...")
    mapjobs = observations._make_mapping_jobs(
        config=config, work_dir=work_dir, task_key="analysis"
    )
    logger.info("Analysis:Mapping: {:d} jobs to do.".format(len(mapjobs)))
    pool.map(_analysis_run_mapjob, mapjobs)
    logger.info("Analysis:Mapping: done.")

    logger.info("Analysis:Reducing: ...")
    reducejobs = observations._make_reducing_jobs(
        config=config, work_dir=work_dir, task_key="analysis"
    )
    logger.info("Analysis:Reducing: {:d} jobs to do".format(len(reducejobs)))
    pool.map(_analysis_run_reducejob, reducejobs)
    logger.info("Analysis:Reducing: done.")

    logger.info("Analysis: Complete.")


def _analysis_run_mapjob(job):
    map_dir = os.path.join(
        job["work_dir"],
        "analysis",
        job["instrument_key"],
        job["observation_key"] + ".map",
    )
    os.makedirs(map_dir, exist_ok=True)

    job_number_str = "{:06d}".format(job["number"])
    outpath = os.path.join(map_dir, "{:s}.job.zip".format(job_number_str))

    responses_path = os.path.join(
        job["work_dir"],
        "responses",
        job["instrument_key"],
        job["observation_key"] + ".zip",
    )

    with zipfile.ZipFile(file=responses_path, mode="r") as z:
        with utils.ZipReader(
            zipfile=z,
            name=os.path.join(job_number_str, "source_config.json"),
            mode="rt",
        ) as f:
            source_config = json_utils.loads(f.read())
        with utils.ZipReader(
            zipfile=z,
            name=os.path.join(job_number_str, "raw_sensor_response.phs.gz"),
            mode="rb|gz",
        ) as f:
            raw_sensor_response = plenopy.raw_light_field_sensor_response.read(
                f=f
            )

    light_field_geometry = plenopy.LightFieldGeometry(
        os.path.join(
            job["work_dir"],
            "instruments",
            job["instrument_key"],
            "light_field_geometry",
        )
    )

    if job["observation_key"] == "star":
        result = sources.star.analyse(
            work_dir=job["work_dir"],
            light_field_geometry=light_field_geometry,
            source_config=source_config,
            raw_sensor_response=raw_sensor_response,
            random_seed=job["number"],
        )
    elif job["observation_key"] == "point":
        result = sources.point.analyse(
            work_dir=job["work_dir"],
            light_field_geometry=light_field_geometry,
            source_config=source_config,
            raw_sensor_response=raw_sensor_response,
            random_seed=job["number"],
        )
    elif job["observation_key"] == "phantom":
        result = {}
    else:
        raise ValueError(
            "Expected observation_key to be in ['star', 'point', 'phantom']."
        )

    with rename_after_writing.open(outpath, "wb") as file:
        with zipfile.ZipFile(
            file=file, mode="w", compression=zipfile.ZIP_STORED
        ) as z:
            with utils.ZipWriter(
                zipfile=z, name="result.json.gz", mode="wt|gz"
            ) as f:
                f.write(json_utils.dumps(result))


def _analysis_run_reducejob(job):
    base_path = os.path.join(
        job["work_dir"],
        "analysis",
        job["instrument_key"],
        job["observation_key"],
    )

    utils.zipfile_reduce(
        map_dir=base_path + ".map",
        out_path=base_path + ".zip",
        job_basenames=[
            "result.json.gz",
        ],
        job_ext=".job.zip",
        remove_after_reduce=True,
    )

    if os.path.exists(base_path + ".zip"):
        shutil.rmtree(base_path + ".map")


"""
def _analysis_reduce_make_jobs(work_dir, task_key="analysis"):
    cfg_dir = os.path.join(work_dir, "config")
    config = json_utils.tree.read(cfg_dir)
    jobs = []
    for instrument_key in config["observations"]["instruments"]:
        if instrument_key not in config["instruments"]:
            continue
        for observation_key in config["observations"]["instruments"][
            instrument_key
        ]:
            outpath = os.path.join(
                work_dir,
                task_key,
                instrument_key,
                observation_key + ".json",
            )
            if not os.path.exists(outpath):
                jobs.append(
                    {
                        "work_dir": work_dir,
                        "instrument_key": instrument_key,
                        "observation_key": observation_key,
                    }
                )
    return jobs


def _analysis_reduce_run_job(job):
    mapdir = os.path.join(
        job["work_dir"],
        "analysis",
        job["instrument_key"],
        job["observation_key"],
    )
    outpath = mapdir + ".json"
    return reduce_analysis_jobs(mapdir=mapdir, outpath=outpath)


def reduce_analysis_jobs(mapdir, outpath):
    paths = glob.glob(os.path.join(mapdir, "*.json"))
    paths.sort()

    out = {}
    for path in paths:
        basename = os.path.basename(path)
        number = str.split(basename, ".")[0]
        out[number] = json_utils.read(path)

    json_utils.write(outpath + ".incomplete", out, indent=None)
    os.rename(outpath + ".incomplete", outpath)

    for path in paths:
        os.remove(path)
"""
