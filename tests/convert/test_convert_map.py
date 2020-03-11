import pytest
from matprot.convert.traces import *


def test_tmpdir_exists():
    assert tmpdir.exists()


def test_tmpdir_lifecycle(capsys):
    tmpdir = TmpDir()
    tname = str(tmpdir.tmpdir)
    captured = capsys.readouterr()
    assert tname in captured.out
    assert "Created" in captured.out
    with tmpdir.matfile.open("w") as f:
        pass
    with tmpdir.mfile.open("w") as f:
        pass
    assert tmpdir.matfile.exists()
    assert tmpdir.mfile.exists()
    tmpdir.refresh()
    assert not tmpdir.matfile.exists()
    assert not tmpdir.mfile.exists()
    del tmpdir
    captured = capsys.readouterr()
    assert tname in captured.out
    assert "Deleted" in captured.out


def test_create_matlab_commands(matfile):
    # this file is being created by the call
    tmpdir.refresh()
    assert not tmpdir.mfile.exists()
    mfile = create_matlab_commands(matfile)
    assert mfile is tmpdir.mfile
    assert tmpdir.mfile.exists()
    assert not tmpdir.matfile.exists()


def test_create_shell_commands(matfile):
    # this file is being created by the call
    tmpdir.refresh()
    mfile = create_matlab_commands(matfile)
    commands = create_shell_commands(mfile)
    assert str(mfile) in " ".join(commands)


@pytest.mark.skipif(is_matlab_installed() == False, reason="Matlab is not installed")
def test_convert_mat(matfile):
    out = convert_mat(matfile)
    assert "chan_names" in out.keys()
    assert "stim_onset" in out.keys()
    assert "data" in out.keys()
    for k, v in out.items():
        print(k, type(v))


def test_cut_into_traces():
    import numpy as np

    chan_names = np.asanyarray([["Fpz", "Cz", "EDC_L"]])
    fs = np.asanyarray([[5000]])
    stim_onset = np.asanyarray([[3749], [9224]])
    data = np.random.randn(10000, 3)
    content: MatFileContent
    content = {
        "chan_names": chan_names,
        "fs": fs,
        "stim_onset": stim_onset,
        "data": data,
    }
    traces = cut_into_traces(content, target_channel="EDC_L")
    assert len(traces) == 2
