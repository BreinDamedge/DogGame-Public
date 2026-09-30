"""
+---------------+
| !DataHoarding |
+---------------+

Authors: Jacob Ableidinger, Matt Loots
File Name: main.py
Date Documented: 11/19/2024
Description:
    - main function for the DogGame! project.
"""

if __name__ == "__main__":
    pass
    from webserver import init, WebsiteRequestHandler, http
    from os import getenv
    from dotenv import load_dotenv

    _: bool = load_dotenv()
    # startup:
    init()

    host: str | None = getenv("HOST")
    if host is None:
        host = "localhost"

    server = http.server.HTTPServer((host, 1234), WebsiteRequestHandler)
    print("Starting Server")
    server.serve_forever()  # slay maxxing
