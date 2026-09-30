# DogGame!
DogGame! is a desktop search engine for text, MHTML, and PDF documents made as a school project. It is a delightfully useful tool when paired with a web browser and an MHTML snapshotting extension.

DogGame! was made as a 3rd year CSProject while attending DigiPen.

Code by Jacob Ableidinger and Matt Loots.  

> [!NOTE]
> Some code has been removed for publication.

## Supported Filetypes:
- `.mht` (recommended)
- `.txt`
- `.pdf`
> [!NOTE]
> Use a browser extension to save web pages into `.mht` files.


# Using The Project:
## Basic Setup
### Running The Program:
[uv](https://docs.astral.sh/uv/) is recommended for creating your Python environment.  
To launch run `bg.pyw` to run the project headless, or `main.py` for testing. Make sure to launch the program from the `src/` directory. The program also works well when packaged with Docker.

> [!NOTE]
> Due to some file restructuring and the switch to uv for environment management Docker deployment hasn't been tested in the last few years. There may be issues but they should be straightforward to fix. Feel free to open an issue and we'll get to it at some point (or you can fix it yourself :O).

### Adding Documents
Your searchable corpus of documents are the contents of `src/Documents`. When you want a file to be searchable, move it into that folder either before startup (as that directory will be indexed on startup), *or* after adding files be sure to click the `Rescan corpus` button in the settings panel on the search page.

## Advanced Setup
### Steps for Windows 11:
#### Setup nginx, hosts, & wsl For Routing
1. add this to your hosts file (`C:/Windows/System32/drivers/etc/hosts` needs admin)
```
# doggame
127.0.0.1 doggame.local
```
1. setup wsl2 (if you haven't already)
1. install nginx in wsl
  - `sudo apt install nginx`
1. get the ip address of wsl (`HOST`)
  - `ip route show | grep -i default | awk '{print $3}'`
1. create an nginx rule for doggame
  1. create the file with `sudo nano /etc/nginx/sites-available/doggame.local`
  1. content is something like this:
  ```
  server {
      listen 80;
      server_name doggame.local;

      location / {
          proxy_pass http://127.0.0.1:1234;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }
  ```
  1. make a symlink to the active connections directory so nginx uses this rule: `sudo ln -s /etc/nginx/sites-available/doggame.local /etc/nginx/sites-enabled/`
  1. restart nginx `sudo systemctl restart nginx`
1. setup your `.env` file.
  - create a `.env` file in `/src` with the following content:
  ```env
  DOWNLOADS_PATH="C:/Users/<your_user>/Downloads/"
  HOST="<your_wsl_ip>"
  ```
  - replace `<your_user>` and `<your_wsl_ip>`
  - Then sanity check. At this point if you run `uv run main.py` DogGame! should be reachable at `doggame.local` in your browser.
#### Setup The Chrome Extension
1. Open chrome and navigate to your installed extensions
1. toggle on developer mode
1. click `load unpacked` and select `./src/ext` in this project folder as the source for your extension.
1. add `EXT_AC="<extension_id>"` to your `.env` file and replace `<extension_id>` with the `ID` field of the DogGame! extension.
[!alt text](./imgs/ext_ss.png)
1. restart DogGame! (with `main.py` or `bg.pyw`) and test saving a page with the extension.

In theory you're good to go but this is a lot of steps and has only been tested on one machine.
