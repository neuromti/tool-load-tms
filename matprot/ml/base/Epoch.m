classdef Epoch < handle
    properties
        state
        it
        data_list
        last_read_list;
        datatime_list;
        up_data_list;
        
        datasamp_list;
        datatime_idx;
        fs;
        
        trials
        
        onPhaseList
        
        durations
        t0
        ellapsed
        
        phase;
        iexec;
       
        labels;
        cnt_labels;
        labels_time;
        timestamps;
        timestamps_i;
        up_mrk;
        disc_time;
        
        dm
        
        t_it_begin; % Time of a given trial iteration begin, i.e. the first phase of it
        
        markers;
        marker_time;
        marker_i;
        
        trial_sample_marker;
        phase_sample_marker;
        label_sample_marker;
        labels_ts;
        
        labeli
        calls;
        
        n_buffers;
        
        timer;
        epoch_data
    end
    
    methods(Access = public)
        function obj = Epoch(durations, varargin)
            obj.state      = 0;
            
            obj.durations  = durations;
            obj.phase      = TrialPhase;
            obj.timer      = TimerService.getInstance();
            
            obj.epoch_data = 0;
            
            for i = 1:2:length(varargin)
               if( strcmpi(varargin{i}, 'EpochData') )
                   obj.epoch_data = varargin{i+1};
               end
            end
        end
        
        
        function addTrialFunction(obj,  trial_func)
            if( ~strcmpi(class(trial_func), 'TrialFunction') )
                error('Parameter must be a TrialFunction class');
            end
                        
            N = numel(obj.onPhaseList);
            obj.onPhaseList{N+1} = trial_func;
        end
        
        % Since the data array is preallocated, it likely will contain lots
        % of trailing zeros. this functions eliminates those zeros
        function clean_data(obj)
              N_DS = length(obj.data_list);
              for i = 1:N_DS
                  obj.data_list{i}(obj.last_read_list(i)+1:end, :)  = [];
                  obj.datasamp_list{i}(obj.last_read_list(i)+1:end) = [];
                  obj.datatime_list{i}(obj.last_read_list(i)+1:end) = [];
              end
              obj.labels((obj.labeli+1):end)      = [];
              obj.labels_time((obj.labeli+1):end) = [];
              
              obj.timestamps(obj.timestamps_i+1:end) = [];
              obj.markers(obj.marker_i+1:end)        = [];
              obj.marker_time(obj.marker_i+1:end)    = [];
        end
        
        function init(obj, buffer_list)
            obj.it             = 0;
            obj.labeli         = 1;
            
            obj.timestamps     = single(zeros(150000,1));
            obj.markers        = single(zeros(2000, 1));
            obj.marker_time    = single(zeros(2000, 1) );
            obj.marker_i       = 1;
            
            obj.n_buffers      = length(buffer_list);
            obj.last_read_list = single(zeros(obj.n_buffers,1));
            obj.datatime_idx   = ones(obj.n_buffers,1);
            
            
            for i = 1:obj.n_buffers
                buffer               = buffer_list{i};
                NSamp                = buffer.getFs() * 60 * 10;

                obj.data_list{i}     = zeros(NSamp, buffer.getNCh(), 'single') ;
                obj.datatime_list{i} = ones(150000, 1, 'single').*realmax('single')-1;
                obj.datasamp_list{i} = ones(150000, 1, 'single').*realmax('single')-1;
                obj.fs(i)            = buffer.getFs();
            end
            
            obj.labels      = int32( ones(2500, 1).*-5 );
            obj.labels_time = uint32( zeros(2500, 1) );
            
            obj.read_data(buffer_list, 'discard');
            obj.calls                    = 1;
            obj.disc_time                = obj.timer.getTime();
            obj.timestamps(obj.calls)    = 0;
            obj.timestamps_i             = 1;
            obj.markers(obj.marker_i)    = 254;
            obj.marker_time(obj.marker_i)= obj.timestamps(obj.calls);
        end
        
        
        function start(obj, buffer_list)
            
            while( obj.durations(ii) == 0 ), ii = ii + 1; end
            
            obj.t0    = obj.timer.getTime() - obj.disc_time;
                
            obj.timestamps(obj.timestamps_i)  =  obj.t0; % Last executed marker
            obj.marker_i                  = obj.marker_i + 1;
            obj.marker_time(obj.marker_i) = obj.timestamps(obj.timestamps_i);
            obj.markers(obj.marker_i)     = 254;
            obj.t_it_begin                = obj.timestamps(obj.timestamps_i);
            
            sched = TaskScheduler.getInstance();
            
            sched.schedule(@obj.start_phase, {ii, buffer_list}, 0 );
        end
        
        function start_phase(obj, phase, buffer_list)
            obj.timestamps_i                 = obj.timestamps_i + 1;
            obj.timestamps(obj.timestamps_i) = obj.timer.getTime() - obj.disc_time;
            phaseID = obj.getExecPhase(i);
            
            % Sets the marker for phase begin
            obj.t0    = obj.timestamps(obj.timestamps_i); % Reset phase duration
            obj.calls = obj.calls + 1;
                    
            obj.marker_i                  = obj.marker_i + 1;
            obj.marker_time(obj.marker_i) = obj.timestamps(obj.timestamps_i);
            obj.markers(obj.marker_i)     = phaseID;
            
            
            % Reads data
            obj.read_data(buffer_list);
            
            % Schedules end of phase
            sched = TaskScheduler.getInstance();
            
            sched.schedule(@obj.end_phase, {i, buffer_list}, obj.durations(phase) );

            % Execute OnBegin functions
            CT = obj.timestamps(obj.timestamps_i);
            if( obj.epoch_data )
                 [new_datalist, tps]       = obj.getNewDataList(phaseID, obj.t_it_begin, CT);
             else
                 [new_datalist, tps]       = obj.getNewDataList(phaseID, obj.t0, CT);
            end
            
            N = numel(obj.onPhaseList);
            
            for f = 1:N
                exFunc = obj.onPhaseList{f};
                if( exFunc.getExecPeriod == -1 )
                    [data_list_m, label, marker] = exFunc.exec( new_datalist, obj.it+1 );

                    if( ~isempty(data_list_m) )
                        obj.modifyDataList(tps, data_list_m);
                    end


                    if( ~isempty(label) )
                        obj.labels(obj.labeli)      = label;
                        obj.labels_time(obj.labeli)  = obj.timestamps(obj.timestamps_i);%obj.datatime_idx(1)-1;
                        obj.labeli = obj.labeli + 1; 
                    end

                    if( ~isempty(marker) )
                        obj.marker_i = obj.marker_i + 1;
                        obj.marker_time(obj.marker_i) = obj.timestamps(obj.timestamps_i);
                        obj.markers(obj.marker_i) = marker;

                    end
                end
            end
            
            % Schedule ALWAYS functions
            phase_duration = obj.durations(phase);
            for f = 1:N
                exFunc = obj.onPhaseList{f};
                T = exFunc.getExecPeriod();
                nrep = floor( phase_duration / T );
                if( T > 0 )
                    sched.scheduleRepeat(@obj.exec_phase, {exFunc}, T, nrep-1, T);
                end
            end
        end
        
        function exec_phase(obj, exFunc)
            obj.timestamps_i                 = obj.timestamps_i + 1;
            obj.timestamps(obj.timestamps_i) = obj.timer.getTime() - obj.disc_time;
            
            % Reads data
            obj.read_data(buffer_list);
            
            % Gets new portion of data
            CT = obj.timestamps(obj.timestamps_i);
            if( obj.epoch_data )
                 [new_datalist, tps]       = obj.getNewDataList(-1, obj.t_it_begin, CT);
             else
                 [new_datalist, tps]       = obj.getNewDataList(-1, obj.t0, CT);
            end
            
            [data_list_m, label, marker] = exFunc.exec( new_datalist, obj.it+1 );
            
            if( ~isempty(data_list_m) )
                obj.modifyDataList(tps, data_list_m);
            end


            if( ~isempty(label) )
                obj.labels(obj.labeli)      = label;
                %obj.labels_time(obj.labeli) = obj.timestamps(obj.calls);
                obj.labels_time(obj.labeli)  = obj.timestamps(obj.timestamps_i);%obj.datatime_idx(1)-1;
                obj.labeli = obj.labeli + 1; 
            end

            if( ~isempty(marker) )
                obj.marker_i = obj.marker_i + 1;
                obj.marker_time(obj.marker_i) = obj.timestamps(obj.timestamps_i);
                obj.markers(obj.marker_i) = marker;

                if( marker == 253 )
                    end_trial = 1; 
                end
            end
            
        end
        
        function end_phase(obj, phase, buffer_list)
            obj.it = obj.it + 1;
            
            N = numel(obj.onPhaseList);
            
            for f = 1:N
                exFunc = obj.onPhaseList{f};
                if( exFunc.getExecPeriod == -1 )
                    [data_list_m, label, marker] = exFunc.exec( new_datalist, obj.it+1 );

                    if( ~isempty(data_list_m) )
                        obj.modifyDataList(tps, data_list_m);
                    end


                    if( ~isempty(label) )
                        obj.labels(obj.labeli)      = label;
                        %obj.labels_time(obj.labeli) = obj.timestamps(obj.calls);
                        obj.labels_time(obj.labeli)  = obj.timestamps(obj.timestamps_i);%obj.datatime_idx(1)-1;
                        obj.labeli = obj.labeli + 1; 
                    end

                    if( ~isempty(marker) )
                        obj.marker_i = obj.marker_i + 1;
                        obj.marker_time(obj.marker_i) = obj.timestamps(obj.timestamps_i);
                        obj.markers(obj.marker_i) = marker;

                    end
                end
            end
            
        end
        
        function N = exec(obj, buffer_list)
            if( obj.state == 0)
                obj.state = 1;
                obj.iexec = 1;
                obj.t0    = obj.timer.getTime() - obj.disc_time;
                
                obj.timestamps(obj.timestamps_i)  =  obj.t0; % Last executed marker
                obj.marker_i                  = obj.marker_i + 1;
                obj.marker_time(obj.marker_i) = obj.timestamps(obj.timestamps_i);
                obj.markers(obj.marker_i)     = 254;
                obj.t_it_begin                = obj.timestamps(obj.timestamps_i);
            end

            switch obj.state
                case 1
                    obj.onPhase(buffer_list, obj.phase.A, obj.durations(1) );
                case 2
                    obj.onPhase(buffer_list, obj.phase.B, obj.durations(2));
                case 3
                    obj.onPhase(buffer_list, obj.phase.C, obj.durations(3) );
                case 4
                    obj.onPhase(buffer_list, obj.phase.D, obj.durations(4) );
                case 5
                    obj.onPhase(buffer_list, obj.phase.E, obj.durations(5) );
                case 6
                    obj.it = obj.it + 1;
                    
                    obj.calls = obj.calls + 1;
                    obj.timestamps_i              = obj.timestamps_i + 1;
                    obj.timestamps(obj.timestamps_i)  =  obj.t0; % Last executed marker
                    
                    
                    obj.marker_i                  = obj.marker_i + 1;
                    obj.marker_time(obj.marker_i) = obj.timestamps(obj.timestamps_i);
                    obj.markers(obj.marker_i)     = 255;
                    
                    obj.state = 0;
                    obj.t_it_begin                = obj.timestamps(obj.timestamps_i);
            end
            
            N = obj.it;
        end

    end
    
    methods(Access = private)
        function ph = getExecPhase(obj, i)
            ph = 0;
            if( i == 1 ), ph = obj.phase.A; end
            if( i == 2 ), ph = obj.phase.B; end
            if( i == 3 ), ph = obj.phase.C; end
            if( i == 4 ), ph = obj.phase.D; end
            if( i == 5 ), ph = obj.phase.E; end
        end
        
        function resize_data(obj, buffer_list)
            for i = 1:obj.n_buffers
                buffer = buffer_list{i};
                
                NSamp            = buffer.getFs() * 10 * 60;
                obj.data_list{i} = [obj.data_list{i}; single( zeros(NSamp, buffer.getNCh()) ) ];
            end
        end
        
        function read_data(obj, buffer_list, varargin)
            
            for i = 1:obj.n_buffers
                buffer          = buffer_list{i};
                last_sample     = obj.last_read_list(i);
                [data_tmp, ~]   = buffer.read_data();
            
                if( ~isempty(data_tmp) )
                    dt0 = last_sample + 1;
                    tf = size(data_tmp,1)+ dt0 - 1;

                    if( tf > size(obj.data_list{1}, 1) )
                        obj.resize_data(buffer_list);
                    end
                    
                    if( isempty(varargin) ) % Otherwise, discards data...
                        obj.last_read_list (i)          = tf;
                        obj.data_list{i}(dt0:tf, :) = single(data_tmp);
                        obj.datasamp_list{i}(obj.datatime_idx(i) ) = dt0;
                        obj.datatime_list{i}(obj.datatime_idx(i) ) = obj.timestamps(obj.timestamps_i);
                        obj.datatime_idx(i) = 1 + obj.datatime_idx(i);
                    end
                end
                
            end
            
        end
        
        % Use a function to change phase, begin trial, end trial and so
        % on...
        % Acquire the data only at those defined points
        
        function onPhase(obj, buffer_list, current_phase, duration)
            % TODO: Change this to MATLAB Scheduler to make it cleaner
            if( duration > 0 ) % Has the phase any defined time?
                obj.timestamps_i                 = obj.timestamps_i + 1;
                obj.timestamps(obj.timestamps_i) = obj.timer.getTime() - obj.disc_time;
                
                if( obj.iexec == 1 )
                    obj.t0    = obj.timestamps(obj.timestamps_i); % Reset phase duration
                    obj.calls = obj.calls + 1;
                    
                    obj.marker_i                  = obj.marker_i + 1;
                    obj.marker_time(obj.marker_i) = obj.timestamps(obj.timestamps_i);
                    obj.markers(obj.marker_i)     = current_phase;
                end
                
                obj.read_data(buffer_list);

                N = numel(obj.onPhaseList);
                exec_n = obj.phase.MIDDLE;

                if( obj.iexec == 1 )
                    exec_n = obj.phase.BEGIN;
                end

                end_trial = 0;
                CT = obj.timestamps(obj.timestamps_i);
                if( obj.epoch_data )
                    [new_datalist, tps]       = obj.getNewDataList(current_phase, obj.t_it_begin, CT);
                else
                    [new_datalist, tps]       = obj.getNewDataList(current_phase, obj.t0, CT);
                end
                for f = 1:N

                    [data_list_m, label, marker] = obj.onPhaseList{f}.exec(current_phase, exec_n, new_datalist, obj.it+1 );
                    
                    if( ~isempty(data_list_m) )
                        obj.modifyDataList(tps, data_list_m);
                    end


                    if( ~isempty(label) )
                        obj.labels(obj.labeli)      = label;
                        %obj.labels_time(obj.labeli) = obj.timestamps(obj.calls);
                        obj.labels_time(obj.labeli)  = obj.timestamps(obj.timestamps_i);%obj.datatime_idx(1)-1;
                        obj.labeli = obj.labeli + 1; 
                    end
                    
                    if( ~isempty(marker) )
                        obj.marker_i = obj.marker_i + 1;
                        obj.marker_time(obj.marker_i) = obj.timestamps(obj.timestamps_i);
                        obj.markers(obj.marker_i) = marker;
                        
                        if( marker == 253 )
                            end_trial = 1; 
                        end
                    end
                end

                if( end_trial )
                    tf = 10000000;
                else
                    tf = obj.timestamps(obj.timestamps_i);
                end
                t_ellapsed = tf - obj.t0;
                obj.iexec = obj.iexec + 1;

                if( t_ellapsed  >= duration*1000 )
                    if( obj.epoch_data )
                        [new_datalist, tps]       = obj.getNewDataList(current_phase, obj.t_it_begin, CT);
                    else
                        [new_datalist, tps]       = obj.getNewDataList(current_phase, obj.t0, CT);
                    end
                    for f = 1:N
                        
                        
                        [data_list_m, label, marker]   = obj.onPhaseList{f}.exec(current_phase, obj.phase.FINISH, new_datalist, obj.it+1 );
                        if( ~isempty(data_list_m ) )
                            obj.modifyDataList(tps, data_list_m);
                        end

                        if( ~isempty(label) )
                            obj.labels(obj.labeli)    = label;
                            obj.labels_time(obj.labeli) = obj.timestamps(obj.timestamps_i);%obj.datatime_idx(1)-1;
                            obj.labeli = obj.labeli + 1; 
                        end
                        
                        if( ~isempty(marker) )
                            obj.marker_i = obj.marker_i + 1;
                            obj.marker_time(obj.marker_i) = obj.timestamps(obj.timestamps_i);
                            obj.markers(obj.marker_i) = marker;
                        end
                    end

                    obj.iexec = 1;
                    obj.state = obj.state + 1;

                    obj.t0 = obj.timer.getTime() - obj.disc_time; % Reset phase duration
                end
            else
                obj.state = obj.state + 1;
            end
        end

        function [data_list t0_list] = getNewDataList(obj, ~, t0, tf)
            t0_list   = cell(obj.n_buffers);
            data_list = cell(obj.n_buffers, 1);
            
            for i = 1:obj.n_buffers
                data      = obj.data_list{i};
                time_list = obj.datatime_list{i};
                samp_list = obj.datasamp_list{i};
                
                %fac = obj.fs(i)/1000;
                
                s0 = samp_list( find( time_list <= t0, 1, 'last') );
                sf = samp_list( find( time_list <= tf, 1, 'last') );
                if( isempty(s0) || s0 == 0), s0 = 1; end
                
                if( s0 ~= sf )
                   t0_list{i}   = [s0 sf];
                   %nch          = size(data,2);
                   data_list{i} = data(s0:sf,:);
                end
            end
        end

        function modifyDataList(obj, t_list, new_data)
            for i = 1:obj.n_buffers
                ts = t_list{i};
                if( ~isempty(ts) && ~isempty(new_data)  )
                    obj.data_list{i}(ts(1):ts(2), :) = new_data{i};
                end
            end
        end
    end
end