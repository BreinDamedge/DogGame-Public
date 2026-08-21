function readFile(file) {
    return new Promise((resolve, reject) => {
        let reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(new Error("Cannot read file"));
        reader.readAsText(file);
    });
}

document.addEventListener("dragover", (e) => {
	e.preventDefault();
});

document.addEventListener("drop", async (e) => {
    e.preventDefault();

	let files = e.dataTransfer.files;
	let file = files.length == 1 ? files[0] : null;

	if (file == null) {
		return;
	}

	let contents = await readFile(file);
	let upload = await fetch("/documents/upload", {
		headers: {
			'Content-Type': 'application/octet-stream'
		},
		method: "POST",
		body: contents
	});

	let data = await upload.json();

    alert(data["message"]);
});