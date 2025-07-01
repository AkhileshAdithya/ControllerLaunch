#!/usr/bin/env python3
# ControllerLaunch - Preferences Window

import os
import gi
import logging
import subprocess

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango

from controller_daemon import ControllerDaemon

logger = logging.getLogger('controller-launch.preferences')

class PreferencesWindow(Gtk.Window):
    """Preferences window for ControllerLaunch."""
    
    def __init__(self, config_manager):
        """Initialize the preferences window.
        
        Args:
            config_manager: ConfigManager instance
        """
        super().__init__(title="ControllerLaunch Preferences")
        self.config = config_manager
        
        # Setup window
        self.set_default_size(700, 500)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(10)
        
        # Connect signals
        self.connect("delete-event", self.on_close)
        
        # Create UI
        self._create_ui()
        
        # Load initial values
        self._load_config()
    
    def _create_ui(self):
        """Create UI elements."""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)
        
        # Create notebook (tabbed interface)
        notebook = Gtk.Notebook()
        main_box.pack_start(notebook, True, True, 0)
        
        # General tab
        general_page = self._create_general_tab()
        notebook.append_page(general_page, Gtk.Label(label="General"))
        
        # Controller tab
        controller_page = self._create_controller_tab()
        notebook.append_page(controller_page, Gtk.Label(label="Controllers"))
        
        # Games tab
        games_page = self._create_games_tab()
        notebook.append_page(games_page, Gtk.Label(label="Games"))
        
        # About tab
        about_page = self._create_about_tab()
        notebook.append_page(about_page, Gtk.Label(label="About"))
        
        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)
        
        # Close button
        close_button = Gtk.Button.new_with_label("Close")
        close_button.connect("clicked", self.on_close)
        button_box.pack_end(close_button, False, False, 0)
        
        # Save button
        save_button = Gtk.Button.new_with_label("Apply")
        save_button.connect("clicked", self.on_save)
        button_box.pack_end(save_button, False, False, 0)
        
        main_box.pack_end(button_box, False, False, 0)
    
    def _create_general_tab(self):
        """Create general settings tab.
        
        Returns:
            Gtk.Widget for the tab content
        """
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_border_width(10)
        
        # Autostart setting
        frame = Gtk.Frame(label="Startup Options")
        frame.set_border_width(5)
        frame_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        frame_box.set_border_width(10)
        
        self.autostart_switch = Gtk.Switch()
        autostart_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        autostart_label = Gtk.Label(label="Start controller daemon on login")
        autostart_label.set_halign(Gtk.Align.START)
        autostart_box.pack_start(autostart_label, True, True, 0)
        autostart_box.pack_end(self.autostart_switch, False, False, 0)
        frame_box.pack_start(autostart_box, False, False, 0)
        
        # Minimize to tray option
        self.minimize_switch = Gtk.Switch()
        minimize_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        minimize_label = Gtk.Label(label="Minimize to system tray when closed")
        minimize_label.set_halign(Gtk.Align.START)
        minimize_box.pack_start(minimize_label, True, True, 0)
        minimize_box.pack_end(self.minimize_switch, False, False, 0)
        frame_box.pack_start(minimize_box, False, False, 0)
        
        frame.add(frame_box)
        page.pack_start(frame, False, False, 0)
        
        # UI Settings
        ui_frame = Gtk.Frame(label="UI Settings")
        ui_frame.set_border_width(5)
        ui_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        ui_box.set_border_width(10)
        
        # Opacity setting
        opacity_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        opacity_label = Gtk.Label(label="Window Opacity:")
        opacity_label.set_halign(Gtk.Align.START)
        self.opacity_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.1, 1.0, 0.05)
        self.opacity_scale.set_digits(2)
        self.opacity_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.opacity_scale.set_draw_value(True)
        self.opacity_scale.set_size_request(200, -1)
        opacity_box.pack_start(opacity_label, False, False, 0)
        opacity_box.pack_start(self.opacity_scale, True, True, 0)
        ui_box.pack_start(opacity_box, False, False, 0)
        
        # Show game art
        self.show_art_switch = Gtk.Switch()
        show_art_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        show_art_label = Gtk.Label(label="Show game artwork when available")
        show_art_label.set_halign(Gtk.Align.START)
        show_art_box.pack_start(show_art_label, True, True, 0)
        show_art_box.pack_end(self.show_art_switch, False, False, 0)
        ui_box.pack_start(show_art_box, False, False, 0)
        
        ui_frame.add(ui_box)
        page.pack_start(ui_frame, False, False, 0)
        
        # Status section
        status_frame = Gtk.Frame(label="Current Status")
        status_frame.set_border_width(5)
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        status_box.set_border_width(10)
        
        # Daemon status
        self.daemon_status_label = Gtk.Label(label="Daemon status: Unknown")
        self.daemon_status_label.set_halign(Gtk.Align.START)
        status_box.pack_start(self.daemon_status_label, False, False, 0)
        
        # Actions
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        # Start/Stop daemon button
        self.daemon_button = Gtk.Button.new_with_label("Start Daemon")
        self.daemon_button.connect("clicked", self.on_daemon_toggle)
        actions_box.pack_start(self.daemon_button, False, False, 0)
        
        # Install/Uninstall service button
        self.service_button = Gtk.Button.new_with_label("Install Service")
        self.service_button.connect("clicked", self.on_service_toggle)
        actions_box.pack_start(self.service_button, False, False, 0)
        
        status_box.pack_start(actions_box, False, False, 0)
        status_frame.add(status_box)
        page.pack_start(status_frame, False, False, 0)
        
        return page
    
    def _create_controller_tab(self):
        """Create controller settings tab.
        
        Returns:
            Gtk.Widget for the tab content
        """
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_border_width(10)
        
        # Controller detection
        detection_frame = Gtk.Frame(label="Controller Detection")
        detection_frame.set_border_width(5)
        detection_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        detection_box.set_border_width(10)
        
        # Controller long press duration
        duration_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        duration_label = Gtk.Label(label="Guide Button Long Press Duration:")
        duration_label.set_halign(Gtk.Align.START)
        self.duration_spin = Gtk.SpinButton.new_with_range(0.1, 5.0, 0.1)
        self.duration_spin.set_digits(1)
        duration_box.pack_start(duration_label, True, True, 0)
        duration_box.pack_end(self.duration_spin, False, False, 0)
        detection_box.pack_start(duration_box, False, False, 0)
        
        # Detect connected controllers button
        detect_button = Gtk.Button.new_with_label("Detect Connected Controllers")
        detect_button.connect("clicked", self.on_detect_controllers)
        detection_box.pack_start(detect_button, False, False, 0)
        
        # Connected controllers list
        list_label = Gtk.Label(label="Connected Controllers:")
        list_label.set_halign(Gtk.Align.START)
        detection_box.pack_start(list_label, False, False, 0)
        
        # Controllers list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 150)
        
        self.controller_store = Gtk.ListStore(str, str, int, int)  # id, name, buttons, axes
        controller_view = Gtk.TreeView(model=self.controller_store)
        
        # Columns
        name_column = Gtk.TreeViewColumn("Controller", Gtk.CellRendererText(), text=1)
        name_column.set_expand(True)
        controller_view.append_column(name_column)
        
        buttons_column = Gtk.TreeViewColumn("Buttons", Gtk.CellRendererText(), text=2)
        controller_view.append_column(buttons_column)
        
        axes_column = Gtk.TreeViewColumn("Axes", Gtk.CellRendererText(), text=3)
        controller_view.append_column(axes_column)
        
        scrolled.add(controller_view)
        detection_box.pack_start(scrolled, True, True, 0)
        
        detection_frame.add(detection_box)
        page.pack_start(detection_frame, True, True, 0)
        
        # Button mapping section
        mapping_frame = Gtk.Frame(label="Button Mapping")
        mapping_frame.set_border_width(5)
        mapping_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        mapping_box.set_border_width(10)
        
        mapping_label = Gtk.Label(
            label="Note: Controller button mapping varies by controller model. "
            "You may need to adjust these values for your specific controller."
        )
        mapping_label.set_line_wrap(True)
        mapping_box.pack_start(mapping_label, False, False, 0)
        
        # Xbox mapping
        xbox_label = Gtk.Label(label="Xbox Controller:")
        xbox_label.set_halign(Gtk.Align.START)
        mapping_box.pack_start(xbox_label, False, False, 0)
        
        xbox_grid = Gtk.Grid()
        xbox_grid.set_column_spacing(10)
        xbox_grid.set_row_spacing(5)
        
        # Xbox button rows
        self._create_button_mapping_row(xbox_grid, 0, "A (Select):", "xbox", "select")
        self._create_button_mapping_row(xbox_grid, 1, "B (Back):", "xbox", "back")
        self._create_button_mapping_row(xbox_grid, 2, "Guide Button:", "xbox", "guide")
        
        mapping_box.pack_start(xbox_grid, False, False, 10)
        
        # PS5 mapping
        ps_label = Gtk.Label(label="PlayStation Controller:")
        ps_label.set_halign(Gtk.Align.START)
        mapping_box.pack_start(ps_label, False, False, 0)
        
        ps_grid = Gtk.Grid()
        ps_grid.set_column_spacing(10)
        ps_grid.set_row_spacing(5)
        
        # PS button rows
        self._create_button_mapping_row(ps_grid, 0, "X (Select):", "playstation", "select")
        self._create_button_mapping_row(ps_grid, 1, "Circle (Back):", "playstation", "back")
        self._create_button_mapping_row(ps_grid, 2, "PS Button:", "playstation", "guide")
        
        mapping_box.pack_start(ps_grid, False, False, 10)
        
        # Button mapping instructions
        help_label = Gtk.Label()
        help_label.set_markup(
            "<small>To change button mappings, enter the button number shown when you press "
            "the button in the controller detection section.</small>"
        )
        help_label.set_line_wrap(True)
        mapping_box.pack_start(help_label, False, False, 0)
        
        mapping_frame.add(mapping_box)
        page.pack_start(mapping_frame, False, False, 0)
        
        return page
    
    def _create_button_mapping_row(self, grid, row, label_text, controller_type, button_name):
        """Create a row for button mapping configuration.
        
        Args:
            grid: Gtk.Grid to add the row to
            row: Row index
            label_text: Label text
            controller_type: Controller type (xbox, playstation)
            button_name: Button name in config
        """
        label = Gtk.Label(label=label_text)
        label.set_halign(Gtk.Align.START)
        
        spinner = Gtk.SpinButton.new_with_range(0, 30, 1)
        spinner.set_numeric(True)
        
        # Store reference to retrieve values later
        attr_name = f"{controller_type}_{button_name}_spin"
        setattr(self, attr_name, spinner)
        
        grid.attach(label, 0, row, 1, 1)
        grid.attach(spinner, 1, row, 1, 1)
    
    def _create_games_tab(self):
        """Create games settings tab.
        
        Returns:
            Gtk.Widget for the tab content
        """
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_border_width(10)
        
        # Game paths frame
        paths_frame = Gtk.Frame(label="Game Search Paths")
        paths_frame.set_border_width(5)
        paths_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        paths_box.set_border_width(10)
        
        # Steam paths
        steam_label = Gtk.Label(label="Steam Paths:")
        steam_label.set_halign(Gtk.Align.START)
        paths_box.pack_start(steam_label, False, False, 0)
        
        self.steam_paths_store = Gtk.ListStore(str)
        self.steam_paths_view = self._create_path_list_view(self.steam_paths_store)
        paths_box.pack_start(self.steam_paths_view, True, True, 0)
        
        steam_buttons = self._create_path_buttons(self.steam_paths_store)
        paths_box.pack_start(steam_buttons, False, False, 0)
        
        # Flatpak paths
        flatpak_label = Gtk.Label(label="Flatpak Paths:")
        flatpak_label.set_halign(Gtk.Align.START)
        paths_box.pack_start(flatpak_label, False, False, 10)
        
        self.flatpak_paths_store = Gtk.ListStore(str)
        self.flatpak_paths_view = self._create_path_list_view(self.flatpak_paths_store)
        paths_box.pack_start(self.flatpak_paths_view, True, True, 0)
        
        flatpak_buttons = self._create_path_buttons(self.flatpak_paths_store)
        paths_box.pack_start(flatpak_buttons, False, False, 0)
        
        # Lutris paths
        lutris_label = Gtk.Label(label="Lutris Paths:")
        lutris_label.set_halign(Gtk.Align.START)
        paths_box.pack_start(lutris_label, False, False, 10)
        
        self.lutris_paths_store = Gtk.ListStore(str)
        self.lutris_paths_view = self._create_path_list_view(self.lutris_paths_store)
        paths_box.pack_start(self.lutris_paths_view, True, True, 0)
        
        lutris_buttons = self._create_path_buttons(self.lutris_paths_store)
        paths_box.pack_start(lutris_buttons, False, False, 0)
        
        # Custom paths
        custom_label = Gtk.Label(label="Custom Game Paths:")
        custom_label.set_halign(Gtk.Align.START)
        paths_box.pack_start(custom_label, False, False, 10)
        
        self.custom_paths_store = Gtk.ListStore(str)
        self.custom_paths_view = self._create_path_list_view(self.custom_paths_store)
        paths_box.pack_start(self.custom_paths_view, True, True, 0)
        
        custom_buttons = self._create_path_buttons(self.custom_paths_store)
        paths_box.pack_start(custom_buttons, False, False, 0)
        
        paths_frame.add(paths_box)
        page.pack_start(paths_frame, True, True, 0)
        
        # Game display settings
        display_frame = Gtk.Frame(label="Game Display Settings")
        display_frame.set_border_width(5)
        display_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        display_box.set_border_width(10)
        
        # Max games shown
        max_games_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        max_games_label = Gtk.Label(label="Maximum games to display:")
        max_games_label.set_halign(Gtk.Align.START)
        self.max_games_spin = Gtk.SpinButton.new_with_range(5, 50, 5)
        self.max_games_spin.set_numeric(True)
        max_games_box.pack_start(max_games_label, True, True, 0)
        max_games_box.pack_end(self.max_games_spin, False, False, 0)
        display_box.pack_start(max_games_box, False, False, 0)
        
        # Clear recently launched
        clear_button = Gtk.Button.new_with_label("Clear Recently Launched Games")
        clear_button.connect("clicked", self.on_clear_recent)
        display_box.pack_start(clear_button, False, False, 10)
        
        display_frame.add(display_box)
        page.pack_start(display_frame, False, False, 0)
        
        return page
    
    def _create_path_list_view(self, store):
        """Create a list view for paths.
        
        Args:
            store: ListStore to use
            
        Returns:
            Gtk.ScrolledWindow containing the list view
        """
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 80)
        
        view = Gtk.TreeView(model=store)
        renderer = Gtk.CellRendererText()
        renderer.set_property("editable", True)
        renderer.connect("edited", self.on_path_edited, store)
        
        column = Gtk.TreeViewColumn("Path", renderer, text=0)
        column.set_expand(True)
        view.append_column(column)
        
        scrolled.add(view)
        return scrolled
    
    def _create_path_buttons(self, store):
        """Create buttons for managing paths.
        
        Args:
            store: ListStore to manage
            
        Returns:
            Gtk.Box containing the buttons
        """
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        add_button = Gtk.Button.new_with_label("Add")
        add_button.connect("clicked", self.on_add_path, store)
        box.pack_start(add_button, False, False, 0)
        
        remove_button = Gtk.Button.new_with_label("Remove")
        remove_button.connect("clicked", self.on_remove_path, store)
        box.pack_start(remove_button, False, False, 0)
        
        browse_button = Gtk.Button.new_with_label("Browse...")
        browse_button.connect("clicked", self.on_browse_path, store)
        box.pack_start(browse_button, False, False, 0)
        
        return box
    
    def _create_about_tab(self):
        """Create about tab.
        
        Returns:
            Gtk.Widget for the tab content
        """
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        page.set_border_width(30)
        
        # App name and version
        title_label = Gtk.Label()
        title_label.set_markup("<span font='20' weight='bold'>ControllerLaunch</span>")
        page.pack_start(title_label, False, False, 0)
        
        version_label = Gtk.Label(label="Version 1.0.0")
        page.pack_start(version_label, False, False, 0)
        
        # Description
        desc_label = Gtk.Label(
            label="A controller-friendly game launcher for Linux."
        )
        desc_label.set_justify(Gtk.Justification.CENTER)
        page.pack_start(desc_label, False, False, 10)
        
        # License
        license_label = Gtk.Label()
        license_label.set_markup(
            "<small>This software is licensed under the MIT License.\n"
            "Copyright © 2025</small>"
        )
        license_label.set_justify(Gtk.Justification.CENTER)
        page.pack_start(license_label, False, False, 20)
        
        return page
    
    def _load_config(self):
        """Load configuration into UI elements."""
        # General settings
        self.autostart_switch.set_active(self.config.get("general", "autostart", True))
        self.minimize_switch.set_active(self.config.get("general", "minimize_to_tray", True))
        
        # UI settings
        self.opacity_scale.set_value(self.config.get("ui", "opacity", 0.9))
        self.show_art_switch.set_active(self.config.get("ui", "show_game_art", True))
        
        # Controller settings
        self.duration_spin.set_value(self.config.get("controller", "long_press_duration", 1.0))
        
        # Load button mappings
        button_mapping = self.config.get("controller", "button_mapping", {})
        xbox_mapping = button_mapping.get("xbox", {})
        ps_mapping = button_mapping.get("playstation", {})
        
        # Set Xbox button mappings
        if hasattr(self, "xbox_select_spin"):
            self.xbox_select_spin.set_value(int(xbox_mapping.get("select", 0)))
        if hasattr(self, "xbox_back_spin"):
            self.xbox_back_spin.set_value(int(xbox_mapping.get("back", 1)))
        if hasattr(self, "xbox_guide_spin"):
            self.xbox_guide_spin.set_value(int(xbox_mapping.get("guide", 8)))
        
        # Set PlayStation button mappings
        if hasattr(self, "playstation_select_spin"):
            self.playstation_select_spin.set_value(int(ps_mapping.get("select", 0)))
        if hasattr(self, "playstation_back_spin"):
            self.playstation_back_spin.set_value(int(ps_mapping.get("back", 1)))
        if hasattr(self, "playstation_guide_spin"):
            self.playstation_guide_spin.set_value(int(ps_mapping.get("guide", 10)))
        
        # Load game paths
        game_paths = self.config.get("games", "paths", {})
        
        # Steam paths
        self.steam_paths_store.clear()
        for path in game_paths.get("steam", ["~/.steam", "~/.local/share/Steam"]):
            self.steam_paths_store.append([path])
        
        # Flatpak paths
        self.flatpak_paths_store.clear()
        for path in game_paths.get("flatpak", ["/var/lib/flatpak/app"]):
            self.flatpak_paths_store.append([path])
        
        # Lutris paths
        self.lutris_paths_store.clear()
        for path in game_paths.get("lutris", ["~/.local/share/lutris"]):
            self.lutris_paths_store.append([path])
        
        # Custom paths
        self.custom_paths_store.clear()
        for path in game_paths.get("custom", []):
            self.custom_paths_store.append([path])
        
        # Max games
        self.max_games_spin.set_value(self.config.get("games", "max_games_shown", 10))
        
        # Update controller list
        self._update_controller_list()
        
        # Update daemon status
        self._update_daemon_status()
    
    def _update_controller_list(self):
        """Update the list of connected controllers."""
        self.controller_store.clear()
        
        controllers = ControllerDaemon.detect_controllers()
        for controller in controllers:
            self.controller_store.append([
                str(controller['id']),
                controller['name'],
                controller['buttons'],
                controller['axes']
            ])
    
    def _update_daemon_status(self):
        """Update the daemon status display."""
        try:
            # Check if daemon is running
            result = subprocess.run(
                ["systemctl", "--user", "is-active", "controller-launch.service"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.stdout.strip() == "active":
                self.daemon_status_label.set_markup("<b>Daemon status:</b> Running")
                self.daemon_button.set_label("Stop Daemon")
                self.service_button.set_label("Uninstall Service")
            else:
                self.daemon_status_label.set_markup("<b>Daemon status:</b> Stopped")
                self.daemon_button.set_label("Start Daemon")
                self.service_button.set_label("Install Service")
        except Exception:
            self.daemon_status_label.set_markup("<b>Daemon status:</b> Unknown")
    
    def _save_config(self):
        """Save configuration from UI elements."""
        # General settings
        self.config.set("general", "autostart", self.autostart_switch.get_active())
        self.config.set("general", "minimize_to_tray", self.minimize_switch.get_active())
        
        # UI settings
        self.config.set("ui", "opacity", self.opacity_scale.get_value())
        self.config.set("ui", "show_game_art", self.show_art_switch.get_active())
        
        # Controller settings
        self.config.set("controller", "long_press_duration", self.duration_spin.get_value())
        
        # Button mappings
        button_mapping = self.config.get("controller", "button_mapping", {})
        
        # Xbox mappings
        xbox_mapping = {}
        if hasattr(self, "xbox_select_spin"):
            xbox_mapping["select"] = int(self.xbox_select_spin.get_value())
        if hasattr(self, "xbox_back_spin"):
            xbox_mapping["back"] = int(self.xbox_back_spin.get_value())
        if hasattr(self, "xbox_guide_spin"):
            xbox_mapping["guide"] = int(self.xbox_guide_spin.get_value())
        
        button_mapping["xbox"] = xbox_mapping
        
        # PlayStation mappings
        ps_mapping = {}
        if hasattr(self, "playstation_select_spin"):
            ps_mapping["select"] = int(self.playstation_select_spin.get_value())
        if hasattr(self, "playstation_back_spin"):
            ps_mapping["back"] = int(self.playstation_back_spin.get_value())
        if hasattr(self, "playstation_guide_spin"):
            ps_mapping["guide"] = int(self.playstation_guide_spin.get_value())
        
        button_mapping["playstation"] = ps_mapping
        
        self.config.set("controller", "button_mapping", button_mapping)
        
        # Game paths
        game_paths = {}
        
        # Steam paths
        steam_paths = []
        for row in self.steam_paths_store:
            steam_paths.append(row[0])
        game_paths["steam"] = steam_paths
        
        # Flatpak paths
        flatpak_paths = []
        for row in self.flatpak_paths_store:
            flatpak_paths.append(row[0])
        game_paths["flatpak"] = flatpak_paths
        
        # Lutris paths
        lutris_paths = []
        for row in self.lutris_paths_store:
            lutris_paths.append(row[0])
        game_paths["lutris"] = lutris_paths
        
        # Custom paths
        custom_paths = []
        for row in self.custom_paths_store:
            custom_paths.append(row[0])
        game_paths["custom"] = custom_paths
        
        self.config.set("games", "paths", game_paths)
        
        # Max games
        self.config.set("games", "max_games_shown", self.max_games_spin.get_value_as_int())
    
    def on_save(self, widget):
        """Handle save button click."""
        self._save_config()
        self._update_daemon_status()
    
    def on_close(self, widget, event=None):
        """Handle close button click."""
        self.destroy()
        return False
    
    def on_daemon_toggle(self, widget):
        """Handle daemon toggle button click."""
        try:
            if self.daemon_button.get_label() == "Start Daemon":
                # Start daemon
                subprocess.run(["systemctl", "--user", "start", "controller-launch.service"])
            else:
                # Stop daemon
                subprocess.run(["systemctl", "--user", "stop", "controller-launch.service"])
            
            # Update status
            self._update_daemon_status()
        except Exception as e:
            logger.error(f"Error toggling daemon: {str(e)}")
            self._show_error_dialog("Error", f"Failed to toggle daemon: {str(e)}")
    
    def on_service_toggle(self, widget):
        """Handle service installation toggle button click."""
        try:
            if self.service_button.get_label() == "Install Service":
                # Install service
                success, message = ControllerDaemon.install_systemd_service()
            else:
                # Uninstall service
                success, message = ControllerDaemon.uninstall_systemd_service()
            
            if success:
                # Update status
                self._update_daemon_status()
            else:
                self._show_error_dialog("Error", message)
        except Exception as e:
            logger.error(f"Error toggling service: {str(e)}")
            self._show_error_dialog("Error", f"Failed to toggle service: {str(e)}")
    
    def on_detect_controllers(self, widget):
        """Handle detect controllers button click."""
        self._update_controller_list()
    
    def on_path_edited(self, renderer, path, new_text, store):
        """Handle path editing.
        
        Args:
            renderer: CellRenderer that was edited
            path: Path to the edited item
            new_text: New text value
            store: ListStore being edited
        """
        store[path][0] = new_text
    
    def on_add_path(self, widget, store):
        """Handle add path button click.
        
        Args:
            widget: Button that was clicked
            store: ListStore to add to
        """
        store.append(["~/new/path"])
    
    def on_remove_path(self, widget, store):
        """Handle remove path button click.
        
        Args:
            widget: Button that was clicked
            store: ListStore to remove from
        """
        # Get the selection
        treeview = widget.get_parent().get_parent().get_children()[0].get_child()
        selection = treeview.get_selection()
        model, treeiter = selection.get_selected()
        
        if treeiter is not None:
            store.remove(treeiter)
    
    def on_browse_path(self, widget, store):
        """Handle browse path button click.
        
        Args:
            widget: Button that was clicked
            store: ListStore to update
        """
        dialog = Gtk.FileChooserDialog(
            title="Select Folder",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, 
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            folder_path = dialog.get_filename()
            # Get the selection
            treeview = widget.get_parent().get_parent().get_children()[0].get_child()
            selection = treeview.get_selection()
            model, treeiter = selection.get_selected()
            
            if treeiter is not None:
                store[treeiter][0] = folder_path
            else:
                store.append([folder_path])
        
        dialog.destroy()
    
    def on_clear_recent(self, widget):
        """Handle clear recent games button click."""
        self.config.set("games", "recently_launched", [])
    
    def _show_error_dialog(self, title, message):
        """Show error dialog.
        
        Args:
            title: Dialog title
            message: Error message
        """
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

# For direct testing
if __name__ == "__main__":
    import sys
    from config_manager import ConfigManager
    
    logging.basicConfig(level=logging.INFO)
    
    # Create config
    config = ConfigManager()
    
    # Create and show window
    win = PreferencesWindow(config)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    
    Gtk.main()
