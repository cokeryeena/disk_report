"""
Safe bash script execution with output capture and error handling.
"""

import subprocess
import tempfile
import os
import signal
import threading
from pathlib import Path
from typing import NamedTuple, Optional, Union
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    """Result of script execution."""
    returncode: int
    stdout: str
    stderr: str
    execution_time: float
    timeout: bool = False

class BashExecutor:
    """Executes bash scripts safely with proper isolation and monitoring."""
    
    def __init__(self, timeout: int = 30, working_dir: Optional[Path] = None):
        self.timeout = timeout
        self.working_dir = working_dir or Path.cwd()
        self.current_process: Optional[subprocess.Popen] = None
        
    def execute(self, script_content: str, timeout: Optional[int] = None) -> ExecutionResult:
        """Execute bash script content and return results."""
        if not script_content.strip():
            raise ValueError("Script content cannot be empty")
        
        timeout = timeout or self.timeout
        
        # Create temporary script file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.sh',
            delete=False,
            encoding='utf-8'
        ) as temp_file:
            temp_file.write(self._prepare_script(script_content))
            temp_script_path = temp_file.name
        
        try:
            # Make script executable
            os.chmod(temp_script_path, 0o755)
            
            # Execute script
            result = self._run_script(temp_script_path, timeout)
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_script_path)
            except OSError:
                pass
        
        return result
    
    def execute_command(self, command: str, timeout: Optional[int] = None) -> ExecutionResult:
        """Execute a single bash command."""
        return self.execute(command, timeout)
    
    def _prepare_script(self, content: str) -> str:
        """Prepare script content with safety measures and error handling."""
        # Add shebang if not present
        lines = content.strip().split('\n')
        if not lines[0].startswith('#!'):
            lines.insert(0, '#!/bin/bash')
        
        # Add safety measures
        safety_header = [
            '#!/bin/bash',
            '',
            '# Script execution safety measures',
            'set -euo pipefail  # Exit on error, undefined vars, pipe failures',
            '',
            '# Function to handle cleanup on exit',
            'cleanup() {',
            '    echo "Script execution finished"',
            '}',
            'trap cleanup EXIT',
            '',
            '# Script content begins here',
        ]
        
        # Combine safety header with original content (skip original shebang if present)
        script_content = content.strip()
        if script_content.startswith('#!/'):
            # Remove existing shebang
            script_content = '\n'.join(script_content.split('\n')[1:])
        
        return '\n'.join(safety_header + ['', script_content])
    
    def _run_script(self, script_path: str, timeout: int) -> ExecutionResult:
        """Run the script and capture output."""
        import time
        start_time = time.time()
        
        try:
            # Set up environment
            env = os.environ.copy()
            env['BASH_ENV'] = '/dev/null'  # Prevent sourcing user's bash config
            
            # Execute script
            self.current_process = subprocess.Popen(
                ['/bin/bash', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.working_dir),
                env=env,
                preexec_fn=os.setsid  # Create new process group
            )
            
            try:
                stdout, stderr = self.current_process.communicate(timeout=timeout)
                execution_time = time.time() - start_time
                
                return ExecutionResult(
                    returncode=self.current_process.returncode,
                    stdout=stdout,
                    stderr=stderr,
                    execution_time=execution_time,
                    timeout=False
                )
                
            except subprocess.TimeoutExpired:
                # Kill the process group
                try:
                    os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
                    # Give it a chance to terminate gracefully
                    try:
                        self.current_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # Force kill if it doesn't terminate
                        os.killpg(os.getpgid(self.current_process.pid), signal.SIGKILL)
                        self.current_process.wait()
                except (OSError, ProcessLookupError):
                    pass
                
                execution_time = time.time() - start_time
                
                return ExecutionResult(
                    returncode=-1,
                    stdout="",
                    stderr=f"Script execution timed out after {timeout} seconds",
                    execution_time=execution_time,
                    timeout=True
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                returncode=-1,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                execution_time=execution_time,
                timeout=False
            )
        finally:
            self.current_process = None
    
    def interrupt_execution(self):
        """Interrupt current script execution."""
        if self.current_process:
            try:
                # Send SIGINT to process group
                os.killpg(os.getpgid(self.current_process.pid), signal.SIGINT)
            except (OSError, ProcessLookupError):
                pass
    
    def validate_script_syntax(self, script_content: str) -> tuple[bool, str]:
        """Validate bash script syntax without executing it."""
        if not script_content.strip():
            return False, "Script content is empty"
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.sh',
            delete=False,
            encoding='utf-8'
        ) as temp_file:
            temp_file.write(script_content)
            temp_script_path = temp_file.name
        
        try:
            # Use bash -n to check syntax without execution
            result = subprocess.run(
                ['/bin/bash', '-n', temp_script_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, "Syntax is valid"
            else:
                return False, result.stderr.strip() or "Syntax error detected"
                
        except subprocess.TimeoutExpired:
            return False, "Syntax check timed out"
        except Exception as e:
            return False, f"Syntax check failed: {str(e)}"
        finally:
            try:
                os.unlink(temp_script_path)
            except OSError:
                pass
    
    def get_script_dependencies(self, script_content: str) -> list[str]:
        """Analyze script to identify external command dependencies."""
        dependencies = set()
        
        # Common patterns for command usage
        import re
        
        # Direct command calls
        command_patterns = [
            r'\b([\w-]+)\s+',  # Simple command calls
            r'which\s+([\w-]+)',  # which command
            r'command\s+-v\s+([\w-]+)',  # command -v
            r'\$\(([\w-]+)',  # Command substitution
            r'`([\w-]+)',  # Backtick command substitution
        ]
        
        for pattern in command_patterns:
            matches = re.findall(pattern, script_content)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                # Filter out bash built-ins and common keywords
                if match not in ['if', 'then', 'else', 'fi', 'for', 'while', 'do', 'done', 
                               'case', 'esac', 'function', 'return', 'exit', 'echo', 'printf']:
                    dependencies.add(match)
        
        return sorted(list(dependencies))
