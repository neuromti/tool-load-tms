Tools to load TMS data from the legacy matlab protocols into Matlab or Python

### Installation

clone the repository with `https://github.com/neuromti/tool-load-tms.git` and `pip install -e .`

Requires a Matlab installation with valid registration.

### Example

If you want to read the MEP traces from an old matfile into Python, you can do as follows:

``` python
from matprot.convert.traces import convert_mat, cut_into_traces
content = convert_mat("path_to.mat")
print(content['chan_names'])
# e.g. [[array(['EDC_L'], dtype='<U5') array(['BB_L'], dtype='<U4')
#        array(['EDC_R'], dtype='<U5')]]
# convert the array of onset sample indices into a list of integers
onsets = [onset[0] for onset in content['stim_onset']]
# select an existing channel, and
# cut from 100 before to 100 samples after each onset
traces = cut_into_traces(content, "EDC_L", 100, 100,  onsets)
```

[![cut traces video](https://img.youtube.com/vi/be6HDzV27QI/0.jpg)](https://www.youtube.com/watch?v=be6HDzV27QI)


#### See also
https://github.com/neuromti/TMS_Toolbox
https://github.com/neuromti/UKT_toolbox
