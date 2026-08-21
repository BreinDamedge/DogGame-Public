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

    # startup:
    init()

    server = http.server.HTTPServer(("localhost", 1234), WebsiteRequestHandler)
    print("Starting Server")
    server.serve_forever()  # slay maxxing

