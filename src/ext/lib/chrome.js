var cat = {};

cat.error = function () {
  return chrome.runtime.lastError;
};

cat.button = {
  "on": {
    "clicked": function (callback) {
      chrome.action.onClicked.addListener(function (e) {
        cat.storage.load(function () {
          callback(e);
        }); 
      });
    }
  }
};

cat.contextmenu = {
  "create": function (options, callback) {
    if (chrome.contextMenus) {
      chrome.contextMenus.create(options, function (e) {
        if (callback) callback(e);
      });
    }
  },
  "on": {
    "clicked": function (callback) {
      if (chrome.contextMenus) {
        chrome.contextMenus.onClicked.addListener(function (e) {
          cat.storage.load(function () {
            callback(e);
          });
        });
      }
    }
  }
};

cat.tab = {
  "query": {
    "index": function (callback) {
      chrome.tabs.query({"active": true, "currentWindow": true}, function (tabs) {
        if (tabs && tabs.length) {
          callback(tabs[0].index);
        } else callback(undefined);
      });
    },
    "active": function (callback) {
      chrome.tabs.query({"active": true, "currentWindow": true}, function (tabs) {
        if (tabs && tabs.length) {
          callback(tabs[0]);
        }
      });
    }
  },
  "open": function (url, index, active, callback) {
    var properties = {
      "url": url, 
      "active": active !== undefined ? active : true
    };
    
    if (index !== undefined) {
      if (typeof index === "number") {
        properties.index = index + 1;
      }
    }
    
    chrome.tabs.create(properties, function (tab) {
      if (callback) callback(tab);
    }); 
  }
};

cat.storage = {
  "local": {},
  "read": function (id) {
    return cat.storage.local[id];
  },
  "update": function (callback) {
    if (cat.session) cat.session.load();
    
    chrome.storage.local.get(null, function (e) {
      cat.storage.local = e;
      if (callback) {
        callback("update");
      }
    });
  },
  "write": function (id, data, callback) {
    let tmp = {};
    tmp[id] = data;
    cat.storage.local[id] = data;
    
    chrome.storage.local.set(tmp, function (e) {
      if (callback) {
        callback(e);
      }
    });
  },
  "load": function (callback) {
    const keys = Object.keys(cat.storage.local);
    if (keys && keys.length) {
      if (callback) {
        callback("cache");
      }
    } else {
      cat.storage.update(function () {
        if (callback) callback("disk");
      });
    }
  } 
};

cat.window = {
  set id (e) {
    cat.storage.write("window.id", e);
  },
  get id () {
    return cat.storage.read("window.id") !== undefined ? cat.storage.read("window.id") : '';
  },
  "create": function (options, callback) {
    chrome.windows.create(options, function (e) {
      if (callback) callback(e);
    });
  },
  "get": function (windowId, callback) {
    chrome.windows.get(windowId, function (e) {
      if (callback) callback(e);
    });
  },
  "update": function (windowId, options, callback) {
    chrome.windows.update(windowId, options, function (e) {
      if (callback) callback(e);
    });
  },
  "remove": function (windowId, callback) {
    chrome.windows.remove(windowId, function (e) {
      if (callback) callback(e);
    });
  },
  "query": {
    "current": function (callback) {
      chrome.windows.getCurrent(callback);
    }
  },
  "on": {
    "removed": function (callback) {
      chrome.windows.onRemoved.addListener(function (e) {
        cat.storage.load(function () {
          callback(e);
        }); 
      });
    }
  }
};

cat.interface = {
  "message": {},
  "path": chrome.runtime.getURL("data/interface/index.html"),
  set id (e) {
    cat.storage.write("interface.id", e);
  },
  get id () {
    return cat.storage.read("interface.id") !== undefined ? cat.storage.read("interface.id") : '';
  },
  "receive": function (id, callback) {
    cat.interface.message[id] = callback;
  },
  "close": function () {
    if (cat.interface.id) {
      cat.window.remove(cat.interface.id);
    }
  },
  "send": function (id, data) {
    chrome.runtime.sendMessage({
      "data": data,
      "method": id,
      "path": "background-to-interface"
    });
  },
  "create": function (url, callback) {
    cat.window.query.current(function (win) {
      cat.window.id = win.id;
      url = url ? url : cat.interface.path;
      
      var width = config.interface.size.width;
      var height = config.interface.size.height;
      var top = win.top + Math.round((win.height - height) / 2);
      var left = win.left + Math.round((win.width - width) / 2);
      
      cat.window.create({
        "url": url,
        "top": top,
        "left": left,
        "width": width,
        "type": "popup",
        "height": height
      }, function (e) {
        cat.interface.id = e.id;
        if (callback) callback(true);
      });
    });
  }
};

cat.on = {
  "management": function (callback) {
    chrome.management.getSelf(callback);
  },
  "uninstalled": function (url) {
    chrome.runtime.setUninstallURL(url, function () {});
  },
  "installed": function (callback) {
    chrome.runtime.onInstalled.addListener(function (e) {
      cat.storage.load(function () {
        callback(e);
      });
    });
  },
  "startup": function (callback) {
    chrome.runtime.onStartup.addListener(function (e) {
      cat.storage.load(function () {
        callback(e);
      });
    });
  },
  "connect": function (callback) {
    chrome.runtime.onConnect.addListener(function (e) {
      cat.storage.load(function () {
        if (callback) callback(e);
      });
    });
  },
  "storage": function (callback) {
    chrome.storage.onChanged.addListener(function (changes, namespace) {
      cat.storage.update(function () {
        if (callback) {
          callback(changes, namespace);
        }
      });
    });
  },
  "message": function (callback) {
    chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
      cat.storage.load(function () {
        callback(request, sender, sendResponse);
      });
      
      return true;
    });
  }
};
