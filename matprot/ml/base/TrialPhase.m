% Defiones the values for the different TrialPhases
classdef TrialPhase < handle
   properties(Constant)
      % CURRENT PHASE
      BEGIN  = 1;
      FINISH = 2;
      MIDDLE = 3;
      
      %PHASE
      A  = 4;
      B  = 5;
      C  = 6;
      D  = 7;
      E  = 8;
      
      % REPEAT
      ON_BEGIN = 9; 
      ON_END   = 10;
      ALWAYS   = 11;
   end
end