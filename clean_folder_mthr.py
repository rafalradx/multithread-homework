# zadanie domowe koncowe z modulu 6
import sys
import shutil
import platform
import concurrent.futures
import logging

# from icecream import ic
from pathlib import Path


def create_dirs_for_sorting(path: Path, dirs_to_create: list[str]) -> dict[str:Path]:
    """creates folders for sorting if they do not exist already;
    returns a dictionary in a form of {'image':Path to image) to these folders;
    two approaches: for case-sensitive system (Linux) and case-insensitive systems (Macos i Windows)
    """
    # list of directories in a folder (paths and names separately)
    dirs = [child for child in path.iterdir() if child.is_dir()]
    dirnames = [child.name for child in dirs]
    result = {}
    if platform.system() == "Linux":  # case-sensitive system (no problems)
        for dir in dirs_to_create:
            new_path = path.joinpath(dir)
            result[dir] = new_path
            try:
                new_path.mkdir(exist_ok=False)
            except FileExistsError:
                continue

    else:  # Windows or Macos case-insensitive systems = problems!
        for dir in dirs_to_create:
            dirnames = [
                child.name.lower() for child in dirs
            ]  # change dirnames to lowercase then check if 'video', 'audio' etc present
            if dir in dirnames:
                result[dir] = dirs[
                    dirnames.index(dir)
                ]  # use existing dird and add their paths to dictionary
            else:
                new_path = path.joinpath(dir)  # if dont exist create them
                result[dir] = new_path
                try:
                    new_path.mkdir(exist_ok=False)
                except:
                    print("Error when creating directory")
                    continue
    return result


def sort_main_folder(
    dir_to_sort: Path,
    main_dir: Path,
    paths_to_sorting_dirs: dict[str:Path],
    ignore_dir_names: list[str],
) -> None:
    """moves files into folders specified for sorting based on their filename extension
    list of subdirectories are passed to thread pool"""
    # main dir content without ignored dirs
    dir_content = [
        child for child in dir_to_sort.iterdir() if child.name not in ignore_dir_names
    ]
    # subdirectories in main folder
    dir_list = [child for child in dir_content if child.is_dir()]

    logging.basicConfig(level=logging.DEBUG, format="%(threadName)s %(message)s")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(
            lambda x: sort_files_into_folders(
                x, main_dir, paths_to_sorting_dirs, ignore_dir_names
            ),
            dir_list,
        )

    # files in main directories moved directly in one thread
    file_list = [child for child in dir_content if not child.is_dir()]
    for file in file_list:
        new_path = where_to_move(file, paths_to_sorting_dirs)
        # move file with rename method
        file.rename(new_path)


def sort_files_into_folders(
    dir_to_sort: Path,
    main_dir: Path,
    paths_to_sorting_dirs: dict[str:Path],
    ignore_dir_names: list[str],
) -> None:
    """moves files into folders specified for sorting based on their filename extension"""
    dir_content = [
        child for child in dir_to_sort.iterdir() if child.name not in ignore_dir_names
    ]
    logging.debug(f"is working on - directory name: '{dir_to_sort.name}'")
    # loop over dir content
    for child in dir_content:
        if child.is_dir():
            # recursive call for subdirectory
            sort_files_into_folders(
                child, main_dir, paths_to_sorting_dirs, ignore_dir_names
            )
        else:
            new_path = where_to_move(child, paths_to_sorting_dirs)
            # move file with rename method
            child.rename(new_path)


def where_to_move(file: Path, paths_to_sorting_dirs: dict[str:Path]) -> Path:
    """determines where to move a file based on its extension that are looked up in dictionary.
    returns path to the directory. # if extension is not known returns path to unknown folder
    """
    global extensions
    # prepare output if extension unknown
    # normalize file names accordingly
    filename = normalize(file.stem)
    move_path = paths_to_sorting_dirs["unknown"].joinpath(filename + file.suffix)
    # check for extensions
    ext = file.suffix
    for dir_name, exts in extensions.items():
        if ext.lower() in exts:
            move_path = paths_to_sorting_dirs[dir_name].joinpath(filename + file.suffix)
    return move_path


def normalize(string: str) -> str:
    """takes a string and normalizes it with following rules:
    changes polish letters to regular letters,
    replaces other unussual (non-ascii) signs and symboles with underscore"""
    translate_polish = str.maketrans("ąęśćńżźółĄĘŚĆŃŻŹÓŁ", "aescnzzolAESCNZZOL")
    new_string = string.translate(translate_polish)
    # now list of chars!!!!
    new_string = [chr for chr in new_string]
    # replace non ascii parameters with underscore
    new_string = [chr if chr.isascii() else "_" for chr in new_string]
    # replace non alphanumeric parameters with underscore
    new_string = [chr if chr.isalnum() else "_" for chr in new_string]
    return "".join(new_string)


def prepare_output(paths_to_sorting_dirs: dict[str:Path]):
    """prints list of files in every directory after sorting,
    recognized and unrecognized extensions, omitts folders"""
    extensions = {}  # dictionary with sets
    file_name_categories = {}  # dictionary with lists
    for dir_name, dir_path in paths_to_sorting_dirs.items():
        name_list = []
        ext_set = set()
        for file in dir_path.iterdir():
            if not file.is_dir():
                name_list.append(file.name)
                ext_set.add(file.suffix.lower())
        if ext_set:
            extensions[dir_name] = ext_set
            file_name_categories[dir_name] = name_list
    return extensions, file_name_categories


def clean_up_dirs(dir_to_sort: Path, paths_to_sorting_dirs: dict[str:Path]) -> None:
    """removes empty subdirectories in folder"""
    # not empty sorting dirs
    ignore_dirs = [
        dirpath.name
        for dirpath in paths_to_sorting_dirs.values()
        if len([child for child in dirpath.iterdir()]) > 0
    ]
    # ic(ignore_dirs)
    # all dirs
    all_dirs = [child for child in dir_to_sort.iterdir() if child.is_dir()]
    # ic(all_dirs)
    dirs_to_remove = [child for child in all_dirs if child.name not in ignore_dirs]
    # ic(dirs_to_remove)
    for child in dirs_to_remove:
        rm_tree(child)
    return


def rm_tree(dir_path: Path):
    """Recursiverly remove empty subdirectories;
    checks if subdirs are empty"""
    content = [child for child in dir_path.iterdir()]
    if len(content) > 0:
        for child in content:
            if child.is_dir():
                rm_tree(child)
    try:
        dir_path.rmdir()
    except:
        print(f"Cannot delete {dir_path}")


def unpack_archives(archives_path: Path):
    if archives_path.exists():
        archv_to_unpack = [
            archv for archv in archives_path.iterdir() if not archv.is_dir()
        ]
        for child in archv_to_unpack:
            # folder to unpack
            unpack_path = child.parent.joinpath(child.stem)
            unpack_path.mkdir(exist_ok=True)
            try:
                shutil.unpack_archive(child, unpack_path)
            except:
                print(f"Unpack error. File: '{child.name}' is not an archive")
                continue
    return


def print_output(extensions, files):
    if not bool(extensions):
        print("Folder you specified has no files!")
        return
    print("Types of recognized files:")
    for category in extensions.keys():
        if category != "unknown":
            print(4 * " " + category + ":", extensions[category])
    if "unknown" in extensions.keys():
        print("Unrecognized files:")
        print(4 * " ", extensions["unknown"])

    print("\nFile names in each category: ")
    for category in files.keys():
        print(category + ":")
        [print(4 * " " + name) for name in files[category]]
    return


# Hard-coded data
# recognized filename extensions
images = (".jpeg", ".png", ".jpg", ".svg", ".tif", ".tiff")
video = (".avi", ".mp4", ".mov", ".mkv")
documents = (".doc", ".docx", ".txt", ".pdf", ".xlsx", ".pptx", ".odt", ".ods", ".odp")
audio = (".mp3", ".ogg", ".wav", ".amr")
archives = (".zip", ".gz", ".tar")

# dictionary of all known extenstion types
# global variable
extensions = {
    "images": images,
    "video": video,
    "documents": documents,
    "audio": audio,
    "archives": archives,
}


def main():
    # folders for sorting, names from keys of recognized extensions dictionary
    dirs_to_create = [key for key in extensions.keys()]

    # add unknown folder for unknown files
    dirs_to_create.append("unknown")

    # read path of a directory to be sorted
    try:
        dir_to_sort = sys.argv[1]
    except IndexError:
        print("Argument missing. Please specify path to a directory")
        quit()

    # create Path object (main path)
    main_dir = Path(dir_to_sort)

    # Checking if path exists and if it's not a file
    if main_dir.exists():
        if main_dir.is_file():
            print("Please specify path to a directory")
            quit()
    else:
        print("No such file or directory")
        quit()

    # create dirs to where sorted files will go
    paths_to_sorting_dirs = create_dirs_for_sorting(main_dir, dirs_to_create)
    # prepare list of directories to ignore (true names) all except unknown)
    # in Linux the names are the same is initial extension.key() (lowercase)
    # in Windows and Macos true names may differ
    ignore_dirs = [
        dirpath.name
        for lowcase_name, dirpath in paths_to_sorting_dirs.items()
        if not lowcase_name == "unknown"
    ]
    # sort the files and move them to dirs
    # sort_files_into_folders(main_dir, main_dir, paths_to_sorting_dirs, ignore_dirs)
    sort_main_folder(main_dir, main_dir, paths_to_sorting_dirs, ignore_dirs)
    # prepare sorted filesname list and recognized extension list found in sorted dir
    ext_output, file_names_output = prepare_output(paths_to_sorting_dirs)
    # clean up, remove empty directories
    clean_up_dirs(main_dir, paths_to_sorting_dirs)
    # unpack all archives
    unpack_archives(paths_to_sorting_dirs["archives"])
    # print the output
    print_output(ext_output, file_names_output)


# run main function
if __name__ == "__main__":
    main()
