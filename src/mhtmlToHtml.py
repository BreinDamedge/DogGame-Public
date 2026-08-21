"""
+---------------+
| !DataHoarding |
+---------------+

Date Documented: 10/31/2024
Description:
    - this file contains a function to convert an mhtml file to an html file.
"""

import email
import base64
import bs4
import re

# Limitations:
# - Does not proccess CSS url attributes


def is_outlink(tag):
    return (
        tag.has_attr("src") or tag.has_attr("href") or tag.has_attr("srcset")
    ) and tag.name != "a"


def process_html_outlink_attr(entries, value):
    def process_html_outlink_url(match):
        return ensure_processed(entries, match.group(0))

    return re.sub(r"(\w+):[^\s]+", process_html_outlink_url, value)


def process_html_outlink(entries, tag):
    for attr in ["src", "srcset", "href"]:
        if tag.has_attr(attr):
            value = process_html_outlink_attr(entries, tag[attr])

            if value is not None:
                tag[attr] = value


def process_html(entries, entry):
    soup = bs4.BeautifulSoup(entry["content"], "html.parser")
    outlinks = soup.find_all(is_outlink)

    for outlink in outlinks:
        process_html_outlink(entries, outlink)

    entry["content"] = str(soup).encode("utf8")


def generate_data_url(entry):
    return (
        "data:"
        + entry["type"]
        + ";charset=utf-8;base64,"
        + base64.b64encode(entry["content"]).decode("ascii")
    )


def ensure_processed(entries, url):
    if not url in entries:
        return "http://invalid.invalid/invalid"

    entry = entries[url]

    if entry["processed"]:
        return generate_data_url(entry)
    else:
        entry["processed"] = True

    if entry["type"] == "text/html":
        process_html(entries, entry)

    return generate_data_url(entry)


def mhtml_to_html_bytes(mhtml_content: bytes) -> bytes:
    """
    Converts an MHTML (MIME HTML) content to HTML content in memory.

    Args:
        mhtml_content (bytes): The raw MHTML content as bytes.

    Returns:
        bytes: The converted HTML content as bytes.
    """

    message = email.message_from_bytes(mhtml_content)
    content = {}
    root = None

    for part in message.walk():
        content_type = part["Content-Type"]
        content_location = part["Content-Location"]
        content_id = part["Content-ID"]

        # print(content_id, content_location, content_type)

        if content_type is None or (content_location is None and content_id is None):
            continue

        if root is None:
            root = content_location

        body = part.get_payload(decode=True)
        entry = {"content": body, "type": content_type, "processed": False}

        if content_location is not None:
            content[content_location] = entry
        if content_id is not None:
            cid_location = "cid:" + content_id[1:-1]
            content[cid_location] = entry

    ensure_processed(content, root)

    return content[root]["content"]


if __name__ == "__main__":
    test_file_dir: str = "mhtmlToHtml_test.mht"

    with open(test_file_dir, "rb") as f:
        file_bytes: bytes = f.read()

    html_bytes: bytes = mhtml_to_html_bytes(file_bytes)

    with open("test.html", "wb") as f:
        f.write(html_bytes)

