import http.server, json, corpus_cleanup
from manager import Manager


_MANAGER: Manager = None


def init(config_file_path_: str = None) -> None:
    """setup the manager, used on startup of DogGame!"""
    global _MANAGER

    import time

    st = time.time()

    print("Starting...")

    # rename, clean, and validate corpus
    print("Cleaning Corpus...")
    corpus_cleanup.setup_metadata()  # still want this for index file
    corpus_cleanup.rename_non_uuid_files()
    corpus_cleanup.delete_orphaned_metadata()

    print("Loading Systems...")
    if config_file_path_ is not None:
        _MANAGER = Manager(config_file_path_)
    else:
        _MANAGER = Manager("default")

    # how many files are indexed:
    files, dm_rows, indexed_ids = _MANAGER.corpus_size_info()
    print(f"Corpus Size:")
    print(f"Files/Metadata/Index")
    print(f"{files}/{dm_rows}/{indexed_ids}")

    print("Ready.")

    print(f"Setup Took {time.time() - st} seconds.")


def rescan_corpus() -> None:
    """rescan corpus"""
    global _MANAGER

    print("Validating...")
    # rename, clean, and validate corpus
    print("Cleaning Corpus...")
    corpus_cleanup.rename_non_uuid_files()
    corpus_cleanup.delete_orphaned_metadata()

    _MANAGER.rescan_corpus()

    # how many files are indexed:
    files, dm_rows, indexed_ids = _MANAGER.corpus_size_info()
    print(f"Corpus Size:")
    print(f"Files/Metadata/Index")
    print(f"{files}/{dm_rows}/{indexed_ids}")

    print("Done.")


# ----- Below is Vadim's Beautiful Code. -----
_MIME_TRANSLATIONS = {
    "txt": "text/plain",
    "mhtml": "multipart/related",  # "multipart/related application/x-mimearchive"
    "mht": "multipart/related",  # "message/rfc822"
    "pdf": "application/pdf",
    "html": "text/html",
}


_FILE_MAPPINGS = {
    "/": {"path": "Website/dist/index.html", "ct": "text/html"},
    "/index.js": {"path": "Website/dist/index.js", "ct": "text/javascript"},
    "/index.css": {"path": "Website/dist/index.css", "ct": "text/css"},
    "/woof.png": {"path": "Website/woof.png", "ct": "image/png"},
}


class WebsiteRequestHandler(http.server.BaseHTTPRequestHandler):
    # Sends a raw reply to the request
    def _reply_raw(self, code, body, content_type):
        self.send_response(code)
        self.send_header("content-type", content_type)
        self.end_headers()
        self.wfile.write(body)

    # Replies to the request with json data
    def _reply(self, code, body):
        self._reply_raw(code, json.dumps(body).encode("utf8"), "application/json")

    # Called by python on every GET request
    def do_GET(self):
        if self.path in _FILE_MAPPINGS:
            mapping = _FILE_MAPPINGS[self.path]

            with open(mapping["path"], "rb") as f:
                self._reply_raw(200, f.read(), mapping["ct"])
        elif self.path.startswith("/documents/"):
            # Get everything after the "documents/" part of the path
            id = self.path[11:].strip("/")
            contents = _MANAGER.open_document(id)

            # Handle document reply
            if contents is None:
                self._reply(404, {"error": "That document does not exist"})
            else:
                if contents["type"] in _MIME_TRANSLATIONS:
                    self._reply_raw(
                        200, contents["contents"], _MIME_TRANSLATIONS[contents["type"]]
                    )
                else:
                    self._reply(
                        500, {"error": "That document has an invalid content type"}
                    )
        else:
            # We dont support any other get requests
            self._reply(404, {"error": "Not found"})

    # Called by python on every POST request
    def do_POST(self):
        # Read post body
        length = (
            int(self.headers["Content-Length"])
            if "Content-Length" in self.headers
            else 0
        )
        body = self.rfile.read(length)

        if self.path == "/documents/upload":
            # Add document
            _MANAGER.add_document(body)

            # Reply with success
            self._reply(200, {"message": "The document has been uploaded succesfully"})
        elif self.path == "/documents/delete":
            # Parse json
            contents = json.loads(body)

            # Check if all params are present
            if "id" in contents:
                target = str(contents["id"])

                # Try to remove document
                if _MANAGER.remove_document(target):
                    self._reply(200, {"message": "The document has been deleted"})
                else:
                    self._reply(200, {"message": "Failed to delete the document"})
            else:
                self._reply(400, {"message": "Expected id parameter!"})
        elif self.path == "/documents/search":
            # Parse json
            contents = json.loads(body)

            # Check if all params are present
            if "query" in contents and "ranker" in contents:
                # Run the search
                query = str(contents["query"])
                ranker = str(contents["ranker"])
                reply = _MANAGER.search_documents(query, ranker_id_=ranker)

                # TODO: Use ranker

                # Reply with results
                self._reply(200, {"results": reply})
            else:
                self._reply(400, {"message": "Missing query"})
        elif self.path == "/documents/update":
            # Parse json
            contents = json.loads(body)

            if "document" in contents and "note" in contents and "title" in contents:
                document = contents["document"]  # doc_id
                note = contents["note"]  # note content
                title = contents["title"]  # document title

                _MANAGER.dm_api.set_note(document, note)
                _MANAGER.dm_api.set_title(document, title)

                self._reply(200, {})
            else:
                self._reply(400, {})

        elif self.path == "/button/shutdown":
            quit()
        elif self.path == "/button/rescan":
            rescan_corpus()  # TODO: Actually rescan here
            self._reply_raw(200, "{}", "application/json")
        elif self.path == "/dump/metadata":
            data = _MANAGER.metadata_for_visualiation()
            self._reply_raw(200, data.encode(), "application/json")
        elif self.path == "/dump/index":
            data = _MANAGER.index_for_visualization()
            self._reply_raw(200, data.encode(), "application/json")
        else:
            self._reply(404, {"error": "Not found"})


if __name__ == "__main__":
    pass

    # server = http.server.HTTPServer(('localhost', 1234), WebsiteRequestHandler)
    # print('Started http server')
    # server.serve_forever()  # slay maxxing
