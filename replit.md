# Bash Script CLI Tool

## Overview

This is an interactive command-line interface (CLI) tool for writing, managing, and executing bash scripts. The application provides a rich terminal interface for creating, editing, saving, and running bash scripts with syntax highlighting and safe execution capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular, object-oriented architecture with clear separation of concerns:

- **CLI Interface Layer**: Handles user interaction and command processing
- **Script Management Layer**: Manages script persistence and organization
- **Execution Layer**: Provides safe bash script execution with monitoring
- **Presentation Layer**: Handles syntax highlighting and terminal formatting
- **Utility Layer**: Common functions and helpers

## Key Components

### 1. Main Entry Point (`main.py`)
- **Purpose**: Application bootstrap and argument parsing
- **Key Features**: Command-line argument handling, directory setup, error handling
- **Technology**: Standard Python argparse

### 2. CLI Interface (`cli.py`)
- **Purpose**: Interactive command-line interface with rich terminal features
- **Key Features**: Command completion, history, interactive prompts
- **Technology**: 
  - `prompt_toolkit` for advanced CLI features
  - `rich` for terminal formatting and display
- **Architecture Decision**: Chose prompt_toolkit over basic input() for better UX with features like auto-completion and command history

### 3. Script Manager (`script_manager.py`)
- **Purpose**: Handles script persistence, loading, and metadata management
- **Key Features**: File-based storage, JSON metadata, script organization
- **Storage Strategy**: Local filesystem with JSON metadata file
- **Architecture Decision**: File-based storage chosen for simplicity and portability over database

### 4. Bash Executor (`bash_executor.py`)
- **Purpose**: Safe execution of bash scripts with monitoring and isolation
- **Key Features**: Timeout handling, output capture, process management
- **Safety Measures**: Temporary file execution, process monitoring, timeout enforcement
- **Architecture Decision**: Subprocess-based execution with proper isolation for security

### 5. Syntax Highlighter (`syntax_highlighter.py`)
- **Purpose**: Provides syntax highlighting for bash code in terminal
- **Key Features**: Pattern-based highlighting, rich text formatting
- **Technology**: Rich library for terminal formatting
- **Architecture Decision**: Custom highlighter implementation for bash-specific patterns

### 6. Utilities (`utils.py`)
- **Purpose**: Common utility functions and formatting helpers
- **Key Features**: Message formatting, filename sanitization
- **Design Pattern**: Utility functions for cross-cutting concerns

## Data Flow

1. **User Input**: Commands entered through prompt_toolkit interface
2. **Command Processing**: CLI processes commands and delegates to appropriate components
3. **Script Management**: ScriptManager handles save/load operations with filesystem
4. **Script Execution**: BashExecutor creates temporary files and executes scripts safely
5. **Output Display**: Rich library formats and displays results with syntax highlighting

## External Dependencies

### Core Libraries
- **prompt_toolkit**: Advanced CLI features (completion, history, prompts)
- **rich**: Terminal formatting, syntax highlighting, and rich text display
- **pathlib**: Modern path handling (Python standard library)
- **subprocess**: Process execution (Python standard library)
- **tempfile**: Temporary file creation for safe execution (Python standard library)

### Design Rationale
- **prompt_toolkit**: Chosen for professional CLI experience with auto-completion
- **rich**: Selected for superior terminal formatting and syntax highlighting capabilities
- **Standard Library**: Maximizes compatibility and reduces external dependencies where possible

## Deployment Strategy

### Local Development
- **Installation**: Direct Python execution with pip install of dependencies
- **Requirements**: Python 3.7+ with prompt_toolkit and rich libraries
- **Script Storage**: Local filesystem directory (default: `./scripts`)

### Distribution Considerations
- **Packaging**: Can be packaged as standalone Python application
- **Dependencies**: Minimal external dependencies for easy installation
- **Cross-platform**: Pure Python implementation works across operating systems

### Security Features
- **Script Isolation**: Temporary file execution prevents script persistence issues
- **Timeout Management**: Prevents runaway script execution
- **Filename Sanitization**: Prevents filesystem security issues
- **Process Management**: Proper cleanup of executed processes

The architecture prioritizes simplicity, security, and user experience while maintaining good separation of concerns and modularity for future enhancement.