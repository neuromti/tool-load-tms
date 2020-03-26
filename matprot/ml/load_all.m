function [data, fs, chan_names, stim_onset, stim_code, mso, subid, recdate]  = load_all(fname)

    % turn of warning, as we cant load all objects in mat
    warning off
    load(fname);
    warning on

    chan_names = obj.ampSettings.ChanNames;
    fs = obj.ampSettings.SampRate;
    data = obj.dataEEGEMG(:,1:end-1);
    stim_chan = obj.dataEEGEMG(:,end);
    stim_onset = find(diff(stim_chan)>0)+1;
    stim_code = stim_chan(stim_onset)*10;
    mso = obj.tms_settings.int_MSO;
    subid = obj.dataSub.initials(1:4);
    try
        recdate = datetime(obj.dataSub.date);
        recdate = [recdate.Year, recdate.Month, recdate.Day];
    catch ME
        disp("Error in datefield")
        recdate = [0, 0, 0];
    end
    
    
