import importlib
import os
import subprocess
import types
from datetime import datetime

DEFAULT_MODULES = ["config_stp", "config_um", "config_stp_wcc", "config_stp_esc", "etc_wcc", "etc_esc"]


def imports(g_imports):
    """
    Extracts the names of modules currently imported in the global namespace.

    Parameters
    ----------
    g_imports : Iterable[Tuple[str, Any]]
        Typically `globals().items()` — a list of global names and their objects.

    Returns
    -------
    List[str]
        Top-level names of modules currently imported.
    """
    return [val.__name__.split(".")[0] for name, val in g_imports if isinstance(val, types.ModuleType)]


def check_imports_and_versions(g_imports, modules_to_check=None, verbose=False, output_file=None):
    """
    Checks import status, installed versions, Git branch, and "dirty" status for a list of modules.

    Parameters
    ----------
    g_imports : Iterable[Tuple[str, Any]]
        Usually `globals().items()`, used to check what's already imported.
    modules_to_check : List[str], optional
        List of module names to inspect. Defaults to DEFAULT_MODULES.
    verbose :(bool, optional
        If True, prints helpful warnings when Git info is missing.
    output_file : str, optional
        If provided, writes the formatted table to this file path.

    Returns
    -------
    str
        A pretty-printed table as a string showing the inspection results.
        | exception if modules_to_check is not a list
    """
    if modules_to_check is None:
        modules_to_check = DEFAULT_MODULES

    try:
        assert type(modules_to_check) is list, "modules_to_check is not a list"
    except AssertionError as e:
        return print(f"Assertion failed: {e}")

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

    pretty_table = generate_pretty_table(data)

    print(pretty_table)

    if output_file:
        with open(output_file, "w") as f:
            f.write(pretty_table)
        if verbose:
            print(f"Table written to: {output_file}")

    return pretty_table


def find_git_root(path):
    """
    Traverses upward from a directory path to find the root of a Git repository.
    Once we get the path to root of the repo for a module, can run 'git rev-parse'

    Parameters
    ----------
    path : str
        Starting directory path.

    Returns
    -------
    str | None
        Path to the Git root if found, otherwise None.
    """
    while path and path != os.path.dirname(path):
        if os.path.isdir(os.path.join(path, ".git")):
            return path
        path = os.path.dirname(path)
    return None


def get_git_branch(git_dir):
    """
    Gets the current Git branch name for a given Git repository directory.

    Parameters
    ----------
    git_dir : str
        Path to the root of a Git repository.

    Returns
    -------
    str
        The current Git branch name, or "Unknown" if it cannot be determined.
    """
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
    """
    Determines if a version string ends in a 'dYYYYMMDD' tag, which indicates a dirty Git state.

    Parameters
    ----------
    version_str : str
        A version string, typically from importlib.metadata.version(module)

    Returns
    -------
    bool
        True if the version string indicates a dirty repo, False otherwise.
    """
    if len(s) < 9 or s[-9] != "d":
        return False
    try:
        datetime.strptime(s[-8:], "%Y%m%d")
        return True
    except ValueError:
        return False


def generate_pretty_table(data):
    """
    Generates a formatted table string from inspection data, with dynamic column widths.

    Parameters
    ----------
    data : dict
        Dictionary with keys: "Module", "Imported", "Installed_Version", "Branch", "is_dirty()?".

    Returns
    -------
    str
        A formatted multi-line string displaying the data as a table.
    """
    headers = ["Module", "Imported", "Installed_Version", "Branch", "is_dirty()?"]

    # Put rows (including header) into column-wise lists
    columns = [
        [headers[0]] + data["Module"],
        [headers[1]] + [str(x) for x in data["Imported"]],
        [headers[2]] + data["Installed_Version"],
        [headers[3]] + data["Branch"],
        [headers[4]] + [str(x) for x in data["is_dirty()?"]],
    ]

    # Generate correct width dynamically
    widths = [max(len(str(cell)) for cell in col) for col in columns]

    def format_row(row_items):
        return " ".join(str(item).ljust(width) for item, width in zip(row_items, widths))

    # Header and separator line
    lines = [format_row(headers), format_row(["-" * w for w in widths])]

    # Data rows
    num_rows = len(data["Module"])
    for i in range(num_rows):
        row = [
            data["Module"][i],
            str(data["Imported"][i]),
            data["Installed_Version"][i],
            data["Branch"][i],
            str(data["is_dirty()?"][i]),
        ]
        lines.append(format_row(row))

    return "\n".join(lines)
