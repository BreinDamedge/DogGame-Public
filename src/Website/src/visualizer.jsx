import React, { useRef, useState, useEffect } from "react"
import * as d3 from "d3";
import { rankerOptions } from "./search.jsx";

function preprocessMetadata(data) {
    let urlToData = {};
    let nodes = [];

    for (let value of data) {
        let id = value[0];
        let content = JSON.parse(value[1]);

        delete content["text"];

        if (content.url == null) {
            content.url = id;
        }

        urlToData[content.url] = { id, ...content };
    }

    for (let data of Object.values(urlToData)) {
        let references = [];

        if (data.references != null) {
            for (let url of data.references) {
                if (urlToData[url] != null) {
                    references.push(url);
                }
            }
        }

        nodes.push({
            id: data.url,
            document: data.id,
            title: data.title,
            references: references
        });
    }

    return nodes;
}

export function VisualizerApp() {
    const [metadataGraph, setMetadataGraph] = useState([]);
    const [searchResults, setSearchResults] = useState([]);
    const [searchQuery, setSearchQuery] = useState("");
    const [ranker, setRanker] = useState(rankerOptions[0]);
    const [fetchingMetadata, setFetchingMetadata] = useState(false);
    const [fetchingResults, setFetchingResults] = useState(false);
    
    const svgReference = useRef();

    useEffect(() => {
        const nodes = metadataGraph.map(x => ({...x}));
        const links = [];
        const scoresByDocument = {};
        
        for (let result of searchResults) {
            scoresByDocument[result.id] = result.score;
        }

        for (let node of nodes) {
            let score = scoresByDocument[node.document];

            if (score != null) {
                node.inQuery = true;
                node.inQueryScore = score;
            } else {
                node.inQuery = false;
                node.inQueryScore = 0;
            }

            for (let reference of node.references) {
                links.push({source: node.id, target: reference, inQuery: node.inQuery, inQueryScore: node.inQueryScore});
            }
        }
        
        const width = 928;
        const height = 600;
        const inQueryColor = "rgb(161, 13, 181)";
        const inQuerySignificantColor = "rgb(255, 0, 0)";

        svgReference.current.innerHTML = "";

        const svg = d3
            .select(svgReference.current)
            .attr("width", width)
            .attr("height", height)
            .attr("viewBox", [-width / 2, -height / 2, width, height])
            .attr("style", "max-width: 100%; height: auto;");

        const zoomable = svg.append("g");
        const significantScore = 0.01;

        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id))
            .force("charge", d3.forceManyBody())
            .force("x", d3.forceX())
            .force("y", d3.forceY());

        const link = zoomable.append("g")
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("stroke", d => d.inQuery ? (d.inQueryScore >= significantScore ? inQuerySignificantColor : inQueryColor) : "#555");

        const node = zoomable.append("g")
            .attr("font-size", "5px")
            .attr("font-family", "Consolas")
            .selectAll("g")
            .data(nodes)
            .join("g");

        node.append("circle")
            .attr("fill", "white")
            .attr("stroke", d => d.inQuery ? (d.inQueryScore >= significantScore ? inQuerySignificantColor : inQueryColor) : "black")
            .attr("r", 3.5);

        node.append("text")
            .attr("x", 5)
            .attr("y", 1.75)
            .attr("fill", d => d.inQuery ? (d.inQueryScore >= significantScore ? inQuerySignificantColor : inQueryColor) : "rgba(0, 0, 0, 0.5)")
            .text(d => `${d.inQuery ?  "[" + d.inQueryScore.toFixed(2) + "] " : ""}${d.title}`);

        const zoom = d3.zoom()
            .on('zoom', (e) => zoomable.attr("transform", e.transform));

        const drag = d3.drag()
            .on("start", (e) => {
                if (!e.active) {
                    simulation.alphaTarget(0.3)
                        .restart();
                }

                e.subject.fx = e.subject.x;
                e.subject.fy = e.subject.y;
            })
            .on("drag", (e) => {
                e.subject.fx = e.x;
                e.subject.fy = e.y;
            })
            .on("end", (e) => {
                if (!e.active) {
                    simulation.alphaTarget(0);
                }

                e.subject.fx = null;
                e.subject.fy = null;
            });

        svg.call(zoom);
        node.call(drag);

        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
        
            node
                .attr("transform", d => `translate(${d.x}, ${d.y})`);
        });
    }, [metadataGraph, searchResults]);

    async function processSearch() {
        setFetchingResults(true);

        let response = await fetch("documents/search", {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            method: "POST",
            body: JSON.stringify({"query": searchQuery, "ranker": ranker})
        });

        setFetchingResults(false);

        if (response.status == 200) {
            let data = await response.json();
        
            setSearchResults(data["results"]);
        } else {
            alert("Error occured while searching");
        }
    }

    useEffect(async () => {
        setFetchingMetadata(true);

        let response = await fetch("dump/metadata", {
            headers: {
                'Accept': 'application/json',
            },
            method: "POST"
        });

        setFetchingMetadata(false);

        if (response.status == 200) {
            let data = await response.json();

            setMetadataGraph(preprocessMetadata(data));
        } else {
            alert("Error occured while fetching metadata");
        }
    }, []);

    return <>
        <h1>Search visualizer</h1>

        <input type="text" value={searchQuery} onChange={(x) => setSearchQuery(x.target.value)}/>

        <select onChange={e => setRanker(e.target.value)}>
            {rankerOptions.map(x => <option>{x}</option>)}
        </select>

        <button onClick={processSearch}>Go</button>

        {fetchingMetadata ? <b>Fetching metadata...</b> : <></>}
        {fetchingResults ? <b>Fetching results...</b> : <></>}

        <p>Search results: {searchResults.length}, Metadata size: {metadataGraph.length}</p>

        <svg ref={svgReference} />

        <h3>Significant results</h3>
        
        <ol>
            {searchResults.filter(x => x.score >= 0.01).map(x => <div key={x.id}>
                <li>{x.score.toFixed(2)} - {x.name}</li>
            </div>)}
        </ol>
    </>;
}