var config = {};

config.welcome = {
  set lastupdate (val) {cat.storage.write("lastupdate", val)},
  get lastupdate () {return cat.storage.read("lastupdate") !== undefined ? cat.storage.read("lastupdate") : 0}
};

config.interface = {
  set size (val) {cat.storage.write("interface.size", val)},
  set context (val) {cat.storage.write("interface.context", val)},
  get size () {return cat.storage.read("interface.size") !== undefined ? cat.storage.read("interface.size") : config.interface.default.size},
  get context () {return cat.storage.read("interface.context") !== undefined ? cat.storage.read("interface.context") : config.interface.default.context},
  "default": {
    "context": "win",
    "size": {
      "width": 500, 
      "height": 300
    }
  }
};
