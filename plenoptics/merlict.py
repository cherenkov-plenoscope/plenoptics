import numpy as np
import os
import tempfile
import plenopy
import merlict_development_kit_python


PROPAGATION_CONFIG = {
    "night_sky_background_ligth": {
        "flux_vs_wavelength": [[250.0e-9, 1.0], [700.0e-9, 1.0]],
        "exposure_time": 50e-9,
        "comment": "Night sky brightness is off. In Photons/(sr s m^2 m), last 'm' is for the wavelength wavelength[m] flux[1/(s m^2 sr m)",
    },
    "photo_electric_converter": {
        "quantum_efficiency_vs_wavelength": [[240e-9, 1.0], [701e-9, 1.0]],
        "dark_rate": 1e-3,
        "probability_for_second_puls": 0.0,
        "comment": "perfect detection",
    },
    "photon_stream": {
        "time_slice_duration": 0.5e-9,
        "single_photon_arrival_time_resolution": 0.416e-9,
    },
}


def append_photons_to_space_seperated_values(
    path, ids, supports, directions, wavelengths
):
    """
    [0] id,
    [1] [2] [3] support
    [4] [5] [6] direction
    [7] wavelength
    """
    with open(path, "at") as f:
        for i in range(len(ids)):
            f.write(
                "{:d} {:.3e} {:.3e} {:.3e} {:.9e} {:.9e} {:.9e} {:.3e}".format(
                    ids[i],
                    supports[i, 0],
                    supports[i, 1],
                    supports[i, 2],
                    directions[i, 0],
                    directions[i, 1],
                    directions[i, 2],
                    wavelengths[i],
                )
            )
            f.write("\n")


def write_light_fields_to_space_seperated_values(light_fields, path):
    curid = 0
    for lf in light_fields:
        sups = lf[0]
        dirs = lf[1]
        ids = np.arange(curid, curid + len(sups))
        curid += len(sups)

        append_photons_to_space_seperated_values(
            path=path,
            ids=ids,
            supports=sups,
            directions=dirs,
            wavelengths=np.ones(len(sups)) * 433e-9,
        )


def make_plenopy_event_and_read_light_field_geometry(
    light_fields,
    light_field_geometry_path,
    merlict_propagate_config_path,
    random_seed=0,
    work_dir=None,
):
    if work_dir == None:
        work_dir_cleanup = True
        tmpdir_handle = tempfile.TemporaryDirectory(prefix="phantom_source_")
        work_dir = tmpdir_handle.name
    else:
        work_dir_cleanup = False
        os.makedirs(work_dir, exist_ok=True)

    photons_path = os.path.join(work_dir, "photons.ssv")
    run_dir = os.path.join(work_dir, "run")

    write_light_fields_to_space_seperated_values(
        light_fields=light_fields,
        path=photons_path,
    )

    rc = merlict_development_kit_python.plenoscope_propagator.plenoscope_propagator_raw_photons(
        input_path=photons_path,
        output_path=run_dir,
        light_field_geometry_path=light_field_geometry_path,
        merlict_plenoscope_propagator_config_path=merlict_propagate_config_path,
        random_seed=0,
    )

    light_field_geometry = plenopy.LightFieldGeometry(
        light_field_geometry_path
    )
    event = plenopy.Event(
        os.path.join(run_dir, "1"),
        light_field_geometry=light_field_geometry,
    )

    if work_dir_cleanup:
        tmpdir_handle.cleanup()

    return event, light_field_geometry
