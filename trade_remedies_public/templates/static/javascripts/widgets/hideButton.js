// Hide things when a button is clicked
define([], function() {
    "use strict";

	function constructor(el) {
        var selector = el.attr('data-selector');
        el.on('click', function() {
        	$(selector).hide();	
        });
	}

	return constructor;
});