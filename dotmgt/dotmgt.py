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


log = lambda msg: print("-", msg)


# TODO : Update
config_path = "dot_files"
txtpp = "txtpp/src/txtpp.py"
default_preproc_path = "/tmp/dotmgt"
dot_deffile = f"{config_path}/deffile.py"


def convert_path(path):
    if path[:1] == "/":
        return path
    else:
        return os.path.expanduser(f"~/{path}")


def iter_conf():
    """
    Iterates through all config files
    - yields user_config_path, dot_config_path, dot_file_id
    """
    ignored = ["config.yml", "deffile.py"]

    conf = f"{config_path}/config.yml"

    with open(conf, "r") as f:
        conf = yaml.load(f, Loader=yaml.CLoader)

    files = conf["files"]

    if "ignored" in conf:
        ignored += conf["ignored"]

    for file in glob.glob(f"{config_path}/*"):
        # Ignore directories...
        if not os.path.isfile(file):
            continue

        file_name = file[len(f"{config_path}/") :]

        if file_name in ignored:
            continue

        if file_name not in files:
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
    # TODO : Def file
    ret = os.system(f"'{txtpp}' --deffile '{dot_deffile}' '{dot}' > '{target}'")

    if ret != 0:
        raise DotManagementError(f"Failed to run txtpp on {dot} (exit code: {ret})")


def diff_file(user, dot, quiet=False):
    """
    - Returns the exit code of the diff program
    """
    preproc_dot(dot)

    if os.path.exists(user):
        quiet_cmd = "2>&1 > /dev/null" if quiet else ""

        return os.system(f"diff --color '{user}' '{default_preproc_path}' " + quiet_cmd)
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
        shutil.copyfile(default_preproc_path, user)
        log(f"update: [{dot_id}] {user}")

        return True
    else:
        return False


def cli_help():
    print("usage:")
    print("dotmgt [diff | d]")
    print("\tCompare between user config and dot files")
    print("dotmgt [update | u]")
    print("\tUpdate user config with dot files")


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


if __name__ == "__main__":
    if len(sys.argv) == 2:
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
        else:
            cli_help()
            exit(2)
    else:
        cli_help()
        exit(2)
