"""
this script parses the entire corpus to translate all mhtml documents into html.
For corpus migration to other projects.
"""

if __name__ == "__main__":
    pass

    from mhtmlToHtml import mhtml_to_html_bytes
    from parsing import list_files_with_extention

    files = list_files_with_extention("Documents", "mht") + list_files_with_extention(
        "Documents", "mhtml"
    )

    for i, file in enumerate(files):
        print(f"{i}/{len(files)}", end="\r")
        try:
            with open("Documents/" + file, "rb") as f:
                data = f.read()
            data = mhtml_to_html_bytes(data)
            with open(
                "C:/Users/jacob/Documents/Code/Go/Woofer/.corpus/"
                + file.split(".")[0]
                + ".html",
                "wb",
            ) as f:
                f.write(data)
        except:
            print(f"failed to parse: {file}")
