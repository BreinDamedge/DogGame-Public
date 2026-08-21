"""
+---------------+
| !DataHoarding |
+---------------+

Authors: Jacob Ableidinger, Matt Loots
GitHub Usernames: BreinDamedge,
Date Documented: 11/19/2024
Description:
    - Contains implementation for manager object.
    - We can use this object to hold our datastructures together and make the systems play nice with one another
    as we continue to develop the project.
"""

import indexing, path_info, urllib, os, json
from parsing import PPS, get_file_extension, list_files
from parser import Parser
from mhtmlToHtml import mhtml_to_html_bytes
import ranking
from ranking import RankerBase
from metadata_crud import DocumentMetadataAPI


class Manager:
    def __init__(self, config_="default"):
        # systems/data structures
        self.dm_api: DocumentMetadataAPI = None
        self.parser: Parser = None
        self.indexes: list[indexing.InvertedIndexBase] = None
        self.ranker = None

        # here we would go through the config to set everything up, for now I'll leave it as a default one with one index and a dummy ranker
        if config_ == "default":
            self.dm_api = DocumentMetadataAPI()
            self.dm_api.kill_orphans()
            self.parser = Parser(
                PPS
            )  # [to_lowercase, to_alpha, clean_whitespace])    # should be a part of config, but maybe a field specific to each index
            self.parser.parse_corpus(self.dm_api)
            self.indexes = [
                indexing.DictionaryIndex(self.dm_api)
            ]  # dm api is not stored in index
            self.ranker: RankerBase = ranking.TitleRanker()
            self.ranker_id: str = "title"

    def set_ranker(self, rank_id_: str) -> None:
        RANKER_TABLE = {"title": ranking.TitleRanker, "tfidf": ranking.DocumentTFIDF}
        if rank_id_ != self.ranker_id:
            try:
                self.ranker = RANKER_TABLE[rank_id_]()
                self.ranker_id = rank_id_
                print(f"set_ranker: '{rank_id_}'")
            except KeyError:
                print(f"set_ranker: '{rank_id_}' not in table")

    def rescan_corpus(self) -> None:
        self.dm_api.kill_orphans()
        self.parser.parse_corpus(self.dm_api)
        self.indexes = [
            indexing.DictionaryIndex(self.dm_api)
        ]  # dm api is not stored in index

    def add_document(self, data_: bytes) -> None:
        import document_adding_helpers as dah

        print("Adding", len(data_))
        # first save to disk -> get file type, get UUID (for the file name)
        extension = get_file_extension(data_)
        UUID = dah.GenerateUUID4()

        # then save file with filename (UUID) + EXTENSION
        filename = UUID + "." + extension
        file_path = path_info.CORPUS_PATH + "/" + filename

        dah.save_file(data_, file_path)

        # Secondly parse it and index it
        # parse to dm file
        self.parser.file_to_datastore(filename, self.dm_api)

        # load metadata add it to indexes
        new_doc = self.dm_api.get(filename)
        for idx in self.indexes:
            idx.add_document(new_doc["text"], filename)

    def remove_document(self, id_: str) -> bool:
        """"""
        print("Deleting", id_)
        # id is brought in formatted as a url for some reason so first we convert it back

        file_path: str = path_info.CORPUS_PATH + "/" + urllib.parse.unquote(id_)

        if os.path.isfile(
            file_path
        ):  # if id is in corpus (can do blacklist checks here as well)
            os.remove(file_path)

            for idx in self.indexes:
                idx.remove_document(id_)

            self.dm_api.delete([id_])

            # successfully deleted
            return True

        else:
            # failed to delete
            return False

    def search_documents(self, query_: str, ranker_id_: str = "tfidf") -> list[dict]:
        """
        1. or search inverted index
        2. get the names of documents with these ids
        - add each to the list of docs
        3. return the list
        """
        self.set_ranker(ranker_id_)

        # retrieve
        doc_ids: set = set()
        for idx in self.indexes:
            for doc_id in idx.get_relevant_ids(query_):
                doc_ids.add(doc_id)

        # rank (order)
        score_id_tuples: list[tuple[float, str]] = self.ranker.rank(
            doc_ids, query_, self.dm_api, self.indexes
        )

        # get titles and organize data to send to the frontend
        docs: list[dict] = []

        for s_id in score_id_tuples:
            score_, id_ = s_id
            docs.append(
                {
                    "name": self.dm_api.get(id_)["title"],
                    "id": id_,
                    "score": score_,
                    "note": self.dm_api.get_note(id_),
                }
            )
        # send the data to the frontend
        return docs

    def open_document(self, id_: str) -> dict | None:
        """{"contents" : file_bytes:bytes, "type" : file_ext:str}"""
        # Get contents of a document AND its type (likeley mhtml, pdf, text)

        # id_ is brought in formatted as a url for some reason so first we convert it back
        file_on_disk_path: str = path_info.CORPUS_PATH + "/" + urllib.parse.unquote(id_)
        id_ = file_on_disk_path

        if os.path.isfile(
            id_
        ):  # if id is in corpus (can do blacklist checks here as well)
            with open(id_, "rb") as f:
                file_bytes: bytes = f.read()

            # get extention
            file_ext = get_file_extension(file_bytes)

            # sneaky mhtml test (if mhtml: convert to html)
            if file_ext == "mht":
                # Vadim Cooked.
                file_bytes = mhtml_to_html_bytes(file_bytes)
                file_ext = "html"

            return {"contents": file_bytes, "type": file_ext}
        else:
            return None

    def corpus_size_info(self) -> tuple[int, int, int]:
        """(files in corpus, rows in metadata store, unique ids in indexes)"""
        indexed_file_ids_ = set()
        for idx in self.indexes:
            indexed_file_ids_.update(idx.get_ids())
        return (
            len(list_files(path_info.CORPUS_PATH)),
            self.dm_api.num_rows(),
            len(indexed_file_ids_),
        )

    def metadata_for_visualiation(self) -> str:
        """retrieve every single piece of metadata and send it as a json str. serialized obj is of type list[tuple[str, str]]"""
        return json.dumps(self.dm_api.get_all_no_convert())

    def index_for_visualization(self) -> str:
        """serialize the first index in the manager"""
        return json.dumps(self.indexes[0].data)


if __name__ == "__main__":
    pass
