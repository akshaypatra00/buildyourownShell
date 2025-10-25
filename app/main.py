import sys
import os
import subprocess


def parse_command(command):
    """Parse command handling single and double quotes"""
    parts = []
    current = []
    in_single_quotes = False
    in_double_quotes = False
    i = 0
    
    while i < len(command):
        char = command[i]
        
        if char == "'" and not in_double_quotes:
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
            if len(parts) > 1:
                print(' '.join(parts[1:]))
            else:
                print()
        
        # Check if command is "type"
        elif cmd_name == "type":
            # Get the command name after "type "
            if len(parts) > 1:
                target_cmd = parts[1]
                
                # First, check if it's a builtin
                if target_cmd in builtins:
                    print(f"{target_cmd} is a shell builtin")
                else:
                    # Search in PATH
                    found = False
                    path_env = os.environ.get("PATH", "")
                    paths = path_env.split(os.pathsep)
                    
                    for directory in paths:
                        file_path = os.path.join(directory, target_cmd)
                        # Check if file exists and is executable
                        if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                            print(f"{target_cmd} is {file_path}")
                            found = True
                            break
                    
                    if not found:
                        print(f"{target_cmd}: not found")
        
        # Check if command is "pwd"
        elif cmd_name == "pwd":
            # Print current working directory
            print(os.getcwd())
        
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
                    result = subprocess.run([cmd_name] + parts[1:])
                    found = True
                    break
            
            if not found:
                # Print error message for commands not found
                print(f"{cmd_name}: command not found")


if __name__ == "__main__":
    main()