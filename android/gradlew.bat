@rem Gradle startup script using the locally cached Gradle 8.9 distribution.
@if "%DEBUG%"=="" @echo off
setlocal

if "%JAVA_HOME%"=="" set JAVA_HOME=D:\Java\ideaIU-2025.2.win\jbr
set JAVA_EXE=%JAVA_HOME%\bin\java.exe

set GRADLE_HOME_DIR=
for /d %%D in ("%USERPROFILE%\.gradle\wrapper\dists\gradle-8.9-bin\*") do (
  if exist "%%D\gradle-8.9\lib" set GRADLE_HOME_DIR=%%D\gradle-8.9
)

if "%GRADLE_HOME_DIR%"=="" (
  echo Gradle 8.9 distribution not found in local wrapper cache.
  exit /b 1
)

set ARGS_FILE=%TEMP%\tutorial-coach-gradle.args
> "%ARGS_FILE%" echo -Dorg.gradle.daemon=false
>> "%ARGS_FILE%" echo -cp
>> "%ARGS_FILE%" echo %GRADLE_HOME_DIR%\lib\*;%GRADLE_HOME_DIR%\lib\plugins\*
>> "%ARGS_FILE%" echo org.gradle.launcher.Main

"%JAVA_EXE%" @"%ARGS_FILE%" %*
set RC=%ERRORLEVEL%
del "%ARGS_FILE%"
exit /b %RC%