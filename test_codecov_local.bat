@echo off
REM Test Codecov integration locally
echo Testing Codecov Integration...
echo.

REM Change to backend directory
cd backend

REM Run pytest with coverage
echo Running pytest with coverage...
python -m pytest --cov --cov-report=xml --junitxml=junit.xml -o junit_family=legacy -v

REM Check if files were generated
echo.
echo Checking generated files...
if exist coverage.xml (
    echo [OK] coverage.xml generated
) else (
    echo [ERROR] coverage.xml not found
)

if exist junit.xml (
    echo [OK] junit.xml generated
) else (
    echo [ERROR] junit.xml not found
)

if exist htmlcov (
    echo [OK] HTML coverage report generated
) else (
    echo [ERROR] HTML coverage report not found
)

echo.
echo Test complete!
echo.
echo To test Codecov integration:
echo 1. Create a Pull Request on GitHub
echo 2. The @codecov-ai-reviewer bot will comment automatically
echo 3. Check https://codecov.io/gh/itcaffenet-Ljubinje/GGnet

cd ..

