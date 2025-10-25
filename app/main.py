import sys
import os


def main():
    # List of builtin commands
    builtins = ["echo", "exit", "type"]
    
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        
        # Wait for user input
        command = input()
        
        # Check if command is "exit"
        if command.startswith("exit"):
            # Extract exit code (default to 0)
            parts = command.split()
            if len(parts) > 1:
                exit_code = int(parts[1])
            else:
                exit_code = 0
            sys.exit(exit_code)
        
        # Check if command is "echo"
        elif command.startswith("echo "):
            # Get everything after "echo "
            text = command[5:]  # Skip "echo " (5 characters)
            print(text)
        
        # Check if command is "type"
        elif command.startswith("type "):
            # Get the command name after "type "
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                cmd_name = parts[1]
                
                # First, check if it's a builtin
                if cmd_name in builtins:
                    print(f"{cmd_name} is a shell builtin")
                else:
                    # Search in PATH
                    found = False
                    path_env = os.environ.get("PATH", "")
                    paths = path_env.split(os.pathsep)
                    
                    for directory in paths:
                        file_path = os.path.join(directory, cmd_name)
                        # Check if file exists and is executable
                        if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                            print(f"{cmd_name} is {file_path}")
                            found = True
                            break
                    
                    if not found:
                        print(f"{cmd_name}: not found")
        
        else:
            # Print error message for other commands
            print(f"{command}: command not found")


if __name__ == "__main__":
    main()