@echo off
setlocal enabledelayedexpansion

REM ZXing JAR Build Script for Windows
echo 🔨 Building ZXing JAR file...

REM Check if Java is installed
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Java is not installed. Please install Java 8 or higher.
    exit /b 1
)

REM Check if Maven is installed
mvn -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Maven is not installed. Please install Maven 3.6 or higher.
    exit /b 1
)

REM Get script directory
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..\
set ZXING_DIR=%PROJECT_DIR%zxing

REM Check if ZXing submodule exists
if not exist "%ZXING_DIR%" (
    echo 📥 Initializing ZXing submodule...
    cd %PROJECT_DIR%
    git submodule update --init --recursive
)

cd %ZXING_DIR%

REM Get ZXing version from config
echo Getting ZXing version...
for /f "delims=" %%i in ('python3 -c "from pyzxing.config import Config; print(Config.DEFAULT_ZXING_VERSION)"') do set ZXING_VERSION=%%i
echo 🎯 Building ZXing version: %ZXING_VERSION%

REM Clean previous builds
echo 🧹 Cleaning previous builds...
call mvn clean -DskipTests

REM Build ZXing core
echo 📦 Building ZXing core...
call mvn install -DskipTests -Drat.skip=true

REM Build JAR with dependencies
echo 🔧 Building JAR with dependencies...
cd javase
call mvn package -DskipTests -Drat.skip=true assembly:single

REM Find the built JAR file
set JAR_FILE=
for /f "delims=" %%f in ('dir /b target\*jar-with-dependencies.jar 2^>nul') do (
    set JAR_FILE=target\%%f
)

if "%JAR_FILE%"=="" (
    echo ❌ JAR file not found in target directory
    exit /b 1
)

REM Copy JAR to project's release directory
set RELEASE_DIR=%PROJECT_DIR%releases
if not exist "%RELEASE_DIR%" mkdir "%RELEASE_DIR%"

set JAR_FILENAME=javase-%ZXING_VERSION%-SNAPSHOT-jar-with-dependencies.jar
copy "%JAR_FILE%" "%RELEASE_DIR%\%JAR_FILENAME%"

echo ✅ JAR file built successfully!
echo 📁 Location: %RELEASE_DIR%\%JAR_FILENAME%

REM Show file size
for %%F in ("%RELEASE_DIR%\%JAR_FILENAME%") do (
    set FILE_SIZE=%%~zF
    set /a FILE_SIZE_MB=!FILE_SIZE!/1024/1024
    echo 📏 Size: !FILE_SIZE_MB! MB
)

REM Test the JAR file
echo 🧪 Testing JAR file...
java -jar "%RELEASE_DIR%\%JAR_FILENAME%" --help >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ JAR file test passed!
) else (
    echo ⚠️  JAR file test failed, but file was created successfully
)

echo 🎉 ZXing JAR build completed!