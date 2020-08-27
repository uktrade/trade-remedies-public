// Enable a button based on a checkbox
define([], function() {
    "use strict";

	function constructor(el) {
        var selector = el.attr('data-selector');
        var checked = el.prop('checked');
        var el = $(selector);
        el.prop('disabled',!checked);
	}

	return constructor;
});