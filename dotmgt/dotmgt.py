#!/usr/bin/env python3

import glob
import os
import sys
import shutil
import yaml
import subprocess as sp


class DotManagementError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


def init_dot_files():
    cwd = os.path.realpath('.')

    with open(dot_config_path, 'w') as f:
        f.write(cwd + '\n')

    if not os.path.exists('.git') and os.system('git init') != 0:
        print('Cannot initialize git repository')
        exit(1)

    with open('config.yml', 'w') as f:
        print('# Sample config.yml for your dot files', file=f)
        print('# files:', file=f)
        print('#   i3: .config/i3/config', file=f)
        print('# directories:', file=f)
        print('#   alacritty_themes: .config/alacritty/themes', file=f)
        print('# ignored:', file=f)
        print('#   vimrc', file=f)

    print('Initialized dot files at', cwd)
    print('Saved config at', dot_config_path)
    exit()


log = lambda msg: print("-", msg)

home_path = os.path.abspath(
        os.path.expanduser('~')
        if not 'DOTMGT_HOME_PATH' in os.environ
        else os.environ['DOTMGT_HOME_PATH'])
dot_config_path = home_path + '/.config/dotmgt.conf'

# Init command
if len(sys.argv) == 2 and sys.argv[1] == 'init':
    init_dot_files()

if not os.path.exists(dot_config_path):
    print(f'No config found at {dot_config_path}', file=sys.stderr)
    print('Use `dotmgt init` to initialize the dot files at the current directory', file=sys.stderr)
    print('The home directory can be overriden by the environment variable DOTMGT_HOME_PATH (used for sudo)')

    exit(1)

with open(dot_config_path, 'r') as f:
    config_path = f.read().strip()

txtpp = "/usr/bin/txtpp"
default_preproc_path = "/tmp/dotmgt"
dot_deffile = f"{config_path}/deffile.py"


if not os.path.exists(dot_deffile):
    dot_deffile = None


def convert_path(path):
    if path[:1] == "/":
        return path
    else:
        return f'{home_path}/{path}'


def iter_conf():
    """
    Iterates through all config files
    - yields user_config_path, dot_config_path, dot_file_id
    """
    ignored = ["config.yml", "deffile.py", "__pycache__"]

    conf = f"{config_path}/config.yml"

    with open(conf, "r") as f:
        conf = yaml.load(f, Loader=yaml.CLoader)

    # Read config files
    files = conf["files"]
    dirs = conf["directories"] if "directories" in conf else dict()

    if "ignored" in conf:
        ignored += conf["ignored"]

    # Read files within config directory
    paths = []
    for file in glob.glob(f"{config_path}/*"):
        file_name = file[len(f"{config_path}/") :]

        if file_name in ignored:
            continue

        if os.path.isdir(file):
            paths += walk_files(file)
        elif os.path.isfile(file):
            paths.append(file)

    for file in paths:
        file_name = file[len(f"{config_path}/") :]

        # Wether this file is within a directory
        subfile = '/' in file_name

        # Add file within directory
        if subfile:
            dir_name = file_name[:file_name.index('/')]
            subpath = file_name[file_name.index('/') + 1:]

            if dir_name in dirs:
                dir_name = dirs[dir_name]
            else:
                # No custom path
                dir_name = f".config/{dir_name}"

            files[file_name] = dir_name + '/' + subpath
        elif file_name not in files:
            # Add file at root
            path = f".{file_name}" if file_name[:1] != "." else file_name
            files[file_name] = path

    for dot_file in files:
        dot_path = f"{config_path}/{dot_file}"
        user_path = convert_path(files[dot_file])

        yield user_path, dot_path, dot_file


def preproc_dot(dot, target=default_preproc_path):
    """
    Preprocesses the dot config file
    """
    deffile = f"--deffile '{dot_deffile}'" if dot_deffile is not None else ""

    ret = os.system(f"cd '{config_path}' && '{txtpp}' {deffile} '{dot}' > '{target}'")

    if ret != 0:
        raise DotManagementError(f"Failed to run txtpp on {dot} (exit code: {ret})")


def diff_file(user, dot, quiet=False):
    """
    - Returns the exit code of the diff program
    """
    preproc_dot(dot)

    if os.path.exists(user):
        quiet_cmd = "2>&1 > /dev/null" if quiet else ""

        return os.system(f"cd '{config_path}' && diff --color '{user}' '{default_preproc_path}' " + quiet_cmd)
    else:
        if not quiet:
            print(f"{user} does not exist", file=sys.stderr)

        return 1


def update_file(user, dot, dot_id):
    """
    - Returns whether the file has been updated (the content was different)
    """
    preproc_dot(dot)

    if diff_file(user, dot, quiet=True) != 0:
        os.makedirs(os.path.dirname(user), exist_ok=True)
        shutil.copyfile(default_preproc_path, user)
        log(f"update: [{dot_id}] {user}")

        return True
    else:
        return False


def cli_help():
    print("usage:")
    print("dotmgt init")
    print("\tInit dot files")
    print("dotmgt [diff | d]")
    print("\tCompare between user config and dot files")
    print("dotmgt [update | u]")
    print("\tUpdate user config with dot files")
    print("dotmgt [commit | c] [<commit-message>]")
    print("\tCommit in the dot files directory")
    print("dotmgt [push | p] [<commit-message>]")
    print("\tCommit and push in the dot files directory")
    print("dotmgt pull")
    print("\tPull in the dot files directory")
    print("dotmgt [backup | b] <path>")
    print("\tCreate a backup of the current user dot files (not within the dot files directory) at path")
    print("dotmgt [list | l]")
    print("\tList every config file path")
    print()
    print("config path:", config_path)


def cli_diff():
    ret = 0
    for user, dot, dot_id in iter_conf():
        print("*", dot_id)
        if diff_file(user, dot) != 0:
            print(f"----- {dot_id} -----\n")
            ret = 1

    return ret


def cli_update():
    for user, dot, dot_id in iter_conf():
        update_file(user, dot, dot_id)

    print("Config updated")


def run_cmd(args):
    if sp.call(args, cwd=config_path) != 0:
        raise DotManagementError('Failed to launch command ' + ' '.join(args))


def cli_commit(msg):
    run_cmd(['git', 'add', '--all'])
    run_cmd(['git', 'commit', '-m', msg])


def cli_push(msg):
    if msg:
        cli_commit(msg)

    run_cmd(['git', 'push'])


def cli_pull():
    run_cmd(['git', 'pull'])


def cli_status():
    run_cmd(['git', 'status'])


def cli_list():
    ls = lambda user, dot, dot_id: print(f'{dot_id:24s} -> {user}')
    ls('User Path', 'Dot Path', 'Id')
    print()
    for user, dot, dot_id in iter_conf():
        ls(user, dot, dot_id)


def cli_backup(path):
    if os.path.exists(path):
        print(path, 'already exist', file=sys.stderr)

        exit(1)

    os.makedirs(path)

    err = 0

    for user, dot, dot_id in iter_conf():
        try:
            if os.path.exists(user):
                dest = f'{path}/{dot_id}'
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copyfile(user, dest)
                print(dot_id)
            else:
                print(f'* Warning: {dot_id} does not exist (should be at location {user})', file=sys.stderr)
        except:
            print(f'* Error: Failed to copy {dot_id} (at location {user})', file=sys.stderr)
            err = 1

    if err:
        print('PARTIALY backed up at', path, file=sys.stderr)
        exit(err)

    print('> Backed up at', path)


def walk_files(path):
    """
    Returns all files within a directory recursively

    - If path is a file, returns a singleton list containing only path
    """
    if not os.path.isdir(path):
        return [path]

    paths = []
    for dirpath, _, files in os.walk(path):
        for f in files:
            paths.append(dirpath + '/' + f)

    return paths


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        cli_help()
        exit(2)

    if sys.argv[1] in ("push", "p"):
        cli_push(None if len(sys.argv) == 2 else sys.argv[2])
    elif len(sys.argv) == 2:
        # TODO : Indicate in diff that < is user file and > is config file
        # TODO : Fetch command that cp user to dot
        # TODO : Push / commit / pull
        cmd = sys.argv[1]
        if cmd in ("help", "h", "--help", "-h"):
            cli_help()
        elif cmd in ("diff", "d"):
            cli_diff()
        elif cmd in ("update", "u"):
            cli_update()
        elif cmd in ("status", "s"):
            cli_status()
        elif cmd == "pull":
            cli_pull()
        elif cmd in ("list", "l"):
            cli_list()
        else:
            cli_help()
            exit(2)
    elif len(sys.argv) == 3 and sys.argv[1] in ("commit", "c"):
        cli_commit(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] in ("backup", "b"):
        cli_backup(sys.argv[2])
    else:
        cli_help()
        exit(2)
