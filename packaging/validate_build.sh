#!/bin/bash
# Validation script for checking AppImage build requirements

set -e

APP_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
echo "Validating ControllerLaunch build environment in: $APP_DIR"

# Check for required directories
echo -n "Checking directory structure... "
REQUIRED_DIRS=("src" "config" "assets" "assets/icons" "install" "packaging")
MISSING_DIRS=0
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$APP_DIR/$dir" ]; then
        echo -e "\nMissing directory: $dir"
        MISSING_DIRS=$((MISSING_DIRS + 1))
    fi
done

if [ $MISSING_DIRS -eq 0 ]; then
    echo "OK"
else
    echo "FAILED: $MISSING_DIRS directories missing"
fi

# Check for required files
echo -n "Checking core files... "
REQUIRED_FILES=(
    "src/main.py"
    "src/controller_daemon.py"
    "src/game_library.py"
    "src/overlay_ui.py"
    "src/config_manager.py"
    "src/preferences_ui.py"
    "config/default_config.json"
    "install/AppRun"
    "install/controller-launch.desktop"
    "assets/icons/controller-launch.svg"
    "requirements.txt"
    "setup.py"
)
MISSING_FILES=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$APP_DIR/$file" ]; then
        echo -e "\nMissing file: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -eq 0 ]; then
    echo "OK"
else
    echo "FAILED: $MISSING_FILES files missing"
fi

# Check Python environment and dependencies
echo -n "Checking Python environment... "
if command -v python3 &> /dev/null; then
    echo "Python found: $(python3 --version)"
    
    echo -n "Checking required Python packages... "
    if ! python3 -c "import gi; gi.require_version('Gtk', '3.0'); import pygame" &> /dev/null; then
        echo "FAILED: Missing required Python packages"
        echo "Please run: pip3 install -r $APP_DIR/requirements.txt"
    else
        echo "OK"
    fi
else
    echo "FAILED: Python 3 not found"
fi

# Check for AppImage build dependencies
echo -n "Checking AppImage build dependencies... "
if ! command -v wget &> /dev/null; then
    echo "FAILED: wget not found"
else
    echo "OK"
fi

# Check packaging script
echo -n "Checking build script... "
if [ ! -x "$APP_DIR/packaging/build_appimage.sh" ]; then
    echo "FAILED: build_appimage.sh is not executable"
    echo "Please run: chmod +x $APP_DIR/packaging/build_appimage.sh"
else
    echo "OK"
fi

# Print summary
echo ""
echo "Validation Summary:"
if [ $MISSING_DIRS -eq 0 ] && [ $MISSING_FILES -eq 0 ]; then
    echo "✅ All required files and directories found"
    echo "✅ Project structure is valid for AppImage building"
    echo ""
    echo "You can now build the AppImage with:"
    echo "  ./packaging/build_appimage.sh"
else
    echo "❌ Missing required files or directories"
    echo "Please fix the issues above before building AppImage"
fi
