#!/usr/bin/python
import pandas
import numpy as np
import json_utils
import os
import sebastians_matplotlib_addons as sebplt
import binning_utils
import plenoptics
import confusion_matrix
import thin_lens
import plenopy
import plenoirf
import argparse

argparser = argparse.ArgumentParser()
argparser.add_argument("--work_dir", type=str)
argparser.add_argument("--out_dir", type=str)
argparser.add_argument("--instrument_key", type=str)
argparser.add_argument("--colormode", default="default")

args = argparser.parse_args()

colormode = args.colormode
work_dir = args.work_dir
out_dir = args.out_dir
instrument_key = args.instrument_key

PLT = plenoptics.plot.config()
CM = PLT["colormodes"][colormode]
sebplt.plt.style.use(colormode)
sebplt.matplotlib.rcParams.update(PLT["matplotlib_rcparams"]["latex"])

os.makedirs(out_dir, exist_ok=True)

config = json_utils.tree.read(os.path.join(work_dir, "config"))
result = plenoptics.utils.zipfile_json_read_to_dict(
    os.path.join(work_dir, "analysis", instrument_key, "point.zip")
)

# properties of plenoscope
# ------------------------
lfg = plenopy.LightFieldGeometry(
    os.path.join(
        work_dir, "instruments", instrument_key, "light_field_geometry"
    )
)

plenoscope = {}
plenoscope["focal_length_m"] = (
    lfg.sensor_plane2imaging_system.expected_imaging_system_focal_length
)
plenoscope["mirror_diameter_m"] = (
    2
    * lfg.sensor_plane2imaging_system.expected_imaging_system_max_aperture_radius
)
plenoscope["diameter_of_pixel_projected_on_sensor_plane_m"] = (
    np.tan(lfg.sensor_plane2imaging_system.pixel_FoV_hex_flat2flat)
    * plenoscope["focal_length_m"]
)

num_paxel_on_diagonal = (
    lfg.sensor_plane2imaging_system.number_of_paxel_on_pixel_diagonal
)

paxelscope = {}
for kk in plenoscope:
    paxelscope[kk] = plenoscope[kk] / num_paxel_on_diagonal


# prepare results
# ---------------
res = []
for point_key in result:
    estimate = result[point_key]
    e = {}
    for key in ["cx_deg", "cy_deg", "object_distance_m", "num_photons"]:
        e[key] = estimate[key]
    afocus = np.argmin(estimate["spreads_pixel_per_photon"])
    e["reco_object_distance_m"] = estimate["depth_m"][afocus]
    e["spread_pixel_per_photon"] = estimate["spreads_pixel_per_photon"][afocus]
    if np.isnan(e["spread_pixel_per_photon"]):
        continue
    else:
        res.append(e)

res = pandas.DataFrame(res).to_records()

systematic_reco_over_true = np.median(
    res["reco_object_distance_m"] / res["object_distance_m"]
)
res["reco_object_distance_m"] /= systematic_reco_over_true

# setup binning
# -------------
num_depth_bins = int(np.sqrt(len(res)))
num_depth_bins = np.max([3, num_depth_bins])

depth_bin = binning_utils.Binning(
    bin_edges=np.geomspace(
        0.75 * config["observations"]["point"]["min_object_distance_m"],
        1.25 * config["observations"]["point"]["max_object_distance_m"],
        num_depth_bins,
    ),
)
min_number_samples = 1

cm = confusion_matrix.init(
    ax0_key="true_depth_m",
    ax0_values=res["object_distance_m"],
    ax0_bin_edges=depth_bin["edges"],
    ax1_key="reco_depth_m",
    ax1_values=res["reco_object_distance_m"],
    ax1_bin_edges=depth_bin["edges"],
    min_exposure_ax0=min_number_samples,
    default_low_exposure=0.0,
)

# theory curve
# ------------
theory_depth_m = depth_bin["edges"]
theory_depth_minus_m = []
theory_depth_plus_m = []
for g in theory_depth_m:
    g_p, g_m = thin_lens.resolution_of_depth(
        object_distance=g,
        focal_length=plenoscope["focal_length_m"],
        aperture_diameter=plenoscope["mirror_diameter_m"],
        diameter_of_pixel_projected_on_sensor_plane=plenoscope[
            "diameter_of_pixel_projected_on_sensor_plane_m"
        ],
    )
    theory_depth_minus_m.append(g_m)
    theory_depth_plus_m.append(g_p)
theory_depth_minus_m = np.array(theory_depth_minus_m)
theory_depth_plus_m = np.array(theory_depth_plus_m)

theory_depth_paxel_minus_m = []
theory_depth_paxel_plus_m = []
for g in theory_depth_m:
    g_p, g_m = thin_lens.resolution_of_depth(
        object_distance=g,
        focal_length=plenoscope["focal_length_m"],
        aperture_diameter=plenoscope["mirror_diameter_m"],
        diameter_of_pixel_projected_on_sensor_plane=plenoscope[
            "diameter_of_pixel_projected_on_sensor_plane_m"
        ],
    )
    theory_depth_paxel_minus_m.append(g_m)
    theory_depth_paxel_plus_m.append(g_p)
theory_depth_paxel_minus_m = np.array(theory_depth_paxel_minus_m)
theory_depth_paxel_plus_m = np.array(theory_depth_paxel_plus_m)

# plot
# ====

SCALE = 1e-3
xticks = [3, 10, 30]
xlabels = ["${:.0f}$".format(_x) for _x in xticks]

# statistics
fig = sebplt.figure(plenoirf.summary.figure.FIGURE_STYLE)
ax_h = sebplt.add_axes(fig=fig, span=plenoirf.summary.figure.AX_SPAN)
sebplt.ax_add_grid(ax=ax_h, add_minor=True)
ax_h.semilogx()
ax_h.set_xlim(
    [np.min(cm["ax0_bin_edges"]) * SCALE, np.max(cm["ax1_bin_edges"]) * SCALE]
)
ax_h.set_xlabel(r"true depth$\,/\,$km")
ax_h.set_ylabel("statistics")
ax_h.axhline(cm["min_exposure_ax0"], linestyle=":", color=CM["k"])
sebplt.ax_add_histogram(
    ax=ax_h,
    bin_edges=cm["ax0_bin_edges"] * SCALE,
    bincounts=cm["exposure_ax0"],
    linestyle="-",
    linecolor=CM["k"],
)
ax_h.set_xticks(xticks)
ax_h.set_xticklabels(xlabels)
fig.savefig(os.path.join(out_dir, "depth_statistics.jpg"))
sebplt.close(fig)


# absolute
# --------

linewidth = 1.0
fig = sebplt.figure(style={"rows": 1600, "cols": 1920, "fontsize": 2})
ax_c = sebplt.add_axes(fig=fig, span=[0.05, 0.14, 0.85, 0.85])
ax_cb = sebplt.add_axes(fig=fig, span=[0.9, 0.14, 0.02, 0.85])

ax_c.plot(
    theory_depth_m * SCALE,
    theory_depth_m * SCALE,
    f'{CM["k"]}--',
    linewidth=linewidth,
)
ax_c.plot(
    theory_depth_m * SCALE,
    theory_depth_minus_m * SCALE,
    f'{CM["k"]}:',
    linewidth=linewidth,
)
ax_c.plot(
    theory_depth_m * SCALE,
    theory_depth_plus_m * SCALE,
    f'{CM["k"]}:',
    linewidth=linewidth,
)

_pcm_confusion = ax_c.pcolormesh(
    cm["ax0_bin_edges"] * SCALE,
    cm["ax1_bin_edges"] * SCALE,
    np.transpose(cm["counts_normalized_on_ax0"]) * np.mean(cm["counts_ax0"]),
    cmap=CM["Greys"],
    norm=sebplt.plt_colors.PowerNorm(gamma=0.5),
)
sebplt.ax_add_grid(ax=ax_c, add_minor=True)
sebplt.plt.colorbar(_pcm_confusion, cax=ax_cb, extend="max")
# ax_cb.set_ylabel("trials / 1")
ax_c.set_aspect("equal")
ax_c.set_ylabel(r"reconstructed depth$\,/\,$km")
ax_c.set_xlabel(r"true depth$\,/\,$km")
ax_c.loglog()
ax_c.set_xlim(depth_bin["limits"] * SCALE)
ax_c.set_ylim(depth_bin["limits"] * SCALE)

ax_c.set_xticks(xticks)
ax_c.set_xticklabels(xlabels)
ax_c.set_yticks(xticks)
ax_c.set_yticklabels(xlabels)

fig.savefig(os.path.join(out_dir, "depth_reco_vs_true.jpg"))
sebplt.close(fig)


# relative
# --------
rel_bin = binning_utils.Binning(
    bin_edges=np.linspace(1 / np.sqrt(2), np.sqrt(2), depth_bin["num"] + 1)
)

cm = confusion_matrix.init(
    ax0_key="true_depth_m",
    ax0_values=res["object_distance_m"],
    ax0_bin_edges=depth_bin["edges"],
    ax1_key="reco_depth_over_true_depth",
    ax1_values=res["reco_object_distance_m"] / res["object_distance_m"],
    ax1_bin_edges=rel_bin["edges"],
    min_exposure_ax0=min_number_samples,
    default_low_exposure=0.0,
)

fig = sebplt.figure({"rows": 960, "cols": 1920, "fontsize": 1.5})
ax_c = sebplt.add_axes(
    fig=fig, span=plenoirf.summary.figure.AX_SPAN_WITH_COLORBAR_PAYLOAD
)
ax_cb = sebplt.add_axes(
    fig=fig, span=plenoirf.summary.figure.AX_SPAN_WITH_COLORBAR_COLORBAR
)
ax_c.plot(
    theory_depth_m,
    theory_depth_m / theory_depth_m,
    f'{CM["k"]}--',
    linewidth=linewidth,
)
ax_c.plot(
    theory_depth_m * SCALE,
    theory_depth_minus_m / theory_depth_m,
    f'{CM["k"]}:',
    linewidth=linewidth,
)
ax_c.plot(
    theory_depth_m * SCALE,
    theory_depth_plus_m / theory_depth_m,
    f'{CM["k"]}:',
    linewidth=linewidth,
)

_pcm_confusion = ax_c.pcolormesh(
    cm["ax0_bin_edges"] * SCALE,
    cm["ax1_bin_edges"],
    np.transpose(cm["counts_normalized_on_ax0"]) * np.mean(cm["counts_ax0"]),
    cmap=CM["Greys"],
    norm=sebplt.plt_colors.PowerNorm(gamma=0.5),
)
sebplt.ax_add_grid(ax=ax_c, add_minor=True)
sebplt.plt.colorbar(_pcm_confusion, cax=ax_cb, extend="max")
ax_c.set_ylabel(r"(reconstructed depth) (true depth)$^{-1}$ $\,/\,$1")
ax_c.set_xlabel(r"true depth$\,/\,$km")
ax_c.semilogx()
ax_c.set_xticklabels([])
ax_c.set_xlim(depth_bin["limits"] * SCALE)
ax_c.set_ylim(rel_bin["limits"])

ax_c.set_xticks(xticks)
ax_c.set_xticklabels(xlabels)

fig.savefig(os.path.join(out_dir, "relative_depth_reco_vs_true.jpg"))
sebplt.close(fig)

num_coarse_depth_bins = int(num_depth_bins / 3)
num_coarse_depth_bins = np.max([num_coarse_depth_bins, 3])

depth_coarse_bin = binning_utils.Binning(
    bin_edges=np.geomspace(
        0.95 * config["observations"]["point"]["min_object_distance_m"],
        1.05 * config["observations"]["point"]["max_object_distance_m"],
        num_coarse_depth_bins + 1,
    ),
)

deltas = [[] for i in range(depth_coarse_bin["num"])]

for i in range(len(res["object_distance_m"])):
    delta_depth = (
        res["object_distance_m"][i] - res["reco_object_distance_m"][i]
    )
    depth = res["object_distance_m"][i]
    b = np.digitize(depth, bins=depth_coarse_bin["edges"]) - 1
    deltas[b].append(delta_depth)


deltas_80 = np.zeros(depth_coarse_bin["num"])
for i in range(depth_coarse_bin["num"]):
    deltas_80[i] = plenoptics.analysis.statistical_estimators.median_spread(
        a=deltas[i], containment=0.8
    )

deltas_std = deltas_80  # np.array([np.std(ll) for ll in deltas])
deltas_std_ru = np.array([np.sqrt(len(ll)) / len(ll) for ll in deltas])
deltas_std_au = deltas_std * deltas_std_ru

G_PLUS_G_MINUS_SCALE = 1e-1

fig = sebplt.figure({"rows": 960, "cols": 1920, "fontsize": 1.5})
ax_h = sebplt.add_axes(fig=fig, span=[0.12, 0.175, 0.87, 0.8])
sebplt.ax_add_grid(ax=ax_h, add_minor=True)
ax_h.loglog()
ax_h.set_xlim(depth_coarse_bin["limits"] * SCALE)
ax_h.set_ylim([5, 5e3])
ax_h.set_xlabel(r"true depth$\,/\,$km")
ax_h.set_ylabel(r"resolution$\,/\,$m")
ax_h.plot(
    theory_depth_m * SCALE,
    (theory_depth_plus_m - theory_depth_minus_m),
    f'{CM["k"]}:',
    alpha=0.3,
    linewidth=linewidth,
)
ax_h.plot(
    theory_depth_m * SCALE,
    (theory_depth_plus_m - theory_depth_minus_m) * G_PLUS_G_MINUS_SCALE,
    f'{CM["k"]}--',
    linewidth=linewidth,
)
sebplt.ax_add_histogram(
    ax=ax_h,
    bin_edges=depth_coarse_bin["edges"] * SCALE,
    bincounts=deltas_std,
    bincounts_lower=deltas_std - deltas_std_au,
    bincounts_upper=deltas_std + deltas_std_au,
    linestyle="-",
    linecolor=CM["k"],
    face_color=CM["k"],
    face_alpha=0.4,
)

ax_h.set_xticks(xticks)
ax_h.set_xticklabels(xlabels)
fig.savefig(os.path.join(out_dir, "depth_resolution.jpg"))
sebplt.close(fig)
