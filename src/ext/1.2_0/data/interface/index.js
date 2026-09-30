var background = {
  "port": null,
  "message": {},
  "receive": function (id, callback) {
    if (id) {
      background.message[id] = callback;
    }
  },
  "connect": function (port) {
    chrome.runtime.onMessage.addListener(background.listener); 
   
    if (port) {
      background.port = port;
      background.port.onMessage.addListener(background.listener);
      background.port.onDisconnect.addListener(function () {
        background.port = null;
      });
    }
  },
  "send": function (id, data) {
    if (id) {
      if (background.port) {
        if (background.port.name !== "webapp") {
          chrome.runtime.sendMessage({
            "method": id,
            "data": data,
            "path": "interface-to-background"
          }, function () {
            return chrome.runtime.lastError;
          });
        }
      }
    }
  },
  "post": function (id, data) {
    if (id) {
      if (background.port) {
        background.port.postMessage({
          "method": id,
          "data": data,
          "port": background.port.name,
          "path": "interface-to-background"
        });
      }
    }
  },
  "listener": function (e) {
    if (e) {
      for (var id in background.message) {
        if (background.message[id]) {
          if ((typeof background.message[id]) === "function") {
            if (e.path === "background-to-interface") {
              if (e.method === id) {
                background.message[id](e.data);
              }
            }
          }
        }
      }
    }
  }
};

var config = {
  "error": function () {
    return chrome.runtime.lastError;
  },
  "port": {
    "name": '',
    "connect": function () {
      config.port.name = "win";
      document.documentElement.setAttribute("context", config.port.name);
      background.connect(chrome.runtime.connect({"name": config.port.name}));
    }
  },
  "load": function () {
    window.setTimeout(function () {
      background.send("load");
    }, 500);
   
    window.removeEventListener("load", config.load, false);
  },
  "capture": {
    "page": function (details, callback) {
      chrome.pageCapture.saveAsMHTML(details, function (e) {
        if (callback) callback(e);
      });
    }
  },
  "file": {
    "size": function (s) {
      if (s) {
        if (s >= Math.pow(2, 30)) {return (s / Math.pow(2, 30)).toFixed(1) + " GB"};
        if (s >= Math.pow(2, 20)) {return (s / Math.pow(2, 20)).toFixed(1) + " MB"};
        if (s >= Math.pow(2, 10)) {return (s / Math.pow(2, 10)).toFixed(1) + " KB"};
        return s + " B";
      } else {
        return '';
      }
    }
  },
  "downloads": {
    "id": null,
    "start": function (options, callback) {
      chrome.downloads.download(options, function (e) {
        if (callback) callback(e);
      });
    },
    "on": {
      "changed": async function (callback) {
        chrome.downloads.onChanged.addListener(async function (e) {
          callback(e);
        });
      }
    }
  },
  "end": async function (e) {
    if (e) {
      if (e.id) {
        if (e.id === config.downloads.id) {
          if (e.state) {
            if (e.state.current) {
              if (e.state.current === "complete") {                
                var svg = document.querySelector(".loader");
                svg.style.display = "none";

                window.setTimeout(async function () {
                  const _ = await fetch("http://doggame.local/ingestdownload", { method: 'POST' });
                  window.close();
                }, 500);
              }
            }
          }
        }
      }
    }
  },
  "start": function (e) {
    if (e) {
      var info = document.querySelector(".info");
      info.textContent = "Capturing the active tab, please wait...";
     
      window.setTimeout(function () {
        config.capture.page({"tabId": e.tab.id}, function (mhtml) {
          if (mhtml) {
            info.textContent = "Preparing to download, please wait...";
           
            window.setTimeout(function () {
              if (config.error() === undefined) {
                var blob = new Blob([mhtml], {"type": "application/x-mimearchive"});
                var hostname = (new URL(e.url ? e.url : e.tab.url)).hostname;
                info.textContent = "Downloading MHT, please wait...";
               
                window.setTimeout(function () {
                  if (blob && hostname) {
                    var url = URL.createObjectURL(blob);
                    var filename = hostname.replace("www.", '');
                   
                    if (url && filename) {
                      config.downloads.start({
                        "url": url,
                        "filename": filename + ".mht"
                      }, function (id) {
                        config.downloads.id = id;
                        URL.revokeObjectURL(url);
                       
                        info.textContent = "Save as MHT is completed! - File size " + config.file.size(blob.size);
                      });
                    }
                  }
                }, 500);
              }
            }, 500);
          }
        });
      }, 500);
    }
  }
};

config.port.connect();

config.downloads.on.changed(config.end);
background.receive("start", config.start);
window.addEventListener("load", config.load, false);
