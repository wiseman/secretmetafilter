goog.provide('SecretMefi.App');

goog.require('goog.net.cookies');
goog.require('goog.dom');


/**
 * SecretMefi App object.
 *
 * @constructor
 */
SecretMefi.App = function() {
};

/**
 * Initializes and starts the app.
 */
SecretMefi.App.prototype.start = function() {
  var colorElement = document.getElementById("color");
  colorElement.addEventListener(
    "change",
    goog.bind(this.colorChanged_, this),
    false);

  var colorPref = goog.net.cookies.get("color", "blue");
  if (colorPref) {
    this.setColor(colorPref);
    colorElement.value = colorPref;
  }
};


/**
 * Loads CSS for a color (blue or white).
 *
 * @param {string} color The desired color.
 * @private
 */
SecretMefi.App.prototype.setColor = function(color) {
  var cssUrl = null;
  if (color === "white") {
    cssUrl = "/static/white.css";
  } else {
    cssUrl = "/static/blue.css";
  }
  var dh = new goog.dom.DomHelper();
  dh.getElementsByTagNameAndClass("head")[0].appendChild(
    goog.dom.createDom(
      "link",
      {
        "rel": "stylesheet",
        "type": "text/css",
        "href": cssUrl
      }));
};


/**
 * Event handler for sticky color dropdown menu.
 *
 * @param {Object} e The event.
 */
SecretMefi.App.prototype.colorChanged_ = function(e) {
  var colorPref = e.target["value"];
  this.setColor(colorPref);
  goog.net.cookies.set("color", colorPref);
}


// Ensures the symbol will be visible after compiler renaming.
goog.exportSymbol("SecretMefi.App", SecretMefi.App);
goog.exportSymbol("SecretMefi.App.prototype.start",
                  SecretMefi.App.prototype.start);
