#!/usr/bin/env python3
# ControllerLaunch - Overlay UI Window

import os
import gi
import logging
import threading
import time
from datetime import datetime

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango
import cairo

import pygame

logger = logging.getLogger('controller-launch.ui')

class OverlayWindow(Gtk.Window):
    """Main overlay window for game selection."""
    
    # Constants
    GRID_COLUMNS = 3  # Number of columns in game grid
    GRID_ROWS = 3     # Number of rows in game grid (plus one for header)
    CELL_WIDTH = 180  # Width of each grid cell
    CELL_HEIGHT = 180  # Height of each grid cell
    SELECTION_BORDER_WIDTH = 4  # Width of selection border
    
    def __init__(self, game_library, config_manager):
        """Initialize the overlay window.
        
        Args:
            game_library: GameLibrary instance
            config_manager: ConfigManager instance
        """
        super().__init__(title="ControllerLaunch")
        self.game_library = game_library
        self.config = config_manager
        self.controller_monitor_thread = None
        self.running = False
        self.game_grid_items = []
        self.current_selection = (0, 0)  # (row, column)
        self.current_page = 0
        
        # Initialize controller handling
        self._init_pygame()
        
        # Set up window properties
        self._setup_window()
        
        # Create UI elements
        self._create_ui()
        
        # Load games
        self._load_games()
        
        # Start controller monitoring
        self._start_controller_monitor()
    
    def _init_pygame(self):
        """Initialize pygame for controller input."""
        # Initialize pygame if not already done
        if not pygame.get_init():
            pygame.init()
        if not pygame.joystick.get_init():
            pygame.joystick.init()
        
        # Initialize all connected controllers
        self.controllers = []
        joystick_count = pygame.joystick.get_count()
        for i in range(joystick_count):
            try:
                joystick = pygame.joystick.Joystick(i)
                joystick.init()
                self.controllers.append(joystick)
                logger.info(f"Initialized controller: {joystick.get_name()}")
            except Exception as e:
                logger.error(f"Failed to initialize joystick {i}: {str(e)}")
    
    def _setup_window(self):
        """Set up window properties."""
        # Get screen dimensions
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geometry = monitor.get_geometry()
        scale_factor = monitor.get_scale_factor()
        width = geometry.width // scale_factor
        height = geometry.height // scale_factor
        
        # Calculate window size (75% of screen)
        window_width = int(width * 0.75)
        window_height = int(height * 0.75)
        
        # Set window properties
        self.set_default_size(window_width, window_height)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_keep_above(True)  # Always on top
        self.set_decorated(False)  # No window decorations
        self.set_app_paintable(True)  # Required for transparency
        
        # Set up transparency
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
        
        # Connect signals
        self.connect("delete-event", self.on_delete_event)
        self.connect("key-press-event", self.on_key_press)
        self.connect("draw", self.on_draw)
        
        # Set opacity
        opacity = self.config.get("ui", "opacity", 0.9)
        self.set_opacity(opacity)
    
    def _create_ui(self):
        """Create the UI elements."""
        # Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(self.main_box)
        
        # Header area
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.header_box.set_margin_top(20)
        self.header_box.set_margin_start(20)
        self.header_box.set_margin_end(20)
        self.header_box.set_margin_bottom(10)
        
        # Title
        self.title_label = Gtk.Label(label="Controller Launch")
        self.title_label.set_halign(Gtk.Align.START)
        self.title_label.set_valign(Gtk.Align.CENTER)
        self.title_label.set_markup("<span font='20' weight='bold'>Controller Launch</span>")
        self.header_box.pack_start(self.title_label, True, True, 0)
        
        # Controller status
        self.controller_status = Gtk.Label(label="No controllers")
        self.controller_status.set_halign(Gtk.Align.END)
        self.controller_status.set_valign(Gtk.Align.CENTER)
        self.header_box.pack_end(self.controller_status, False, False, 0)
        
        self.main_box.pack_start(self.header_box, False, False, 0)
        
        # Games grid
        self.grid_scroll = Gtk.ScrolledWindow()
        self.grid_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.game_grid = Gtk.Grid()
        self.game_grid.set_row_spacing(10)
        self.game_grid.set_column_spacing(10)
        self.game_grid.set_margin_start(20)
        self.game_grid.set_margin_end(20)
        self.game_grid.set_margin_top(10)
        self.game_grid.set_margin_bottom(20)
        
        self.grid_scroll.add(self.game_grid)
        self.main_box.pack_start(self.grid_scroll, True, True, 0)
        
        # Footer with navigation help
        self.footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.footer_box.set_margin_start(20)
        self.footer_box.set_margin_end(20)
        self.footer_box.set_margin_top(10)
        self.footer_box.set_margin_bottom(20)
        
        self.help_label = Gtk.Label()
        self.help_label.set_markup("<span font='12'>D-Pad: Navigate | A/X: Launch | B/Circle: Exit</span>")
        self.footer_box.pack_start(self.help_label, True, False, 0)
        
        self.main_box.pack_start(self.footer_box, False, False, 0)
    
    def _load_games(self):
        """Load games into the grid."""
        # Clear existing grid
        for child in self.game_grid.get_children():
            self.game_grid.remove(child)
        
        self.game_grid_items = []
        
        # Get games from library
        games = self.game_library.get_recent_games(
            max_count=self.config.get("games", "max_games_shown", 10)
        )
        
        # Set up grid items
        row, col = 0, 0
        for i, game in enumerate(games):
            # Create game item frame (with border for selection highlighting)
            frame = Gtk.Frame()
            frame.set_shadow_type(Gtk.ShadowType.NONE)
            
            # Container for game info
            game_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            game_box.set_margin_top(10)
            game_box.set_margin_bottom(10)
            game_box.set_margin_start(10)
            game_box.set_margin_end(10)
            
            # Game icon/image
            icon_box = Gtk.Box()
            icon_box.set_size_request(self.CELL_WIDTH - 40, self.CELL_HEIGHT - 80)
            
            if game.get('icon') and os.path.isfile(game['icon']):
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        game['icon'], 
                        self.CELL_WIDTH - 60, 
                        self.CELL_HEIGHT - 100, 
                        True
                    )
                    image = Gtk.Image.new_from_pixbuf(pixbuf)
                    icon_box.pack_start(image, True, True, 0)
                except Exception as e:
                    logger.error(f"Error loading game icon: {e}")
                    # Fallback to text label
                    label = Gtk.Label(label=game['name'][0].upper())
                    label.set_markup(f"<span font='32' weight='bold'>{game['name'][0].upper()}</span>")
                    icon_box.pack_start(label, True, True, 0)
            else:
                # Use first letter as icon
                label = Gtk.Label(label=game['name'][0].upper())
                label.set_markup(f"<span font='32' weight='bold'>{game['name'][0].upper()}</span>")
                icon_box.pack_start(label, True, True, 0)
            
            game_box.pack_start(icon_box, True, True, 0)
            
            # Game name
            name_label = Gtk.Label(label=game['name'])
            name_label.set_max_width_chars(20)
            name_label.set_line_wrap(True)
            name_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            name_label.set_ellipsize(Pango.EllipsizeMode.END)
            name_label.set_lines(2)
            game_box.pack_start(name_label, False, False, 0)
            
            # Source label (Steam, Flatpak, etc)
            source_label = Gtk.Label()
            source_label.set_markup(f"<span font='10'>{game.get('source', 'Unknown')}</span>")
            game_box.pack_start(source_label, False, False, 0)
            
            frame.add(game_box)
            
            # Store for later access
            self.game_grid_items.append({
                'frame': frame,
                'game_id': game.get('id', str(i)),
                'game_data': game
            })
            
            # Add to grid
            self.game_grid.attach(frame, col, row, 1, 1)
            
            # Next position
            col += 1
            if col >= self.GRID_COLUMNS:
                col = 0
                row += 1
        
        # Show everything
        self.game_grid.show_all()
        
        # Set initial selection
        if self.game_grid_items:
            self._set_selection(0, 0)
        
        # Update controller status
        self._update_controller_status()
    
    def _set_selection(self, row, col):
        """Set the current selection in the grid.
        
        Args:
            row: Row index
            col: Column index
        """
        # Validate selection
        max_row = (len(self.game_grid_items) - 1) // self.GRID_COLUMNS
        max_col = min(self.GRID_COLUMNS - 1, len(self.game_grid_items) - 1 - row * self.GRID_COLUMNS)
        
        if row < 0:
            row = max_row
        elif row > max_row:
            row = 0
            
        if col < 0:
            col = max_col
        elif col > max_col:
            col = 0
        
        # Calculate index
        index = row * self.GRID_COLUMNS + col
        if index >= len(self.game_grid_items):
            # Adjust if out of bounds
            row = 0
            col = 0
            index = 0
        
        # Clear previous selection
        prev_row, prev_col = self.current_selection
        prev_index = prev_row * self.GRID_COLUMNS + prev_col
        if 0 <= prev_index < len(self.game_grid_items):
            prev_frame = self.game_grid_items[prev_index]['frame']
            prev_frame.set_shadow_type(Gtk.ShadowType.NONE)
        
        # Set new selection
        if index < len(self.game_grid_items):
            self.current_selection = (row, col)
            frame = self.game_grid_items[index]['frame']
            frame.set_shadow_type(Gtk.ShadowType.OUT)
            
            # Scroll to ensure visibility
            child = frame.get_child()
            adjustment = self.grid_scroll.get_vadjustment()
            if adjustment:
                alloc = child.get_allocation()
                adjustment.set_value(alloc.y - 10)
    
    def _move_selection(self, direction):
        """Move the selection in the specified direction.
        
        Args:
            direction: One of 'up', 'down', 'left', 'right'
        """
        row, col = self.current_selection
        
        if direction == 'up':
            self._set_selection(row - 1, col)
        elif direction == 'down':
            self._set_selection(row + 1, col)
        elif direction == 'left':
            self._set_selection(row, col - 1)
        elif direction == 'right':
            self._set_selection(row, col + 1)
    
    def _select_current(self):
        """Launch the currently selected game."""
        row, col = self.current_selection
        index = row * self.GRID_COLUMNS + col
        
        if 0 <= index < len(self.game_grid_items):
            game_data = self.game_grid_items[index]['game_data']
            game_id = self.game_grid_items[index]['game_id']
            
            logger.info(f"Launching game: {game_data['name']}")
            success = self.game_library.launch_game(game_id, game_data)
            
            if success:
                # Hide the overlay
                self.hide()
            else:
                # Show error dialog
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text=f"Failed to launch {game_data['name']}"
                )
                dialog.format_secondary_text(
                    "The game executable could not be launched. Would you like to remove it from the list?"
                )
                
                # Add controller navigation to dialog
                dialog.connect("key-press-event", self._on_dialog_key_press)
                
                # Add Yes/No buttons
                dialog.add_button("Remove", Gtk.ResponseType.YES)
                dialog.add_button("Keep", Gtk.ResponseType.NO)
                
                # Set default to No
                dialog.set_default_response(Gtk.ResponseType.NO)
                
                response = dialog.run()
                if response == Gtk.ResponseType.YES:
                    # Remove game from library
                    self.game_library.remove_game(game_id)
                    # Reload games
                    self._load_games()
                
                dialog.destroy()
    
    def _on_dialog_key_press(self, widget, event):
        """Handle key press events in dialogs for controller navigation."""
        keyval = event.keyval
        
        if keyval in [Gtk.gdk.KEY_Return, Gtk.gdk.KEY_a, Gtk.gdk.KEY_x]:
            # A/X button - Activate default
            widget.response(widget.get_default_response())
            return True
        elif keyval in [Gtk.gdk.KEY_Escape, Gtk.gdk.KEY_b, Gtk.gdk.KEY_o]:
            # B/Circle button - Cancel
            widget.response(Gtk.ResponseType.CANCEL)
            return True
            
        return False
    
    def _update_controller_status(self):
        """Update the controller status label."""
        pygame.joystick.init()  # Make sure it's initialized
        joystick_count = pygame.joystick.get_count()
        
        if joystick_count == 0:
            self.controller_status.set_markup("<span foreground='red'>No controllers</span>")
        else:
            controller_names = []
            for i in range(joystick_count):
                try:
                    joystick = pygame.joystick.Joystick(i)
                    if not joystick.get_init():
                        joystick.init()
                    controller_names.append(joystick.get_name())
                except Exception:
                    controller_names.append(f"Controller {i+1}")
            
            self.controller_status.set_markup(
                f"<span foreground='green'>{joystick_count} Controller{'s' if joystick_count > 1 else ''}</span>"
            )
    
    def _start_controller_monitor(self):
        """Start the controller input monitoring thread."""
        if self.controller_monitor_thread is not None:
            return
            
        self.running = True
        self.controller_monitor_thread = threading.Thread(
            target=self._monitor_controller_input, 
            daemon=True
        )
        self.controller_monitor_thread.start()
    
    def _stop_controller_monitor(self):
        """Stop the controller input monitoring thread."""
        self.running = False
        if self.controller_monitor_thread:
            self.controller_monitor_thread.join(timeout=1.0)
            self.controller_monitor_thread = None
    
    def _monitor_controller_input(self):
        """Monitor controller input in a separate thread."""
        while self.running:
            try:
                # Process pygame events
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        # Handle button press
                        self._handle_controller_button(event.button)
                    elif event.type == pygame.JOYHATMOTION:
                        # Handle D-pad
                        x, y = event.value
                        if x > 0:
                            GLib.idle_add(self._move_selection, 'right')
                        elif x < 0:
                            GLib.idle_add(self._move_selection, 'left')
                        if y > 0:
                            GLib.idle_add(self._move_selection, 'up')
                        elif y < 0:
                            GLib.idle_add(self._move_selection, 'down')
                    elif event.type == pygame.JOYAXISMOTION:
                        # Handle analog stick
                        if event.axis in [0, 2]:  # X-axis
                            if event.value > 0.5:
                                GLib.idle_add(self._move_selection, 'right')
                            elif event.value < -0.5:
                                GLib.idle_add(self._move_selection, 'left')
                        elif event.type in [1, 3]:  # Y-axis
                            if event.value > 0.5:
                                GLib.idle_add(self._move_selection, 'down')
                            elif event.value < -0.5:
                                GLib.idle_add(self._move_selection, 'up')
                    elif event.type == pygame.JOYDEVICEADDED:
                        # Controller connected
                        GLib.idle_add(self._update_controller_status)
                    elif event.type == pygame.JOYDEVICEREMOVED:
                        # Controller disconnected
                        GLib.idle_add(self._update_controller_status)
            except Exception as e:
                logger.error(f"Error in controller monitor: {str(e)}")
                
            # Sleep briefly to avoid high CPU usage
            time.sleep(0.05)
    
    def _handle_controller_button(self, button):
        """Handle controller button press.
        
        Args:
            button: Button index
        """
        # Common button mappings
        # Note: These may vary by controller type
        if button in [0, 1]:  # A/X button (confirm)
            GLib.idle_add(self._select_current)
        elif button in [1, 2]:  # B/Circle button (back/cancel)
            GLib.idle_add(self.hide)
        elif button in [4, 6]:  # LB/L1 button
            pass  # TODO: Previous page
        elif button in [5, 7]:  # RB/R1 button
            pass  # TODO: Next page
    
    def on_draw(self, widget, cr):
        """Draw the window background with semi-transparency."""
        cr.set_source_rgba(0.1, 0.1, 0.1, self.config.get("ui", "opacity", 0.9))
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        return False
    
    def on_key_press(self, widget, event):
        """Handle keyboard navigation."""
        keyval = event.keyval
        
        if keyval == Gdk.KEY_Escape:
            self.hide()
            return True
        elif keyval == Gdk.KEY_Return:
            self._select_current()
            return True
        elif keyval == Gdk.KEY_Up:
            self._move_selection('up')
            return True
        elif keyval == Gdk.KEY_Down:
            self._move_selection('down')
            return True
        elif keyval == Gdk.KEY_Left:
            self._move_selection('left')
            return True
        elif keyval == Gdk.KEY_Right:
            self._move_selection('right')
            return True
        
        return False
    
    def on_delete_event(self, widget, event):
        """Handle window close."""
        self._stop_controller_monitor()
        return False
    
    def do_hide(self):
        """Override the hide method to stop controller monitor."""
        self._stop_controller_monitor()
        Gtk.Window.do_hide(self)
    
    def do_show(self):
        """Override the show method to restart controller monitor."""
        self._init_pygame()  # Re-init pygame
        self._update_controller_status()
        self._load_games()  # Reload games in case library has changed
        self._start_controller_monitor()
        Gtk.Window.do_show(self)

# For direct testing
if __name__ == "__main__":
    import sys
    from config_manager import ConfigManager
    
    class DummyGameLibrary:
        def get_recent_games(self, max_count=10):
            return [
                {
                    'id': '1',
                    'name': 'Test Game 1',
                    'source': 'Steam',
                    'executable': '/usr/bin/test1',
                    'icon': None,
                },
                {
                    'id': '2',
                    'name': 'Test Game 2',
                    'source': 'Flatpak',
                    'executable': '/usr/bin/test2',
                    'icon': None,
                }
            ]
            
        def launch_game(self, game_id, game_data):
            print(f"Launching game: {game_data['name']}")
            return True
            
        def remove_game(self, game_id):
            print(f"Removing game: {game_id}")
            return True
    
    logging.basicConfig(level=logging.INFO)
    
    # Create dummy config and library
    config = ConfigManager()
    library = DummyGameLibrary()
    
    # Create and show window
    win = OverlayWindow(library, config)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    
    Gtk.main()
