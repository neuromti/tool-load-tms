from matprot.convert.coords import *
import pytest


def test_classify_hemisphere():
    coords = [[-1, 0, 0], [1, 0, 0], [0, 0, 0]]
    hemi, lcog, rcog = classify_hemisphere(coords)
    assert lcog == [-1, 0, 0]
    assert rcog == [1, 0, 0]
    assert hemi == ["L", "R", "V"]


def test_shift_origin():
    coords = [[-1, 0, 0], [1, 0, 0], [0, 0, 0]]
    coords = shift_origin(coords)
    assert coords[0] == get_M1("L")
    assert coords[1] == get_M1("R")
    assert coords[2] == [0.0, *get_M1("R")[1:]]


def test_get_M1():
    assert get_M1("L") == [-36.6300, -17.6768, 54.3147]
    assert get_M1("L", cosys="Tailarach") == [-37.0, -21.0, 58.0]
    with pytest.raises(NotImplementedError):
        get_M1("X")
    with pytest.raises(NotImplementedError):
        get_M1("L", cosys="X")


def test_convert_xml_to_coords(xmlfile):
    coords = convert_xml_to_coords(xmlfile)
    assert coords[0] == [48.45623613856192, -46.05708755673308, 87.11054478615597]
    coords = convert_xml_to_coords(xmlfile, normalize=True)
    assert coords[0] == [45.07319361533528, -51.35910745824133, 54.4287950655647]
