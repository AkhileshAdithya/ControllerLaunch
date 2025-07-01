#!/usr/bin/env python3
# Module validation script for ControllerLaunch

import os
import sys
import importlib
import importlib.util
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("validator")

def add_src_to_path():
    """Add the src directory to the Python path."""
    # Find project root
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    src_dir = project_root / "src"
    
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))
        return True
    else:
        logger.error(f"Source directory not found at {src_dir}")
        return False

def check_module(module_name, imported_by=None):
    """Check if a module can be imported without errors."""
    try:
        if imported_by:
            logger.info(f"Checking import of {module_name} from {imported_by}")
        else:
            logger.info(f"Checking module {module_name}")
            
        module = importlib.import_module(module_name)
        return True, module
    except ModuleNotFoundError as e:
        logger.error(f"Module not found: {e}")
        return False, None
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False, None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False, None

def check_core_modules():
    """Check all core modules for import errors."""
    core_modules = [
        "main",
        "config_manager",
        "controller_daemon",
        "game_library",
        "overlay_ui",
        "preferences_ui"
    ]
    
    success = True
    for module_name in core_modules:
        module_success, _ = check_module(module_name)
        if not module_success:
            success = False
            
    return success

def check_circular_imports():
    """Check for potential circular imports."""
    # Map of modules and their direct imports
    import_graph = {}
    
    # Source directory
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    src_dir = project_root / "src"
    
    # Get all Python files in src directory
    python_files = list(src_dir.glob("*.py"))
    logger.info(f"Found {len(python_files)} Python files in {src_dir}")
    
    # Parse imports from each file
    for py_file in python_files:
        module_name = py_file.stem
        import_graph[module_name] = []
        
        # Simple parsing to find import statements
        with open(py_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('from ') and ' import ' in line:
                    # Extract module name (handling relative imports)
                    parts = line.split(' import ')[0].split('from ')[1].strip()
                    if parts.startswith('.'):
                        parts = parts[1:]
                    if parts and parts != '__future__':
                        import_graph[module_name].append(parts)
                elif line.startswith('import '):
                    # Extract module name
                    parts = line[7:].strip().split(' as ')[0].split(',')
                    for p in parts:
                        p = p.strip()
                        if p and p != '__future__':
                            import_graph[module_name].append(p)
    
    # Check for circular imports
    def find_cycles(node, visited, path):
        """Use DFS to find cycles in the import graph."""
        visited.add(node)
        path.append(node)
        
        cycles = []
        if node in import_graph:
            for neighbor in import_graph[node]:
                # Only check local imports
                if neighbor in import_graph:
                    if neighbor in path:
                        # Found a cycle
                        cycle_start = path.index(neighbor)
                        cycles.append(path[cycle_start:] + [neighbor])
                    elif neighbor not in visited:
                        new_cycles = find_cycles(neighbor, visited.copy(), path.copy())
                        cycles.extend(new_cycles)
                        
        return cycles
    
    # Find all cycles in the import graph
    all_cycles = []
    for node in import_graph:
        cycles = find_cycles(node, set(), [])
        all_cycles.extend(cycles)
    
    # Remove duplicates
    unique_cycles = []
    for cycle in all_cycles:
        cycle_str = "->".join(cycle)
        is_duplicate = False
        for unique in unique_cycles:
            unique_str = "->".join(unique)
            if set(cycle) == set(unique):
                is_duplicate = True
                break
        if not is_duplicate:
            unique_cycles.append(cycle)
    
    if unique_cycles:
        logger.error(f"Found {len(unique_cycles)} circular import chains:")
        for i, cycle in enumerate(unique_cycles):
            logger.error(f"  {i+1}. {' -> '.join(cycle)}")
        return False
    else:
        logger.info("No circular imports detected.")
        return True

def main():
    """Run the module validation."""
    logger.info("Starting module validation...")
    
    # Add src directory to Python path
    if not add_src_to_path():
        return 1
    
    # Check for circular imports
    logger.info("\nChecking for circular imports:")
    no_circular = check_circular_imports()
    
    # Check core modules
    logger.info("\nValidating core modules:")
    modules_valid = check_core_modules()
    
    # Print summary
    logger.info("\nValidation Summary:")
    if no_circular and modules_valid:
        logger.info("✅ All modules validated successfully.")
        return 0
    else:
        logger.error("❌ Module validation failed. See errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
