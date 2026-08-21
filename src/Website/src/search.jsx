import React, { useState } from "react";
import styles from "./search.module.css";

const deletionInitial = "Delete";
const deletionConfirm = "Are you sure?";
const deletionDeleting = "Deleting...";
const deletionDone = "Deleted!";

export const rankerOptions = ["tfidf", "title"];

function SearchEntry(props) {
  const [deletionStatus, setDeletionStatus] = useState(deletionInitial);
  const [isEditing, setIsEditing] = useState(false);

  const [activeTitle, setActiveTitle] = useState(props.title);
  const [title, setTitle] = useState(props.title);

  const [activeBlurb, setActiveBlurb] = useState(props.blurb);
  const [blurb, setBlurb] = useState(props.blurb);

  async function deleteDocument() {
    if (deletionStatus == deletionInitial) {
      setDeletionStatus(deletionConfirm);
    } else if (deletionStatus == deletionConfirm) {
      setDeletionStatus(deletionDeleting);
    
      await fetch("/documents/delete", {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        method: "POST",
        body: JSON.stringify({"id": props.id})
      });

      setDeletionStatus(deletionDone);
    }
  }

  async function saveDocument() {
    setIsEditing(false);
    setActiveBlurb(blurb);
    setActiveTitle(title);

    await fetch("/documents/update", {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      method: "POST",
      body: JSON.stringify({
        "document": props.id,
        "note": blurb,
        "title": title,
      })
    });
  }

  function startEditing() {
    setIsEditing(true);
    setDeletionStatus(deletionInitial);
    setBlurb(activeBlurb);
    setTitle(activeTitle);
  }

  return (
    <div>
      {!isEditing ? <>
        <b>
          <a href={`/documents/${encodeURIComponent(props.id)}`}>{activeTitle}</a>
        </b>
      </> : null}

      {isEditing ? <>
        <b>
          <input type="text" value={title} onChange={e => setTitle(e.target.value)}/>
        </b>
      </> : null}

      {!isEditing ? <>
        <button className={styles.textButton} onClick={startEditing}>(Edit)</button>
      </> : null}

      {!isEditing ? <>
        <div className={styles.content}>
          <p>{activeBlurb}</p>
        </div>
      </> : null}

      {isEditing ? <>
        <br/><br/>
        <div className={styles.content}>
          <textarea value={blurb} onChange={e => setBlurb(e.target.value)}/>
          
          <br/><br/>

          <button className={styles.editButton} onClick={_ => saveDocument()}>Save</button>
          <button className={styles.editButton} onClick={_ => deleteDocument()}>{deletionStatus}</button>
          <button className={styles.editButton} onClick={_ => setIsEditing(false)}>Cancel</button>
        </div>
        <br/>
      </> : null}
    </div>
  )
}

function SearchBar() {
  const [expanded, setExpanded] = useState(false);
  const [searchStatus, setSearchStatus] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [ranker, setRanker] = useState(rankerOptions[0]);

  async function search() {
    setSearchStatus("Searching the corpus...");

    let response = await fetch("/documents/search", {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      method: "POST",
      body: JSON.stringify({"query": searchQuery, "ranker": ranker})
    });

    if (response.status == 200) {
      let data = await response.json();

      setSearchResults(data["results"]);
      setSearchStatus(null);
    } else {
      setSearchStatus("An error occured while searching");
    }
  }

  async function rescan() {
    setSearchStatus("Rescanning the corpus...");
    setSearchResults([]);

    await fetch("/button/rescan", {
      headers: {
        'Accept': 'application/json',
      },
      method: "POST",
    });

    setSearchStatus("Rescanned!");
  }

  async function shutdown() {
    if (!confirm("Are you sure you want to shut down?")) {
      return;
    }

    setSearchStatus("Shutting down!");
    setSearchResults([]);

    await fetch("/button/shutdown", {
      headers: {
        'Accept': 'application/json',
      },
      method: "POST",
    });
  }

  async function rescan() {
    setSearchStatus("Rescanning the corpus...");
    setSearchResults([]);

    await fetch("/button/rescan", {
      headers: {
        'Accept': 'application/json',
      },
      method: "POST",
    });

    setSearchStatus("Rescanned!");
  }

  async function shutdown() {
    if (!confirm("Are you sure you want to shut down?")) {
      return;
    }

    setSearchStatus("Shutting down!");
    setSearchResults([]);

    await fetch("/button/shutdown", {
      headers: {
        'Accept': 'application/json',
      },
      method: "POST",
    });
  }

  function keyDownHandler(e) {
    if (e.key == "Enter") {
      search();
    }
  }

  return (
    <>
      <div className={styles.searchBar}>
        <input
          type="text"
          name="search"
          placeholder="Search anything!"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className={styles.searchInput}
          onKeyDown={keyDownHandler}
        />

        <button className={styles.searchModifyButton} onClick={() => setExpanded(!expanded)}>⚙️</button>
      </div>

      {expanded ? <div className={styles.searchSettings}>
        <div>
          <button onClick={rescan} className={styles.editButton}>Rescan corpus</button>
          <button onClick={shutdown} className={styles.editButton}>Shutdown</button>

          <select onChange={e => setRanker(e.target.value)}>
            {rankerOptions.map(x => <option>{x}</option>)}
          </select>
        </div>
      </div> : null}

      {searchStatus ? <h2>{searchStatus}</h2> : null}
      {searchResults.map(x => <SearchEntry key={x.id} id={x.id} title={x.name} blurb={x.note ?? ""} />)}
    </>
  )
}

export function SearchApp() {
  return (
    <div>
      <SearchBar/>
    </div>
  );
}