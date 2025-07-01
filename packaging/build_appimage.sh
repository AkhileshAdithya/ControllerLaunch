#!/bin/bash
# Build script for ControllerLaunch AppImage

set -e

# Define variables
APP_NAME="ControllerLaunch"
APP_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
BUILD_DIR="${APP_DIR}/build"
APPIMAGE_DIR="${BUILD_DIR}/AppDir"
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

echo "Building ${APP_NAME} AppImage..."
echo "App directory: ${APP_DIR}"
echo "Python version: ${PYTHON_VERSION}"

# Create build directories
mkdir -p "${APPIMAGE_DIR}/usr/bin"
mkdir -p "${APPIMAGE_DIR}/usr/lib"
mkdir -p "${APPIMAGE_DIR}/usr/share/applications"
mkdir -p "${APPIMAGE_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${APPIMAGE_DIR}/usr/share/controller-launch"

# Copy application files
echo "Copying application files..."
cp -r "${APP_DIR}/src/"* "${APPIMAGE_DIR}/usr/share/controller-launch/"
cp -r "${APP_DIR}/config" "${APPIMAGE_DIR}/usr/share/controller-launch/"
cp "${APP_DIR}/install/AppRun" "${APPIMAGE_DIR}/"
chmod +x "${APPIMAGE_DIR}/AppRun"
cp "${APP_DIR}/install/controller-launch.desktop" "${APPIMAGE_DIR}/usr/share/applications/"
cp "${APP_DIR}/install/controller-launch.desktop" "${APPIMAGE_DIR}/"

# Copy manually converted PNG icon
ICON_PATH="${APP_DIR}/assets/icons/controller-launch.png"
if [ -f "$ICON_PATH" ]; then
    echo "Copying icon from $ICON_PATH"
    cp "$ICON_PATH" "${APPIMAGE_DIR}/usr/share/icons/hicolor/256x256/apps/"
    cp "$ICON_PATH" "${APPIMAGE_DIR}/"
else
    echo "Warning: PNG icon not found at ${ICON_PATH}"
fi

# Install Python dependencies into AppDir
echo "Installing Python dependencies..."
python3 -m pip install --ignore-installed --prefix="${APPIMAGE_DIR}/usr" --no-warn-script-location -r "${APP_DIR}/requirements.txt"

# Check for runtime dependencies
echo "Checking runtime dependencies..."
MISSING_DEPS=0

if command -v apt-get &> /dev/null; then
    echo "Detected Debian-based system"
    TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0"
    PACKAGES="python3-gi python3-gi-cairo gir1.2-gtk-3.0 libcairo2-dev pkg-config python3-dev"
    for pkg in $PACKAGES; do
        if ! dpkg -l | grep -q "$pkg"; then
            echo "Missing package: $pkg"
            MISSING_DEPS=$((MISSING_DEPS + 1))
        fi
    done
elif command -v pacman &> /dev/null; then
    echo "Detected Arch-based system"
    TYPELIB_PATH="/usr/lib/girepository-1.0"
    PACKAGES="python-gobject python-cairo gtk3"
    for pkg in $PACKAGES; do
        if ! pacman -Q "$pkg" &> /dev/null; then
            echo "Missing package: $pkg"
            MISSING_DEPS=$((MISSING_DEPS + 1))
        fi
    done
else
    echo "Warning: Unsupported distribution. Build may fail."
    for path in "/usr/lib/girepository-1.0" "/usr/lib/x86_64-linux-gnu/girepository-1.0" "/usr/lib64/girepository-1.0"; do
        if [ -d "$path" ]; then
            TYPELIB_PATH="$path"
            break
        fi
    done
fi

if [ $MISSING_DEPS -gt 0 ]; then
    echo "Warning: Missing dependencies detected."
    echo "You can install them with: sudo apt-get install $PACKAGES"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Build aborted."
        exit 1
    fi
fi

# Copy .typelib files
echo "Copying system libraries and GObject introspection files..."
mkdir -p "${APPIMAGE_DIR}/usr/lib/girepository-1.0"
copy_typelib() {
    local name=$1
    for path in "$TYPELIB_PATH" /usr/lib/girepository-1.0 /usr/lib64/girepository-1.0; do
        if [ -f "${path}/${name}.typelib" ]; then
            cp "${path}/${name}.typelib" "${APPIMAGE_DIR}/usr/lib/girepository-1.0/"
            echo "Found and copied: ${name}.typelib"
            return
        fi
    done
    echo "Warning: Could not find ${name}.typelib"
}
for typelib in Gtk-3.0 GLib-2.0 Gdk-3.0 GdkPixbuf-2.0 Pango-1.0 cairo-1.0; do
    copy_typelib $typelib
done

# Create AppImage using linuxdeploy
echo "Creating AppImage..."
cd "${BUILD_DIR}"
if [ ! -f linuxdeploy-x86_64.AppImage ]; then
    wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
    chmod +x linuxdeploy-x86_64.AppImage
fi

./linuxdeploy-x86_64.AppImage --appdir="${APPIMAGE_DIR}" --output appimage

# Move result to project root
mv "${APP_NAME}"*.AppImage "${APP_DIR}/"
echo "Build complete! AppImage created at: ${APP_DIR}/${APP_NAME}"*.AppImage
