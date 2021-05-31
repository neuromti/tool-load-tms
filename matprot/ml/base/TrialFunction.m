% Defines which function will be called and how often during the Study main
% loop.
% 
% To create a trial function, create a function with the folowing
% signature:
%
% [out_data, label, marker] = func_name(in_data, epoch_idx, ...)
% in_data: SAMPS X NCH for each data source (buffer) since beginning of
% phase or epoch
% epoch_idx: index of epoch in the run
% out_data: modified in_data
% label:   class label for the data
% marker: software timestamp marker with value  20 .. 200
%
% If in_data is not modified or there is no need of label and marker
% functionality, just set them to empty.
%
% Once the function is defined, create a TrialFunction as follows
%
%
% TrialFunction(@func_name, { ... }, trialPhase.C, trialPhase.ALWAYS, opts )
%
% ... -> arbitrary parameters
% TrialPhase: A, B, C, D or E
% TrialPhase: ALWAYS, ON_BEGIN or ON_END
% opts: Pair Name/Value from the following list
%
% Frequency   N      How often the function will be called if REP is ALWAYS
classdef TrialFunction < handle
   properties(Access = private)
       func_ptr
       args
       repeat
       executed
       phase
       trial_phase
       freq
       
       t_last_exec
   end

   methods(Access = public)
       
       
       function obj = TrialFunction(func_ptr, args, phase, repeat, varargin)
           obj.func_ptr     = func_ptr;
           obj.args         = args;
           obj.repeat       = repeat;
           obj.phase        = phase;
           obj.executed     = 0;
           obj.trial_phase  = TrialPhase;
           
           obj.freq         = -1;
           obj.t_last_exec  = tic;
           
           if( length(varargin) == 1 )
               obj.freq = varargin{1};
           else
               for i = 1:2:length(varargin)
                    if( strcmpi(varargin{i}, 'Frequency'))
                        obj.freq = varargin{i+1};
                    end

                    if( strcmpi(varargin{i}, 'TrialData'))
                        obj.trial_data = varargin{i+1};
                    end
               end
           end
       end
       
       
       % DEPRECATED. Will be deleted
       function TrialFunction__(obj, func_ptr, args, phase, repeat, freq)
           fprintf('WARN: This function is deprecated and wil be removed in future versions');
           obj.func_ptr     = func_ptr;
           obj.args         = args;
           obj.repeat       = repeat;
           obj.phase        = phase;
           obj.executed     = 0;
           obj.trial_phase  = TrialPhase;
           
           obj.freq         = freq;
           obj.t_last_exec  = tic;
       end
       
       function T = getExecPeriod(obj)
          if( obj.repeat == obj.trial_phase.ON_BEGIN)
              T = -1;
          elseif( obj.repeat == obj.trial_phase.ON_END)
              T = 0;
          else
              T = 1/obj.freq; 
          end
       end
       
%        function [ptr, args] = getFunction(obj);
%            ptr = obj.func_ptr;
%            args = obj.args;
%        end
%        
%        function [data_m label marker] = exec(obj, data, trial_idx)
%             data_m = {};
%             label  = [];
%             marker = [];
%             
%             args   = {data, trial_idx, obj.args{:}};
%             [data_m label marker] = feval(obj.func_ptr, args{:}); 
%         end
       
        function [data_m label marker] = exec(obj, current_phase, current_rep, data, trial_idx)
            data_m = {};
            label  = [];
            marker = [];
            exec = 0;
            if( current_phase == obj.phase )
               if( obj.repeat == obj.trial_phase.ALWAYS && obj.isOnTimeExec() ), exec = 1; end
               if( obj.repeat == obj.trial_phase.ON_BEGIN && current_rep == obj.trial_phase.BEGIN ), exec = 1; end
               if( obj.repeat == obj.trial_phase.ON_END   && current_rep == obj.trial_phase.FINISH ),exec = 1; end
            end
            
            if( exec )
               args   = {data, trial_idx, obj.args{:}};
               [data_m label marker] = feval(obj.func_ptr, args{:}); 
               
               obj.executed     = 1; % Currently not used
            end
        end
   end
   
   methods(Access = private)
       function exec = isOnTimeExec(obj)
           exec = 0;
           if( obj.freq > 0 )
              T = 1/obj.freq; 
              %tn = clock;
              %tn = tn(end);
              % Account for the turn of the minute
              %if( tn < obj.t_last_exec )
              %    tn = tn + 60;
              %end
              
              %if( tn - obj.t_last_exec >= T )
              if( toc( obj.t_last_exec ) >= T )
                  obj.t_last_exec = tic;
                  exec = 1;
              end
           end
       end
   end
end