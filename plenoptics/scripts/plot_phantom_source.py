#!/usr/bin/python
import os
import numpy as np
import plenoptics
import plenopy
import plenoirf
import phantom_source
import json_utils
import binning_utils
import sebastians_matplotlib_addons as sebplt
import argparse
import skimage
from skimage import io


def gzip_read_raw_sensor_response_into_time_lixel_repr(path):
    out = plenoptics.utils.zipfile_responses_read(
        file=path, job_number_keys=["000000"]
    )
    raw = out["000000"]["raw_sensor_response"]
    loph = plenopy.photon_stream.loph.raw_sensor_response_to_photon_stream_in_loph_repr(
        raw_sensor_response=raw
    )
    _photon_arrival_times_s = (
        loph["sensor"]["time_slice_duration"]
        * loph["photons"]["arrival_time_slices"]
    )
    _photon_lixel_ids = loph["photons"]["channels"]
    return (_photon_arrival_times_s, _photon_lixel_ids)


sebplt.matplotlib.rcParams.update(
    plenoirf.summary.figure.MATPLOTLIB_RCPARAMS_LATEX
)

argparser = argparse.ArgumentParser()
argparser.add_argument("--work_dir", type=str)
argparser.add_argument("--out_dir", type=str)
argparser.add_argument("--instrument_key", type=str)
args = argparser.parse_args()

work_dir = args.work_dir
out_dir = args.out_dir
instrument_key = args.instrument_key

os.makedirs(out_dir, exist_ok=True)

config = json_utils.tree.read(os.path.join(work_dir, "config"))

prng = np.random.Generator(np.random.MT19937(seed=53))

light_field_geometry = plenopy.LightFieldGeometry(
    os.path.join(
        work_dir, "instruments", instrument_key, "light_field_geometry"
    )
)
max_FoV_diameter_deg = np.rad2deg(
    light_field_geometry.sensor_plane2imaging_system.max_FoV_diameter
)

phantom_source_light_field_path = os.path.join(
    work_dir, "responses", instrument_key, "phantom.zip"
)

phantom_source_light_field = (
    gzip_read_raw_sensor_response_into_time_lixel_repr(
        phantom_source_light_field_path
    )
)

phantom_source_mesh = config["observations"]["phantom"][
    "phantom_source_meshes_img"
]

image_edge_ticks_deg = np.linspace(-3, 3, 7)
image_edge_bin = binning_utils.Binning(
    bin_edges=np.deg2rad(np.linspace(-3.5, 3.5, int(3 * (7 / 0.067)))),
)
image_bins = [image_edge_bin["edges"], image_edge_bin["edges"]]

# from 1210_demonstrate_resolution_of_depth
# -----------------------------------------
systematic_reco_over_true = 1.0169723853658978

# find true depth
# ---------------
TRUE_DEPTH = config["observations"]["phantom"]["phantom_source_meshes_depth"]
object_distances = np.array([TRUE_DEPTH[key] for key in TRUE_DEPTH])
reco_object_distances = systematic_reco_over_true * object_distances

images_dir = os.path.join(out_dir, "images.cache")
os.makedirs(images_dir, exist_ok=True)

img_vmax = 0.0
for obj_idx in range(len(reco_object_distances)):
    reco_object_distance = reco_object_distances[obj_idx]

    image_path = os.path.join(images_dir, "{:06d}.float32".format(obj_idx))

    if os.path.exists(image_path):
        img = plenoptics.analysis.image.read_image(path=image_path)
    else:
        img = plenoptics.analysis.image.compute_image(
            light_field_geometry=light_field_geometry,
            light_field=phantom_source_light_field,
            object_distance=reco_object_distance,
            bins=image_bins,
            prng=prng,
        )
        plenoptics.analysis.image.write_image(path=image_path, image=img)

    img_vmax = np.max([img_vmax, np.max(img)])

CMAPS = plenoptics.plot.CMAPS
NPIX = 1280

FIG_FILENAME_FORMAT = "instrument_{:s}_cmap_{:s}_{:06d}.jpg"

for cmapkey in CMAPS:
    cmap_dir = os.path.join(out_dir, cmapkey)
    os.makedirs(cmap_dir, exist_ok=True)

    for obj_idx in range(len(object_distances)):
        image_path = os.path.join(images_dir, "{:06d}.float32".format(obj_idx))
        img = plenoptics.analysis.image.read_image(path=image_path)

        fig_filename = FIG_FILENAME_FORMAT.format(
            instrument_key, cmapkey, obj_idx
        )
        fig_path = os.path.join(cmap_dir, fig_filename)

        fig = sebplt.figure(
            style={"rows": NPIX, "cols": NPIX, "fontsize": 1.0}
        )
        ax = sebplt.add_axes(
            fig=fig,
            span=[0.0, 0.0, 1, 1],
        )
        ax.set_aspect("equal")
        cmap = ax.pcolormesh(
            np.rad2deg(image_edge_bin["edges"]),
            np.rad2deg(image_edge_bin["edges"]),
            np.transpose(img) / img_vmax,
            cmap=cmapkey,
            norm=sebplt.plt_colors.PowerNorm(
                gamma=CMAPS[cmapkey]["gamma"],
                vmin=0.0,
                vmax=1.0,
            ),
        )
        sebplt.ax_add_circle(
            ax=ax,
            x=0.0,
            y=0.0,
            r=0.5 * max_FoV_diameter_deg,
            linewidth=1.2,
            linestyle="-",
            color=CMAPS[cmapkey]["linecolor"],
            alpha=0.1,
            num_steps=360 * 5,
        )
        ax.set_xlim(np.rad2deg(image_edge_bin["limits"]))
        ax.set_ylim(np.rad2deg(image_edge_bin["limits"]))
        sebplt.ax_add_grid_with_explicit_ticks(
            ax=ax,
            xticks=image_edge_ticks_deg,
            yticks=image_edge_ticks_deg,
            alpha=0.1,
            linewidth=1.2,
            color=CMAPS[cmapkey]["linecolor"],
        )
        fig.savefig(fig_path)
        sebplt.close(fig)

    # colormap
    # --------
    fig_cmap = sebplt.figure(style={"rows": 120, "cols": 1280, "fontsize": 1})
    ax_cmap = sebplt.add_axes(fig_cmap, [0.1, 0.8, 0.8, 0.15])
    ax_cmap.text(0.5, -4.7, r"intensity$\,/\,$1")
    sebplt.plt.colorbar(
        cmap, cax=ax_cmap, extend="max", orientation="horizontal"
    )
    fig_cmap_filename = "cmap_{:s}.jpg".format(cmapkey)
    fig_cmap.savefig(os.path.join(cmap_dir, fig_cmap_filename))
    sebplt.close(fig_cmap)

    # avg image
    # ---------
    avg_img = np.zeros(shape=(NPIX, NPIX, 3), dtype=np.float32)
    for obj_idx in range(len(object_distances)):
        fig_filename = FIG_FILENAME_FORMAT.format(
            instrument_key, cmapkey, obj_idx
        )
        fig_path = os.path.join(cmap_dir, fig_filename)
        avg_img += skimage.io.imread(fig_path)
    fig_filename = "instrument_{:s}_cmap_{:s}_average.jpg".format(
        instrument_key, cmapkey
    )
    fig_path = os.path.join(cmap_dir, fig_filename)
    avg_img /= len(object_distances)
    avg_img = avg_img.astype(np.uint8)
    skimage.io.imsave(fig_path, avg_img)


fig_filename = "phantom_source_meshes.jpg"
fig_path = os.path.join(out_dir, fig_filename)

fig = sebplt.figure(style={"rows": 1280, "cols": 1280, "fontsize": 1.0})
ax = sebplt.add_axes(
    fig=fig,
    span=[0.0, 0.0, 1, 1],
)
for mesh in phantom_source_mesh:
    phantom_source.plot.ax_add_mesh(ax=ax, mesh=mesh, color="k")
ax.set_aspect("equal")
sebplt.ax_add_circle(
    ax=ax,
    x=0.0,
    y=0.0,
    r=0.5 * max_FoV_diameter_deg,
    linewidth=1.2,
    linestyle="-",
    color=CMAPS[cmapkey]["linecolor"],
    alpha=0.1,
    num_steps=360 * 5,
)
ax.set_xlim(np.rad2deg(image_edge_bin["limits"]))
ax.set_ylim(np.rad2deg(image_edge_bin["limits"]))
sebplt.ax_add_grid_with_explicit_ticks(
    ax=ax, xticks=image_edge_ticks_deg, yticks=image_edge_ticks_deg, alpha=0.1
)
fig.savefig(fig_path)
sebplt.close(fig)


fig_filename = "phantom_source_meshes_3d.jpg"
fig_path = os.path.join(out_dir, fig_filename)

fig = sebplt.figure(style={"rows": 2000, "cols": 1280, "fontsize": 1.0})
ax = sebplt.add_axes(fig=fig, span=[0.0, 0.0, 1, 1], style=sebplt.AXES_BLANK)

UU = 0.1
the = np.deg2rad(50)
for imesh, mesh in enumerate(phantom_source_mesh):
    zz = 5.3 * imesh
    projection = np.array(
        [
            [np.cos(the), -np.sin(the) * (1.0 / UU), 0],
            [np.sin(the), np.cos(the) * UU, zz],
            [0, 0, 1],
        ]
    )
    depth_m = object_distances[imesh]
    depth_km = 1e-3 * depth_m
    ax.text(
        x=5 * 0.5 * max_FoV_diameter_deg,
        y=zz - 2.5,
        s="{: 2.1f}".format(depth_km) + r"$\,$" + "km",
        fontsize=12 * 1.5,
    )
    sebplt.pseudo3d.ax_add_grid(
        ax=ax,
        projection=projection,
        x_bin_edges=image_edge_ticks_deg,
        y_bin_edges=image_edge_ticks_deg,
        alpha=0.33,
        linewidth=0.4,
        color="k",
        linestyle="-",
    )
    sebplt.pseudo3d.ax_add_circle(
        ax=ax,
        projection=projection,
        x=0.0,
        y=0.0,
        r=0.5 * max_FoV_diameter_deg,
        alpha=0.33,
        linewidth=0.4,
        color="k",
        linestyle="-",
    )
    sebplt.pseudo3d.ax_add_mesh(
        ax=ax,
        projection=projection,
        mesh=mesh,
        color="k",
        linestyle="-",
    )

fig.savefig(fig_path)
sebplt.close(fig)
