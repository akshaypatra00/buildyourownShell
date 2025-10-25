import sys
import os
import subprocess


def parse_command(command):
    """Parse command handling single quotes, double quotes, and backslashes"""
    parts = []
    current = []
    in_single_quotes = False
    in_double_quotes = False
    i = 0
    
    while i < len(command):
        char = command[i]
        
        if char == '\\' and not in_single_quotes:
            # Backslash escape
            if i + 1 < len(command):
                next_char = command[i + 1]
                
                if in_double_quotes:
                    # Inside double quotes: only escape special characters
                    # Special characters: \ " $ ` and newline
                    if next_char in ['\\', '"', '$', '`', '\n']:
                        # Escape the special character
                        i += 1
                        current.append(next_char)
                    else:
                        # Not a special character, keep the backslash
                        current.append(char)
                else:
                    # Outside quotes: escape any character
                    i += 1
                    current.append(next_char)
        elif char == "'" and not in_double_quotes:
            # Toggle single quotes (unless inside double quotes)
            in_single_quotes = not in_single_quotes
        elif char == '"' and not in_single_quotes:
            # Toggle double quotes (unless inside single quotes)
            in_double_quotes = not in_double_quotes
        elif char == ' ' and not in_single_quotes and not in_double_quotes:
            # Space outside quotes - separator
            if current:
                parts.append(''.join(current))
                current = []
        else:
            # Regular character or space inside quotes
            current.append(char)
        
        i += 1
    
    # Add last part if any
    if current:
        parts.append(''.join(current))
    
    return parts


def parse_redirects(parts):
    """Extract redirection operators and return (command_parts, output_file, error_file)"""
    output_file = None
    error_file = None
    command_parts = []
    i = 0
    
    while i < len(parts):
        part = parts[i]
        
        # Check for stdout redirection: > or 1>
        if part == '>' or part == '1>':
            # Next part should be the filename
            if i + 1 < len(parts):
                output_file = parts[i + 1]
                i += 2
                continue
        elif part.startswith('1>'):
            # 1>file (no space)
            output_file = part[2:]
            i += 1
            continue
        elif part.startswith('>') and not part.startswith('>>'):
            # >file (no space) - but not >>
            output_file = part[1:]
            i += 1
            continue
        # Check for stderr redirection: 2>
        elif part == '2>':
            # Next part should be the filename
            if i + 1 < len(parts):
                error_file = parts[i + 1]
                i += 2
                continue
        elif part.startswith('2>'):
            # 2>file (no space)
            error_file = part[2:]
            i += 1
            continue
        
        command_parts.append(part)
        i += 1
    
    return command_parts, output_file, error_file


def main():
    # List of builtin commands
    builtins = ["echo", "exit", "type", "pwd", "cd"]
    
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        
        # Wait for user input
        command = input()
        
        # Parse command with quote handling
        parts = parse_command(command)
        if not parts:
            continue
        
        # Extract redirections
        parts, output_file, error_file = parse_redirects(parts)
        if not parts:
            continue
        
        cmd_name = parts[0]
        
        # Check if command is "exit"
        if cmd_name == "exit":
            # Extract exit code (default to 0)
            if len(parts) > 1:
                exit_code = int(parts[1])
            else:
                exit_code = 0
            sys.exit(exit_code)
        
        # Check if command is "echo"
        elif cmd_name == "echo":
            # Print all arguments separated by spaces
            output = ' '.join(parts[1:]) if len(parts) > 1 else ''
            
            if output_file:
                # Write to file
                with open(output_file, 'w') as f:
                    f.write(output + '\n')
            else:
                # Print to stdout
                print(output)
        
        # Check if command is "type"
        elif cmd_name == "type":
            # Get the command name after "type "
            if len(parts) > 1:
                target_cmd = parts[1]
                
                # First, check if it's a builtin
                if target_cmd in builtins:
                    result = f"{target_cmd} is a shell builtin"
                else:
                    # Search in PATH
                    found = False
                    path_env = os.environ.get("PATH", "")
                    paths = path_env.split(os.pathsep)
                    
                    for directory in paths:
                        file_path = os.path.join(directory, target_cmd)
                        # Check if file exists and is executable
                        if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                            result = f"{target_cmd} is {file_path}"
                            found = True
                            break
                    
                    if not found:
                        result = f"{target_cmd}: not found"
                
                if output_file:
                    with open(output_file, 'w') as f:
                        f.write(result + '\n')
                else:
                    print(result)
        
        # Check if command is "pwd"
        elif cmd_name == "pwd":
            # Print current working directory
            result = os.getcwd()
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(result + '\n')
            else:
                print(result)
        
        # Check if command is "cd"
        elif cmd_name == "cd":
            if len(parts) > 1:
                directory = parts[1]
                
                # Handle ~ for home directory
                if directory.startswith("~"):
                    home = os.environ.get("HOME")
                    if home:
                        # Replace ~ with home directory
                        if directory == "~":
                            directory = home
                        else:
                            # Handle paths like ~/something
                            directory = home + directory[1:]
                
                # Try to change directory
                try:
                    os.chdir(directory)
                except FileNotFoundError:
                    print(f"cd: {parts[1]}: No such file or directory")
                except NotADirectoryError:
                    print(f"cd: {parts[1]}: No such file or directory")
                except PermissionError:
                    print(f"cd: {parts[1]}: Permission denied")
        
        else:
            # Try to execute as external program
            # Search in PATH
            found = False
            path_env = os.environ.get("PATH", "")
            paths = path_env.split(os.pathsep)
            
            for directory in paths:
                file_path = os.path.join(directory, cmd_name)
                # Check if file exists and is executable
                if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                    # Execute the program with arguments
                    stdout_dest = open(output_file, 'w') if output_file else None
                    stderr_dest = open(error_file, 'w') if error_file else None
                    
                    result = subprocess.run(
                        [cmd_name] + parts[1:],
                        stdout=stdout_dest,
                        stderr=stderr_dest
                    )
                    
                    if stdout_dest:
                        stdout_dest.close()
                    if stderr_dest:
                        stderr_dest.close()
                    
                    found = True
                    break
            
            if not found:
                # Print error message for commands not found
                print(f"{cmd_name}: command not found")


if __name__ == "__main__":
    main()