import xml.etree.ElementTree as ET
import numpy as np
from matprot.types import TargetCoords
from typing import List


def parse_gumMarker(root=None):
    if root is None:
        tree = ET.parse(
            "/media/rgugg/projects/projects/Stroke/daten/tms-maps/coordinates/SaCe/pre3/contralesional.xml"
        )
        root = tree.getroot()
    entries = []
    for child in root:
        el = child[0][0][0][0]
        entry = [float(pos) for pos in el.attrib.values()]
        entries.append(entry)

    return np.atleast_2d(entries)


def parse_trigMarker(root=None):
    if root is None:
        tree = ET.parse(
            "/media/rgugg/projects/projects/Stroke/daten/tms-maps/coordinates/SaCe/pre1/contralesional.xml"
        )
        root = tree.getroot()

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


def coordlist_to_targetcoords(entries: List[List[float]]) -> TargetCoords:
    coords: TargetCoords = dict()
    for idx, coord in enumerate(entries.tolist()):
        coords[idx] = coord
    return coords


def get_M1(hemisphere="L", cosys="MNI") -> List[float]:
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
        M1 = [-37, -21, 58]
    else:
        raise NotImplementedError("Unknown coordinate system")
    if hemisphere == "R":
        M1[0] = -M1[0]
        return M1
    elif hemisphere == "L":
        return M1
    else:
        raise NotImplementedError("Unknown hemisphere")


def classify_hemisphere(coords: TargetCoords) -> List[str]:
    from numpy.linalg import norm

    rM1 = get_M1("R")
    lM1 = get_M1("L")
    coords = np.atleast_2d(coords)
    hemi = []
    left = []
    right = []
    for pos in coords:
        rd = norm(pos - rM1)
        ld = norm(pos - lM1)
        if rd < ld:
            right.append(pos)
            hemi.append("R")
        else:
            left.append(pos)
            hemi.append("L")
    return hemi


def shift_origin(coords: List[List[float]]) -> List[List[float]]:
    if len(coords) == 0:
        return coords
    from numpy.linalg import norm

    rM1 = get_M1("R")
    lM1 = get_M1("L")
    coords = np.atleast_2d(coords)
    cog = np.mean(coords, 0)
    # take either left or right M1 depending on distance of Cog
    rd = norm(cog - rM1)
    ld = norm(cog - lM1)
    M1 = rM1 if rd < ld else lM1
    shift = cog - M1
    shifted = []
    for pos in coords:
        shifted.append((pos - shift).tolist())
    return shifted


def split_shift_origin(coords: List[List[float]]) -> List[List[float]]:
    if len(coords) == 0:
        return coords
    from numpy.linalg import norm

    rM1 = get_M1("R")
    lM1 = get_M1("L")
    coords = np.atleast_2d(coords)
    hemi = []
    left = []
    right = []
    for pos in coords:
        rd = norm(pos - rM1)
        ld = norm(pos - lM1)
        if rd < ld:
            right.append(pos)
            hemi.append("R")
        else:
            left.append(pos)
            hemi.append("L")
    if len(left) == 0 or len(right) == 0:
        ## all points are right or left, can do a regular
        return shift_origin(coords)

    lCoG = np.mean(left, 0)
    rCoG = np.mean(right, 0)
    rshift = rCoG - rM1
    lshift = lCoG - lM1
    shifted = []
    for h, pos in zip(hemi, coords):
        if h == "R":
            shifted.append((pos - rshift).tolist())
        else:
            shifted.append((pos - lshift).tolist())
    return shifted


def convert_xml_to_coords(xmlfile: str, normalize: bool = False) -> TargetCoords:
    root = ET.parse(xmlfile).getroot()
    coords = parse(root)
    if normalize:
        coords = split_shift_origin(coords)
    return coords
