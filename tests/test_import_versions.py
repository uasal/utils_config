import importlib
import os
import subprocess
import types
from datetime import datetime

import pytest


def imports(g_imports):
    module_list = []
    for name, val in g_imports:
        if isinstance(val, types.ModuleType):
            module_list.append(val.__name__.split(".")[0])
    return module_list


def check_imports_and_versions(g_imports, modules_to_check, output_file, verbose=False):
    imported_modules = imports(g_imports)

    data = {"Module": [], "Imported": [], "Installed_Version": [], "Branch": [], "is_dirty()?": []}

    for module in modules_to_check:
        imported = module in imported_modules
        version = "Not_Installed"
        branch = "N/A"

        if importlib.util.find_spec(module) is not None:
            try:
                version = importlib.metadata.version(module)

                # Get module's path for git branch
                module_spec = importlib.util.find_spec(module)
                if module_spec and module_spec.origin:
                    module_dir = os.path.dirname(module_spec.origin)
                    git_dir = find_git_root(module_dir)
                    if git_dir:
                        branch = get_git_branch(git_dir)

            except Exception as e:
                version = str(e)

        data["Module"].append(module)
        data["Imported"].append(imported)
        data["Installed_Version"].append(version)
        data["Branch"].append(branch)
        data["is_dirty()?"].append(check_git_dirty_repo_tag(version))

    write_table(output_file, data)
    if verbose:
        print(f"Results written to {output_file}")
    return data


def find_git_root(path):
    """Traverse up to find .git directory"""
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
    date_str = s[-8:]
    try:
        datetime.strptime(date_str, "%Y%m%d")
        return True
    except ValueError:
        return False


def write_table(file_path, data):
    with open(file_path, "w") as f:
        import_string = [str(b) for b in data["Imported"]]
        is_dirty_string = [str(b) for b in data["is_dirty()?"]]
        branch_string = [str(b) for b in data["Branch"]]
        mod_list = pad_strings(data["Module"], "Module")
        imported_list = pad_strings(import_string, "Imported")
        installed_list = pad_strings(data["Installed_Version"], "Installed_Version")
        branch_list = pad_strings(branch_string, "Branch")
        is_dirty_list = pad_strings(is_dirty_string, "is_dirty()?")

        for i in range(len(mod_list)):
            f.write(
                f"{mod_list[i]} {imported_list[i]} {installed_list[i]} {branch_list[i]} {is_dirty_list[i]}\n"
            )


def pad_strings(strings, header):
    strings_with_header = [header] + strings
    max_length = max(len(s) for s in strings_with_header)
    padded_list = [s.ljust(max_length) for s in strings_with_header]
    padded_list.insert(1, "-" * max_length)
    return padded_list


# =======================
# 🧪 Pytest Regression Test
# =======================


@pytest.mark.parametrize(
    "modules_to_check", [["config_stp", "config_um", "config_stp_wcc", "config_stp_esc", "etc_wcc"]]
)
def test_check_imports_and_versions(modules_to_check):
    output_file = os.path.join(os.path.dirname(__file__), "expected_outputs", "module_versions.txt")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    data = check_imports_and_versions(globals().items(), modules_to_check, output_file)

    assert os.path.exists(output_file)

    assert len(data["Module"]) == len(modules_to_check)
    assert set(data["Module"]) == set(modules_to_check)

    for version in data["Installed_Version"]:
        assert isinstance(version, str)

    for branch in data["Branch"]:
        assert isinstance(branch, str)

    for dirty_flag in data["is_dirty()?"]:
        assert isinstance(dirty_flag, bool)
