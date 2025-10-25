import sys
import os
import subprocess


def main():
    # List of builtin commands
    builtins = ["echo", "exit", "type", "pwd"]
    
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        
        # Wait for user input
        command = input()
        
        # Split command into parts
        parts = command.split()
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
            # Get everything after "echo "
            text = command[5:]  # Skip "echo " (5 characters)
            print(text)
        
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
                    # Pass cmd_name (not file_path) as first argument
                    result = subprocess.run([cmd_name] + parts[1:])
                    found = True
                    break
            
            if not found:
                # Print error message for commands not found
                print(f"{cmd_name}: command not found")


if __name__ == "__main__":
    main()