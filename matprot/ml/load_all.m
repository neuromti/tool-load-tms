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
    try
        mso = obj.tms_settings.int_MSO;
    catch ME
        mso = 0;
    end
    subid = obj.dataSub.initials(1:4);
    try
        recdate = datetime(obj.dataSub.date);
        recdate = [recdate.Year, recdate.Month, recdate.Day];
    catch ME
        recdate = obj.dataSub.initials(6:16);        
        recdate = datevec(recdate);
        recdate = [recdate(1), recdate(2), recdate(3)];
    end
    
    
