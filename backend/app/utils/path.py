import os
import platform

# BaseDir
if platform.system() == "Windows":
    BASEAUX = os.path.dirname(os.path.realpath(__file__))
else:
    BASEAUX = os.path.dirname(os.path.realpath(__file__))

BASEDIR = os.path.abspath(os.path.join(BASEAUX, os.pardir, os.pardir))
PATHLOG = os.path.join(BASEDIR, "logs")
PATHUTILS = os.path.join(BASEDIR, "app", "utils")
PATHDATABASE = os.path.join(BASEDIR, "app", "database")


def create_dir_logs():
    if not os.path.exists(PATHLOG):
        os.makedirs(PATHLOG)


def get_path_log():
    return PATHLOG


def get_path_project():
    return BASEDIR
