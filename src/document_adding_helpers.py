"""
+---------------+
| !DataHoarding |
+---------------+

Author: Matt Loots
File Name: document_adding_helpers.py
Date Documented: 11/19/2024
Description:
    - functions for adding documents
"""

from uuid import uuid4


##############################################################
# Getting the file type
##############################################################


# looked up different file type magic number and created a dictionary to use
def GetFileType(data):
    # Define some common file signatures (magic numbers)
    file_codes = {
        b"%PDF-": "pdf",
        b"MIME-Version: 1.0\r\nContent-Type: multipart/related;": "mhtml",
    }

    # Check the file's bytes against known signatures
    for signature, file_type in file_codes.items():
        if data.startswith(signature):
            return file_type

    # Check for plain text files (basic heuristic)
    if all(32 <= byte <= 126 or byte in (9, 10, 13) for byte in data):
        return "txt"

    raise TypeError("Unknown file type")


##############################################################


##############################################################
# Generating UUID
##############################################################
def GenerateUUID4() -> str:
    return str(uuid4())


##############################################################


##############################################################
# Saving to disk
##############################################################


def save_file(file_bytes, file_path):
    """
    Saves binary data to a specified file path.

    Parameters:
        file_bytes (bytes): The binary content to save.
        file_path (str): The path where the file will be saved.
    """
    try:
        with open(file_path, "wb") as file:
            file.write(file_bytes)
        print(f"File saved successfully to {file_path}")
    except IOError as e:
        print(f"Error saving file: {e}")


# Example usage
# file_data = b"Sample file content"
# save_file(file_data, "sample_file.txt")

##############################################################


if __name__ == "__main__":
    pass
    # example of how to use
    with open("example_file", "rb") as file:
        data = file.read(10)  # Read the first 10 bytes
        file_type = GetFileType(data)
        print(f"File type: {file_type}")
