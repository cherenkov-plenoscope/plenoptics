#!/usr/bin/python
import os
import plenoirf
import numpy as np
import plenoptics
import json_utils
import sebastians_matplotlib_addons as sebplt
import argparse

argparser = argparse.ArgumentParser()
argparser.add_argument("--work_dir", type=str)
argparser.add_argument("--out_dir", type=str)
argparser.add_argument("--instrument_key", type=str)
argparser.add_argument("--star_key", type=str)
argparser.add_argument("--vmax", type=float)
argparser.add_argument("--colormode", default="default")

args = argparser.parse_args()

colormode = args.colormode
work_dir = args.work_dir
out_dir = args.out_dir
instrument_key = args.instrument_key
star_key = args.star_key
cmap_vmax = args.vmax

PLT = plenoptics.plot.config()
CM = PLT["colormodes"][colormode]
sebplt.plt.style.use(colormode)
sebplt.matplotlib.rcParams.update(PLT["matplotlib_rcparams"]["latex"])

os.makedirs(out_dir, exist_ok=True)

config = json_utils.tree.read(os.path.join(work_dir, "config"))
instrument_sensor_key = config["instruments"][instrument_key]["sensor"]

GRID_ANGLE_DEG = 0.1
CMAPS = plenoptics.plot.CMAPS

point_source_report = plenoptics.utils.zipfile_json_read_to_dict(
    os.path.join(work_dir, "analysis", instrument_key, "star.zip")
)[star_key]


if int(star_key) == 0:
    hasy = True
else:
    hasy = False

cols = 640 if hasy else int(640 * 0.75)

for cmap_key in CMAPS:
    cmap_dir = os.path.join(out_dir, cmap_key)
    os.makedirs(cmap_dir, exist_ok=True)

    fig_filename = "instrument_{:s}_star_{:s}_cmap_{:s}.jpg".format(
        instrument_key,
        star_key,
        cmap_key,
    )
    fig_path = os.path.join(cmap_dir, fig_filename)

    if os.path.exists(fig_path):
        continue

    fig_psf = sebplt.figure(style={"rows": 640, "cols": cols, "fontsize": 1.5})

    (
        bin_edges_cx,
        bin_edges_cy,
    ) = plenoptics.analysis.image.binning_image_bin_edges(
        binning=point_source_report["image"]["binning"]
    )
    bin_edges_cx_deg = np.rad2deg(bin_edges_cx)
    bin_edges_cy_deg = np.rad2deg(bin_edges_cy)
    (
        ticks_cx_deg,
        ticks_cy_deg,
    ) = plenoptics.plot.make_explicit_cx_cy_ticks(
        image_response=point_source_report, tick_angle=GRID_ANGLE_DEG
    )

    ax_xlow = 0.25 if hasy else 0.0
    ax_xwid = 0.75 if hasy else 1.0
    ax_psf = sebplt.add_axes(
        fig=fig_psf,
        span=[ax_xlow, 0.15, ax_xwid, 0.85],
    )
    ax_psf.set_aspect("equal")

    image_response_norm = (
        plenoptics.analysis.point_source_report.make_norm_image(
            point_source_report=point_source_report
        )
    )

    cmap_psf = ax_psf.pcolormesh(
        bin_edges_cx_deg,
        bin_edges_cy_deg,
        np.transpose(image_response_norm) / cmap_vmax,
        cmap=cmap_key,
        norm=sebplt.plt_colors.PowerNorm(
            gamma=CMAPS[cmap_key]["gamma"],
            vmin=0.0,
            vmax=1.0,
        ),
    )
    sebplt.ax_add_grid_with_explicit_ticks(
        xticks=ticks_cx_deg,
        yticks=ticks_cy_deg,
        ax=ax_psf,
        color=CMAPS[cmap_key]["linecolor"],
        linestyle="-",
        linewidth=0.33,
        alpha=0.33,
    )
    sebplt.ax_add_circle(
        ax=ax_psf,
        x=point_source_report["image"]["binning"]["image"]["center"]["cx_deg"],
        y=point_source_report["image"]["binning"]["image"]["center"]["cy_deg"],
        r=np.rad2deg(point_source_report["image"]["angle80"]),
        linewidth=1.0,
        linestyle="--",
        color=CMAPS[cmap_key]["linecolor"],
        alpha=0.5,
        num_steps=360,
    )
    sebplt.ax_add_circle(
        ax=ax_psf,
        x=0.0,
        y=0.0,
        r=0.5
        * config["sensors"][instrument_sensor_key]["max_FoV_diameter_deg"],
        linewidth=1.0,
        linestyle="-",
        color=CMAPS[cmap_key]["linecolor"],
        alpha=0.5,
        num_steps=360 * 5,
    )
    plenoptics.plot.ax_psf_set_ticks(
        ax=ax_psf,
        image_response=point_source_report,
        grid_angle_deg=GRID_ANGLE_DEG,
        x=True,
        y=True,
    )
    plenoptics.plot.ax_psf_add_eye(
        ax=ax_psf,
        image_response=point_source_report,
        bin_edges_cx_deg=bin_edges_cx_deg,
        bin_edges_cy_deg=bin_edges_cy_deg,
        linecolor=CMAPS[cmap_key]["linecolor"],
        eye_FoV_flat2flat_deg=config["sensors"][instrument_sensor_key][
            "hex_pixel_FoV_flat2flat_deg"
        ],
    )
    ccx_deg = point_source_report["image"]["binning"]["image"]["center"][
        "cx_deg"
    ]
    ccy_deg = point_source_report["image"]["binning"]["image"]["center"][
        "cy_deg"
    ]
    ccxr_deg = 0.5 * (
        point_source_report["image"]["binning"]["image"]["pixel_angle_deg"]
        * point_source_report["image"]["binning"]["image"]["num_pixel_cx"]
    )
    ccyr_deg = 0.5 * (
        point_source_report["image"]["binning"]["image"]["pixel_angle_deg"]
        * point_source_report["image"]["binning"]["image"]["num_pixel_cy"]
    )
    ax_psf.set_xlim([ccx_deg - ccxr_deg, ccx_deg + ccxr_deg])
    ax_psf.set_ylim([ccy_deg - ccyr_deg, ccy_deg + ccyr_deg])

    fig_psf.savefig(fig_path)
    sebplt.close(fig_psf)
