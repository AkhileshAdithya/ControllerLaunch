# ControllerLaunch

A GTK3 game launcher for Linux that can be navigated using Xbox or PS5 controllers (xinput).

## Features

- Launch the GUI using PS/Xbox guide button (long press)
- Navigate game library using controller D-pad or analog stick
- Support for Steam, Flatpak, and Lutris games
- Controller-friendly interface optimized for TV/couch gaming
- Background service for controller button monitoring
- Custom game path support
- Recently launched games tracking

## Requirements

- Python 3.6+
- GTK3
- PyGObject
- Pygame (for controller input)
- Linux distribution (tested on Linux Mint, Ubuntu, Debian, Arch)

## Installation

### AppImage (Recommended)

The easiest way to install ControllerLaunch is using the AppImage:

1. Download the latest `ControllerLaunch-x86_64.AppImage` from the releases page
2. Make it executable: `chmod +x ControllerLaunch-x86_64.AppImage`
3. Run it: `./ControllerLaunch-x86_64.AppImage`

### Building from Source

If you prefer to build from source:

1. Install dependencies:
   ```
   # For Debian/Ubuntu/Linux Mint
   sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-pip
   
   # For Arch Linux
   sudo pacman -S python-gobject python-cairo gtk3
   ```

2. Install Python dependencies:
   ```
   pip3 install -r requirements.txt
   ```

3. Build the AppImage:
   ```
   ./packaging/build_appimage.sh
   ```

## Usage

### First Run

On first run, the application will:
1. Scan for installed games from Steam, Flatpak, and Lutris
2. Set up the controller daemon for background monitoring
3. Create a configuration file in `~/.config/controller-launch/`

### Controller Navigation

- **Guide Button** (Long Press): Show/hide the launcher
- **D-Pad / Left Stick**: Navigate game grid
- **A / X Button**: Launch selected game
- **B / O Button**: Exit launcher
- **LB/RB Buttons**: Navigate between pages

### Preferences

Open preferences with Ctrl+, or via the menu. Here you can:
- Configure controller button mappings
- Add custom game paths
- Set autostart options
- Adjust UI settings

## Development

The project structure is organized as follows:

```
ControllerLaunch/
├── src/              # Source code
├── assets/           # Images, icons, etc.
├── config/           # Configuration files
├── install/          # Installation files
├── packaging/        # Packaging scripts
└── requirements.txt  # Python dependencies
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.
