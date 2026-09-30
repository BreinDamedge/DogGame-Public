cat.version = function () {return chrome.runtime.getManifest().version};
cat.homepage = function () {return chrome.runtime.getManifest().homepage_url};

if (!navigator.webdriver) {
  // cat.on.uninstalled(cat.homepage() + "#uninstall");
  cat.on.installed(function (e) {
    cat.on.management(function (result) {
      if (result.installType === "normal") {
        cat.tab.query.index(function (index) {
          var previous = e.previousVersion !== undefined && e.previousVersion !== cat.version();
          var doupdate = previous && parseInt((Date.now() - config.welcome.lastupdate) / (24 * 3600 * 1000)) > 45;
          if (e.reason === "install" || (e.reason === "update" && doupdate)) {
            var url = cat.homepage();
            cat.tab.open(url, index, e.reason === "install");
            config.welcome.lastupdate = Date.now();
          }
        });
      }
    });
  });
}

cat.on.message(function (request) {
  if (request) {
    if (request.path === "interface-to-background") {
      for (var id in cat.interface.message) {
        if (cat.interface.message[id]) {
          if ((typeof cat.interface.message[id]) === "function") {
            if (id === request.method) {
              cat.interface.message[id](request.data);
            }
          }
        }
      }
    }
  }
});

cat.on.connect(function (port) {
  if (port) {
    if (port.name) {
      if (port.name in cat) {
        cat[port.name].port = port;
      }
     
      if (port.sender) {
        if (port.sender.tab) {
          cat.interface.port = port;
        }
      }
    }
   
    port.onDisconnect.addListener(function (e) {
      cat.storage.load(function () {
        if (e) {
          if (e.name) {
            if (e.name in cat) {
              cat[e.name].port = null;
            }
           
            if (e.sender) {
              if (e.sender.tab) {
                cat.interface.port = null;
              }
            }
          }
        }
      });
    });
   
    port.onMessage.addListener(function (e) {
      cat.storage.load(function () {
        if (e) {
          if (e.path) {
            if (e.port) {
              if (e.port in cat) {
                if (e.path === (e.port + "-to-background")) {
                  for (var id in cat[e.port].message) {
                    if (cat[e.port].message[id]) {
                      if ((typeof cat[e.port].message[id]) === "function") {
                        if (id === e.method) {
                          cat[e.port].message[id](e.data);
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      });
    });
  }
});
