if __name__ == "__main__":
    import os
    import sys

    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

    from webserver import init, WebsiteRequestHandler, http

    # startup:
    init()

    server = http.server.HTTPServer(("localhost", 1234), WebsiteRequestHandler)
    print("Starting Server")
    server.serve_forever()  # slay maxxing
