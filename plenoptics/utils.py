import os
import plenopy
import io
import gzip
import json_utils
import glob
import re
import rename_after_writing
import json_line_logger
import zipfile
import posixpath


def LoggerStdout_if_None(logger):
    if logger is None:
        return json_line_logger.LoggerStdout()
    else:
        return logger


def guess_scaling_of_num_photons_used_to_estimate_light_field_geometry(
    num_paxel_on_pixel_diagonal,
):
    return num_paxel_on_pixel_diagonal * num_paxel_on_pixel_diagonal


def get_instrument_geometry_from_light_field_geometry(
    light_field_geometry=None,
    light_field_geometry_path=None,
):
    if light_field_geometry_path:
        assert light_field_geometry is None
        geom_path = os.path.join(
            light_field_geometry_path, "light_field_sensor_geometry.header.bin"
        )
        geom_header = plenopy.corsika.utils.hr.read_float32_header(geom_path)
        geom = plenopy.light_field_geometry.PlenoscopeGeometry(raw=geom_header)
    else:
        geom = light_field_geometry.sensor_plane2imaging_system
    return class_members_to_dict(c=geom)


def class_members_to_dict(c):
    member_keys = []
    for key in dir(c):
        if not callable(getattr(c, key)):
            if not str.startswith(key, "__"):
                member_keys.append(key)
    out = {}
    for key in member_keys:
        out[key] = getattr(c, key)
    return out


def gzip_read_raw_sensor_response(path):
    with gzip.open(path, "rb") as f:
        raw = plenopy.raw_light_field_sensor_response.read(f)
    return raw


def gzip_write_raw_sensor_response(path, raw_sensor_response):
    with gzip.open(path + ".incomplete", "wb") as f:
        plenopy.raw_light_field_sensor_response.write(
            f=f, raw_sensor_response=raw_sensor_response
        )
    os.rename(path + ".incomplete", path)


def json_write(path, o):
    with rename_after_writing.open(path, "wt") as f:
        f.write(json_utils.dumps(o))


def json_read(path):
    with open(path, "rt") as f:
        o = json_utils.loads(f.read())
    return o


class ZipWriter:
    def __init__(self, zipfile, name, mode="wt"):
        self.mode = mode
        self.name = name
        self.zipfile = zipfile

        assert self.mode in ["wt", "wb", "wt|gz", "wb|gz"]

        if "t" in self.mode:
            self.buff = io.StringIO()
        elif "b" in self.mode:
            self.buff = io.BytesIO()
        else:
            raise ValueError("Expected mode to contain either 'b' or 't'.")

    def __enter__(self):
        return self.buff

    def __exit__(self, type, value, traceback):
        self.buff.seek(0)

        if "t" in self.mode:
            payload_bytes = str.encode(self.buff.read())
        elif "b" in self.mode:
            payload_bytes = self.buff.read()
        del self.buff

        if "|gz" in self.mode:
            payload_raw = gzip.compress(payload_bytes)
            del payload_bytes
        else:
            payload_raw = payload_bytes

        with self.zipfile.open(self.name, "w") as z:
            z.write(payload_raw)

    def __repr__(self):
        return "{:s}(name='{:s}', mode='{:s}')".format(
            self.__class__.__name__, self.name, self.mode
        )


class ZipReader:
    def __init__(self, zipfile, name, mode="rt"):
        self.mode = mode
        self.name = name

        assert self.mode in ["rt", "rb", "rt|gz", "rb|gz"]

        with zipfile.open(self.name, "r") as z:
            payload_raw = z.read()

        if "|gz" in self.mode:
            payload_bytes = gzip.decompress(payload_raw)
            del payload_raw
        else:
            payload_bytes = payload_raw

        if "t" in self.mode:
            self.buff = io.StringIO()
            self.buff.write(bytes.decode(payload_bytes))
        elif "b" in self.mode:
            self.buff = io.BytesIO()
            self.buff.write(payload_bytes)
        else:
            raise ValueError("Expected mode to contain either 'b' or 't'.")

        self.buff.seek(0)

    def __enter__(self):
        return self.buff

    def __exit__(self, type, value, traceback):
        pass

    def __repr__(self):
        return "{:s}(name='{:s}', mode='{:s}')".format(
            self.__class__.__name__, self.name, self.mode
        )


def zipfile_reduce(
    map_dir,
    out_path,
    job_basenames=[],
    job_ext=".job.zip",
    remove_after_reduce=True,
):
    pot_job_paths = sorted(glob.glob(os.path.join(map_dir, "*" + job_ext)))
    job_paths = {}

    for pot_job_path in pot_job_paths:
        basename = os.path.basename(pot_job_path)
        if re.findall(r"\d+" + job_ext, basename):
            job_number_str = re.findall(r"\d+", basename)[0]
            job_paths[job_number_str] = pot_job_path

    with rename_after_writing.open(out_path, "wb") as file:
        with zipfile.ZipFile(
            file=file, mode="w", compression=zipfile.ZIP_STORED
        ) as zout:
            for job_number_str in job_paths:
                with zipfile.ZipFile(job_paths[job_number_str], "r") as zin:
                    for basename in job_basenames:
                        with zin.open(basename, "r") as fin:
                            with zout.open(
                                os.path.join(job_number_str, basename), "w"
                            ) as fout:
                                fout.write(fin.read())

    if remove_after_reduce:
        for job_number_str in job_paths:
            os.remove(job_paths[job_number_str])


def zipfile_json_read_to_dict(file):
    out = {}
    with zipfile.ZipFile(file=file, mode="r") as zin:
        infos = zin.infolist()
        for info in infos:
            key = posixpath.dirname(info.filename)
            if str.endswith(info.filename, ".json.gz"):
                item_mode = "rt|gz"
            elif str.endswith(info.filename, ".json"):
                item_mode = "rt"
            else:
                continue
            with ZipReader(
                zipfile=zin, name=info.filename, mode=item_mode
            ) as f:
                out[key] = json_utils.loads(f.read())
    return out


def zipfile_responses_read(file, job_number_keys=[]):
    out = {}
    with zipfile.ZipFile(file=file, mode="r") as zin:
        for job_number_key in job_number_keys:
            out[job_number_key] = {}
            name = posixpath.join(job_number_key, "source_config.json")
            with ZipReader(zipfile=zin, name=name, mode="rt") as f:
                out[job_number_key]["source_config"] = json_utils.loads(
                    f.read()
                )
            name = posixpath.join(job_number_key, "raw_sensor_response.phs.gz")
            with ZipReader(zipfile=zin, name=name, mode="rb|gz") as f:
                out[job_number_key][
                    "raw_sensor_response"
                ] = plenopy.raw_light_field_sensor_response.read(f=f)
    return out
