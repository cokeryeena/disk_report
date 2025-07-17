"""
Script management functionality for saving, loading, and organizing bash scripts.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

class ScriptManager:
    """Manages bash script persistence and organization."""
    
    def __init__(self, script_dir: Path):
        self.script_dir = Path(script_dir)
        self.script_dir.mkdir(exist_ok=True)
        
        # Metadata file for script information
        self.metadata_file = self.script_dir / ".metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load script metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {}
    
    def _save_metadata(self):
        """Save script metadata to file."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
        except OSError as e:
            raise Exception(f"Failed to save metadata: {e}")
    
    def _get_script_path(self, name: str) -> Path:
        """Get the full path for a script file."""
        # Sanitize script name
        safe_name = "".join(c for c in name if c.isalnum() or c in "._-")
        if not safe_name:
            raise ValueError("Invalid script name")
        
        if not safe_name.endswith('.sh'):
            safe_name += '.sh'
        
        return self.script_dir / safe_name
    
    def save_script(self, name: str, content: str) -> None:
        """Save a script to disk."""
        if not name or not name.strip():
            raise ValueError("Script name cannot be empty")
        
        script_path = self._get_script_path(name)
        
        try:
            # Write script content
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            # Update metadata
            self.metadata[name] = {
                'filename': script_path.name,
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat(),
                'size': len(content.encode('utf-8'))
            }
            self._save_metadata()
            
        except OSError as e:
            raise Exception(f"Failed to save script '{name}': {e}")
    
    def load_script(self, name: str) -> str:
        """Load a script from disk."""
        script_path = self._get_script_path(name)
        
        if not script_path.exists():
            raise FileNotFoundError(f"Script '{name}' not found")
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update last accessed time in metadata
            if name in self.metadata:
                self.metadata[name]['accessed'] = datetime.now().isoformat()
                self._save_metadata()
            
            return content
            
        except OSError as e:
            raise Exception(f"Failed to load script '{name}': {e}")
    
    def delete_script(self, name: str) -> None:
        """Delete a script from disk."""
        script_path = self._get_script_path(name)
        
        if not script_path.exists():
            raise FileNotFoundError(f"Script '{name}' not found")
        
        try:
            script_path.unlink()
            
            # Remove from metadata
            if name in self.metadata:
                del self.metadata[name]
                self._save_metadata()
                
        except OSError as e:
            raise Exception(f"Failed to delete script '{name}': {e}")
    
    def list_scripts(self) -> List[Dict[str, str]]:
        """List all saved scripts with their information."""
        scripts = []
        
        for script_file in self.script_dir.glob("*.sh"):
            if script_file.name.startswith('.'):
                continue
            
            name = script_file.stem
            if script_file.name.endswith('.sh'):
                name = script_file.name[:-3]  # Remove .sh extension
            
            try:
                stat = script_file.stat()
                size = self._format_size(stat.st_size)
                modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                
                scripts.append({
                    'name': name,
                    'size': size,
                    'modified': modified,
                    'path': str(script_file)
                })
                
            except OSError:
                continue
        
        return sorted(scripts, key=lambda x: x['name'])
    
    def script_exists(self, name: str) -> bool:
        """Check if a script exists."""
        script_path = self._get_script_path(name)
        return script_path.exists()
    
    def get_script_info(self, name: str) -> Dict[str, Any]:
        """Get detailed information about a script."""
        script_path = self._get_script_path(name)
        
        if not script_path.exists():
            raise FileNotFoundError(f"Script '{name}' not found")
        
        try:
            stat = script_path.stat()
            
            info = {
                'name': name,
                'path': str(script_path),
                'size': stat.st_size,
                'size_formatted': self._format_size(stat.st_size),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'permissions': oct(stat.st_mode)[-3:]
            }
            
            # Add metadata if available
            if name in self.metadata:
                info.update(self.metadata[name])
            
            return info
            
        except OSError as e:
            raise Exception(f"Failed to get script info: {e}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f}MB"
    
    def backup_scripts(self, backup_dir: Path) -> None:
        """Create a backup of all scripts."""
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"scripts_backup_{timestamp}"
        backup_path.mkdir()
        
        try:
            # Copy all script files
            for script_file in self.script_dir.glob("*.sh"):
                if not script_file.name.startswith('.'):
                    (backup_path / script_file.name).write_text(
                        script_file.read_text(encoding='utf-8'),
                        encoding='utf-8'
                    )
            
            # Copy metadata
            if self.metadata_file.exists():
                (backup_path / ".metadata.json").write_text(
                    self.metadata_file.read_text(encoding='utf-8'),
                    encoding='utf-8'
                )
            
        except OSError as e:
            raise Exception(f"Failed to create backup: {e}")
