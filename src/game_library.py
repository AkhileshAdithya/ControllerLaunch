#!/usr/bin/env python3
# ControllerLaunch - Game Library
# Handles game detection and management from various sources

import os
import re
import json
import glob
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime

logger = logging.getLogger('controller-launch.library')

class GameLibrary:
    """Manages game discovery and launching from various sources."""
    
    def __init__(self, config_manager):
        """Initialize the game library.
        
        Args:
            config_manager: ConfigManager instance
        """
        self.config = config_manager
        self.games = {}  # ID -> game info
        self.last_scan_time = 0
        
        # Scan for games initially
        self.scan_all_sources()
    
    def scan_all_sources(self, force=False):
        """Scan all configured game sources.
        
        Args:
            force: Force a rescan even if cache is recent
        """
        # Skip if we've scanned recently (within last 5 minutes)
        current_time = time.time()
        if not force and current_time - self.last_scan_time < 300:
            return
        
        logger.info("Scanning for games from all sources")
        
        # Reset game list while keeping last_played data
        last_played_data = {}
        for game_id, game_info in self.games.items():
            if 'last_played' in game_info:
                last_played_data[game_id] = game_info['last_played']
        
        self.games = {}
        
        # Scan each source
        self._scan_steam()
        self._scan_flatpak()
        self._scan_lutris()
        self._scan_custom_paths()
        
        # Restore last played data
        for game_id, timestamp in last_played_data.items():
            if game_id in self.games:
                self.games[game_id]['last_played'] = timestamp
        
        # Update last scan time
        self.last_scan_time = current_time
        
        logger.info(f"Found {len(self.games)} games from all sources")
    
    def _scan_steam(self):
        """Scan for Steam games."""
        logger.info("Scanning for Steam games")
        
        steam_paths = self.config.get("games", "paths", {}).get("steam", [])
        if not steam_paths:
            steam_paths = ["~/.steam", "~/.local/share/Steam"]
            
        # Expand paths
        steam_paths = [os.path.expanduser(path) for path in steam_paths]
        
        found_games = 0
        
        for steam_path in steam_paths:
            if not os.path.exists(steam_path):
                continue
                
            # Look for libraryfolders.vdf to find all Steam libraries
            vdf_paths = [
                os.path.join(steam_path, "steamapps", "libraryfolders.vdf"),
                os.path.join(steam_path, "steam", "steamapps", "libraryfolders.vdf")
            ]
            
            library_paths = []
            
            for vdf_path in vdf_paths:
                if os.path.exists(vdf_path):
                    # Parse VDF file to extract library paths
                    library_paths.extend(self._parse_steam_libraryfolders(vdf_path))
            
            # Always add the default steamapps directory
            default_apps = os.path.join(steam_path, "steamapps")
            if os.path.exists(default_apps) and default_apps not in library_paths:
                library_paths.append(default_apps)
            
            # Look for appmanifest_*.acf files in each library
            for library_path in library_paths:
                if not os.path.exists(library_path):
                    continue
                    
                app_manifests = glob.glob(os.path.join(library_path, "appmanifest_*.acf"))
                
                for manifest in app_manifests:
                    try:
                        app_id = os.path.basename(manifest).replace("appmanifest_", "").replace(".acf", "")
                        app_data = self._parse_steam_appmanifest(manifest)
                        
                        if not app_data:
                            continue
                        
                        name = app_data.get('name', f"Steam App {app_id}")
                        
                        # Check for executable
                        install_dir = os.path.join(library_path, "common", app_data.get('installdir', ''))
                        
                        if not os.path.exists(install_dir):
                            continue
                        
                        # Try to find an icon
                        icon_path = None
                        for icon_file in ['logo.png', 'header.jpg', 'icon.png', 'steam_icon.png']:
                            potential_icon = os.path.join(install_dir, icon_file)
                            if os.path.exists(potential_icon):
                                icon_path = potential_icon
                                break
                        
                        # Store game info
                        game_id = f"steam:{app_id}"
                        self.games[game_id] = {
                            'id': game_id,
                            'name': name,
                            'source': 'Steam',
                            'executable': f"steam://rungameid/{app_id}",
                            'install_dir': install_dir,
                            'icon': icon_path,
                            'app_id': app_id,
                        }
                        found_games += 1
                    except Exception as e:
                        logger.error(f"Error parsing Steam app manifest {manifest}: {str(e)}")
        
        logger.info(f"Found {found_games} Steam games")
    
    def _parse_steam_libraryfolders(self, vdf_path):
        """Parse Steam libraryfolders.vdf file to get library paths.
        
        Args:
            vdf_path: Path to libraryfolders.vdf
            
        Returns:
            List of library paths
        """
        library_paths = []
        
        try:
            with open(vdf_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract paths using regex
            # This is a simple parser and might break with VDF format changes
            path_matches = re.finditer(r'"path"\s+"([^"]+)"', content)
            
            for match in path_matches:
                path = match.group(1).replace('\\\\', '/')
                steamapps_path = os.path.join(path, "steamapps")
                if os.path.exists(steamapps_path):
                    library_paths.append(steamapps_path)
        except Exception as e:
            logger.error(f"Error parsing Steam library folders: {str(e)}")
        
        return library_paths
    
    def _parse_steam_appmanifest(self, manifest_path):
        """Parse Steam app manifest file.
        
        Args:
            manifest_path: Path to appmanifest_*.acf
            
        Returns:
            Dict with app data
        """
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract key fields using regex
            name_match = re.search(r'"name"\s+"([^"]+)"', content)
            installdir_match = re.search(r'"installdir"\s+"([^"]+)"', content)
            
            return {
                'name': name_match.group(1) if name_match else None,
                'installdir': installdir_match.group(1) if installdir_match else None,
            }
        except Exception as e:
            logger.error(f"Error parsing Steam app manifest {manifest_path}: {str(e)}")
            return None
    
    def _scan_flatpak(self):
        """Scan for Flatpak games."""
        logger.info("Scanning for Flatpak games")
        
        # Check if flatpak is installed
        try:
            subprocess.run(['flatpak', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.info("Flatpak not installed, skipping")
            return
        
        found_games = 0
        
        try:
            # Get list of installed Flatpak apps
            result = subprocess.run(
                ['flatpak', 'list', '--app', '--columns=application,name,version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            # Parse output
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if not line.strip():
                    continue
                
                parts = line.split('\t')
                if len(parts) < 2:
                    continue
                
                app_id = parts[0].strip()
                name = parts[1].strip() if len(parts) > 1 else app_id
                
                # Check if this is a game
                # There's no perfect way to do this, but we can check the app_id
                if self._is_flatpak_game(app_id):
                    icon_path = self._find_flatpak_icon(app_id)
                    
                    # Store game info
                    game_id = f"flatpak:{app_id}"
                    self.games[game_id] = {
                        'id': game_id,
                        'name': name,
                        'source': 'Flatpak',
                        'executable': f"flatpak run {app_id}",
                        'icon': icon_path,
                        'app_id': app_id,
                    }
                    found_games += 1
        except Exception as e:
            logger.error(f"Error scanning Flatpak games: {str(e)}")
        
        logger.info(f"Found {found_games} Flatpak games")
    
    def _is_flatpak_game(self, app_id):
        """Check if a Flatpak app is likely a game.
        
        Args:
            app_id: Flatpak application ID
            
        Returns:
            True if likely a game, False otherwise
        """
        # Check for common game-related app ID patterns
        game_patterns = [
            r'\.Game$',
            r'game',
            r'play',
            r'steam',
            r'itch',
            r'^com\.valvesoftware',
            r'^io\.itch',
            r'^net\.lutris',
        ]
        
        for pattern in game_patterns:
            if re.search(pattern, app_id, re.IGNORECASE):
                return True
        
        # Try to check desktop file for game category
        try:
            # Find desktop file
            result = subprocess.run(
                ['flatpak', 'info', app_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            output = result.stdout
            
            # Look for Application section
            app_section = re.search(r'Application:\s*([^\n]+)', output)
            if not app_section:
                return False
                
            app_name = app_section.group(1).strip()
            
            # Check desktop file for game category
            desktop_paths = [
                os.path.expanduser(f"~/.local/share/flatpak/exports/share/applications/{app_id}.desktop"),
                f"/var/lib/flatpak/exports/share/applications/{app_id}.desktop",
            ]
            
            for desktop_path in desktop_paths:
                if os.path.exists(desktop_path):
                    with open(desktop_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Check for game category
                    categories_match = re.search(r'Categories=([^\n]+)', content)
                    if categories_match:
                        categories = categories_match.group(1).lower()
                        if 'game' in categories:
                            return True
        except Exception as e:
            logger.error(f"Error checking if {app_id} is a game: {str(e)}")
        
        return False
    
    def _find_flatpak_icon(self, app_id):
        """Find icon for a Flatpak application.
        
        Args:
            app_id: Flatpak application ID
            
        Returns:
            Path to icon or None
        """
        # Try several common icon locations
        icon_paths = [
            os.path.expanduser(f"~/.local/share/flatpak/exports/share/icons/hicolor/128x128/apps/{app_id}.png"),
            os.path.expanduser(f"~/.local/share/flatpak/exports/share/icons/hicolor/scalable/apps/{app_id}.svg"),
            f"/var/lib/flatpak/exports/share/icons/hicolor/128x128/apps/{app_id}.png",
            f"/var/lib/flatpak/exports/share/icons/hicolor/scalable/apps/{app_id}.svg",
        ]
        
        # Check system icon theme if app_id contains a dot
        if '.' in app_id:
            icon_name = app_id.split('.')[-1]
            icon_paths.extend([
                f"/usr/share/icons/hicolor/128x128/apps/{icon_name}.png",
                f"/usr/share/icons/hicolor/scalable/apps/{icon_name}.svg",
            ])
        
        for path in icon_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _scan_lutris(self):
        """Scan for Lutris games."""
        logger.info("Scanning for Lutris games")
        
        lutris_paths = self.config.get("games", "paths", {}).get("lutris", [])
        if not lutris_paths:
            lutris_paths = ["~/.local/share/lutris"]
            
        # Expand paths
        lutris_paths = [os.path.expanduser(path) for path in lutris_paths]
        
        found_games = 0
        
        for lutris_path in lutris_paths:
            if not os.path.exists(lutris_path):
                continue
                
            # Look for game configs
            config_dir = os.path.join(lutris_path, "games")
            if not os.path.exists(config_dir):
                continue
                
            # Parse each game config
            for config_file in glob.glob(os.path.join(config_dir, "*.yml")):
                try:
                    # Basic YAML parsing without pyyaml dependency
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract key fields using regex
                    name_match = re.search(r'name: (.+)', content)
                    slug_match = re.search(r'slug: (.+)', content)
                    
                    if not name_match or not slug_match:
                        continue
                    
                    name = name_match.group(1).strip()
                    slug = slug_match.group(1).strip()
                    
                    # Look for icon
                    icon_path = os.path.join(lutris_path, "banners", f"{slug}.jpg")
                    if not os.path.exists(icon_path):
                        icon_path = None
                    
                    # Store game info
                    game_id = f"lutris:{slug}"
                    self.games[game_id] = {
                        'id': game_id,
                        'name': name,
                        'source': 'Lutris',
                        'executable': f"lutris lutris:{slug}",
                        'icon': icon_path,
                        'slug': slug,
                    }
                    found_games += 1
                except Exception as e:
                    logger.error(f"Error parsing Lutris config {config_file}: {str(e)}")
        
        logger.info(f"Found {found_games} Lutris games")
    
    def _scan_custom_paths(self):
        """Scan custom paths defined by the user."""
        logger.info("Scanning custom game paths")
        
        custom_paths = self.config.get("games", "paths", {}).get("custom", [])
        
        # Expand paths
        custom_paths = [os.path.expanduser(path) for path in custom_paths]
        
        found_games = 0
        
        for path in custom_paths:
            if not os.path.exists(path) or not os.path.isdir(path):
                continue
                
            # Look for executable files
            for root, dirs, files in os.walk(path):
                for file in files:
                    # Skip if already too many games found in this path
                    if found_games > 100:
                        logger.warning(f"Too many potential games found in {path}, stopping scan")
                        break
                        
                    file_path = os.path.join(root, file)
                    
                    # Check if file is executable
                    if not os.access(file_path, os.X_OK):
                        continue
                        
                    # Skip common non-game executables
                    if file in ['steam', 'lutris', 'flatpak', 'python', 'python3']:
                        continue
                        
                    # Use directory name as game name
                    name = os.path.basename(root)
                    
                    # Look for icon
                    icon_path = None
                    for icon_file in ['icon.png', 'icon.jpg', 'logo.png', 'logo.jpg']:
                        potential_icon = os.path.join(root, icon_file)
                        if os.path.exists(potential_icon):
                            icon_path = potential_icon
                            break
                    
                    # Store game info
                    game_id = f"custom:{file_path}"
                    self.games[game_id] = {
                        'id': game_id,
                        'name': name,
                        'source': 'Custom',
                        'executable': file_path,
                        'install_dir': root,
                        'icon': icon_path,
                    }
                    found_games += 1
        
        logger.info(f"Found {found_games} custom games")
    
    def get_all_games(self):
        """Get all discovered games.
        
        Returns:
            List of game info dicts
        """
        # Ensure we have up-to-date games
        self.scan_all_sources()
        
        return list(self.games.values())
    
    def get_recent_games(self, max_count=10):
        """Get recently played games.
        
        Args:
            max_count: Maximum number of games to return
            
        Returns:
            List of game info dicts, sorted by recency
        """
        # First, get recently launched games from config
        recent_games = self.config.get("games", "recently_launched", [])
        
        # Convert to list of game info dicts
        result = []
        
        for recent in recent_games:
            game_id = recent.get("id")
            if game_id in self.games:
                # Game still exists, use current metadata
                game_info = self.games[game_id].copy()
                # But keep timestamp from recent list
                game_info["last_played"] = recent.get("last_played", 0)
                result.append(game_info)
            elif "executable" in recent and os.path.exists(recent["executable"]):
                # Game not found in library but executable exists
                result.append(recent)
        
        # If we don't have enough recent games, add more from library
        if len(result) < max_count:
            # Sort remaining games by name
            other_games = sorted(
                [g for g in self.games.values() if g["id"] not in [r["id"] for r in result]],
                key=lambda g: g["name"]
            )
            result.extend(other_games[:max_count - len(result)])
        
        # Ensure we don't exceed max_count
        return result[:max_count]
    
    def launch_game(self, game_id, game_info=None):
        """Launch a game.
        
        Args:
            game_id: Game identifier
            game_info: Game info dict (optional if game_id exists in library)
            
        Returns:
            True if launch succeeded, False otherwise
        """
        if game_info is None:
            if game_id in self.games:
                game_info = self.games[game_id]
            else:
                logger.error(f"Game not found: {game_id}")
                return False
        
        executable = game_info.get("executable")
        if not executable:
            logger.error(f"No executable for game {game_id}")
            return False
        
        logger.info(f"Launching game: {game_info.get('name')} ({executable})")
        
        try:
            # Different launch methods depending on source
            if game_id.startswith("steam:"):
                # Launch via steam URL
                subprocess.Popen(["xdg-open", executable])
            elif game_id.startswith("flatpak:"):
                # Launch via flatpak run
                subprocess.Popen(executable.split())
            elif game_id.startswith("lutris:"):
                # Launch via lutris command
                subprocess.Popen(executable.split())
            else:
                # Direct executable
                subprocess.Popen([executable])
            
            # Update last played time
            now = int(time.time())
            if game_id in self.games:
                self.games[game_id]["last_played"] = now
            
            # Update recently launched games list
            self.config.update_recently_launched(game_id, {
                "name": game_info.get("name", "Unknown"),
                "source": game_info.get("source", "Unknown"),
                "executable": executable,
                "icon": game_info.get("icon"),
                "last_played": now
            })
            
            return True
        except Exception as e:
            logger.error(f"Error launching game {game_id}: {str(e)}")
            return False
    
    def remove_game(self, game_id):
        """Remove a game from the library and recent list.
        
        Args:
            game_id: Game identifier
            
        Returns:
            True if successful, False otherwise
        """
        # Remove from games dict
        if game_id in self.games:
            del self.games[game_id]
        
        # Remove from recently launched list
        recently = self.config.get("games", "recently_launched", [])
        updated = [g for g in recently if g.get("id") != game_id]
        
        if len(updated) != len(recently):
            self.config.set("games", "recently_launched", updated)
            return True
        
        return False

# For direct testing
if __name__ == "__main__":
    import sys
    from config_manager import ConfigManager
    
    logging.basicConfig(level=logging.INFO)
    
    config = ConfigManager()
    library = GameLibrary(config)
    
    games = library.get_all_games()
    print(f"Found {len(games)} games:")
    
    for game in games[:10]:  # Show first 10
        print(f"- {game['name']} ({game['source']})")
        
    if len(games) > 10:
        print(f"... and {len(games) - 10} more")
