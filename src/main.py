#!/usr/bin/env python3
# ControllerLaunch - GTK3 Game Launcher for Controller Navigation
# Main application entry point

import os
import gi
import sys
import logging

# Set up GTK3
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

# Local imports
from overlay_ui import OverlayWindow
from game_library import GameLibrary
from preferences_ui import PreferencesWindow
from config_manager import ConfigManager
from controller_daemon import ControllerDaemon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser('~/.config/controller-launch/app.log'))
    ]
)
logger = logging.getLogger('controller-launch')

class ControllerLaunch:
    """Main application class for ControllerLaunch."""
    
    def __init__(self):
        """Initialize the application."""
        logger.info("Initializing ControllerLaunch")
        
        # Ensure config directory exists
        config_dir = os.path.expanduser('~/.config/controller-launch')
        os.makedirs(config_dir, exist_ok=True)
        
        # Initialize components
        self.config = ConfigManager()
        self.game_library = GameLibrary(self.config)
        self.overlay = OverlayWindow(self.game_library, self.config)
        self.preferences = None  # Created on demand
        
        # Set up application actions
        self.setup_actions()
    
    def setup_actions(self):
        """Set up application keyboard shortcuts and actions."""
        self.overlay.connect('key-press-event', self.on_key_press)
        
    def on_key_press(self, widget, event):
        """Handle key press events."""
        # Ctrl+, to open preferences
        if event.state & Gdk.ModifierType.CONTROL_MASK and event.keyval == Gdk.KEY_comma:
            self.open_preferences()
            return True
        return False
    
    def open_preferences(self):
        """Open the preferences window."""
        if not self.preferences:
            self.preferences = PreferencesWindow(self.config)
        self.preferences.present()
    
    def run(self):
        """Run the application."""
        logger.info("Starting ControllerLaunch")
        self.overlay.show_all()
        Gtk.main()

def main():
    """Application entry point."""
    # Create and run the application
    app = ControllerLaunch()
    app.run()

if __name__ == "__main__":
    main()
