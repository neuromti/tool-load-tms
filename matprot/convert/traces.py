"""
Map
---

Convert the matlab file which contains the electrophysiological data to a file readable with python

"""

from scipy.io import loadmat
from pathlib import Path
import subprocess
import numpy as np
from scipy.signal import resample
from tempfile import mkdtemp
import atexit
from shutil import rmtree
from typing import List, Dict
from numpy import ndarray

TraceData = ndarray
MatFileContent = Dict[str, ndarray]


class TmpDir:
    def __init__(self):
        self.tmpdir = Path(mkdtemp())
        self.matfile = self.tmpdir / "conversion.mat"
        self.mfile = self.tmpdir / "conversion.m"
        assert self.tmpdir.exists()
        print("Created temporary directory at", self.tmpdir)

    def __del__(self):
        print("Deleted", self.tmpdir)
        rmtree(str(self.tmpdir))

    def refresh(self):
        if self.matfile.exists():
            self.matfile.unlink()
        if self.mfile.exists():
            self.mfile.unlink()

    def exists(self):
        return self.tmpdir.exists()


tmpdir = TmpDir()

# -----------------------------------------------------------------------------
def create_matlab_commands(matfile: str) -> Path:
    """create an mfile to convert the object in a matfile

    args
    ----
    fname:str
        the path to the :code:`.mat`-file 

    returns
    -------
    mfile: Path
        the path to the mfile 

    this matlab code would load the object and save it as simpler .mat-file readable with python
    """
    template = """
    addpath("/media/rgugg/tools/matlab/mltools")
    [data, fs, chan_names, stim_onset, stim_code] = tms.load_mat(\"{fname}\");
    save(\"{savefile}\", "data", "fs", "chan_names", "stim_onset", "stim_code");
    """
    content = template.format(fname=matfile, savefile=tmpdir.matfile)
    tmpdir.refresh()
    with tmpdir.mfile.open("w") as f:
        print(content, file=f)
    return tmpdir.mfile


def create_shell_commands(mfile: str) -> List[str]:
    "create the bash command to start matlab converting an automated-mat"
    command = "-r \"run('{mfile}'); exit;\""
    commands = [
        "matlab",
        "-nodesktop",
        "-nosplash",
        "-nodisplay",
        command.format(mfile=mfile),
    ]
    return commands


def convert_mat(fname: str) -> MatFileContent:
    "convert an automated-mat to a python dictionary"
    tmpdir.refresh()
    create_matlab_commands(fname)
    assert tmpdir.mfile.exists()
    try:
        commands = create_shell_commands(tmpdir.mfile)

        if subprocess.run(
            commands, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ):
            content = loadmat(tmpdir.matfile)
        else:
            raise Exception("Conversion was not successfull")
    finally:
        tmpdir.refresh()
    return content


def is_matlab_installed() -> bool:
    "returns true if a matlab installation was found, false otherwise"
    try:
        ret = subprocess.run(
            ["matlab", "-help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return ret.stderr == b""
    except FileNotFoundError:
        return False


def get_fs(content: MatFileContent) -> int:
    "returns the sampling rate of the converted matfile"
    return int(content["fs"][0][0])


def get_channel(content: MatFileContent, target_channel: str) -> ndarray:
    "return the full trace for a single channel"
    try:
        channel_index = np.where(content["chan_names"][0] == target_channel)[0][0]
    except IndexError:
        raise IndexError(f"{target_channel} was not found in the available channels!")

    full_trace = content["data"][:, channel_index]
    return full_trace


def get_onsets(content: MatFileContent) -> List[int]:
    "return the sample indices for each trigger onset"
    return content["stim_onset"][:, 0].tolist()


def cut_into_traces(
    content: MatFileContent,
    target_channel: str,
    pre_in_ms: float = 500,
    post_in_ms: float = 500,
) -> List[TraceData]:
    """cut data recorded with automated-mat into epochs

    args
    ----
    content: MatFileContent
        the content of a matfile converted via :func:`convert_mat`
    target_channele: str
        which channel to cut
    pre_in_ms:float
        how many milliseconds to cut before the TMS pulse
    post_in_ms:float
        how many milliseconds to cut after the TMS pulse

    returns
    -------
    traces: List[TraceData]
        a list of traces for each trigger recorded

    """
    full_trace = get_channel(content, target_channel)
    fs = get_fs(content)
    onsets = get_onsets(content)

    # convert pre/post from ms to samples
    pre_in_samples = int(pre_in_ms * fs / 1000)
    post_in_samples = int(post_in_ms * fs / 1000)

    # pad the signal to make sure we have enough data left and right of
    # the stimulus. padding is done to the left and right by default
    # this causes an offset of pad_size for the onsets, and we correct for that
    pad_size = pre_in_samples + post_in_samples
    padded = np.pad(full_trace, pad_size, "constant")
    onsets = [onset + pad_size for onset in onsets]

    # cut the padded full_trace from pre to post, with the TMS pulse in the
    # middle (based on the trigger information)
    traces = []
    for onset in onsets:
        a, b = onset - pre_in_samples, onset + post_in_samples
        trial = padded[a:b]
        traces.append(trial)
    return traces
