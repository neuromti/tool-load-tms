classdef TimerService < handle
    properties
        t0;
    end
    
    methods(Access = public)
        function initialize(obj)
           obj.t0 = tic; 
        end
        
        function ms = getTime(obj)
            ms = toc(obj.t0) * 1000;
        end
    end
    
    methods(Static)
        function ins = getInstance()
            persistent instance;
            
            if( ~strcmpi(class(instance), 'TimerService') )
                instance = TimerService();
            end
            
            ins = instance;
        end
    end
    
     methods(Access = private)
        function obj = TimerService()
            
        end
    end
end