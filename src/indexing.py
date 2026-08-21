"""
+---------------+
| !DataHoarding |
+---------------+

Date Documented: 11/05/2024
Description:
    - renames files in our corpus when run. Updated to check if files are already
    assigned a uuid4 as their name before renaming them. it now only updates file names
    if they are not already a uuid4.
    - You should add a confirm stage before all the renaming actually happens that shows your changes
"""

from parsing import list_files, stemmed_keywords
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json, os, path_info
from metadata_crud import DocumentMetadataAPI


@dataclass
class document:
    id: str
    content: str


class InvertedIndexBase(ABC):
    @abstractmethod
    def add_document(self, content_: str, document_id_: str) -> None:
        """given document content and that document's id, add it to the index"""
        ...

    @abstractmethod
    def remove_document(self, document_id_: str) -> None:
        """remove a document from the index. once removed the document id should not appear in results of search"""
        ...

    @abstractmethod
    def get_relevant_ids(self, query_: str) -> set[str]:
        """given a query return a set of relavent document ids"""
        ...

    @abstractmethod
    def get_ids(self) -> set[str]:
        """return every id in the dictionary"""
        ...

    def archive_file_name(self) -> str:
        return self.__class__.__name__ + ".idx"


class DictionaryIndex(InvertedIndexBase):
    def __init__(self, datastore_: DocumentMetadataAPI):
        self.data: dict[str, set[str]] = {}
        self.document_ids: set[str] = set()
        self.removed_ids: set[str] = set()

        # initialize the index:
        self.from_idx(datastore_=datastore_)

    def add_document(self, content_: str, document_id_: str) -> None:
        """given document content and that document's id, add it to the index"""
        # don't add it if it's already there
        if document_id_ in self.document_ids:
            return

        for kw in stemmed_keywords(content_):
            try:
                self.data[kw].add(document_id_)
            except AttributeError:
                self.data[kw] = set(self.data[kw])
                self.data[kw].add(document_id_)
            except KeyError:
                self.data[kw] = {
                    document_id_
                }  # set containing just the document id, not string to set

        self.document_ids.add(document_id_)

    def remove_document(self, document_id_: str) -> None:
        """remove a document from the index. once removed the document id should not appear in results of search"""
        if document_id_ in self.document_ids:
            self.removed_ids.add(document_id_)

    def get_relevant_ids(self, query_: str) -> set[str]:
        """given a query return a set of relavent document ids"""
        ids: set[str] = set()

        for kw in stemmed_keywords(query_):
            try:
                ids_to_remove: list[str] = []
                for id in self.data[kw]:
                    # check to make sure the value hasn't been removed
                    if id in self.removed_ids:
                        ids_to_remove.append(self.data[kw])
                    # otherwise just add it to the relevent_ids set
                    else:
                        ids.add(id)

                for id in ids_to_remove:
                    if id in self.data[kw]:
                        self.data[kw].remove(id)

            # if the keyword isn't in the index
            except KeyError:
                continue
        return ids

    def to_idx(self) -> None:
        # before you save, clean up any removed ids from the data structure.
        if len(self.removed_ids) > 0:
            for kw in self.data.keys():
                for id in self.removed_ids:
                    if id in self.data[kw]:
                        self.data[kw].remove(id)

            for id in self.removed_ids:
                if id in self.document_ids:
                    self.document_ids.remove(id)

        self.prune()

        # convert this object into a dict and then save it
        # to serialize we can't serialize a set so convert the sets to lists and then serialize
        for k in self.data.keys():
            self.data[k] = list(self.data[k])

        data: dict = {"data": self.data, "document_ids": list(self.document_ids)}

        # figure out where to write the file and write it
        # create the metadata dir if it doesn't exist
        if not os.path.exists(path_info.METADATA_PATH):
            os.makedirs(path_info.METADATA_PATH)

        idx_file_name: str = path_info.METADATA_PATH + "/" + self.archive_file_name()
        with open(idx_file_name, "w") as f:
            json.dump(data, f, indent=4, default=lambda o: o.__dict__)

    def from_idx(self, datastore_: DocumentMetadataAPI) -> None:
        file_name: str = path_info.METADATA_PATH + "/" + self.archive_file_name()
        if os.path.exists(file_name):
            # load the data
            with open(file_name, "r") as f:
                data: dict = json.load(f)

            # set the fields
            self.data = data["data"]
            for k in (
                self.data.keys()
            ):  # convert the lists back to sets for speed at runtime
                if type(self.data[k]) == type(str):
                    self.data[k] = {self.data[k]}
                    if type(self.data[k]) != type(set()):
                        raise TypeError(
                            "Index field loaded in as single string and failed to convert to set"
                        )
                elif type(self.data[k]) == type(list()):
                    self.data[k] = set(self.data[k])
                else:
                    raise TypeError(
                        f"field '{k}' in index is type '{type(self.data[k])}'"
                    )
            self.document_ids = set(data["document_ids"])
            self.removed_ids = set()

        # once we've loaded the document, if there's any documents not in the index, go through and add them now!
        new_file_ids: set[str] = set(datastore_.get_ids()).difference(self.document_ids)

        for file_id in new_file_ids:
            try:
                doc_metadata: dict = datastore_.get(file_id)
                self.add_document(doc_metadata["text"], doc_metadata["file_id"])
            except TypeError:
                raise LookupError(
                    f"failed to retrieve metadata from datastore. '{file_id}'"
                )

        # finally, if any documents were removed while we weren't looking, make sure we get rid of those:
        sneaky_file_ids: set[str] = set(self.document_ids).difference(
            set(datastore_.get_ids())
        )
        for file_id in sneaky_file_ids:
            self.remove_document(file_id)

        # Save the json for next time
        self.to_idx()

    def get_ids(self) -> set[str]:
        """return every id in the dictionary"""
        return self.document_ids  # document ids might contain ids that have been removed at runtime. we should add a dirty flag to this data structure.

    def prune(self) -> None:
        """it appears for some reason the construction of this index is making a lot of useless keys with nothing mapped to them. here is a bandaid."""
        to_pop: list[str] = []
        for k in self.data.keys():
            if len(self.data[k]) == 0:
                to_pop.append(k)

        for k in to_pop:
            self.data.pop(k)


if __name__ == "__main__":
    pass

    # create an empty index
    index = DictionaryIndex(DocumentMetadataAPI("metadata.db"))

    # # test search
    print(index.get_relevant_ids("luminescence"))
