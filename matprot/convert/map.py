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
from typing import List


class TmpDir:
    def __init__(self):
        self.tmpdir = Path(mkdtemp())
        self.matfile = self.tmpdir / "conversion.mat"
        self.mfile = self.tmpdir / "conversion.m"
        assert self.tmpdir.exists()
        print("Created temporary directory at", self.tmpdir)

    def __del__(self):
        print("Deleting", self.tmpdir)
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
def create_m_cmds(fname: str):
    """create an mfile to convert the object in matlab

    loads the object and saves it as simple .mat-file
    """
    template = """
    addpath("/media/rgugg/tools/matlab/mltools")
    [data, fs, chan_names, stim_onset, stim_code] = tms.load_mat(\"{fname}\");
    save(\"{savefile}\", "data", "fs", "chan_names", "stim_onset", "stim_code");
    """
    content = template.format(fname=fname, savefile=tmpdir.matfile)
    tmpdir.refresh()
    with tmpdir.mfile.open("w") as f:
        print(content, file=f)

    return tmpdir.mfile, tmpdir.matfile


def create_bash_cmd(mfile: str) -> List[str]:
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


def convert_mat(fname: str) -> dict:
    "convert an automated-mat to a python dictionary"
    mfile, matfile = create_m_cmds(fname)
    try:
        commands = create_bash_cmd(mfile)

        if subprocess.run(
            commands, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ):
            content = loadmat(matfile)
        else:
            content = None
    finally:
        Path(mfile).unlink()
        Path(matfile).unlink()
    return content


# -----------------------------------------------------------------------------
def tkeo(a):
    """
	Calculates the TKEO of a given recording by using 2 samples.
	See Li et al., 2007
	Arguments:
	a 			--- 1D numpy array.
	Returns:
	1D numpy array containing the tkeo per sample
	"""

    # Create two temporary arrays of equal length, shifted 1 sample to the right
    # and left and squared:
    i = a[1:-1] * a[1:-1]
    j = a[2:] * a[:-2]

    # Calculate the difference between the two temporary arrays:
    aTkeo = i - j

    return aTkeo


def cut_epoch_mat(
    content: dict, muscle: str, pre_in_ms: float = 500, post_in_ms: float = 500
):
    """cut data recorded with automated-mat into epochs

    resample if necessary to 1kHz
    """
    try:
        channel_index = np.where(content["chan_names"][0] == muscle)[0][0]
    except IndexError:
        raise IndexError(f"{muscle} was not found in the available channels!")

    trace = content["data"][:, channel_index]
    fs = content["fs"][0][0]
    # upsample all signals to 5kHz
    trial_len = pre_in_ms + post_in_ms
    pre_in_samples = int(pre_in_ms * fs / 1000)
    post_in_samples = int(post_in_ms * fs / 1000)
    # padding the signal to make sure we have enough data left and right of
    # the stimulus. padding is done to the left and right by default with a # +
    # zero, but causes an offset to the left of the pad_size
    pad_size = pre_in_samples + post_in_samples
    padded = np.pad(trace, pad_size, "constant")
    # l0 = np.pad(trace, padding_offset, "constant").shape[0]
    # l1 = trace.shape[0]
    # assert (l0 - l1) == 2 * padding_offset

    ERROR = np.zeros((pre_in_samples + post_in_samples))
    ERROR.fill(np.NaN)
    epochs = []
    look_around = int(10 * fs / 1000)  # look 10ms before and after
    for onset in content["stim_onset"][:, 0].tolist():
        # cut signals from pre to post, with TMS pulse in the middle
        a, b = onset - look_around, onset + look_around
        # shift to account for the offset due to padding
        a += pad_size
        b += pad_size
        trial = padded[a:b]
        if trial.std() == np.inf:
            epochs.append(ERROR)
            continue
        shift = np.argmax(tkeo(trial)) - look_around
        # found the empirical strongest peak of the artifact
        # shift the center of the trial there
        a, b = onset - pre_in_samples, onset + post_in_samples
        a += pad_size + shift
        b += pad_size + shift
        trial = padded[a:b]
        if np.ptp(trial[: pre_in_samples - 5]) > 50:
            epochs.append(ERROR)
            continue
        if fs != 1000:
            trial = resample(trial, trial_len)

        epochs.append(trial)
    return np.asanyarray(epochs)
