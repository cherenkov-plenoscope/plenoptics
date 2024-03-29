MIRROR = {
    "focal_length": 106.5,
    "max_outer_aperture_radius": 41.0,
    "min_inner_aperture_radius": 3.05,
    "outer_aperture_shape_hex": True,
    "facet_inner_hex_radius": 0.75,
    "gap_between_facets": 0.025,
}

SENSOR_TRANSFORMATION_DEFAULT = {
    "pos": [0, 0, MIRROR["focal_length"]],
    "rot": {"repr": "tait_bryan", "xyz_deg": [0.0, 0.0, 0.0]},
}

SENSOR_TRANSFORMATION_GENTLE = {
    "pos": [-0.1, 0.2, 0.995 * MIRROR["focal_length"]],
    "rot": {"repr": "tait_bryan", "xyz_deg": [1.0, 3.0, 5.0]},
}

SENSOR = {
    "expected_imaging_system_focal_length": 106.5,
    "expected_imaging_system_aperture_radius": 35.5,
    "max_FoV_diameter_deg": 6.5,
    "hex_pixel_FoV_flat2flat_deg": 0.06667,
    "housing_overhead": 1.1,
}
SENSOR_NUM_PAXEL_ON_PIXEL_DIAGONAL = 9


def lens_refraction_vs_wavelength():
    return {
        "name": "lens_refraction_vs_wavelength",
        "argument_versus_value": [
            [240e-9, 1.5133],
            [280e-9, 1.4942],
            [320e-9, 1.4827],
            [360e-9, 1.4753],
            [400e-9, 1.4701],
            [486e-9, 1.4631],
            [546e-9, 1.4601],
            [633e-9, 1.4570],
            [694e-9, 1.4554],
            [753e-9, 1.4542],
        ],
        "comment": (
            "Hereaus Quarzglas GmbH and Co. KG, Quarzstr. 8, 63450 Hanau, "
            "Suprasil Family 311/312/313"
        ),
    }


def mirror_reflectivity_vs_wavelength(key="cta_mst_dielectric_after"):
    return {
        "name": "mirror_reflectivity_vs_wavelength",
        "argument_versus_value": [
            [2.238e-07, 5.985e-01],
            [2.255e-07, 6.097e-01],
            [2.273e-07, 6.214e-01],
            [2.292e-07, 6.329e-01],
            [2.302e-07, 6.350e-01],
            [2.313e-07, 6.447e-01],
            [2.334e-07, 6.560e-01],
            [2.356e-07, 6.677e-01],
            [2.377e-07, 6.800e-01],
            [2.406e-07, 6.921e-01],
            [2.434e-07, 7.013e-01],
            [2.460e-07, 7.129e-01],
            [2.491e-07, 7.251e-01],
            [2.524e-07, 7.358e-01],
            [2.559e-07, 7.462e-01],
            [2.596e-07, 7.569e-01],
            [2.640e-07, 7.662e-01],
            [2.657e-07, 7.680e-01],
            [2.696e-07, 7.768e-01],
            [2.735e-07, 7.849e-01],
            [2.749e-07, 7.860e-01],
            [2.792e-07, 7.934e-01],
            [2.808e-07, 7.944e-01],
            [2.857e-07, 8.019e-01],
            [2.870e-07, 8.029e-01],
            [2.915e-07, 8.085e-01],
            [2.927e-07, 8.095e-01],
            [2.982e-07, 8.147e-01],
            [3.044e-07, 8.208e-01],
            [3.059e-07, 8.216e-01],
            [3.116e-07, 8.256e-01],
            [3.135e-07, 8.260e-01],
            [3.196e-07, 8.301e-01],
            [3.211e-07, 8.308e-01],
            [3.270e-07, 8.340e-01],
            [3.285e-07, 8.345e-01],
            [3.347e-07, 8.380e-01],
            [3.363e-07, 8.384e-01],
            [3.423e-07, 8.414e-01],
            [3.440e-07, 8.418e-01],
            [3.503e-07, 8.446e-01],
            [3.520e-07, 8.450e-01],
            [3.581e-07, 8.472e-01],
            [3.596e-07, 8.479e-01],
            [3.663e-07, 8.500e-01],
            [3.679e-07, 8.501e-01],
            [3.736e-07, 8.519e-01],
            [3.754e-07, 8.521e-01],
            [3.818e-07, 8.538e-01],
            [3.835e-07, 8.541e-01],
            [3.898e-07, 8.560e-01],
            [3.915e-07, 8.565e-01],
            [3.986e-07, 8.583e-01],
            [4.058e-07, 8.592e-01],
            [4.075e-07, 8.594e-01],
            [4.140e-07, 8.602e-01],
            [4.157e-07, 8.605e-01],
            [4.222e-07, 8.615e-01],
            [4.239e-07, 8.615e-01],
            [4.302e-07, 8.627e-01],
            [4.319e-07, 8.627e-01],
            [4.382e-07, 8.637e-01],
            [4.399e-07, 8.640e-01],
            [4.464e-07, 8.650e-01],
            [4.479e-07, 8.651e-01],
            [4.544e-07, 8.659e-01],
            [4.562e-07, 8.661e-01],
            [4.626e-07, 8.669e-01],
            [4.642e-07, 8.669e-01],
            [4.706e-07, 8.678e-01],
            [4.723e-07, 8.679e-01],
            [4.788e-07, 8.692e-01],
            [4.803e-07, 8.694e-01],
            [4.870e-07, 8.702e-01],
            [4.884e-07, 8.704e-01],
            [4.950e-07, 8.708e-01],
            [4.966e-07, 8.709e-01],
            [5.028e-07, 8.713e-01],
            [5.047e-07, 8.713e-01],
            [5.110e-07, 8.719e-01],
            [5.208e-07, 8.725e-01],
            [5.276e-07, 8.721e-01],
            [5.291e-07, 8.720e-01],
            [5.358e-07, 8.724e-01],
            [5.373e-07, 8.724e-01],
            [5.438e-07, 8.727e-01],
            [5.455e-07, 8.728e-01],
            [5.516e-07, 8.728e-01],
            [5.532e-07, 8.728e-01],
            [5.598e-07, 8.730e-01],
            [5.615e-07, 8.730e-01],
            [5.680e-07, 8.728e-01],
            [5.697e-07, 8.729e-01],
            [5.760e-07, 8.728e-01],
            [5.778e-07, 8.728e-01],
            [5.842e-07, 8.724e-01],
            [5.857e-07, 8.724e-01],
            [5.924e-07, 8.719e-01],
            [5.940e-07, 8.717e-01],
            [6.004e-07, 8.716e-01],
            [6.021e-07, 8.716e-01],
            [6.086e-07, 8.714e-01],
            [6.104e-07, 8.713e-01],
            [6.178e-07, 8.707e-01],
            [6.190e-07, 8.707e-01],
            [6.250e-07, 8.703e-01],
            [6.266e-07, 8.698e-01],
            [6.330e-07, 8.696e-01],
            [6.346e-07, 8.694e-01],
            [6.412e-07, 8.688e-01],
            [6.427e-07, 8.687e-01],
            [6.492e-07, 8.681e-01],
            [6.510e-07, 8.680e-01],
            [6.572e-07, 8.673e-01],
            [6.589e-07, 8.672e-01],
            [6.654e-07, 8.664e-01],
            [6.671e-07, 8.663e-01],
            [6.734e-07, 8.661e-01],
            [6.749e-07, 8.657e-01],
            [6.814e-07, 8.642e-01],
            [6.832e-07, 8.639e-01],
            [6.896e-07, 8.628e-01],
            [6.913e-07, 8.626e-01],
            [6.974e-07, 8.615e-01],
            [6.991e-07, 8.615e-01],
            [7.010e-07, 8.600e-01],
        ],
        "comment": (
            "'CTA-MST-Al-SiO2-after' from https://arxiv.org/abs/1310.1713; "
            "See also @proceeding{"
            "doi: 10.1117/12.2025476,"
            "author = { G.  Pareschi,T.  Armstrong,H.  Baba,J.  Bähr,A.  "
            "Bonardi,G.  Bonnoli,P.  Brun,R.  Canestrari,P.  Chadwick,M.  "
            "Chikawa,P.-H.  Carton,V.  de Souza,J.  Dipold,M.  Doro,D.  "
            "Durand,M.  Dyrda,A.  Förster,M.  Garczarczyk,E.  Giro,J.-F.  "
            "Glicenstein,Y.  Hanabata,M.  Hayashida,M.  Hrabovski,C.  "
            "Jeanney,M.  Kagaya,H.  Katagiri,L.  Lessio,D.  Mandat,M.  "
            "Mariotti,C.  Medina,J.  Michalowski,P.  Micolon,D.  Nakajima,J.  "
            "Niemiec,A.  Nozato,M.  Palatka,M.  Pech,B.  Peyaud,G.  "
            "Pühlhofer,M.  Rataj,G.  Rodeghiero,G.  Rojas,J.  Rousselle,R.  "
            "Sakonaka,P.  Schovanek,K.  Seweryn,C.  Schultz,S.  Shu,F.  "
            "Stinzing,M.  Stodulski,M.  Teshima,P.  Travniczek,C.  "
            "van Eldik,V.  Vassiliev,Ł  Wiśniewski,A.  Wörnlein,T.  Yoshida},"
            "title = {Status of the technologies for the production of the "
            "Cherenkov Telescope Array (CTA) mirrors},"
            "journal = {Proc.SPIE},"
            "volume = {8861},"
            "number = {},"
            "pages = {8861 - 8861 - 19},"
            "year = {2013},"
            "doi = {10.1117/12.2025476},"
            "URL = {https://doi.org/10.1117/12.2025476},"
            "}"
        ),
    }
