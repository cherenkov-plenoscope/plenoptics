from . import image
from . import statistical_estimators
import binning_utils
import copy
import numpy as np
import plenopy


def make_point_source_report(
    image_center_cx_deg,
    image_center_cy_deg,
    raw_sensor_response,
    light_field_geometry,
    object_distance_m,
    containment_percentile,
    binning,
    prng,
):
    calibrated_response = calibrate_plenoscope_response(
        light_field_geometry=light_field_geometry,
        raw_sensor_response=raw_sensor_response,
        object_distance=object_distance_m,
    )

    cres = calibrated_response

    # print("image encirclement2d")
    psf_cx, psf_cy, psf_angle80 = statistical_estimators.encirclement2d(
        x=cres["image_beams"]["cx"],
        y=cres["image_beams"]["cy"],
        x_std=cres["image_beams"]["cx_std"],
        y_std=cres["image_beams"]["cy_std"],
        weights=cres["image_beams"]["weights"],
        prng=prng,
        percentile=containment_percentile,
        num_sub_samples=1,
    )

    thisbinning = copy.deepcopy(binning)
    thisbinning["image"]["center"]["cx_deg"] = image_center_cx_deg
    thisbinning["image"]["center"]["cy_deg"] = image_center_cy_deg
    thisimg_bin_edges = image.binning_image_bin_edges(binning=thisbinning)

    # print("image histogram2d_std")
    imgraw = image.histogram2d_std(
        x=cres["image_beams"]["cx"],
        y=cres["image_beams"]["cy"],
        x_std=cres["image_beams"]["cx_std"],
        y_std=cres["image_beams"]["cy_std"],
        weights=cres["image_beams"]["weights"],
        bins=thisimg_bin_edges,
        prng=prng,
        num_sub_samples=1000,
    )[0]

    # print("time encirclement1d")
    time_80_start, time_80_stop = statistical_estimators.encirclement1d(
        x=cres["time"]["bin_centers"],
        f=cres["time"]["weights"],
        percentile=containment_percentile,
    )
    # print("time full_width_half_maximum")
    (
        time_fwhm_start,
        time_fwhm_stop,
    ) = statistical_estimators.full_width_half_maximum(
        x=cres["time"]["bin_centers"],
        f=cres["time"]["weights"],
    )

    # export
    out = {}
    out["statistics"] = {}
    out["statistics"]["image_beams"] = {}
    out["statistics"]["image_beams"][
        "total"
    ] = light_field_geometry.number_lixel
    out["statistics"]["image_beams"]["valid"] = np.sum(
        cres["image_beams"]["valid"]
    )
    out["statistics"]["photons"] = {}
    out["statistics"]["photons"]["total"] = raw_sensor_response[
        "number_photons"
    ]
    out["statistics"]["photons"]["valid"] = np.sum(
        cres["image_beams"]["weights"]
    )

    out["time"] = cres["time"]
    out["time"]["fwhm"] = {}
    out["time"]["fwhm"]["start"] = time_fwhm_start
    out["time"]["fwhm"]["stop"] = time_fwhm_stop
    out["time"]["containment80"] = {}
    out["time"]["containment80"]["start"] = time_80_start
    out["time"]["containment80"]["stop"] = time_80_stop

    out["image"] = {}
    out["image"]["angle80"] = psf_angle80
    out["image"]["binning"] = thisbinning
    out["image"]["raw"] = imgraw
    return out


def make_norm_image(point_source_report):
    norm_image = (
        point_source_report["image"]["raw"]
        / point_source_report["statistics"]["photons"]["valid"]
    )
    return norm_image


def calibrate_plenoscope_response(
    raw_sensor_response,
    light_field_geometry,
    object_distance,
):
    image_rays = plenopy.image.ImageRays(
        light_field_geometry=light_field_geometry
    )

    time_bin_edges = binning_utils.edges_from_width_and_num(
        bin_width=raw_sensor_response["time_slice_duration"],
        num_bins=raw_sensor_response["number_time_slices"],
        first_bin_center=0.0,
    )
    time_bin_centers = binning_utils.centers(bin_edges=time_bin_edges)

    out = {}
    out["time"] = {}
    out["time"]["bin_edges"] = time_bin_edges
    out["time"]["bin_centers"] = time_bin_centers

    isochor_image_seqence = plenopy.light_field_sequence.make_isochor_image(
        raw_sensor_response=raw_sensor_response,
        time_delay_image_mean=light_field_geometry.time_delay_image_mean,
    )

    out["time"]["weights"] = isochor_image_seqence.sum(axis=1)

    out["image_beams"] = {}
    out["image_beams"]["_weights"] = isochor_image_seqence.sum(axis=0)
    (
        out["image_beams"]["_cx"],
        out["image_beams"]["_cy"],
    ) = image_rays.cx_cy_in_object_distance(object_distance)
    out["image_beams"]["_cx_std"] = light_field_geometry.cx_std
    out["image_beams"]["_cy_std"] = light_field_geometry.cy_std

    valid_cxcy = np.logical_and(
        np.logical_not(np.isnan(out["image_beams"]["_cx"])),
        np.logical_not(np.isnan(out["image_beams"]["_cy"])),
    )
    valid_cxcy_std = np.logical_and(
        np.logical_not(np.isnan(out["image_beams"]["_cx_std"])),
        np.logical_not(np.isnan(out["image_beams"]["_cy_std"])),
    )
    valid = np.logical_and(valid_cxcy, valid_cxcy_std)
    out["image_beams"]["valid"] = valid
    out["image_beams"]["weights"] = out["image_beams"]["_weights"][valid]
    out["image_beams"]["cx"] = out["image_beams"]["_cx"][valid]
    out["image_beams"]["cy"] = out["image_beams"]["_cy"][valid]
    out["image_beams"]["cx_std"] = out["image_beams"]["_cx_std"][valid]
    out["image_beams"]["cy_std"] = out["image_beams"]["_cy_std"][valid]
    return out
