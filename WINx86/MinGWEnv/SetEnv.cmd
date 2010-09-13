@ECHO OFF
echo ********************************************************************************
echo     Configuring Environment Vars for Building with MinGW...
echo ********************************************************************************
:: Set up all Environment Variables
SET _MinGWBuild=%~dp0Build
SET _MinGWTEMP=%~dp0TEMP
SET _MinGWRoot=%~dp0MinGW
SET _MinGWBin=%_MinGWRoot%\Bin
SET _MinGWLib=%_MinGWRoot%\lib
SET _MinGWInc=%_MinGWRoot%\include

:: Generate Build and TEMP dirs if they don't exist
IF NOT EXIST %_MinGWBuild% mkdir %_MinGWBuild%
IF NOT EXIST %_MinGWTEMP% mkdir %_MinGWTEMP%

:: Check if PATH was previously already altered
echo %PATH% | findstr %_MinGWBin% >NUL
SET _PathAltered=%ERRORLEVEL%

IF NOT %_PathAltered%==0 (
	:: Add MinGW Binaries to PATH
	SET _PreMinGWPATH=%PATH%
	SET PATH=%_MinGWBin%;%PATH%
) else (
	:: Skip Path Modification
	echo.
	echo ----- MinGW Already in Path, Not Altering PATH
	echo.
)

echo     The Following Variables are now available:
echo       _MinGWBuild    = %_MinGWBuild%
echo       _MinGWTEMP     = %_MinGWTEMP%
echo       _MinGWRoot     = %_MinGWRoot%
echo       _MinGWBin      = %_MinGWBin%
echo       _MinGWLib      = %_MinGWLib%
echo       _MinGWInc      = %_MinGWInc%
echo.
echo       Your PATH variable used to be:
echo       %_PreMinGWPATH%
echo.
echo       Your Path is now:
echo       %PATH%
echo.
echo       To Restore your PATH statement, copy and execute the following:
echo       SET PATH=%_PreMinGWPATH%
echo ********************************************************************************

prompt [MinGW] $p$g
