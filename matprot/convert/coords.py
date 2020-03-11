import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
import numpy as np
from matprot.types import Coordinate
from typing import List, Tuple
from numpy.linalg import norm
from pathlib import Path

DEFAULT_TARGETS_RIGHT = [
    [45.07, -51.36, 54.43],
    [39.63, -45.3, 57.48],
    [34.29, -38.85, 61.55],
    [27.47, -32.06, 63.71],
    [20.29, -24.64, 65.73],
    [12.43, -15.51, 66.56],
    [3.95, -6.9, 65.43],
    [10.84, 0.45, 61.7],
    [18.91, -7.97, 62.27],
    [26.57, -16.74, 61.79],
    [33.24, -25.75, 59.61],
    [39.64, -32.54, 57.5],
    [45.06, -38.98, 54.41],
    [50.52, -45.06, 51.95],
    [54.13, -39.09, 47.69],
    [50.54, -32.98, 51.98],
    [45.05, -26.6, 54.4],
    [38.53, -18.32, 55.69],
    [32.11, -9.56, 57.54],
    [24.68, -1.18, 57.79],
    [16.98, 6.94, 57.43],
    [22.79, 13.11, 53.76],
    [30.09, 5.15, 53.82],
    [36.57, -3.38, 52.51],
    [42.61, -11.82, 50.84],
    [48.91, -19.84, 49.83],
    [53.22, -27.68, 46.59],
    [57.34, -33.63, 43.66],
    [61.73, -28.4, 41.43],
    [57.32, -21.44, 43.64],
    [52.67, -13.48, 45.93],
    [46.59, -5.77, 46.77],
    [40.62, 2.25, 47.94],
    [33.74, 9.75, 47.9],
    [27.9, 18.49, 49.77],
]


def parse_gumMarker(root: Element):
    entries = []
    for child in root:
        el = child[0][0][0][0]
        entry = [float(pos) for pos in el.attrib.values()]
        entries.append(entry)

    return np.atleast_2d(entries)


def parse_trigMarker(root: Element):

    entries = []
    for child in root:
        if child.tag == "TriggerMarker":
            data = np.zeros((4, 4))
            data.fill(np.NaN)
            for key, value in child[1].attrib.items():
                c, r = int(key[-2]), int(key[-1])
                data[r, c] = float(value)
                # data[r, c] = float(key[-2:])
            entry = data[-1, :-1].tolist()
            entries.append(entry)

    return np.atleast_2d(entries)


def parse(root) -> List[List[float]]:
    if root.tag == "GUMMarkerList":
        entries = parse_gumMarker(root)
    elif root.tag == "TriggerMarkerList":
        entries = parse_trigMarker(root)
    else:
        raise ValueError(f"{root.tag} is an unknown xml-file-format")
    # file_fmt = root.tag.split("MarkerList")[0]
    return entries.tolist()


def get_M1(hemisphere="L", cosys="MNI") -> Coordinate:
    """
    According to Mayka, M. A., Corcos, D. M., Leurgans, S. E., & Vaillancourt, D. E. (2006):
    Three-dimensional locations and boundaries of motor and premotor cortices as defined by functional brain imaging: a meta-analysis. NeuroImage, 31(4), 14531474. https://doi.org/10.1016/j.neuroimage.2006.02.004
    Consider that any MNI coordinates not reported in Talairach space were converted using the transformation equations for above the AC line (z > 0):
    xV = 0.9900x yV = 0.9688y + 0.0460z, zV = -0.0485y + 0.9189z
    xyz_in_Tailarach    = [-37, -21, 58];
    Tailarach2MNI       = [0.9900,0,0;0,0.9688,0.0460;0,-0.0485,0.9189];
    xyz_in_MNI          = (Tailarach2MNI*xyz_in_Tailarach')';
    Result as literals for speed

    See also
    https://neuroimage.usc.edu/brainstorm/CoordinateSystems
    https://www.brainvoyager.com/bv/doc/UsersGuide/CoordsAndTransforms/CoordinateSystems.html

    """
    if cosys == "MNI":
        M1 = [-36.6300, -17.6768, 54.3147]
    elif cosys == "Tailarach":
        M1 = [-37.0, -21.0, 58.0]
    else:
        raise NotImplementedError("Unknown coordinate system")
    if hemisphere == "R":
        M1[0] = -M1[0]
        return M1
    elif hemisphere == "L":
        return M1
    else:
        raise NotImplementedError("Unknown hemisphere")


def classify_hemisphere(
    coords: List[Coordinate],
) -> Tuple[List[str], Coordinate, Coordinate]:
    """for each coordinate, assign whether it lies in the right or left hemisphere

    args
    ----
    coords: List[Coordinate]
        a list of target coordinates

    returns
    -------
    hemisphere: List[str]
        a list of strings (either "L", or "R", or "V" for vertex line) describing the hemisphere
    lCoG: Coordinate
        Center of Gravity of coordinates assigned to left hemisphere
    rCoG: Coordinate
        Center of Gravity of coordinates assigned to right hemisphere

    """

    hemi = []
    right = []
    left = []
    for pos in coords:
        if pos[0] < 0:
            left.append(pos)
            hemi.append("L")
        elif pos[0] > 0:
            right.append(pos)
            hemi.append("R")
        else:
            hemi.append("V")

    MISSING_COG = [np.NaN] * 3
    lCoG = np.mean(left, 0).tolist() if len(left) != 0 else MISSING_COG
    rCoG = np.mean(right, 0).tolist() if len(right) != 0 else MISSING_COG
    return hemi, lCoG, rCoG


def shift_origin(coords: List[List[float]]) -> List[List[float]]:
    hemi, lcog, rcog = classify_hemisphere(coords)
    rshift = np.atleast_2d(rcog) - np.atleast_2d(get_M1("R"))
    lshift = np.atleast_2d(lcog) - np.atleast_2d(get_M1("L"))
    vshift = np.atleast_2d([0, rshift[0][1], rshift[0][2]])
    shifted = []
    for h, pos in zip(hemi, coords):
        if h == "R":
            shifted.append((pos - rshift).tolist()[0])
        elif h == "L":
            shifted.append((pos - lshift).tolist()[0])
        else:
            shifted.append((pos - vshift).tolist()[0])

    return shifted


def convert_xml_to_coords(xmlfile: str, normalize: bool = False) -> List[Coordinate]:
    root = ET.parse(xmlfile).getroot()
    coords = parse(root)
    if normalize:
        coords = shift_origin(coords)
    return coords
