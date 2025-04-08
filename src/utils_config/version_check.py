import importlib
import os
import subprocess
import types
from datetime import datetime

DEFAULT_MODULES = ["config_stp", "config_um", "config_stp_wcc", "config_stp_esc", "etc_wcc", "etc_esc"]


def imports(g_imports):
    return [val.__name__.split(".")[0] for name, val in g_imports if isinstance(val, types.ModuleType)]


def check_imports_and_versions(g_imports, modules_to_check=None, verbose=False):
    if modules_to_check is None:
        modules_to_check = DEFAULT_MODULES

    imported_modules = imports(g_imports)

    data = {"Module": [], "Imported": [], "Installed_Version": [], "Branch": [], "is_dirty()?": []}

    for module in modules_to_check:
        imported = module in imported_modules
        version = "Not_Installed"
        branch = "N/A"

        if importlib.util.find_spec(module):
            try:
                version = importlib.metadata.version(module)
                module_spec = importlib.util.find_spec(module)
                if module_spec and module_spec.origin:
                    git_dir = find_git_root(os.path.dirname(module_spec.origin))
                    if git_dir:
                        branch = get_git_branch(git_dir)
            except Exception as e:
                version = str(e)

        data["Module"].append(module)
        data["Imported"].append(imported)
        data["Installed_Version"].append(version)
        data["Branch"].append(branch)
        data["is_dirty()?"].append(check_git_dirty_repo_tag(version))

    pretty_print_table(data)
    return None  # No return value


def find_git_root(path):
    while path and path != os.path.dirname(path):
        if os.path.isdir(os.path.join(path, ".git")):
            return path
        path = os.path.dirname(path)
    return None


def get_git_branch(git_dir):
    try:
        result = subprocess.run(
            ["git", "-C", git_dir, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "Unknown"


def check_git_dirty_repo_tag(s):
    if len(s) < 9 or s[-9] != "d":
        return False
    try:
        datetime.strptime(s[-8:], "%Y%m%d")
        return True
    except ValueError:
        return False


def pretty_print_table(data):
    headers = ["Module", "Imported", "Installed_Version", "Branch", "is_dirty()?"]
    widths = [14, 8, 20, 32, 11]

    def format_row(row_items):
        return " ".join(str(item).ljust(width) for item, width in zip(row_items, widths))

    print(format_row(headers))
    print(format_row(["-" * w for w in widths]))

    for i in range(len(data["Module"])):
        row = [
            data["Module"][i],
            str(data["Imported"][i]),
            data["Installed_Version"][i],
            data["Branch"][i],
            str(data["is_dirty()?"][i]),
        ]
        print(format_row(row))
