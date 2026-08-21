"""
+---------------+
| !DataHoarding |
+---------------+

Author: Jacob Ableidinger,
GitHub Username: BreinDamedge,
File Name: document_renaming.py
Date Documented: 11/05/2024
Description:
    - renames files in our corpus when run. Updated to check if files are already
    assigned a uuid4 as their name before renaming them. it now only updates file names
    if they are not already a uuid4.
    - You should add a confirm stage before all the renaming actually happens that shows your changes
"""

import uuid, os, path_info
from parsing import list_files_with_extention, list_files


def is_uuid4(file_name_: str) -> bool:
    uuid_string: str = file_name_.split(".")[0]
    try:
        # Convert the string to a UUID object, assuming it's in UUID4 format
        val = uuid.UUID(uuid_string, version=4)
    except ValueError:
        # Raised if uuid_string is not valid or not a UUID
        return False
    # Check if the formatted string is the same as the input to confirm proper format
    return str(val) == uuid_string


def id_str() -> str:
    return str(uuid.uuid4())


def setup_metadata() -> None:
    """if the metadata path doesn't exist, create it"""
    if not os.path.exists(path_info.METADATA_PATH):
        os.makedirs(path_info.METADATA_PATH)


def rename_non_uuid_files() -> None:
    print("Assigning file_ids...")
    for file_name in list_files(path_info.CORPUS_PATH):
        # skip this file if it's already a uuid
        if is_uuid4(file_name):
            continue

        # rename file in corpus
        extention: str = file_name.split(".")[-1]
        new_name: str = f"{id_str()}.{extention}"
        print(f"{file_name} -> {new_name}")
        os.rename(
            f"{path_info.CORPUS_PATH}/{file_name}",
            f"{path_info.CORPUS_PATH}/{new_name}",
        )

        # also rename any files in metadata that are for this file
        ascociated_metadata_path: str = (
            path_info.METADATA_PATH + "/" + file_name + ".dm"
        )
        if os.path.exists(ascociated_metadata_path):
            os.rename(
                ascociated_metadata_path, f"{path_info.METADATA_PATH}/{new_name}.dm"
            )


def delete_orphaned_metadata() -> None:
    print("Deleting Orphans...")
    for dm_file_name in list_files_with_extention(path_info.METADATA_PATH, "dm"):
        if not os.path.exists(f"{path_info.CORPUS_PATH}/{dm_file_name[:-3]}"):
            print(f"'{path_info.METADATA_PATH}/{dm_file_name}'")
            os.remove(f"{path_info.METADATA_PATH}/{dm_file_name}")


def corpus_size() -> int:
    return len(list_files(path_info.CORPUS_PATH))


if __name__ == "__main__":
    pass

    # rename_non_uuid_files()

    """
    HEY YOU YES YOU:
    so I thought I had is that you can take the whole "do the big rename" section and wrap it into the program
    startup process. it should involve renaming any documents that need it and then also cleaning up the metadata folder
    (deleting any metadata (or just renaming it) for any files that just had their names changed)

    *on second thought adding a "corpus/metadata cleanup/validation" step to startup sounds like a great idea.
    """

    # loop through the corpus and assign all files uuid who don't already have them. (using uuid4)
    print(f"Corpus contains {corpus_size()} documents")

    delete_orphaned_metadata()
