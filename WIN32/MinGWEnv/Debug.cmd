@ECHO OFF
setlocal

echo This is a diagnostics Debug file to display various variables in the
echo command shell to interpret from.
echo.
echo The command shell takes percent zero, through percent nine where percent
echo zero is the name of the executing file itself.  For details on command
echo interpreter variables substitution, type in Help For on the command prompt.
echo.
echo For this debug file, here are the following values:
echo -Var-      = -Value-
echo.
echo ~          = %~0
echo ~f         = %~f0
echo ~d         = %~d0
echo ~p         = %~p0
echo ~n         = %~n0
echo ~x         = %~x0
echo ~s         = %~s0
echo ~a         = %~a0
echo ~t         = %~t0
echo ~z         = %~z0
echo ~dp        = %~dp0
echo ~nx        = %~nx0
echo ~fs        = %~fs0
echo ~ftza      = %~ftza0

echo ~dp$PATH:  = %~dp$PATH:0

SET PATH=%~dp0;%PATH%

echo ~dp$PATH:  = %~dp$PATH:0

endlocal
