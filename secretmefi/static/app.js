goog.provide('SecretMefi.App');

goog.require('goog.net.cookies');
goog.require('goog.dom');


/**
 * SecretMefi App object.
 *
 * @constructor
 */
SecretMefi.App = function() {
  this.colorPref = "blue";
};

/**
 * Loads CSS according to the user's preference as stored in a cookie.
 */
SecretMefi.App.prototype.setColorFromCookie = function() {
  this.colorPref = goog.net.cookies.get("color", this.colorPref);
  if (this.colorPref) {
    this.setColor(this.colorPref);
  }
};


SecretMefi.App.prototype.addColorEventHandler = function(element) {
  if (this.colorPref) {
    element.value = this.colorPref;
  }
  element.addEventListener(
    "change",
    goog.bind(this.colorChanged_, this),
    false);
}


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
goog.exportSymbol("SecretMefi.App.prototype.setColorFromCookie",
                  SecretMefi.App.prototype.setColorFromCookie)
goog.exportSymbol("SecretMefi.App.prototype.addColorEventHandler",
                  SecretMefi.App.prototype.addColorEventHandler);
