var core = {
  "start": function () {
    core.load();
  },
  "install": function () {
    core.load();
  },
  "load": function () {
    cat.interface.id = '';

    cat.contextmenu.create({
      "contexts": ["page"],
      "id": "save-as-mhtml", 
      "title": "Save page as .mhtml"
    }, cat.error);
  },
  "action": {
    "storage": function (changes, namespace) {
  
    },
    "button": function (url) {
      if (url) {
        cat.tab.query.active(function (tab) {
          if (tab) {
            core.interface.create();
            core.interface.data = {
              "url": url,
              "tab": tab
            };
          }
        });
      }
    }
  },
  "interface": {
    "data": null,
    "update": function () {
      var data = core.interface.data;
      if (data) {
        cat.interface.send("start", {
          "url": data.url,
          "tab": {
            "id": data.tab.id,
            "url": data.tab.url
          }
        });
      }
    },
    "create": function () {
      if (cat.interface.id) {
        cat.window.get(cat.interface.id, function (win) {
          if (win) {
            cat.window.update(cat.interface.id, {"focused": true});
          } else {
            cat.interface.id = '';
            cat.interface.create();
          }
        });
      } else {
        cat.interface.create();
      }
    }
  }
};

cat.button.on.clicked(function (e) {
  core.action.button(e.url);
});

cat.contextmenu.on.clicked(function (e) {
  core.action.button(e.pageUrl);
});

cat.interface.receive("load", function () {
  core.interface.update();
});

cat.window.on.removed(function (e) {
  if (e === cat.interface.id) {
    cat.interface.id = '';
  }
});

cat.on.startup(core.start);
cat.on.connect(cat.connect);
cat.on.installed(core.install);
cat.on.storage(core.action.storage);