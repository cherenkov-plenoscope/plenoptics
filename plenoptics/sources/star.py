import corsika_primary
import numpy as np
import json_utils
import plenopy
import os
import tempfile
import merlict_development_kit_python

from .. import utils
from .. import analysis
from .. import production


EXAMPLE_STAR_CONFIG = {
    "type": "star",
    "cx_deg": 0.0,
    "cy_deg": 1.0,
    "areal_photon_density_per_m2": 20,
    "seed": 122,
}


def make_response_to_star(
    star_config,
    light_field_geometry_path,
    merlict_config,
):
    instgeom = utils.get_instrument_geometry_from_light_field_geometry(
        light_field_geometry_path=light_field_geometry_path
    )
    illum_radius = (
        1.5 * instgeom["expected_imaging_system_max_aperture_radius"]
    )
    illum_area = np.pi * illum_radius**2
    num_photons = int(
        np.round(star_config["areal_photon_density_per_m2"] * illum_area)
    )

    prng = np.random.Generator(np.random.PCG64(star_config["seed"]))

    with tempfile.TemporaryDirectory(
        prefix="plenoscope-aberration-demo_"
    ) as tmp_dir:
        star_light_path = os.path.join(tmp_dir, "star_light.tar")

        write_photon_bunches(
            cx=np.deg2rad(star_config["cx_deg"]),
            cy=np.deg2rad(star_config["cy_deg"]),
            size=num_photons,
            path=star_light_path,
            prng=prng,
            aperture_radius=illum_radius,
            BUFFER_SIZE=10000,
        )

        run_path = os.path.join(tmp_dir, "run")

        merlict_plenoscope_propagator_config_path = os.path.join(
            tmp_dir, "merlict_propagation_config.json"
        )
        json_utils.write(
            merlict_plenoscope_propagator_config_path,
            merlict_config["merlict_propagation_config"],
        )

        merlict_development_kit_python.plenoscope_propagator.plenoscope_propagator(
            corsika_run_path=star_light_path,
            output_path=run_path,
            light_field_geometry_path=light_field_geometry_path,
            merlict_plenoscope_propagator_config_path=merlict_plenoscope_propagator_config_path,
            random_seed=star_config["seed"],
            photon_origins=True,
            stdout_path=run_path + ".o",
            stderr_path=run_path + ".e",
        )

        run = plenopy.Run(path=run_path)
        event = run[0]
        return event.raw_sensor_response


def write_photon_bunches(
    cx, cy, size, path, prng, aperture_radius, BUFFER_SIZE=10000
):
    """
    Draw parallel and isochor corsika-bunches and write them into a
    corsika like EventTape.

    Parameters
    ----------
    path : str
        Path to write Event-Tape to.
    size : int
        Number of bunches
    """
    I = corsika_primary.I

    assert size >= 0
    tmp_path = path + ".tmp"
    with corsika_primary.cherenkov.CherenkovEventTapeWriter(
        path=tmp_path
    ) as run:
        runh = np.zeros(273, dtype=np.float32)
        runh[I.RUNH.MARKER] = I.RUNH.MARKER_FLOAT32
        runh[I.RUNH.RUN_NUMBER] = 1
        runh[I.RUNH.NUM_EVENTS] = 1

        evth = np.zeros(273, dtype=np.float32)
        evth[I.EVTH.MARKER] = I.EVTH.MARKER_FLOAT32
        evth[I.EVTH.EVENT_NUMBER] = 1
        evth[I.EVTH.PARTICLE_ID] = 1
        evth[I.EVTH.TOTAL_ENERGY_GEV] = 1.0
        evth[I.EVTH.RUN_NUMBER] = runh[I.RUNH.RUN_NUMBER]
        evth[I.EVTH.NUM_REUSES_OF_CHERENKOV_EVENT] = 1

        run.write_runh(runh)
        run.write_evth(evth)

        size_written = 0
        while size_written < size:
            block_size = BUFFER_SIZE
            if block_size + size_written > size:
                block_size = size - size_written
            size_written += block_size

            bunches = corsika_primary.calibration_light_source.draw_parallel_and_isochor_bunches(
                cx=cx,
                cy=cy,
                aperture_radius=aperture_radius,
                wavelength=433e-9,
                size=block_size,
                prng=prng,
                speed_of_light=299792458,
            )
            run.write_payload(bunches)
    os.rename(tmp_path, path)


def make_source_config_from_job(job):
    star_cfg = json_utils.read(
        os.path.join(job["work_dir"], "config", "observations", "star.json")
    )

    num_guide_stars = len(star_cfg["guide_stars"])

    if job["number"] < num_guide_stars:
        # guide star

        source_config = {
            "type": "star",
            "cx_deg": star_cfg["guide_stars"][job["number"]]["cx_deg"],
            "cy_deg": star_cfg["guide_stars"][job["number"]]["cy_deg"],
            "areal_photon_density_per_m2": star_cfg[
                "areal_photon_density_per_m2"
            ],
            "seed": job["number"],
        }

    else:
        # random star
        prng = np.random.Generator(np.random.PCG64(job["number"]))

        (
            cx_deg,
            cy_deg,
        ) = corsika_primary.random.distributions.draw_x_y_in_disc(
            prng=prng, radius=star_cfg["max_angle_off_optical_axis_deg"]
        )

        source_config = {
            "type": "star",
            "cx_deg": cx_deg,
            "cy_deg": cy_deg,
            "areal_photon_density_per_m2": star_cfg[
                "areal_photon_density_per_m2"
            ],
            "seed": job["number"],
        }

    return source_config


def analyse(
    work_dir,
    light_field_geometry,
    source_config,
    raw_sensor_response,
    random_seed,
):
    prng = np.random.Generator(np.random.PCG64(random_seed))

    cfg_analysis = json_utils.read(
        os.path.join(work_dir, "config", "analysis", "star.json")
    )

    result = analysis.point_source_report.make_point_source_report(
        image_center_cx_deg=source_config["cx_deg"],
        image_center_cy_deg=source_config["cy_deg"],
        raw_sensor_response=raw_sensor_response,
        light_field_geometry=light_field_geometry,
        object_distance_m=cfg_analysis["object_distance_m"],
        containment_percentile=cfg_analysis["containment_percentile"],
        binning=cfg_analysis["binning"],
        prng=prng,
    )

    return result


"""
def analysis_run_job(job):
    nkey = "{:06d}".format(job["number"])

    indir = os.path.join(
        job["work_dir"],
        "responses",
        job["instrument_key"],
        job["observation_key"],
    )

    outdir = os.path.join(
        job["work_dir"],
        "analysis",
        job["instrument_key"],
        job["observation_key"],
    )

    os.makedirs(outdir, exist_ok=True)

    inpath = os.path.join(indir, nkey)

    source_config = utils.json_read(inpath + ".json")
    raw_sensor_response = utils.gzip_read_raw_sensor_response(inpath + ".gz")

    prng = np.random.Generator(np.random.PCG64(job["number"]))

    light_field_geometry = plenopy.LightFieldGeometry(
        os.path.join(
            job["work_dir"],
            "instruments",
            job["instrument_key"],
            "light_field_geometry",
        )
    )

    cfg_analysis = json_utils.read(
        os.path.join(job["work_dir"], "config", "analysis", "star.json")
    )

    result = analysis.point_source_report.make_point_source_report(
        image_center_cx_deg=source_config["cx_deg"],
        image_center_cy_deg=source_config["cy_deg"],
        raw_sensor_response=raw_sensor_response,
        light_field_geometry=light_field_geometry,
        object_distance_m=cfg_analysis["object_distance_m"],
        containment_percentile=cfg_analysis["containment_percentile"],
        binning=cfg_analysis["binning"],
        prng=prng,
    )

    outpath = os.path.join(outdir, nkey + ".json")
    json_utils.write(outpath + ".incomplete", result)
    os.rename(outpath + ".incomplete", outpath)
"""
