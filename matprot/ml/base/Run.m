% A Run is collection of trials, i.e. the actual repeatable task performed
% by the subject. Common functions whithin the Run are the data acquisition
% and processing steps. Timing is NOT controlled here (see Trial)
classdef Run < handle
    properties
        trial    % Task to be executed
        nTrials  % How many times the task shoud be repeated
        screenId
        
        onFinish
        onFinishArgs
        NF
        
        onInit
        onInitArgs
        NB
        
        begin_timestamp;
        end_timestamp;
        
        description;
        
        notes;
        logger;
        
        % Save run parameters here
        condition_params
    end
    methods
        function obj = Run(trial, N)
            obj.trial    = trial;
            obj.nTrials  = N;
            obj.NB = 0;
            obj.NF = 0;
            obj.logger = Logger.getInstance();
        end
        
        function setConditionParams(obj, val)
            obj.condition_params = val;
        end
        
        % Executed at the end of runs
        function onAfterFinish(obj, func_ptr, args)
            if( ~strcmpi(class(func_ptr), 'function_handle') )
                error('Arg 1 is not a function_handle');
            end
            
            if( ~strcmpi(class(args), 'cell') )
                error('Arg 2 has to be a cell-array');
            end
            
            obj.onFinish     = func_ptr;
            obj.onFinishArgs = args;
            obj.NF = 1;
        end
        
        function onBeforeStart(obj, func_ptr, args)
            if( ~strcmpi(class(func_ptr), 'function_handle') )
                error('Arg 1 is not a function_handle');
            end
            
            if( ~strcmpi(class(args), 'cell') )
                error('Arg 2 has to be a cell-array');
            end
            
            obj.onInit     = func_ptr;
            obj.onInitArgs = args;
            obj.NB = 1;
        end
        
        function setDescription(obj, desc)
            obj.description = desc;
        end
        
        function run(obj, buffer_list)
            tr = 0;
            timer = TimerService.getInstance();
            obj.begin_timestamp = timer.getTime();
            
            if( obj.NB )
                args = obj.onInitArgs;
                feval(obj.onInit, args{:});
            end
            
            obj.logger.info('Calling trial initialization', 'Run');
            obj.trial.init(buffer_list);
            
            obj.logger.info('Starting trial execution', 'Run');
            while tr < obj.nTrials
                tr = obj.trial.exec(buffer_list);
            end
            
            obj.trial.clean_data();
            
            if( obj.NF )
                finArgs{1} = obj.trial.data_list;
                finArgs{2} = obj.trial.markers;
                finArgs{3} = obj.trial.marker_time;
                
                for i = 1:length(obj.onFinishArgs)
                    finArgs{i+3} = obj.onFinishArgs{i};
                end
                feval(obj.onFinish, finArgs{:} );
            end
            
            obj.end_timestamp = timer.getTime();
            
        end
    end
end