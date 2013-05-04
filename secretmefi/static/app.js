goog.provide('SecretMefi.App');

goog.require('goog.net.cookies');

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
  var colorElement = document.getElementById('color');
  colorElement.addEventListener(
    "change",
    goog.bind(this.colorChanged, this),
    false);

  var colorPref = goog.net.cookies.get('color');
  if (colorPref) {
    this.setColor(colorPref);
    colorElement.value = colorPref;
  }
};

SecretMefi.App.prototype.setColor = function(color) {
  if (color === "blue") {
    document.getElementById("white-css").setAttribute(
      "disabled", "disabled");
    document.getElementById("blue-css").removeAttribute(
      "disabled");
  } else {
    document.getElementById("blue-css").setAttribute(
      "disabled", "disabled");
    document.getElementById("white-css").removeAttribute(
      "disabled");
  }
};

SecretMefi.App.prototype.colorChanged = function(e) {
  var colorPref = e.target['value'];
  this.setColor(colorPref);
  goog.net.cookies.set('color', colorPref);
}



// Ensures the symbol will be visible after compiler renaming.
goog.exportSymbol('SecretMefi.App', SecretMefi.App);
goog.exportSymbol('SecretMefi.App.prototype.start', SecretMefi.App.prototype.start);
