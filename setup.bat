@echo off
echo Creating Apna Bhagalpur Project Structure...

REM Create folders
mkdir frontend\css
mkdir frontend\js
mkdir frontend\images
mkdir backend\app\models
mkdir backend\app\schemas
mkdir backend\app\routes
mkdir backend\app\services
mkdir .vscode

REM Create files
type nul > frontend\css\style.css
type nul > frontend\js\app.js
type nul > frontend\index.html
type nul > frontend\booking.html
type nul > frontend\tracking.html
type nul > frontend\admin.html
type nul > frontend\my-bookings.html
type nul > backend\requirements.txt
type nul > backend\.env
type nul > backend\app\__init__.py
type nul > backend\app\main.py
type nul > backend\app\config.py
type nul > backend\app\database.py
type nul > .vscode\settings.json
type nul > .gitignore
type nul > README.md

echo.
echo ✅ Project structure created successfully!
echo Opening in VS Code...
code .
pause