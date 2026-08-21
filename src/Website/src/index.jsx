import React from "react";
import { createRoot } from "react-dom/client";
import { SearchApp } from "./search";
import "./uploadHandler";
import "./index.css";
import { VisualizerApp } from "./visualizer";

function App() {
  let hash = window.location.hash;

  return <>
    {hash == "#debug" ? <VisualizerApp/> : <SearchApp/>}
  </>
}

const root = createRoot(document.getElementById("root"));
root.render(<App/>);
