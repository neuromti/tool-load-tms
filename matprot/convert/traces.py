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
from typing import List, Dict, Union
from matprot.types import TraceData, MatFileContent, FileName
from sys import platform


class TmpDir:
    def __init__(self):
        self.tmpdir = Path(mkdtemp()).expanduser().absolute()
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
def create_matlab_commands(matfile: FileName) -> Path:
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
    addpath("{addpath}")
    [data, fs, chan_names, stim_onset, stim_code, mso, subid, recdate] = load_all(\"{fname}\");
    save(\"{savefile}\", "data", "fs", "chan_names", "stim_onset", "stim_code", "mso", "subid", "recdate");
    """
    matfile = Path(matfile).expanduser().absolute()
    if not matfile.exists():
        raise FileNotFoundError(f"{matfile} not found")
    addpath = str(Path(__file__).parent.parent / "ml")
    content = template.format(addpath=addpath, fname=matfile, savefile=tmpdir.matfile)
    tmpdir.refresh()
    with tmpdir.mfile.open("w") as f:
        print(content, file=f)
    return tmpdir.mfile


def create_shell_commands(mfile: FileName) -> List[str]:
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


def convert_mat(fname: FileName) -> MatFileContent:
    "convert an automated-mat to a python dictionary"
    tmpdir.refresh()
    create_matlab_commands(fname)
    assert tmpdir.mfile.exists()
    try:
        commands: Union[str, List[str]]
        commands = create_shell_commands(tmpdir.mfile)
        print(f"MATPROT: Running on {platform}")
        if "win" in platform:
            commands = " ".join(commands)
        print(f"MATPROT: executing {commands}")
        subprocess.run(commands, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        content = loadmat(tmpdir.matfile)
    except Exception as e:
        print("MATPROT: Conversion was not successfull due to:", e)
        if not is_matlab_installed():
            print("MATPROT: Found no matlab installation")
    finally:
        tmpdir.refresh()
    return content


# -----------------------------------------------------------------------------


def get_fs(content: MatFileContent) -> int:
    "returns the sampling rate of the converted matfile"
    return int(content["fs"][0][0])


def get_channel(content: MatFileContent, target_channel: str) -> TraceData:
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


def get_enames(content: MatFileContent) -> List[str]:
    "return the name of the events in matfile content"
    sc = content["stim_code"].tolist()
    return [str(sc[0]) for sc in sc]


# -----------------------------------------------------------------------------
def is_matlab_installed() -> bool:
    "returns true if a matlab installation was found, false otherwise"
    try:
        ret = subprocess.run(
            ["matlab", "-help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return ret.stderr == b""
    except FileNotFoundError:
        return False


def cut_into_traces(
    content: MatFileContent,
    target_channel: str,
    pre_in_samples: int = 100,
    post_in_samples: int = 100,
    onsets=List[int],
) -> List[TraceData]:
    """cut data recorded with automated-mat into epochs

    args
    ----
    content: MatFileContent
        the content of a matfile converted via :func:`convert_mat`
    target_channele: str
        which channel to cut
    pre_in_samples: int    
        how many samples to cut before the TMS pulse
    post_in_samples: int
        how many samples to cut after the TMS pulse
    onsets:List[int]
        when TMS was triggered
    returns
    -------
    traces: List[TraceData]
        a list of traces for each trigger recorded

    """
    full_trace = get_channel(content, target_channel)

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
