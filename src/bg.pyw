"""
+---------------+
| !DataHoarding |
+---------------+

Authors: Jacob Ableidinger, Matt Loots
File Name: bg.pyw
Date Documented: 9/30/2026
Description:
    - main function for the DogGame! project when run as bg process
"""

if __name__ == "__main__":
    import os
    import sys
    from webserver import init, WebsiteRequestHandler, http
    from os import getenv
    from dotenv import load_dotenv

    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

    _: bool = load_dotenv()
    # startup:
    init()

    host: str | None = getenv("HOST")
    if host is None:
        host = "localhost"

    server = http.server.HTTPServer((host, 1234), WebsiteRequestHandler)
    print("Starting Server")
    server.serve_forever()  # slay maxxing
