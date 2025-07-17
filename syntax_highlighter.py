"""
Bash syntax highlighting for terminal display.
"""

import re
from typing import List, Tuple, Dict, Any
from rich.text import Text
from rich.console import Console

class BashSyntaxHighlighter:
    """Provides syntax highlighting for bash scripts."""
    
    def __init__(self):
        self.console = Console()
        
        # Define bash syntax patterns
        self.patterns = {
            'comment': (r'#.*$', 'dim green'),
            'string_double': (r'"([^"\\\\]|\\\\.)*"', 'yellow'),
            'string_single': (r"'([^'\\\\]|\\\\.)*'", 'yellow'),
            'variable': (r'\$\{[^}]+\}|\$\w+', 'cyan'),
            'keyword': (r'\b(if|then|else|elif|fi|for|while|do|done|case|esac|function|return|exit|break|continue|local|export|readonly|declare|set|unset)\b', 'magenta'),
            'builtin': (r'\b(echo|printf|read|cd|pwd|ls|cp|mv|rm|mkdir|rmdir|chmod|chown|grep|sed|awk|sort|uniq|head|tail|cat|less|more|find|xargs|test)\b', 'blue'),
            'operator': (r'[&|;()<>]|\|\||\&\&|==|!=|<=|>=|=~', 'red'),
            'number': (r'\b\d+\b', 'cyan'),
            'option': (r'\s-[a-zA-Z0-9]+|\s--[a-zA-Z0-9-]+', 'green'),
            'shebang': (r'^#!.*$', 'bright_blue'),
        }
    
    def highlight(self, code: str) -> Text:
        """Apply syntax highlighting to bash code."""
        text = Text()
        lines = code.split('\n')
        
        for i, line in enumerate(lines):
            if i > 0:
                text.append('\n')
            
            highlighted_line = self._highlight_line(line)
            text.append(highlighted_line)
        
        return text
    
    def _highlight_line(self, line: str) -> Text:
        """Highlight a single line of bash code."""
        text = Text()
        pos = 0
        length = len(line)
        
        # Track which parts of the line have been highlighted
        highlighted = [False] * length
        
        # Apply highlighting patterns in order of priority
        for pattern_name, (regex, style) in self.patterns.items():
            for match in re.finditer(regex, line, re.MULTILINE):
                start, end = match.span()
                
                # Only highlight if this part hasn't been highlighted yet
                if not any(highlighted[start:end]):
                    # Mark this region as highlighted
                    highlighted[start:end] = [True] * (end - start)
                    
                    # Add the text with highlighting
                    if start > pos:
                        text.append(line[pos:start])
                    
                    text.append(line[start:end], style=style)
                    pos = end
        
        # Add any remaining unhighlighted text
        if pos < length:
            text.append(line[pos:])
        
        return text
    
    def highlight_to_console(self, code: str, line_numbers: bool = True) -> None:
        """Print highlighted code to console."""
        lines = code.split('\n')
        
        if line_numbers:
            # Calculate width needed for line numbers
            max_line_num = len(lines)
            num_width = len(str(max_line_num))
            
            for i, line in enumerate(lines, 1):
                line_num = Text(f"{i:>{num_width}} │ ", style="dim")
                highlighted_line = self._highlight_line(line)
                
                combined = Text()
                combined.append(line_num)
                combined.append(highlighted_line)
                
                self.console.print(combined)
        else:
            for line in lines:
                highlighted_line = self._highlight_line(line)
                self.console.print(highlighted_line)
    
    def get_syntax_errors(self, code: str) -> List[Dict[str, Any]]:
        """Basic syntax error detection for bash scripts."""
        errors = []
        lines = code.split('\n')
        
        # Track bracket/quote balancing
        brace_stack = []
        paren_stack = []
        bracket_stack = []
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip comments and empty lines
            if not stripped or stripped.startswith('#'):
                continue
            
            # Check for unmatched quotes (basic check)
            in_single_quote = False
            in_double_quote = False
            escaped = False
            
            for i, char in enumerate(line):
                if escaped:
                    escaped = False
                    continue
                
                if char == '\\':
                    escaped = True
                    continue
                
                if char == "'" and not in_double_quote:
                    in_single_quote = not in_single_quote
                elif char == '"' and not in_single_quote:
                    in_double_quote = not in_double_quote
                elif not in_single_quote and not in_double_quote:
                    if char == '{':
                        brace_stack.append((line_num, i))
                    elif char == '}':
                        if not brace_stack:
                            errors.append({
                                'line': line_num,
                                'column': i,
                                'message': 'Unmatched closing brace',
                                'type': 'syntax'
                            })
                        else:
                            brace_stack.pop()
                    elif char == '(':
                        paren_stack.append((line_num, i))
                    elif char == ')':
                        if not paren_stack:
                            errors.append({
                                'line': line_num,
                                'column': i,
                                'message': 'Unmatched closing parenthesis',
                                'type': 'syntax'
                            })
                        else:
                            paren_stack.pop()
                    elif char == '[':
                        bracket_stack.append((line_num, i))
                    elif char == ']':
                        if not bracket_stack:
                            errors.append({
                                'line': line_num,
                                'column': i,
                                'message': 'Unmatched closing bracket',
                                'type': 'syntax'
                            })
                        else:
                            bracket_stack.pop()
            
            # Check for unmatched quotes at end of line
            if in_single_quote:
                errors.append({
                    'line': line_num,
                    'column': len(line),
                    'message': 'Unmatched single quote',
                    'type': 'syntax'
                })
            elif in_double_quote:
                errors.append({
                    'line': line_num,
                    'column': len(line),
                    'message': 'Unmatched double quote',
                    'type': 'syntax'
                })
            
            # Check for common bash syntax issues
            if re.search(r'\bif\b.*\bthen\b', stripped) and not stripped.endswith('then'):
                if 'then' not in stripped:
                    errors.append({
                        'line': line_num,
                        'column': 0,
                        'message': 'Missing "then" after "if" statement',
                        'type': 'syntax'
                    })
            
            if stripped.startswith('fi') and len(stripped) == 2:
                # This is okay
                pass
            elif 'fi' in stripped and not re.search(r'\bfi\b\s*$', stripped):
                errors.append({
                    'line': line_num,
                    'column': stripped.find('fi'),
                    'message': 'Unexpected text after "fi"',
                    'type': 'syntax'
                })
        
        # Check for unmatched opening brackets/braces/parentheses
        for stack, name in [(brace_stack, 'brace'), (paren_stack, 'parenthesis'), (bracket_stack, 'bracket')]:
            for line_num, col in stack:
                errors.append({
                    'line': line_num,
                    'column': col,
                    'message': f'Unmatched opening {name}',
                    'type': 'syntax'
                })
        
        return errors
    
    def format_error_message(self, error: Dict[str, Any]) -> str:
        """Format a syntax error message for display."""
        return f"Line {error['line']}, Column {error['column']}: {error['message']}"
