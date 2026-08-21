from parsing import (
    parse_mhtml_file,
    parse_pdf_file,
    parse_text_file,
    list_files,
    to_lowercase,
    to_alpha,
    clean_whitespace,
)
from typing import Callable
from metadata_crud import DocumentMetadataAPI
import path_info
from multiprocessing import Pool


def parsing_delegate(file_id_: str, pps_: list[Callable[[str], str]]) -> dict:
    file_path: str = path_info.CORPUS_PATH + "/" + file_id_
    print(f"Parsing '{file_path}'")

    # file extention
    ext: str = file_path.split(".")[-1]

    if ext == "mhtml" or ext == "mht":
        return parse_mhtml_file(file_path, pps_)
    elif ext == "pdf":
        return parse_pdf_file(file_path, pps_)
    elif ext == "txt":
        return parse_text_file(file_path, pps_)
    else:
        print(f"Skipping {file_path} : (Unsupported Extention: '.{ext}')")


def chunk_list(list_: list, chunk_size_: int) -> list[list]:
    out = []
    start = 0
    while True:
        end = start + chunk_size_
        if end >= len(list_):
            end = len(list_) - 1
        out.append(list_[start:end])
        if end == len(list_) - 1:
            break
        start = end
    return out


class Parser:
    def __init__(self, pps_: list[Callable[[str], str]]):
        self.pps: list[Callable[[str], str]] = pps_

    def file_to_metadata(self, file_id_: str) -> dict:
        return parsing_delegate(file_id_, self.pps)

    def file_to_datastore(
        self, file_id_: str, datastore_: DocumentMetadataAPI
    ) -> None:  # int:
        """parse file and store it in a datastore"""
        datastore_.create(self.file_to_metadata(file_id_))

    def parse_corpus(self, datastore_: DocumentMetadataAPI) -> None:
        """make a metadata file for everything in the corpus that doesn't already have one"""

        files_to_parse: set[str] = set(list_files(path_info.CORPUS_PATH))
        files_to_parse = files_to_parse.difference(set(datastore_.get_ids()))

        NUM_PROCESSES = 16
        CHUNK_SIZE = 500
        BATCH_THRESHOLD = 10

        if len(files_to_parse) >= BATCH_THRESHOLD:
            files_to_parse = list(
                files_to_parse
            )  # a bit cringe but we're low on time and this should make chopping it up easier
            # setup the pool
            p = Pool(NUM_PROCESSES)

            for chunk in chunk_list(files_to_parse, CHUNK_SIZE):
                # process
                out = p.starmap(
                    parsing_delegate, zip(chunk, [self.pps for _ in range(len(chunk))])
                )

                # push the parsed files to the db
                datastore_.create_many(out, p)

            # free the pool
            del p
        else:
            # process each file
            for file_name in files_to_parse:
                # check if the file metadata is already saved
                self.file_to_datastore(file_name, datastore_=datastore_)


if __name__ == "__main__":
    pass
    from parsing import PPS, list_files

    p = Parser(PPS)
    p.parse_corpus(DocumentMetadataAPI())

