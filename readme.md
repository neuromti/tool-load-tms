This repo contains the source code of the objects required to load the `.mat`-files of the objects recorded with the UKT-Toolbox.

### Installation

```matlab

% add the installation directory to the path
addpath("/installation/directory")
% load data
[data, fs, chan_names, stim_onset, stim_code]  = tms.load_mat(fname)
```
