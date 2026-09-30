# DogGame!
DogGame! is a desktop search engine for text, MHTML, and PDF documents made as a school project. It is a delightfully useful tool when paired with a web browser and an MHTML snapshotting extension.

DogGame! was made as a 3rd year CSProject while attending DigiPen.

Code by Jacob Ableidinger and Matt Loots.  

> [!NOTE]
> Some code has been removed for publication.


# Using The Project:
## Running The Program:
[uv](https://docs.astral.sh/uv/) is recommended for creating your Python environment.  
To launch run `bg.pyw` to run the project headless, or `main.py` for testing. Make sure to launch the program from the `src/` directory. The program also works well when packaged with Docker.

> [!NOTE]
> Due to some file restructuring and the switch to uv for environment management Docker deployment hasn't been tested in the last few years. There may be issues but they should be straightforward to fix. Feel free to open an issue and we'll get to it at some point (or you can fix it yourself :O).

## Adding Documents
Your searchable corpus of documents are the contents of `src/Documents`. When you want a file to be searchable, move it into that folder either before startup (as that directory will be indexed on startup), *or* after adding files be sure to click the `Rescan corpus` button in the settings panel on the search page.
### Supported Filetypes:
- `.mht` (recommended)
- `.txt`
- `.pdf`
> [!NOTE]
> Use a browser extension to save web pages into `.mht` files.
