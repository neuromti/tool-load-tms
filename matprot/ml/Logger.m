classdef Logger < handle
   properties
      type
      path
      fid
      level
      is_init = 0;
   end
   
   methods(Access = public)
       function init(obj, type, level, varargin)
           if( strcmpi(type, 'screen') )
               obj.fid = 1; % Default screen fileID
               obj.type = 1;
           elseif(strcmpi(type, 'file'))
               if( isempty(varargin) )
                   error('[Logger] Log path is necessary\n');
               end
               obj.type = 2;
               obj.path = varargin{1};
               obj.fid = fopen(obj.path, 'w+'); 
           else
               error('[Logger] Type must either be screen or file\n');
           end
           
           if( strcmpi(level, 'info') || strcmpi(level, 'all') )
              obj.level = 0; 
           end
           
           if( strcmpi(level, 'warn') )
              obj.level = 1; 
           end
           
           if( strcmpi(level, 'error')  )
              obj.level = 2; 
           end
           
           obj.is_init = 1;
       end
       
       function release(obj)
           obj.is_init = 0;
           if( obj.type == 2 )
              fclose(obj.fid);
           end
       end
       
       function info(obj, message, varargin)
           if( obj.is_init && obj.level >= 0 )
               if( isempty(varargin) )
                    obj.printMessage('[INFO]', message);
               else
                    obj.printMessage('[INFO]', message, varargin);
               end
           end
       end
       
       
       function warn(obj, message, varargin)
           if( obj.is_init && obj.level >= 1 )
               if( isempty(varargin) )
                    obj.printMessage('[WARN]', message);
               else
                    obj.printMessage('[WARN]', message, varargin);
               end
           end
       end
       
       function error(obj, message, varargin)
           if( obj.is_init && obj.level >= 2 )
               if( isempty(varargin) )
                    obj.printMessage('[ERROR]', message);
               else
                    obj.printMessage('[ERROR]', message, varargin);
               end
           end
       end
   end
   
   methods(Static)
       function ins = getInstance()
           persistent instance;

           if( ~strcmpi(class(instance), 'logger') )
               instance = Logger();
           end
           
           ins = instance;
       end
   end
   
   methods(Access = private)
       function obj = Logger()
           
       end
       
       function printMessage(obj, type, message, varargin)
            nargin = length(varargin);
            
            fprintf(obj.fid, '%s\t', type);
            fprintf(obj.fid, '%s\t', obj.getTime());
            
            % Origin class
            if( nargin > 0 )
                fprintf(obj.fid, '%s | \t', cell2mat(varargin{1}) );
            end
            
            fprintf(obj.fid, '%s\n', message);
       end
       
       function s = getTime(obj)
           c = clock();
           
           minutes = num2str(c(end-1));
           if( length(minutes) == 1 ), minutes = ['0' minutes]; end
           
           hours = num2str(c(end-2));
           if( length(hours) == 1 ), hours = ['0' hours]; end
           
           seconds = num2str(c(end));
           if( length(seconds) == 1 ), seconds = ['0' seconds]; end
           
           s = [hours ':' minutes ':' seconds];

       end
   end

end