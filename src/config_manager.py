#!/usr/bin/env python3
# ControllerLaunch - Configuration Manager

import os
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger('controller-launch.config')

class ConfigManager:
    """Manages application configuration and user preferences."""
    
    def __init__(self, config_path=None):
        """Initialize the configuration manager.
        
        Args:
            config_path: Optional custom path to config file
        """
        if config_path is None:
            self.config_path = os.path.expanduser("~/.config/controller-launch/config.json")
        else:
            self.config_path = config_path
            
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Get the default config path
        self.default_config_path = self._get_default_config_path()
        
        # Load or create configuration
        self.config = self.load()
        
    def _get_default_config_path(self):
        """Get the path to the default configuration file."""
        # Check if we're running from source or as installed package
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        
        # Try to find default config in various locations
        potential_paths = [
            os.path.join(parent_dir, "config", "default_config.json"),  # Source tree
            "/etc/controller-launch/default_config.json",  # System-wide installation
            os.path.join(sys.prefix, "share", "controller-launch", "default_config.json")  # Python installation
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                logger.info(f"Found default configuration at {path}")
                return path
                
        # If default config not found, use a minimal fallback
        logger.warning("Default configuration not found, using minimal defaults")
        return None
        
    def _get_default_config(self):
        """Load the default configuration."""
        try:
            if self.default_config_path and os.path.exists(self.default_config_path):
                with open(self.default_config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading default configuration: {str(e)}")
            
        # Minimal fallback configuration
        return {
            "general": {"autostart": True},
            "controller": {"long_press_duration": 1.0},
            "games": {"paths": {}, "max_games_shown": 10, "recently_launched": []},
            "ui": {"opacity": 0.9}
        }
            
    def load(self):
        """Load configuration from file or create default if it doesn't exist."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    logger.info(f"Configuration loaded from {self.config_path}")
                    
                    # Merge with defaults for any missing keys
                    return self._merge_with_defaults(config)
            else:
                logger.info("No configuration file found, creating default")
                default_config = self._get_default_config()
                self.save(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return self._get_default_config()
    
    def _merge_with_defaults(self, config):
        """Merge loaded config with defaults to ensure all keys exist."""
        result = self._get_default_config()
        
        # Update each section with values from loaded config
        for section, values in config.items():
            if section in result:
                if isinstance(values, dict) and isinstance(result[section], dict):
                    # Recursively merge nested dictionaries
                    for key, value in values.items():
                        if key in result[section] and isinstance(value, dict) and isinstance(result[section][key], dict):
                            result[section][key].update(value)
                        else:
                            result[section][key] = value
                else:
                    result[section] = values
            else:
                result[section] = values
                
        return result
    
    def save(self, config=None):
        """Save current configuration to file."""
        if config is None:
            config = self.config
        else:
            self.config = config
            
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
                logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            return False
    
    def get(self, section, key=None, default=None):
        """Get configuration value by section and key.
        
        Args:
            section: Configuration section name
            key: Optional key within section
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        if section not in self.config:
            return default
            
        if key is None:
            return self.config[section]
            
        return self.config[section].get(key, default)
    
    def set(self, section, key, value):
        """Set configuration value.
        
        Args:
            section: Configuration section name
            key: Key within section
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}
            
        self.config[section][key] = value
        self.save()
    
    def update_recently_launched(self, game_id, game_info):
        """Update the recently launched games list.
        
        Args:
            game_id: Unique game identifier
            game_info: Game information dict
        """
        if "games" not in self.config:
            self.config["games"] = {"recently_launched": []}
            
        if "recently_launched" not in self.config["games"]:
            self.config["games"]["recently_launched"] = []
            
        recently = self.config["games"]["recently_launched"]
        
        # Remove if already in list
        recently = [g for g in recently if g["id"] != game_id]
        
        # Add to front of list
        recently.insert(0, {
            "id": game_id,
            "name": game_info["name"],
            "source": game_info["source"],
            "last_played": game_info.get("last_played", 0),
            "executable": game_info.get("executable", ""),
            "icon": game_info.get("icon", "")
        })
        
        # Keep only the latest games
        max_recent = self.get("games", "max_games_shown", 10) * 2
        self.config["games"]["recently_launched"] = recently[:max_recent]
        
        self.save()
