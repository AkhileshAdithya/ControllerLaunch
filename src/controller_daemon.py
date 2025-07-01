#!/usr/bin/env python3
# ControllerLaunch - Controller Daemon using Pygame

import os
import sys
import time
import logging
import threading
import subprocess
from pathlib import Path

# Pygame for controller input
import pygame

logger = logging.getLogger('controller-launch.daemon')

class ControllerDaemon:
    """Background service for monitoring controller button presses using pygame."""
    
    # Define button constants
    # Note: These are common mappings but might need adjustment based on controller/platform
    XBOX_GUIDE_BUTTON = 8  # Xbox guide button (may vary by controller model)
    PS_BUTTON = 10         # PS button (may vary by controller model)
    
    def __init__(self, config_manager):
        """Initialize the controller daemon.
        
        Args:
            config_manager: ConfigManager instance
        """
        self.config = config_manager
        self.button_states = {}
        self.button_times = {}
        self.running = False
        self.thread = None
        self._pygame_initialized = False
        
        # Long press duration in seconds
        self.long_press_duration = self.config.get("controller", "long_press_duration", 1.0)
        
    def start(self):
        """Start the controller daemon."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_thread, daemon=True)
        self.thread.start()
        logger.info("Controller daemon started")
        
    def stop(self):
        """Stop the controller daemon."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        logger.info("Controller daemon stopped")
        
        # Quit pygame if initialized
        if self._pygame_initialized:
            pygame.quit()
            self._pygame_initialized = False
            
    def _monitor_thread(self):
        """Main monitoring thread."""
        # Initialize pygame
        if not self._pygame_initialized:
            try:
                pygame.init()
                pygame.joystick.init()
                self._pygame_initialized = True
                logger.info("Pygame initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize pygame: {str(e)}")
                return

        # Main monitoring loop
        while self.running:
            try:
                self._monitor_controllers()
                time.sleep(0.01)  # Short sleep to avoid high CPU usage
            except Exception as e:
                logger.error(f"Error in controller monitor: {str(e)}")
                time.sleep(1)  # Longer sleep on error
                
    def _monitor_controllers(self):
        """Monitor controllers using pygame."""
        # Check for connected controllers and initialize new ones
        joystick_count = pygame.joystick.get_count()
        for i in range(joystick_count):
            if not pygame.joystick.Joystick(i).get_init():
                try:
                    joystick = pygame.joystick.Joystick(i)
                    joystick.init()
                    logger.info(f"Initialized controller: {joystick.get_name()}")
                except Exception as e:
                    logger.error(f"Failed to initialize joystick {i}: {str(e)}")
                    
        # Process events
        for event in pygame.event.get():
            self._process_event(event)
                
    def _process_event(self, event):
        """Process a single pygame event."""
        try:
            if event.type == pygame.JOYBUTTONDOWN:
                # Store button press time
                device_id = f"pygame_{event.joy}"
                button = event.button
                self.button_states[device_id] = button
                self.button_times[device_id] = time.time()
                logger.debug(f"Button {button} pressed on controller {device_id}")
                
            elif event.type == pygame.JOYBUTTONUP:
                device_id = f"pygame_{event.joy}"
                button = event.button
                
                if device_id in self.button_states:
                    press_time = time.time() - self.button_times.get(device_id, 0)
                    
                    # Check for guide/PS button long press
                    # These button mappings may need to be adjusted based on controller model
                    if button in [self.XBOX_GUIDE_BUTTON, self.PS_BUTTON]:
                        if press_time >= self.long_press_duration:
                            logger.info(f"Guide button long press detected ({press_time:.2f}s)")
                            self._trigger_overlay()
                        else:
                            logger.debug(f"Guide button short press ignored ({press_time:.2f}s)")
                            
                    # Clean up
                    del self.button_states[device_id]
                    if device_id in self.button_times:
                        del self.button_times[device_id]
                        
            elif event.type == pygame.JOYDEVICEADDED:
                joystick_id = event.device_index
                try:
                    joystick = pygame.joystick.Joystick(joystick_id)
                    joystick.init()
                    logger.info(f"Controller connected: {joystick.get_name()}")
                except Exception as e:
                    logger.error(f"Error initializing new controller: {str(e)}")
                    
            elif event.type == pygame.JOYDEVICEREMOVED:
                joystick_id = event.instance_id
                logger.info(f"Controller disconnected: {joystick_id}")
                
        except Exception as e:
            logger.error(f"Error processing controller event: {str(e)}")
        
    def _trigger_overlay(self):
        """Trigger the overlay to appear."""
        logger.info("Launching overlay")
        try:
            # Get the path to the main script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            main_script = os.path.join(script_dir, "main.py")
            
            # Launch the application
            if os.path.exists(main_script):
                subprocess.Popen(["python3", main_script])
            else:
                # Try to launch by package name if installed
                subprocess.Popen(["controller-launch"])
        except Exception as e:
            logger.error(f"Error launching overlay: {str(e)}")
            
    @classmethod
    def install_systemd_service(cls):
        """Install systemd user service for autostart."""
        try:
            # Get the path to this script
            script_path = os.path.abspath(__file__)
            script_dir = os.path.dirname(script_path)
            main_script = os.path.join(script_dir, "main.py")
            
            # Create user service directory if it doesn't exist
            service_dir = os.path.expanduser("~/.config/systemd/user")
            os.makedirs(service_dir, exist_ok=True)
            
            # Create service file
            service_path = os.path.join(service_dir, "controller-launch.service")
            with open(service_path, 'w') as f:
                f.write(f"""[Unit]
Description=Controller Launch Daemon
After=graphical-session.target

[Service]
ExecStart=/usr/bin/python3 {main_script} --daemon
Restart=on-failure
Environment=DISPLAY=:0

[Install]
WantedBy=graphical-session.target
""")
            
            # Enable and start the service
            subprocess.run(["systemctl", "--user", "daemon-reload"])
            subprocess.run(["systemctl", "--user", "enable", "controller-launch.service"])
            subprocess.run(["systemctl", "--user", "start", "controller-launch.service"])
            
            return True, "Service installed and started successfully"
        except Exception as e:
            return False, f"Error installing service: {str(e)}"
            
    @classmethod
    def uninstall_systemd_service(cls):
        """Uninstall systemd user service."""
        try:
            # Stop and disable the service
            subprocess.run(["systemctl", "--user", "stop", "controller-launch.service"])
            subprocess.run(["systemctl", "--user", "disable", "controller-launch.service"])
            
            # Remove service file
            service_path = os.path.expanduser("~/.config/systemd/user/controller-launch.service")
            if os.path.exists(service_path):
                os.unlink(service_path)
                
            return True, "Service uninstalled successfully"
        except Exception as e:
            return False, f"Error uninstalling service: {str(e)}"
            
    @classmethod
    def detect_controllers(cls):
        """Detect and list connected controllers.
        
        Returns:
            List of controller names
        """
        controllers = []
        
        # Initialize pygame temporarily
        temp_init = False
        if not pygame.get_init():
            pygame.init()
            pygame.joystick.init()
            temp_init = True
            
        try:
            # Get list of controllers
            joystick_count = pygame.joystick.get_count()
            for i in range(joystick_count):
                try:
                    joystick = pygame.joystick.Joystick(i)
                    controllers.append({
                        'id': i,
                        'name': joystick.get_name(),
                        'buttons': joystick.get_numbuttons(),
                        'axes': joystick.get_numaxes()
                    })
                except Exception:
                    controllers.append({
                        'id': i,
                        'name': f"Unknown Controller {i}",
                        'buttons': 0,
                        'axes': 0
                    })
        finally:
            # Quit pygame if we initialized it
            if temp_init:
                pygame.quit()
                
        return controllers

# For direct testing
if __name__ == "__main__":
    import time
    
    logging.basicConfig(level=logging.INFO)
    
    # Create a simple config manager for testing
    class DummyConfig:
        def get(self, section, key, default=None):
            if section == "controller" and key == "long_press_duration":
                return 1.0
            return default
    
    # Create and start daemon
    daemon = ControllerDaemon(DummyConfig())
    daemon.start()
    
    print("Controller daemon started. Press Ctrl+C to exit.")
    print("Connected controllers:")
    for controller in ControllerDaemon.detect_controllers():
        print(f"  - {controller['name']} ({controller['buttons']} buttons, {controller['axes']} axes)")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        daemon.stop()
        print("Controller daemon stopped.")
