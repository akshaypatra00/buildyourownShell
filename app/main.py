import sys
import shutil
import os
from typing import Tuple, List
import shlex
import readline


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
            if all(match.startswith(matches[0]) for match in matches[1:]):
                return matches[0]

            sys.stdout.write("\a")
            tab_state["count"] += 1
            return None
        else:
            print("\n" + "  ".join(matches))
            sys.stdout.write("$ {}".format(text))
            sys.stdout.flush()
            return text

    if state < len(matches):
        return matches[state] + " "
    sys.stdout.write("\a")
    return None


def parse_arguments(command: str) -> Tuple[str, List[str]]:
    command_parts = shlex.split(command)
    filename = None
    redirect_mode = ""
    cmd = command_parts[0]

    if len(command_parts) == 1:
        return (cmd, [], None, redirect_mode)

    args = command_parts[1:]
    out_op_idx = -1

    modes = ["1>", "2>", ">", ">>", "1>>", "2>>"]

    for mode in modes:
        if mode in args:
            out_op_idx = args.index(mode)
            redirect_mode = mode
            break

    if out_op_idx != -1:
        filename = args[out_op_idx + 1]
        args = args[:out_op_idx]

    return (cmd, args, filename, redirect_mode)


def parse_command(command: str):
    cmd, args, filename, redirect_mode = parse_arguments(command)

    if redirect_mode == "1>" or redirect_mode == ">":
        file = open(filename, "w")
    elif redirect_mode == "2>":
        with open(filename, "w") as f:
            f.write("")
        file = sys.stderr
    elif redirect_mode == ">>" or redirect_mode == "1>>":
        file = open(filename, "a")
    elif redirect_mode == "2>>":
        with open(filename, "a") as f:
            f.write("")
        file = sys.stderr
    else:
        file = sys.stdout

    if cmd == "echo":
        print(" ".join(args), file=file)
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
                    file=file,
                )
            return

    if cmd in executables.keys():
        os.system(command)
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