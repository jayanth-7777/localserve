@echo off
setlocal
echo ==============================================================
echo   LOCALServe - 1-Click Push to GitHub
echo ==============================================================
echo.
set "GIT_EXE=%LOCALAPPDATA%\MinGit\cmd\git.exe"
if not exist "%GIT_EXE%" (
    where git >nul 2>nul
    if %errorlevel% equ 0 (
        set "GIT_EXE=git"
    ) else (
        echo [ERROR] Git was not found!
        pause
        exit /b 1
    )
)

echo Enter your GitHub repository URL:
echo (Example: https://github.com/your-username/localserve.git)
echo.
set /p REPO_URL="Repository URL: "

if "%REPO_URL%"=="" (
    echo [ERROR] No URL provided.
    pause
    exit /b 1
)

echo.
echo Adding remote origin...
"%GIT_EXE%" remote remove origin >nul 2>nul
"%GIT_EXE%" remote add origin %REPO_URL%
"%GIT_EXE%" branch -M main

echo Pushing code to GitHub...
"%GIT_EXE%" push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ==============================================================
    echo [SUCCESS] Code pushed to GitHub successfully!
    echo.
    echo Now open Render.com to deploy:
    echo 1. Go to https://dashboard.render.com
    echo 2. Click "New +" -> "Web Service"
    echo 3. Select your repository: %REPO_URL%
    echo 4. Click "Deploy Web Service"!
    echo ==============================================================
) else (
    echo.
    echo [NOTICE] If push failed, make sure you created the empty repo
    echo on GitHub and entered your GitHub credentials if prompted.
)
echo.
pause
