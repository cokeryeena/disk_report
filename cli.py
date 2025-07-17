"""
Interactive CLI interface for the bash script tool.
Handles user interaction, command parsing, and coordination between components.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import confirm
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from script_manager import ScriptManager
from bash_executor import BashExecutor
from syntax_highlighter import BashSyntaxHighlighter
from utils import format_error, format_success, format_info

class BashScriptCLI:
    """Main CLI interface for the bash script tool."""
    
    def __init__(self, script_dir: Path):
        self.script_dir = script_dir
        self.console = Console()
        self.script_manager = ScriptManager(script_dir)
        self.bash_executor = BashExecutor()
        self.syntax_highlighter = BashSyntaxHighlighter()
        self.history = InMemoryHistory()
        
        # Current script being edited
        self.current_script: Optional[str] = None
        self.current_script_name: Optional[str] = None
        self.script_lines: List[str] = []
        
        # Command completer
        self.commands = [
            'new', 'edit', 'save', 'load', 'list', 'delete', 'run',
            'execute', 'show', 'clear', 'help', 'exit', 'quit'
        ]
        self.completer = WordCompleter(self.commands)
        
    def run(self):
        """Main CLI loop."""
        self.show_welcome()
        
        while True:
            try:
                # Show current script status
                status = self._get_status()
                
                # Get user input
                user_input = prompt(
                    HTML(f"<ansigreen>bash-cli</ansigreen> {status}> "),
                    history=self.history,
                    completer=self.completer,
                ).strip()
                
                if not user_input:
                    continue
                    
                # Parse and execute command
                self._execute_command(user_input)
                
            except KeyboardInterrupt:
                if confirm("Do you want to exit?"):
                    break
            except EOFError:
                break
                
        self.console.print("\n[yellow]Goodbye![/yellow]")
    
    def show_welcome(self):
        """Display welcome message and help."""
        welcome_text = """
[bold blue]Bash Script CLI Tool[/bold blue]
Interactive tool for writing, managing, and executing bash scripts.

[bold]Available Commands:[/bold]
• [green]new[/green] [name]          - Create a new script
• [green]edit[/green] [name]         - Edit an existing script
• [green]save[/green] [name]         - Save current script
• [green]load[/green] <name>         - Load a saved script
• [green]list[/green]                - List all saved scripts
• [green]delete[/green] <name>       - Delete a saved script
• [green]run[/green]                 - Execute current script
• [green]execute[/green] <name>      - Execute a saved script
• [green]show[/green]                - Display current script
• [green]clear[/green]               - Clear current script
• [green]help[/green]                - Show this help message
• [green]exit[/green]/[green]quit[/green]           - Exit the tool

[bold]Script Editing:[/bold]
When creating or editing a script, enter bash commands line by line.
Type [yellow]:done[/yellow] to finish editing, [yellow]:cancel[/yellow] to cancel.
"""
        
        panel = Panel(welcome_text, title="Welcome", border_style="blue")
        self.console.print(panel)
    
    def _get_status(self) -> str:
        """Get current status for prompt."""
        if self.current_script_name:
            modified = "*" if self.script_lines else ""
            return f"[{self.current_script_name}{modified}]"
        return ""
    
    def _execute_command(self, user_input: str):
        """Parse and execute a user command."""
        parts = user_input.split()
        command = parts[0].lower()
        args = parts[1:]
        
        try:
            if command in ['exit', 'quit']:
                if self._check_unsaved_changes():
                    return
                sys.exit(0)
                
            elif command == 'help':
                self.show_welcome()
                
            elif command == 'new':
                self._new_script(args[0] if args else None)
                
            elif command == 'edit':
                if args:
                    self._edit_script(args[0])
                else:
                    self._edit_current_script()
                    
            elif command == 'save':
                self._save_script(args[0] if args else None)
                
            elif command == 'load':
                if not args:
                    self.console.print(format_error("Usage: load <script_name>"))
                    return
                self._load_script(args[0])
                
            elif command == 'list':
                self._list_scripts()
                
            elif command == 'delete':
                if not args:
                    self.console.print(format_error("Usage: delete <script_name>"))
                    return
                self._delete_script(args[0])
                
            elif command == 'run':
                self._run_current_script()
                
            elif command == 'execute':
                if not args:
                    self.console.print(format_error("Usage: execute <script_name>"))
                    return
                self._execute_script(args[0])
                
            elif command == 'show':
                self._show_current_script()
                
            elif command == 'clear':
                self._clear_script()
                
            else:
                self.console.print(format_error(f"Unknown command: {command}. Type 'help' for available commands."))
                
        except Exception as e:
            self.console.print(format_error(f"Error executing command: {e}"))
    
    def _new_script(self, name: Optional[str] = None):
        """Create a new script."""
        if self._check_unsaved_changes():
            return
            
        if not name:
            name = prompt("Enter script name: ").strip()
            if not name:
                self.console.print(format_error("Script name cannot be empty."))
                return
        
        self.current_script_name = name
        self.script_lines = []
        self.console.print(format_success(f"Created new script: {name}"))
        self._edit_current_script()
    
    def _edit_script(self, name: str):
        """Edit an existing script."""
        if self._check_unsaved_changes():
            return
            
        try:
            content = self.script_manager.load_script(name)
            self.current_script_name = name
            self.script_lines = content.split('\n')
            self.console.print(format_success(f"Loaded script: {name}"))
            self._edit_current_script()
        except FileNotFoundError:
            self.console.print(format_error(f"Script '{name}' not found."))
    
    def _edit_current_script(self):
        """Edit the current script interactively."""
        if not self.current_script_name:
            self.console.print(format_error("No script to edit. Use 'new' to create a script."))
            return
        
        self.console.print(format_info(f"Editing script: {self.current_script_name}"))
        self.console.print(format_info("Enter bash commands line by line. Type ':done' to finish, ':cancel' to cancel."))
        
        # Display existing content
        if self.script_lines:
            self.console.print("\n[bold]Current content:[/bold]")
            self._show_script_content(self.script_lines)
            self.console.print()
        
        temp_lines = self.script_lines.copy()
        
        while True:
            try:
                line = prompt(f"[{len(temp_lines) + 1:2}] ", history=self.history).rstrip()
                
                if line == ':done':
                    self.script_lines = temp_lines
                    self.console.print(format_success("Script editing completed."))
                    break
                elif line == ':cancel':
                    self.console.print(format_info("Script editing cancelled."))
                    break
                elif line == ':show':
                    self._show_script_content(temp_lines)
                elif line == ':clear':
                    temp_lines = []
                    self.console.print(format_info("Script cleared."))
                else:
                    temp_lines.append(line)
                    
            except KeyboardInterrupt:
                if confirm("Cancel editing?"):
                    break
    
    def _save_script(self, name: Optional[str] = None):
        """Save the current script."""
        if not self.script_lines:
            self.console.print(format_error("No script content to save."))
            return
        
        if name:
            self.current_script_name = name
        elif not self.current_script_name:
            name = prompt("Enter script name: ").strip()
            if not name:
                self.console.print(format_error("Script name cannot be empty."))
                return
            self.current_script_name = name
        
        try:
            content = '\n'.join(self.script_lines)
            self.script_manager.save_script(self.current_script_name, content)
            self.console.print(format_success(f"Script saved: {self.current_script_name}"))
        except Exception as e:
            self.console.print(format_error(f"Failed to save script: {e}"))
    
    def _load_script(self, name: str):
        """Load a saved script."""
        if self._check_unsaved_changes():
            return
            
        try:
            content = self.script_manager.load_script(name)
            self.current_script_name = name
            self.script_lines = content.split('\n')
            self.console.print(format_success(f"Loaded script: {name}"))
            self._show_current_script()
        except FileNotFoundError:
            self.console.print(format_error(f"Script '{name}' not found."))
        except Exception as e:
            self.console.print(format_error(f"Failed to load script: {e}"))
    
    def _list_scripts(self):
        """List all saved scripts."""
        try:
            scripts = self.script_manager.list_scripts()
            if not scripts:
                self.console.print(format_info("No saved scripts found."))
                return
            
            table = Table(title="Saved Scripts")
            table.add_column("Name", style="cyan")
            table.add_column("Size", style="magenta")
            table.add_column("Modified", style="green")
            
            for script_info in scripts:
                table.add_row(
                    script_info['name'],
                    script_info['size'],
                    script_info['modified']
                )
            
            self.console.print(table)
            
        except Exception as e:
            self.console.print(format_error(f"Failed to list scripts: {e}"))
    
    def _delete_script(self, name: str):
        """Delete a saved script."""
        try:
            if not self.script_manager.script_exists(name):
                self.console.print(format_error(f"Script '{name}' not found."))
                return
            
            if confirm(f"Delete script '{name}'?"):
                self.script_manager.delete_script(name)
                self.console.print(format_success(f"Script '{name}' deleted."))
                
                # Clear current script if it was the deleted one
                if self.current_script_name == name:
                    self.current_script_name = None
                    self.script_lines = []
                    
        except Exception as e:
            self.console.print(format_error(f"Failed to delete script: {e}"))
    
    def _run_current_script(self):
        """Execute the current script."""
        if not self.script_lines:
            self.console.print(format_error("No script to run. Create or load a script first."))
            return
        
        content = '\n'.join(self.script_lines)
        self._execute_script_content(content, self.current_script_name or "current")
    
    def _execute_script(self, name: str):
        """Execute a saved script."""
        try:
            content = self.script_manager.load_script(name)
            self._execute_script_content(content, name)
        except FileNotFoundError:
            self.console.print(format_error(f"Script '{name}' not found."))
        except Exception as e:
            self.console.print(format_error(f"Failed to execute script: {e}"))
    
    def _execute_script_content(self, content: str, name: str):
        """Execute script content and display results."""
        if not content.strip():
            self.console.print(format_error("Script is empty."))
            return
        
        self.console.print(format_info(f"Executing script: {name}"))
        
        # Show script content with syntax highlighting
        syntax = Syntax(content, "bash", theme="monokai", line_numbers=True)
        panel = Panel(syntax, title=f"Script: {name}", border_style="blue")
        self.console.print(panel)
        
        # Confirm execution for safety
        if not confirm("Execute this script?"):
            self.console.print(format_info("Execution cancelled."))
            return
        
        try:
            result = self.bash_executor.execute(content)
            
            # Display results
            self.console.print("\n" + "="*60)
            self.console.print(format_success("Execution completed"))
            
            if result.stdout:
                self.console.print("\n[bold green]Output:[/bold green]")
                self.console.print(result.stdout)
            
            if result.stderr:
                self.console.print("\n[bold red]Errors:[/bold red]")
                self.console.print(result.stderr)
            
            self.console.print(f"\n[bold]Exit code:[/bold] {result.returncode}")
            self.console.print("="*60)
            
        except Exception as e:
            self.console.print(format_error(f"Execution failed: {e}"))
    
    def _show_current_script(self):
        """Display the current script."""
        if not self.script_lines:
            self.console.print(format_info("No script loaded."))
            return
        
        self._show_script_content(self.script_lines)
    
    def _show_script_content(self, lines: List[str]):
        """Display script content with syntax highlighting."""
        if not lines:
            self.console.print(format_info("Script is empty."))
            return
        
        content = '\n'.join(lines)
        syntax = Syntax(content, "bash", theme="monokai", line_numbers=True)
        
        title = f"Script: {self.current_script_name}" if self.current_script_name else "Current Script"
        panel = Panel(syntax, title=title, border_style="blue")
        self.console.print(panel)
    
    def _clear_script(self):
        """Clear the current script."""
        if self.script_lines and not confirm("Clear current script?"):
            return
        
        self.script_lines = []
        self.console.print(format_success("Script cleared."))
    
    def _check_unsaved_changes(self) -> bool:
        """Check for unsaved changes and prompt user."""
        if not self.script_lines:
            return False
        
        if self.current_script_name:
            try:
                saved_content = self.script_manager.load_script(self.current_script_name)
                current_content = '\n'.join(self.script_lines)
                if saved_content == current_content:
                    return False
            except FileNotFoundError:
                pass  # Script not saved yet
        
        return not confirm("You have unsaved changes. Continue anyway?")
