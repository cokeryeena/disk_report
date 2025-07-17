"""
Utility functions for the bash script CLI tool.
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from rich.text import Text

def format_error(message: str) -> Text:
    """Format an error message for display."""
    text = Text()
    text.append("✗ ", style="bold red")
    text.append(message, style="red")
    return text

def format_success(message: str) -> Text:
    """Format a success message for display."""
    text = Text()
    text.append("✓ ", style="bold green")
    text.append(message, style="green")
    return text

def format_info(message: str) -> Text:
    """Format an info message for display."""
    text = Text()
    text.append("ℹ ", style="bold blue")
    text.append(message, style="blue")
    return text

def format_warning(message: str) -> Text:
    """Format a warning message for display."""
    text = Text()
    text.append("⚠ ", style="bold yellow")
    text.append(message, style="yellow")
    return text

def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to be safe for filesystem use."""
    # Remove or replace problematic characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip('. ')
    
    # Ensure it's not empty
    if not filename:
        filename = 'untitled'
    
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename

def is_valid_script_name(name: str) -> tuple[bool, str]:
    """Validate if a script name is valid."""
    if not name or not name.strip():
        return False, "Script name cannot be empty"
    
    name = name.strip()
    
    # Check for invalid characters
    if re.search(r'[<>:"/\\|?*]', name):
        return False, "Script name contains invalid characters"
    
    # Check for reserved names
    reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
    if name.upper() in reserved_names:
        return False, "Script name is reserved"
    
    # Check length
    if len(name) > 100:
        return False, "Script name is too long (max 100 characters)"
    
    return True, "Valid script name"

def get_terminal_size() -> tuple[int, int]:
    """Get terminal size (width, height)."""
    try:
        size = shutil.get_terminal_size()
        return size.columns, size.lines
    except OSError:
        return 80, 24  # Default fallback

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to fit within specified length."""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def parse_command_line(line: str) -> tuple[str, List[str]]:
    """Parse a command line into command and arguments."""
    parts = line.strip().split()
    if not parts:
        return "", []
    
    command = parts[0]
    args = parts[1:] if len(parts) > 1 else []
    
    return command, args

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes}m {seconds:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def check_bash_availability() -> tuple[bool, str]:
    """Check if bash is available on the system."""
    try:
        bash_path = shutil.which('bash')
        if bash_path:
            return True, bash_path
        else:
            return False, "Bash not found in PATH"
    except Exception as e:
        return False, f"Error checking bash availability: {e}"

def get_common_bash_commands() -> List[str]:
    """Get list of common bash commands for completion."""
    return [
        # File operations
        'ls', 'cd', 'pwd', 'mkdir', 'rmdir', 'rm', 'cp', 'mv', 'find', 'locate',
        'touch', 'ln', 'chmod', 'chown', 'chgrp', 'du', 'df', 'stat',
        
        # Text processing
        'cat', 'less', 'more', 'head', 'tail', 'grep', 'sed', 'awk', 'sort',
        'uniq', 'cut', 'tr', 'wc', 'diff', 'comm', 'join',
        
        # Process management
        'ps', 'top', 'htop', 'kill', 'killall', 'jobs', 'bg', 'fg', 'nohup',
        'screen', 'tmux',
        
        # Network
        'ping', 'wget', 'curl', 'ssh', 'scp', 'rsync', 'netstat', 'ss',
        
        # System info
        'uname', 'whoami', 'who', 'w', 'id', 'groups', 'date', 'uptime',
        'free', 'lscpu', 'lsblk', 'lsusb', 'lspci',
        
        # Archive/compression
        'tar', 'gzip', 'gunzip', 'zip', 'unzip', 'rar', 'unrar',
        
        # Text editors
        'nano', 'vim', 'emacs', 'gedit',
        
        # Package management (common)
        'apt', 'yum', 'dnf', 'pacman', 'brew', 'pip', 'npm',
        
        # Version control
        'git', 'svn', 'hg',
        
        # Development
        'make', 'gcc', 'g++', 'python', 'python3', 'node', 'java', 'javac',
        
        # System control
        'sudo', 'su', 'systemctl', 'service', 'mount', 'umount', 'fdisk',
        'crontab', 'at', 'batch',
    ]

def escape_shell_arg(arg: str) -> str:
    """Escape a shell argument to prevent injection."""
    # Simple escaping - wrap in single quotes and escape any single quotes
    return "'" + arg.replace("'", "'\"'\"'") + "'"

def validate_bash_syntax_basic(content: str) -> tuple[bool, List[str]]:
    """Basic bash syntax validation."""
    errors = []
    lines = content.split('\n')
    
    # Check for basic structure issues
    if_count = 0
    fi_count = 0
    
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Skip comments and empty lines
        if not stripped or stripped.startswith('#'):
            continue
        
        # Count if/fi statements
        if re.search(r'\bif\b', stripped):
            if_count += 1
        if re.search(r'\bfi\b', stripped):
            fi_count += 1
        
        # Check for common issues
        if stripped.endswith('\\') and line_num == len(lines):
            errors.append(f"Line {line_num}: Line continuation at end of script")
        
        # Check for unmatched quotes (very basic)
        single_quotes = stripped.count("'")
        double_quotes = stripped.count('"')
        
        if single_quotes % 2 != 0:
            errors.append(f"Line {line_num}: Possible unmatched single quotes")
        if double_quotes % 2 != 0:
            errors.append(f"Line {line_num}: Possible unmatched double quotes")
    
    # Check if/fi balance
    if if_count != fi_count:
        errors.append(f"Unbalanced if/fi statements: {if_count} if, {fi_count} fi")
    
    return len(errors) == 0, errors

def create_safe_temp_dir() -> Path:
    """Create a safe temporary directory for script execution."""
    import tempfile
    temp_dir = Path(tempfile.mkdtemp(prefix='bash_cli_'))
    return temp_dir

def cleanup_temp_dir(temp_dir: Path) -> None:
    """Safely clean up a temporary directory."""
    try:
        shutil.rmtree(temp_dir)
    except OSError:
        pass  # Ignore cleanup errors
