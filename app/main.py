import sys
import shutil
import os
from typing import Tuple, List
import shlex
import readline
import subprocess


def completer(text, state):
    load_exec()
    autocomplete_list = list(set(commands + list(executables.keys())))
    autocomplete_list.sort()
    matches = [cmd for cmd in autocomplete_list if cmd.startswith(text)]

    # Reset the tab counter if text is modified
    if tab_state["last_text"] != text:
        tab_state["count"] = 0
        tab_state["last_text"] = text

    if state == 0 and len(matches) > 1:
        if tab_state["count"] == 0:
            # Check if we can complete to a common prefix
            common_prefix = matches[0]
            for match in matches[1:]:
                i = 0
                while i < len(common_prefix) and i < len(match) and common_prefix[i] == match[i]:
                    i += 1
                common_prefix = common_prefix[:i]
            
            if len(common_prefix) > len(text):
                return common_prefix

            sys.stdout.write("\a")
            tab_state["count"] += 1
            return None
        else:
            print("\n" + "  ".join(matches))
            sys.stdout.write("$ {}".format(text))
            sys.stdout.flush()
            tab_state["count"] = 0
            return None

    if state < len(matches):
        return matches[state] + " "
    sys.stdout.write("\a")
    return None


def parse_arguments(command: str) -> Tuple[str, List[str], str, str]:
    try:
        command_parts = shlex.split(command)
    except:
        return (command, [], None, "")
    
    if len(command_parts) == 0:
        return ("", [], None, "")
    
    filename = None
    redirect_mode = ""
    cmd = command_parts[0]

    if len(command_parts) == 1:
        return (cmd, [], None, redirect_mode)

    args = command_parts[1:]
    out_op_idx = -1

    modes = ["1>>", "2>>", ">>", "1>", "2>", ">"]

    for mode in modes:
        if mode in args:
            out_op_idx = args.index(mode)
            redirect_mode = mode
            break

    if out_op_idx != -1:
        if out_op_idx + 1 < len(args):
            filename = args[out_op_idx + 1]
            args = args[:out_op_idx]
        else:
            args = args[:out_op_idx]

    return (cmd, args, filename, redirect_mode)


def execute_pipeline(command: str):
    """Execute a pipeline of commands"""
    commands_list = command.split('|')
    commands_list = [cmd.strip() for cmd in commands_list]
    
    processes = []
    prev_stdout = None
    
    for i, cmd_str in enumerate(commands_list):
        try:
            cmd_parts = shlex.split(cmd_str)
        except:
            print("Parse error")
            return
        
        if len(cmd_parts) == 0:
            continue
            
        cmd = cmd_parts[0]
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []
        
        # Determine if this is a builtin
        is_builtin = cmd in commands
        
        if is_builtin:
            # Builtin command
            if i == 0:
                # First command - execute and capture output
                if cmd == "echo":
                    output = " ".join(args) + "\n"
                elif cmd == "type":
                    if len(args) == 0:
                        output = "type: missing argument\n"
                    elif args[0] in commands:
                        output = "{} is a shell builtin\n".format(args[0])
                    elif path := shutil.which(args[0]):
                        output = "{} is {}\n".format(args[0], path)
                    else:
                        output = "{}: not found\n".format(args[0])
                elif cmd == "pwd":
                    output = os.getcwd() + "\n"
                elif cmd == "history":
                    output = ""
                    for idx, hist_cmd in enumerate(history_list, 1):
                        output += "    {}  {}\n".format(idx, hist_cmd)
                else:
                    output = ""
                
                # Create a process to pipe this output
                proc = subprocess.Popen(['cat'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
                proc.stdin.write(output)
                proc.stdin.close()
                processes.append(proc)
                prev_stdout = proc.stdout
            
            elif i == len(commands_list) - 1:
                # Last command - read from previous, execute builtin, output to stdout
                if prev_stdout:
                    # Consume the input but ignore it for most builtins
                    prev_stdout.read()
                    prev_stdout.close()
                
                # Execute builtin to stdout
                if cmd == "echo":
                    print(" ".join(args))
                elif cmd == "type":
                    if len(args) == 0:
                        print("type: missing argument")
                    elif args[0] in commands:
                        print("{} is a shell builtin".format(args[0]))
                    elif path := shutil.which(args[0]):
                        print("{} is {}".format(args[0], path))
                    else:
                        print("{}: not found".format(args[0]))
                elif cmd == "pwd":
                    print(os.getcwd())
                elif cmd == "history":
                    for idx, hist_cmd in enumerate(history_list, 1):
                        print("    {}  {}".format(idx, hist_cmd))
        else:
            # External command
            if cmd in executables:
                cmd_path = executables[cmd]
            else:
                cmd_path = shutil.which(cmd)
            
            if cmd_path:
                if i == 0:
                    # First command
                    proc = subprocess.Popen([cmd] + args, stdout=subprocess.PIPE)
                    processes.append(proc)
                    prev_stdout = proc.stdout
                elif i == len(commands_list) - 1:
                    # Last command
                    proc = subprocess.Popen([cmd] + args, stdin=prev_stdout)
                    processes.append(proc)
                    if len(processes) > 1:
                        processes[-2].stdout.close()
                else:
                    # Middle command
                    proc = subprocess.Popen([cmd] + args, stdin=prev_stdout, stdout=subprocess.PIPE)
                    processes.append(proc)
                    if len(processes) > 1:
                        processes[-2].stdout.close()
                    prev_stdout = proc.stdout
            else:
                print("{}: command not found".format(cmd))
                return
    
    # Wait for all processes
    for proc in processes:
        proc.wait()


def parse_command(command: str):
    # Add to history
    history_list.append(command)
    
    # Check if command contains a pipe
    if '|' in command:
        execute_pipeline(command)
        return
    
    cmd, args, filename, redirect_mode = parse_arguments(command)
    
    if not cmd:
        return

    # Handle file redirection
    stdout_file = None
    stderr_file = None
    
    if redirect_mode == "1>" or redirect_mode == ">":
        if filename:
            stdout_file = open(filename, "w")
    elif redirect_mode == "2>":
        if filename:
            stderr_file = open(filename, "w")
    elif redirect_mode == ">>" or redirect_mode == "1>>":
        if filename:
            stdout_file = open(filename, "a")
    elif redirect_mode == "2>>":
        if filename:
            stderr_file = open(filename, "a")

    # Determine output destination
    if stdout_file:
        output = stdout_file
    else:
        output = sys.stdout

    if cmd == "echo":
        print(" ".join(args), file=output)
        if stdout_file:
            stdout_file.close()
        if stderr_file:
            stderr_file.close()
        return

    if cmd == "type":
        if len(args) == 0:
            print("{}: missing file operand".format(command), file=output)
        elif args[0] in commands:
            print("{} is a shell builtin".format(args[0]), file=output)
        elif path := shutil.which(args[0]):
            print("{} is {}".format(args[0], path), file=output)
        else:
            print("{}: not found".format(args[0]), file=output)
        
        if stdout_file:
            stdout_file.close()
        if stderr_file:
            stderr_file.close()
        return

    if cmd == "exit":
        err_code = 0
        if len(args) > 0:
            err_code = int(args[0])
        sys.exit(err_code)

    if cmd == "pwd":
        print(os.getcwd(), file=output)
        if stdout_file:
            stdout_file.close()
        if stderr_file:
            stderr_file.close()
        return

    if cmd == "cd":
        if len(args) == 1:
            dir_path = os.path.expanduser(args[0])
            if os.path.exists(dir_path):
                os.chdir(dir_path)
            else:
                print("{}: {}: No such file or directory".format(cmd, args[0]))
        if stdout_file:
            stdout_file.close()
        if stderr_file:
            stderr_file.close()
        return

    if cmd == "history":
        for idx, hist_cmd in enumerate(history_list, 1):
            print("    {}  {}".format(idx, hist_cmd), file=output)
        if stdout_file:
            stdout_file.close()
        if stderr_file:
            stderr_file.close()
        return

    # External commands
    if cmd in executables:
        cmd_path = executables[cmd]
    else:
        cmd_path = shutil.which(cmd)
    
    if cmd_path:
        subprocess.run([cmd] + args, stdout=stdout_file, stderr=stderr_file)
        if stdout_file:
            stdout_file.close()
        if stderr_file:
            stderr_file.close()
        return

    print("{}: command not found".format(cmd), file=output)
    if stdout_file:
        stdout_file.close()
    if stderr_file:
        stderr_file.close()


def main():
    try:
        command = input("$ ")
        parse_command(command)
        main()
    except EOFError:
        sys.exit(0)
    except KeyboardInterrupt:
        print()
        main()


def load_exec():
    paths = os.getenv("PATH")
    if not paths:
        return
    paths = paths.split(os.pathsep)
    for dir in paths:
        if os.path.isdir(dir):
            try:
                for file in os.listdir(dir):
                    if file not in executables and os.path.isfile(os.path.join(dir, file)):
                        executables[file] = os.path.join(dir, file)
            except PermissionError:
                continue


if __name__ == "__main__":
    commands = ["echo", "exit", "type", "pwd", "cd", "history"]
    executables = {}
    tab_state = {"count": 0, "last_text": ""}
    history_list = []

    load_exec()
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    main()