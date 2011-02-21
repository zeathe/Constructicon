@ECHO OFF

pushd %~dp0

pushd ..\WINx86\java\jre6\bin
SET PATH=%cd%;%PATH%
cd ..
SET JAVA_HOME=%cd%
popd

pushd ..\WINx86\Python27
SET PYTHONBIN=%cd%\python.exe
SET PYTHONPATH=%cd%\libs
popd

SET PYTHONPATH=%PYTHONPATH%;%cd%\lib

popd

%PYTHONBIN% %*


