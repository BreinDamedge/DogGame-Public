"""
+---------------+
| !DataHoarding |
+---------------+

Authors: Jacob Ableidinger,
GitHub Usernames: BreinDamedge,
File Name: parsing.py
Date Documented: 11/19/2024
Description:
        - This file contains functions for the parsing system and also just general functions that can be used as needed.
"""

import os, string, io, bs4, email, json, warnings
from typing import Callable
from pypdf import PdfReader
from nltk.stem import PorterStemmer


def stem_text(text_: str) -> str:
    """text_ should be preprocessed before it's passed in"""
    ps = PorterStemmer()
    words = text_.split(" ")
    known_stems: dict[str, str] = dict()
    for i in range(len(words)):
        try:
            words[i] = known_stems[words[i]]
        except KeyError:
            known_stems[words[i]] = ps.stem(words[i])
            words[i] = known_stems[words[i]]
    return " ".join(words)


def word_counts(text_: str) -> dict[str, int]:
    counts = dict()
    for w in text_.split(" "):
        counts[w] = counts.get(w, 0) + 1
    return counts


def preprocess_n_stem(content_: str, pps_: list[Callable[[str], str]]) -> str:
    for f in pps_:
        content_ = f(content_)
    return stem_text(content_)


def pretty_json(data_: dict) -> str:
    return json.dumps(data_, indent=4, default=lambda o: o.__dict__)


def list_files(dir_: str) -> list[str]:
    file_names: list[str] = []
    for fn in os.listdir(dir_):
        if os.path.isfile(f"{dir_}/{fn}"):
            file_names.append(fn)
    return file_names


def list_files_absolute(dir_: str):
    return [f"{dir_}/{fn}" for fn in list_files(dir_)]


def get_file_extension(file_bytes_):
    # Magic numbers for PDF and MHTML
    magic_numbers = {
        b"%PDF-": "pdf",  # PDF files
    }

    # Check for each strict magic number
    for magic, ext in magic_numbers.items():
        if file_bytes_.startswith(magic):
            return ext

    # Check for MHTML by scanning for key phrases within the first 512 bytes
    if (
        b"MIME-Version: 1.0" in file_bytes_[:512]
        or b"Content-Type: multipart/related" in file_bytes_[:512]
        or b"From: <Saved by Blink>" in file_bytes_[:512]
    ):
        return "mht"

    # Check for plain text files (basic heuristic)
    if all(32 <= byte <= 126 or byte in (9, 10, 13) for byte in file_bytes_):
        return "txt"

    warnings.warn("defaulting to '.txt'")
    return "txt"


def to_lowercase(s_: str) -> str:
    """returns a lowercase copy of a string"""
    return s_.lower()


def clean_whitespace(s_: str) -> str:
    """splits string on whitespace and joins it all back together"""
    return " ".join(s_.split())


def to_alpha(s_: str) -> str:
    """returns a copy of s_ where all non-alphabetical characters are a space."""
    keep_letters: set[str] = set(list(string.ascii_lowercase + " "))
    # this is a bit of a scary list comprehension but it's basically:
    """
	output_string = ""
	for c in input_string:
		if c in keep_letters: output_string += c
		else: output_string += " "
	return output_string
	"""
    return "".join([c if c in keep_letters else " " for c in s_])


"""very similar to to_alpha"""


def strip_text(text_: str) -> str:
    text_ = text_.replace("\n", " ")
    # Learn how translation tables work. This is chatgpt black magic atm
    # Create a translation table that maps punctuation and newline characters to None
    remove_chars = string.punctuation + string.digits
    translator = str.maketrans("", "", remove_chars)

    # Use the translate method to remove the specified characters
    return text_.translate(translator)


def backslash_single_quotes(text_: str) -> str:
    return text_.replace("'", "\\'")


def keywords(text_: str) -> set[str]:
    no_punc = strip_text(text_)
    return set(no_punc.lower().split(" "))


def stemmed_keywords(text_: str) -> set[str]:
    no_punc: str = strip_text(text_)
    pre_stem: set = set(no_punc.lower().split(" "))
    keywords: set = set()

    ps: PorterStemmer = PorterStemmer()
    for w in pre_stem:
        keywords.add(ps.stem(w))

    return keywords


def parse_mhtml_data(
    document_data_: io.BufferedReader, post_parsing_: list[Callable[[str], str]] = []
) -> dict:
    """
    This function takes an open mhtml file and pulls the text out of it.
    it also keeps track of outlinks (maybe, probably not correctly)
    and stores the original url. all of this is returned in a
    DocumentMetadata object.
    """

    # create a container to store the info as we parse
    doc_metadata: dict = dict()
    DEFAULT_TITLE = "DEFAULT_TITLE"
    doc_metadata["title"] = DEFAULT_TITLE
    doc_metadata["text"] = ""

    # Break the document apart since it's an email
    message = email.message_from_bytes(document_data_.read())

    # grab the base url
    doc_metadata["url"] = message["Snapshot-Content-Location"]

    # walk through the mhtml content
    for part in message.walk():
        # only grabbing text content so what we're gonna do is huck all of the
        # outlinks into references, and then if the type of other content is
        # text we're gonna throw all that into a big ol string

        # check if this section has a url
        part_url: str = part["Content-Location"]
        if part_url is None:
            # not sure why it's done this way atm so come back and explain
            continue

        # check content type and parse it if it's html or text
        content_type: str = part.get_content_type()
        if content_type == "text/html":
            body = part.get_payload(decode=True)
            soup = bs4.BeautifulSoup(body, "html.parser")
            doc_metadata["text"] += soup.get_text() + " "  # is it magic?

            # get outlinks
            doc_metadata["references"] = list(
                {a["href"] for a in soup.find_all("a", href=True)}
            )

            # # grab the title if it doesn't have one yet
            if (
                doc_metadata["title"] == DEFAULT_TITLE
            ):  # i know it's not an instance, I'm checking if it's still the default value for the class
                # doc_metadata["title"] = message["Subject"]
                # find the <title> tag
                title_tag = soup.find("title")
                # if it found a title, grab the text
                if title_tag:
                    page_title = title_tag.get_text(strip=True)
                    doc_metadata["title"] = page_title

    # This section loops through any functions given for the post processing step
    for f in post_parsing_:
        doc_metadata["text"] = f(doc_metadata["text"])

    return doc_metadata


def parse_pdf_file(
    file_path_: str, post_parsing_: list[Callable[[str], str]] = []
) -> dict:
    """I wonder if this works on scans, i bet it won't"""
    # creating a pdf reader object
    reader = PdfReader(file_path_)

    doc_data: dict = dict()
    doc_data["text"] = ""

    # loop through pages and extract the text from a pdf
    for p in reader.pages:
        doc_data["text"] += p.extract_text() + " "

    # This section loops through any functions given for the post processing step
    for f in post_parsing_:
        doc_data["text"] = f(doc_data["text"])

    # add file id
    doc_data["file_id"] = file_path_.split("/")[-1]

    # add a title (placeholder atm)
    doc_data["title"] = "This is a PDF"

    return doc_data


def parse_text_file(
    file_path_: str, post_parsing_: list[Callable[[str], str]] = []
) -> dict:
    """this just opens a text file and returns it as a DocumentMetadata object"""
    doc_data: dict = dict()
    with open(file_path_, "r") as f:
        doc_data["text"] = f.read()

    # post process
    for f in post_parsing_:
        doc_data["text"] = f(doc_data["text"])

    # add name on disk (filename, not full path)
    doc_data["file_id"] = file_path_.split("/")[-1]

    # give file a title
    doc_data["title"] = ""
    words_in_title: int = 3
    for i, w in enumerate(doc_data["text"].split(" ")):
        doc_data["title"] += w
        if i == words_in_title:
            break
        doc_data["title"] += " "

    return doc_data


def parse_mhtml_file(file_path_: str, post_functions_: list) -> dict:
    """open the doc, parse it, label it with it's disk name, return the object"""
    with open(file_path_, "rb") as f:
        doc = parse_mhtml_data(f, post_functions_)

    # add filename to data (not full path)
    doc["file_id"] = file_path_.split("/")[-1]

    return doc


def list_files_with_extention(dir_: str, ext_: str) -> list[str]:
    file_names: list[str] = []
    for file_name in os.listdir(dir_):
        if os.path.isfile(f"{dir_}/{file_name}") and file_name.split(".")[-1] == ext_:
            file_names.append(file_name)
    return file_names


def set_of_chars_to_string(char_set_: set) -> str:
    out = ""
    for c in char_set_:
        out += c
    return out


TRANSLATION_TABLE = str.maketrans(
    string.ascii_letters,
    string.ascii_letters.lower(),
    set_of_chars_to_string(set(string.punctuation) - set("-"))
    + set_of_chars_to_string(set(list(string.whitespace)) - set(" ")),
)


# to_lowercase, to_alpha, clean_whitespace
def pps_in_one(text_: str) -> str:
    global TRANSLATION_TABLE
    return " ".join(text_.translate(TRANSLATION_TABLE).split())


# might not want this to be global - though it's not that bad and it gives a bit of consistancy for what our preprocessing steps are.
# I think it's okay for now, and a more formal documented solution would be better down the line if this project is continued.
PPS: list[Callable[[str], str]] = [
    pps_in_one
]  # [to_lowercase, to_alpha, clean_whitespace]


if __name__ == "__main__":
    pass

    # POST_PROCESSING:list[Callable[[str], str]] = [to_lowercase, to_alpha, clean_whitespace]
    # bee_movie_dir = "documents/8b702343-2dc9-4fa6-bdb3-2888732ff4c2.txt"

    # with open(bee_movie_dir, "r") as f:
    # 	bee_movie = f.read()

    # print(bee_movie[-100:])

    # for f in POST_PROCESSING: bee_movie = f(bee_movie)

    # import time
    # st = time.time()
    # for i in range(10):
    # 	bee_movie_stemmed = stem_text(bee_movie)
    # print(time.time()-st)
    # print(bee_movie[-100:])

    print(pps_in_one("test123!()!()!(!)           (---MaTTis(((((Yup))))))"))

