import sys
import shutil
import subprocess
import os
import shlex
import re
import readline
import glob

def exit_handler(args):
    return True

def pwd_handler(args):
    print(os.getcwd())
    return False

def cd_handler(args):
    if not args:
        return False
    target = args[0]
    path = os.path.expanduser(target)
    try:
        os.chdir(path)
    except OSError as e:
        print(f"cd: {target}: {e.strerror}")
    return False

def echo_handler(args):
    print(" ".join(args))
    return False

def type_handler(args):
    if not args:
        return False
    target = args[0]
    if target in BUILTINS:
        print(f"{target} is a shell builtin")
    else:
        path = shutil.which(target)
        if path:
            print(f"{target} is {path}")
        else:
            print(f"{target}: not found")
    return False

BUILTINS = {
    "exit": exit_handler,
    "pwd": pwd_handler,
    "cd": cd_handler,
    "echo": echo_handler,
    "type": type_handler,
}

def parse_redirection(command_parts):
    """Parse redirection operators and return command parts and output files if any."""
    stdout_file = None
    stderr_file = None
    stdout_append = False
    stderr_append = False
    i = 0
    
    while i < len(command_parts):
        if command_parts[i] in [">", "1>"]:
            if i + 1 < len(command_parts):
                stdout_file = command_parts[i + 1]
                stdout_append = False
                command_parts = command_parts[:i] + command_parts[i+2:]
                continue
        elif command_parts[i] in [">>", "1>>"]:
            if i + 1 < len(command_parts):
                stdout_file = command_parts[i + 1]
                stdout_append = True
                command_parts = command_parts[:i] + command_parts[i+2:]
                continue
        elif command_parts[i] == "2>":
            if i + 1 < len(command_parts):
                stderr_file = command_parts[i + 1]
                stderr_append = False
                command_parts = command_parts[:i] + command_parts[i+2:]
                continue
        elif command_parts[i] == "2>>":
            if i + 1 < len(command_parts):
                stderr_file = command_parts[i + 1]
                stderr_append = True
                command_parts = command_parts[:i] + command_parts[i+2:]
                continue
        i += 1
        
    return command_parts, stdout_file, stderr_file, stdout_append, stderr_append

# Variables to track completion state
last_tab_text = ""
last_tab_matches = []
last_tab_count = 0

def get_executable_matches(text):
    """Find all executables in PATH that match the given prefix."""
    matches = []
    
    # First, check builtins
    for cmd in BUILTINS.keys():
        if cmd.startswith(text):
            matches.append(cmd)
    
    # Then check executables in PATH
    path_dirs = os.environ.get("PATH", "").split(":")
    for dir_path in path_dirs:
        if not dir_path:
            continue
        
        # Use glob to find all files in the directory
        try:
            for file_path in glob.glob(os.path.join(dir_path, "*")):
                if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                    cmd_name = os.path.basename(file_path)
                    if cmd_name.startswith(text) and cmd_name not in matches:
                        matches.append(cmd_name)
        except Exception:
            # Skip directories we can't access
            pass
    
    return sorted(matches)

def get_longest_common_prefix(strings):
    """Get the longest common prefix of a list of strings."""
    if not strings:
        return ""
    if len(strings) == 1:
        return strings[0]
        
    prefix = strings[0]
    for string in strings[1:]:
        # Find the length of common prefix
        length = 0
        for i, (c1, c2) in enumerate(zip(prefix, string)):
            if c1 != c2:
                break
            length = i + 1
        
        # Update prefix to common part
        prefix = prefix[:length]
        if not prefix:
            break
            
    return prefix

def complete(text, state):
    """Custom tab completion function for readline."""
    global last_tab_text, last_tab_matches, last_tab_count
    
    # Split the line to get the current command/args
    line = readline.get_line_buffer()
    
    # First word (command) completion
    if not line.strip() or " " not in line.lstrip():
        # New completion attempt or different text
        if text != last_tab_text:
            last_tab_text = text
            last_tab_matches = get_executable_matches(text)
            last_tab_count = 0
        
        # No matches
        if not last_tab_matches:
            return None
            
        # Single match - add space
        if len(last_tab_matches) == 1:
            if state == 0:
                return last_tab_matches[0] + " "
            return None
            
        # Multiple matches
        if last_tab_count == 0:
            # First tab press - increment counter, ring bell, return the text
            last_tab_count += 1
            if state == 0:
                sys.stdout.write('\a')  # Ring bell
                sys.stdout.flush()
                return text
            return None
        else:
            # Second tab press - display all matches
            if state == 0:
                print()  # New line
                print("  ".join(last_tab_matches))
                sys.stdout.write(f"$ {text}")
                sys.stdout.flush()
                return text
            
            # Complete to longest common prefix
            longest_prefix = get_longest_common_prefix(last_tab_matches)
            if len(longest_prefix) > len(text) and state == 0:
                return longest_prefix
                
            return None
    
    # Multiple word completion (not implemented yet)
    if state == 0:
        return text
    return None

def setup_readline():
    """Set up readline with custom completion."""
    # Set up tab completion
    readline.parse_and_bind("tab: complete")
    # Set our custom completion function
    readline.set_completer(complete)
    # Set word delimiters (characters that separate words)
    readline.set_completer_delims(" \t\n")

def main():
    # Set up readline
    setup_readline()
    
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        try:
            command = input()
        except EOFError:
            break
        try:
            parts = shlex.split(command)
        except ValueError as e:
            print(f"Error parsing command: {e}")
            continue
        if not parts:
            continue
            
        # Parse redirection
        parts, stdout_file, stderr_file, stdout_append, stderr_append = parse_redirection(parts)
        if not parts:  # If after redirection parsing, nothing's left
            continue
            
        cmd, *args = parts
        handler = BUILTINS.get(cmd)
        
        # Setup file redirection if needed
        stdout_backup = None
        stderr_backup = None
        stdout_fd = None
        stderr_fd = None
        
        try:
            # Set up stdout redirection
            if stdout_file:
                try:
                    # Use 'a' for append mode, 'w' for write mode
                    mode = 'a' if stdout_append else 'w'
                    stdout_fd = open(stdout_file, mode)
                    stdout_backup = os.dup(sys.stdout.fileno())
                    os.dup2(stdout_fd.fileno(), sys.stdout.fileno())
                except Exception as e:
                    print(f"Error setting up stdout redirection: {e}")
                    if stdout_fd:
                        stdout_fd.close()
                    continue
            
            # Set up stderr redirection
            if stderr_file:
                try:
                    # Use 'a' for append mode, 'w' for write mode
                    mode = 'a' if stderr_append else 'w'
                    stderr_fd = open(stderr_file, mode)
                    stderr_backup = os.dup(sys.stderr.fileno())
                    os.dup2(stderr_fd.fileno(), sys.stderr.fileno())
                except Exception as e:
                    print(f"Error setting up stderr redirection: {e}")
                    if stderr_fd:
                        stderr_fd.close()
                    continue
        
            if handler:
                exit_shell = handler(args)
                if exit_shell:
                    break
            else:
                path = shutil.which(cmd)
                if path:
                    # Run external command
                    process = subprocess.run([cmd] + args)
                else:
                    print(f"{cmd}: command not found", file=sys.stderr)
        finally:
            # Restore stdout if redirected
            if stdout_backup is not None:
                os.dup2(stdout_backup, sys.stdout.fileno())
                os.close(stdout_backup)
                if stdout_fd:
                    stdout_fd.close()
            
            # Restore stderr if redirected
            if stderr_backup is not None:
                os.dup2(stderr_backup, sys.stderr.fileno())
                os.close(stderr_backup)
                if stderr_fd:
                    stderr_fd.close()

if __name__ == "__main__":
    main()