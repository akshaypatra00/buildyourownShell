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
    command_parts = shlex.split(command)
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
        filename = args[out_op_idx + 1]
        args = args[:out_op_idx]

    return (cmd, args, filename, redirect_mode)


def execute_builtin(cmd, args, stdin_pipe=None):
    """Execute a builtin command and return output as string"""
    import io
    
    output = io.StringIO()
    
    if cmd == "echo":
        print(" ".join(args), file=output)
    elif cmd == "type":
        if len(args) == 0:
            print("type: missing argument", file=output)
        elif args[0] in commands:
            print("{} is a shell builtin".format(args[0]), file=output)
        elif path := shutil.which(args[0]):
            print("{} is {}".format(args[0], path), file=output)
        else:
            print("{}: not found".format(args[0]), file=output)
    elif cmd == "pwd":
        print(os.getcwd(), file=output)
    
    return output.getvalue()


def execute_pipeline(command: str):
    """Execute a pipeline of commands"""
    # Split by pipe
    commands_list = command.split('|')
    commands_list = [cmd.strip() for cmd in commands_list]
    
    processes = []
    
    for i, cmd_str in enumerate(commands_list):
        cmd_parts = shlex.split(cmd_str)
        cmd = cmd_parts[0]
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []
        
        # Determine stdin for this command
        if i == 0:
            stdin = None
        else:
            stdin = processes[-1].stdout
        
        # Check if it's a builtin
        if cmd in ["echo", "type", "pwd"]:
            # For builtins in pipeline
            if i == len(commands_list) - 1:
                # Last command - read from previous and output to stdout
                if stdin:
                    stdin_data = stdin.read()
                    stdin.close()
                output = execute_builtin(cmd, args)
                sys.stdout.write(output)
                sys.stdout.flush()
            else:
                # Middle command - not typical but handle it
                output = execute_builtin(cmd, args)
                proc = subprocess.Popen(['cat'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
                proc.stdin.write(output)
                proc.stdin.close()
                processes.append(proc)
        else:
            # External command
            if cmd in executables:
                cmd_path = executables[cmd]
            else:
                cmd_path = shutil.which(cmd)
            
            if cmd_path:
                if i == len(commands_list) - 1:
                    # Last command
                    proc = subprocess.Popen([cmd_path] + args, stdin=stdin)
                    processes.append(proc)
                else:
                    # Not last command
                    proc = subprocess.Popen([cmd_path] + args, stdin=stdin, stdout=subprocess.PIPE)
                    processes.append(proc)
                
                # Close the previous stdout after passing it
                if stdin and i > 0:
                    processes[-2].stdout.close()
            else:
                print("{}: command not found".format(cmd))
                return
    
    # Wait for all processes to complete
    for proc in processes:
        proc.wait()


def parse_command(command: str):
    # Check if command contains a pipe
    if '|' in command:
        execute_pipeline(command)
        return
    
    cmd, args, filename, redirect_mode = parse_arguments(command)

    if redirect_mode == "1>" or redirect_mode == ">":
        file = open(filename, "w")
    elif redirect_mode == "2>":
        file = open(filename, "w")
        sys.stderr = file
    elif redirect_mode == ">>" or redirect_mode == "1>>":
        file = open(filename, "a")
    elif redirect_mode == "2>>":
        file = open(filename, "a")
        sys.stderr = file
    else:
        file = sys.stdout

    if cmd == "echo":
        print(" ".join(args), file=file)
        if redirect_mode in ["2>", "2>>"]:
            sys.stderr = sys.__stderr__
        return

    if cmd == "type":
        if len(args) == 0:
            print("{}: missing file operand".format(command), file=file)
            return

        if args[0] in commands:
            print("{} is a shell builtin".format(args[0]), file=file)
            return

        if path := shutil.which(args[0]):
            print("{} is {}".format(args[0], path), file=file)
            return

        print("{}: not found".format(args[0]), file=file)
        return

    if cmd == "exit":
        err_code = 0
        if len(args) > 0:
            err_code = int(args[0])
        sys.exit(err_code)

    if cmd == "pwd":
        print(os.getcwd(), file=file)
        return

    if cmd == "cd":
        if len(args) == 1:
            dir_path = os.path.expanduser(args[0])
            if os.path.exists(dir_path):
                os.chdir(dir_path)
            else:
                print(
                    "{}: {}: No such file or directory".format(cmd, args[0]),
                    file=sys.stdout,
                )
            return

    if cmd in executables.keys():
        if redirect_mode in ["1>", ">"]:
            subprocess.run([executables[cmd]] + args, stdout=file)
        elif redirect_mode in [">>", "1>>"]:
            subprocess.run([executables[cmd]] + args, stdout=file)
        elif redirect_mode in ["2>"]:
            subprocess.run([executables[cmd]] + args, stderr=file)
        elif redirect_mode in ["2>>"]:
            subprocess.run([executables[cmd]] + args, stderr=file)
        else:
            subprocess.run([executables[cmd]] + args)
        
        if redirect_mode in ["2>", "2>>"]:
            sys.stderr = sys.__stderr__
        return

    print("{}: command not found".format(cmd), file=file)


def main():
    # Wait for user input
    command = input("$ ")
    parse_command(command)
    main()


def load_exec():
    paths = os.getenv("PATH").split(os.pathsep)
    for dir in paths:
        if os.path.isdir(dir):
            for file in os.listdir(dir):
                if file not in executables and os.path.isfile(os.path.join(dir, file)):
                    executables[file] = os.path.join(dir, file)


if __name__ == "__main__":
    commands = ["echo", "exit", "type", "pwd", "cd"]
    executables = {}
    tab_state = {"count": 0, "last_text": ""}

    load_exec()
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    main()