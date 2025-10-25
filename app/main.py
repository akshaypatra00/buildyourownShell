import sys


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
                if cmd_name in builtins:
                    print(f"{cmd_name} is a shell builtin")
                else:
                    print(f"{cmd_name}: not found")
        
        else:
            # Print error message for other commands
            print(f"{command}: command not found")


if __name__ == "__main__":
    main()