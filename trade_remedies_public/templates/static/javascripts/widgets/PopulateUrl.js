// Typeahead - using the jqueryUI autocomplete widget
define(function() {
    "use strict";
	var constructor = function(el) {
       el.val(window.location.href);
	}
	return constructor;
});
