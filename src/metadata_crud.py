"""
+---------------+
| !DataHoarding |
+---------------+

Authors: Jacob Ableidinger,
File Name: metadata_crud.py
Date Documented: 02/18/2025
Description:
    - Crud wrapper around SQLite for document metadata
"""

import sqlite3, json, path_info
from parsing import list_files
from multiprocessing import Pool

"""
THIS API WAS MADE SPECIFICLY FOR INTERACTING WITH THIS TABLE:

    db_name:str = "metadata.db"

    document_table_creation_query:str = \
        "CREATE TABLE IF NOT EXISTS documents (" + \
        "file_id TEXT PRIMARY KEY," + \
        "metadata TEXT" + \
        ");"
"""


def dm_dict_to_json_with_id_delegate(dm_obj_: dict) -> list[str]:
    if dm_obj_ is None:
        return []
    return [dm_obj_["file_id"], json.dumps(dm_obj_)]


class DocumentMetadataAPI:
    def __init__(self):
        self._db_name: str = path_info.METADATA_PATH + "/document_metadata.db"
        self.con: sqlite3.Connection = sqlite3.connect(self._db_name)
        self.table_name: str = "documents"
        self.notes_table_name: str = "notes"

        # create table on startup
        table_creation_query: str = (
            f"CREATE TABLE IF NOT EXISTS {self.table_name} ("
            + "file_id TEXT PRIMARY KEY,"
            + "metadata TEXT"
            + ");"
        )
        self.con.execute(table_creation_query)

        # notes table
        # create table on startup
        table_creation_query: str = (
            f"CREATE TABLE IF NOT EXISTS {self.notes_table_name} ("
            + "file_id TEXT PRIMARY KEY,"
            + "doc_notes TEXT"
            + ");"
        )
        self.con.execute(table_creation_query)

        self.con.commit()

    def create(self, dm_obj_: dict):
        if dm_obj_ is not None:
            self.con.execute(
                f"INSERT INTO {self.table_name} VALUES(?,?)",
                [dm_obj_["file_id"], json.dumps(dm_obj_)],
            )
            self.con.commit()  # commit the transaction

    def create_many(self, dm_objects_: list[dict], pool_=None):
        for i in range(len(dm_objects_) - 1, -1, -1):
            if dm_objects_[i] is None:
                dm_objects_.pop(i)

        query_str = f"INSERT INTO {self.table_name} VALUES (?,?)" + ", (?,?)" * (
            len(dm_objects_) - 1
        )

        if pool_ is None:
            question_mark_values = []
            for obj in dm_objects_:
                question_mark_values += [obj["file_id"], json.dumps(obj)]
        else:
            question_mark_values = [
                el
                for sub_list in pool_.map(dm_dict_to_json_with_id_delegate, dm_objects_)
                for el in sub_list
            ]

        self.con.execute(query_str, question_mark_values)

        self.con.commit()

    def get(self, id_: str) -> dict | None:
        """return a list of metadata objs given document_ids. returns None if retrieval got nothing."""
        cur = self.con.cursor()

        if type(id_) != type(str()):
            raise TypeError("non-str type passed.")

        res = cur.execute(f"SELECT * FROM {self.table_name} WHERE file_id = ?", [id_])
        row = res.fetchone()

        if row is None:
            return None
        return json.loads(row[1])

    def get_note(self, id_: str) -> str:
        cur = self.con.cursor()
        if type(id_) != type(str()):
            raise TypeError("non-str type passed.")
        res = cur.execute(
            f"SELECT doc_notes FROM {self.notes_table_name} WHERE file_id = ?", [id_]
        )
        row = res.fetchone()
        if row is not None:
            return row[0]
        else:
            return ""

    def set_note(self, id_: str, content_: str) -> None:
        # use an upsert/replace. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging. pogging.
        cur = self.con.cursor()
        if type(id_) != type(str()):
            raise TypeError("non-str type passed.")
        cur.execute(
            f"INSERT INTO {self.notes_table_name} (file_id, doc_notes) VALUES (?,?)\
                    ON CONFLICT(file_id) DO UPDATE SET doc_notes = ? WHERE file_id = ?",
            [id_, content_, content_, id_],
        )
        self.con.commit()

    def set_title(self, id_: str, new_title_: str) -> None:
        if type(id_) != type(str()):
            raise TypeError("non-str id")
        elif type(new_title_) != type(str()):
            raise TypeError("non-str title")

        record = self.get(id_)
        record["title"] = new_title_
        self.update(id_, record)

    def update(self, id_: str, data_: dict) -> None:
        self.con.execute(
            f"UPDATE {self.table_name} SET metadata = ? WHERE file_id = ?",
            [json.dumps(data_), id_],
        )
        self.con.commit()  # commit the transaction

    def get_many(self, ids_: list[str]) -> list[dict]:
        """return a list of metadata objs given document_ids"""
        cur = self.con.cursor()
        metadata: list[dict] = []
        if type(ids_) != type(list()):
            raise TypeError("non-list type passed.")
        for id in ids_:
            res = cur.execute(
                f"SELECT * FROM {self.table_name} WHERE file_id = ?", [id]
            )
            row = res.fetchone()
            if row is None:
                continue
            metadata.append(json.loads(row[1]))
        return metadata

    def delete(self, ids_: list[str]):
        if type(ids_) != type(list()):
            raise TypeError("non-list type passed.")

        cur = self.con.cursor()
        for id in ids_:
            cur.execute(f"DELETE FROM {self.table_name} WHERE file_id = ?", [id])

        self.con.commit()

    def get_ids(self) -> list[str]:
        cur = self.con.cursor()
        cur.execute(f"SELECT file_id FROM {self.table_name};")
        return [
            x[0] for x in cur.fetchall()
        ]  # pulls the file id out of the tuple from each doc

    def kill_orphans(self) -> None:
        orphans = set(self.get_ids()).difference(set(list_files(path_info.CORPUS_PATH)))
        self.delete(list(orphans))

    def num_rows(self) -> int:
        return self.con.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]

    def get_all_no_convert(self) -> list[tuple[str, str]]:
        """returns all data in the metadata table and leaves data as json str"""
        cur = self.con.cursor()
        res = cur.execute(f"SELECT * FROM {self.table_name}")
        out = res.fetchall()
        return out


if __name__ == "__main__":
    pass
    import parsing, path_info
    # api = DocumentMetadataAPI()

    # # avocado doc
    # test_doc_id = "af3ce632-2b11-4886-89a4-8fd81f64ab6b.pdf"

    # note = api.get_note(test_doc_id)
    # print(note)
    # api.set_note(test_doc_id, "it's the avocaaaado...\nthaanks!")
    # note = api.get_note(test_doc_id)
    # print(note)

    print("test" + " test?" * 1)
