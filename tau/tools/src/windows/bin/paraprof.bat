::
:: set TAU_ROOT below and make sure java is in your path
::
@echo off
set TAU_ROOT=..

set JAR_ROOT=%TAU_ROOT%\bin
set ETC=%TAU_ROOT%\etc
set PERFDMF_JAR=%JAR_ROOT%/perfdmf.jar
set JARGS_JAR=%JAR_ROOT%/jargs.jar
set JDBC_JAR=%JAR_ROOT%/postgresql.jar;%JAR_ROOT%/mysql.jar;%JAR_ROOT%/oracle.jar;%JAR_ROOT%/derby.jar
set COMMON_JAR=%JAR_ROOT%/tau-common.jar

java -d64 -version >nul 2>&1
if errorlevel 1 goto 32bitjava
set JOGL_ROOT=%JAR_ROOT%\jogl64
goto SETJARS
:32bitjava
set JOGL_ROOT=%JAR_ROOT%\jogl32
:SETJARS

set JARS=%JAR_ROOT%/paraprof.jar;%JAR_ROOT%/vis.jar;%PERFDMF_JAR%;%JOGL_ROOT%/jogl.jar;%JOGL_ROOT%/gluegen-rt.jar;%JAR_ROOT%/jgraph.jar;%JDBC_JAR%;%JAR_ROOT%/jargs.jar;%JAR_ROOT%/epsgraphics.jar;%JAR_ROOT%/batik-combined.jar;%JAR_ROOT%/tau-common.jar;%JAR_ROOT%/jfreechart-1.0.12.jar;%JAR_ROOT%/jcommon-1.0.15.jar;%JAR_ROOT%/xerces.jar;%JAR_ROOT%/mesp.jar;%JAR_ROOT%/CubeReader.jar

echo.
java -Xmx500m -Djava.library.path=%JAR_ROOT%;%JOGL_ROOT% -Dderby.system.home="%HOMEPATH%/.ParaProf" -cp %JARS% edu/uoregon/tau/paraprof/ParaProf -j %JAR_ROOT% -c %ETC% %1 %2 %3 %4 %5

:handleError
if not errorlevel 1 goto finalActions
echo.
echo Failed to execute ParaProf... 
echo Please check to make sure Sun Java is installed and is in the path
echo. 

pause
:finalActions
