FROM python:3.11.9-slim-bullseye

# dependencies
RUN pip install beautifulsoup4
RUN pip install pypdf
RUN pip install nltk

# src
WORKDIR /usr/local/app
COPY Website /usr/local/app/Website
COPY corpus_cleanup.py /usr/local/app/corpus_cleanup.py
COPY document_adding_helpers.py /usr/local/app/document_adding_helpers.py
COPY indexing.py /usr/local/app/indexing.py
COPY main.py /usr/local/app/main.py
COPY manager.py /usr/local/app/manager.py
COPY metadata_crud.py /usr/local/app/metadata_crud.py
COPY mhtmlToHtml.py /usr/local/app/mhtmlToHtml.py
COPY parser.py /usr/local/app/parser.py
COPY parsing.py /usr/local/app/parsing.py
COPY path_info.py /usr/local/app/path_info.py
COPY ranking.py /usr/local/app/ranking.py
COPY webserver.py /usr/local/app/webserver.py
RUN mkdir Documents

# port
EXPOSE 1234

# Setup an app user so the container doesn't run as the root user   # suggested in example
RUN useradd app
USER app

CMD ["python", "main.py"]