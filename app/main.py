import sys


def main():
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
        if command.startswith("echo "):
            # Get everything after "echo "
            text = command[5:]  # Skip "echo " (5 characters)
            print(text)
        else:
            # Print error message for other commands
            print(f"{command}: command not found")


if __name__ == "__main__":
    main()