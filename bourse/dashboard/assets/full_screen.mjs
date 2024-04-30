/**
 * Toggle full screen mode chart container
 */
window.dash_clientside = Object.assign({}, window.dash_clientside, {
  clientside: {
    toggle_full_screen: function (nClicks) {
      var elem = document.getElementById("graph-container");

      if (elem.requestFullscreen) {
        elem.requestFullscreen();
      } else if (elem.webkitRequestFullscreen) { /* Safari */
        elem.webkitRequestFullscreen();
      } else if (elem.msRequestFullscreen) { /* IE11 */
        elem.msRequestFullscreen();
      }

      return nClicks;
    }
  }
});