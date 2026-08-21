# DogGame!: Design Document | !DataHoarding


## Conceptual Overview:
The goal of this project is to create a system to store documents from the internet on a local machine and retrieve them. This type of system is sometimes called a desktop search engine.


### Long Term Data Storage:
Long term data storage is just a directory on disk. On startup this directory is scanned and an index is built and loaded into memory.

#### Data Structures and Key Information
Metadata about files is stored. When serialized it is stored in an SQLite database on disk in the `corpus/.metadata` directory, but when used by python it is loaded into this dataclass:
```python
# Can be found in parsing.py
@dataclass
class DocumentMetadata:
	url:str = None
	file_id:str = None
	title:str = ""
	text:str = ""
	references:list[str] = field(default_factory=list)
```


### Retrieval:
To perform a search on the corpus a user writes a search **query** and that query is used by a ranking algorithm to find the most relavent documents in the corpus. This engine has two ranking algorithms: a TF-IDF implementation, and a Title Matching score. On search an ordered list of relavent documents are displayed to the user (documents are deemed relevent using an inverted index, then ranked with the currently selected algorithm). The final step of **ranking** the retrieved documents may be skipped if the user chooses. An example where this could be done is if the index in use already ranks the documents. The ranking step can be used to reorder relavent documents on the results page based on some metric if the user so chooses. 

## UI
The UI is a webpage provided. By default it exists at `localhost:1234`


## Files
one file for each system
```
indexing.py
metadataSystem.py
parsing.py
ranking.py
webserver.py
main.py
manager.py
```

### What does startup look like?
The manager knows what systems need to be started and what resources need to be loaded into memory


### Metadata Caching
In an effort to avoid parsing over and over again, and at the same time be able to make blurbs (yet to be implemented) we store parsed document metadata on disk and in memory. We use a small SQLite db for this.  

# Implemented Systems
A brief description of the systems in play here:

## The Manager:
The manager is a class that we are using as a sort of point of communication between all the other systems. it holds any state that we may need (like a configuration file for what kind of search you want to do)
and it can see all of the other systems so that when you make a search it can route the data from your search through all of the systems and then back to you.

### The Manager API
- `init()`:
    initializes all other systems:
    - parser
    - indexes
    - document metadata
    - ranker
- `add_document()`
    given the data for a new mhtml file adds it to the system
- `remove_document()`
    given a document id, removes that document and all related data from the system (*the related data is not always removed until the system starts up again and the corpus data is validated).
- `search_documents()`
    given a search query, returns a ranked list of relavent document titles and their ids
- `open_document()`
    given a document's id, parses the file into html and sends the data as json to the webserver to be displayed in a browser
- `corpus_size()`
    returns the number of unique file ids present in all currently loaded indecies.

### One Last Note On The Manager
Is this the best way to organize the system? Absolutely not. Does it work? Yes it does. It may in the future be worthwhile to modify the manager and the other systems (like the parser and the document metadata system) to be "stateless" or RESTful (full on rest compliance is definitely overkill) so that modifying bits and pieces of each system can be done with a little more flexability. It would also allow all of the systems to have a global API so that they could be accessible from anywhere. One example of where this is nice/needed is in the ranker *right now*. The ranker recieves a list of document ids but it knows nothing about their metadata and it has to read this off of the disk even though it's already loaded in memory as an attribute of the manager. Right now as I said, not really a problem, but it is quite silly and probably worth a look.  


## Parser
The parser is the system responsible for ingesting new documents and extracting useful information about them.

## Index(es)
The Index is responsible for mapping keywords to documents that contain them so that we can quickly retrieve relevant documents.

## Metadata Store
This exists so that we don't have to parse the corpus on every startup.

## Ranker
This system is responsible for ordering retrieved documents by relevance to a given query.

## Webserver 
The webserver and webui allow a user to easily use the system.

### API
_add_document  -> add doc id to corpus  
- add_document(index_, doc_contents_:bytes, filetype_:str)  

_remove_doc    -> remove doc id  
- we have no way to remove a document from search results entirely unless we do a linear search through our index and remove every instance of it's name. To solve this issue we can have a blacklist of removed document_ids and then  

_search        -> ordered list of doc ids and titles  

_open_document -> Get contents of a document  

