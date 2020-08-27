// Copies the text from the value of an input to a visually-hidden tag for accessibility
define([], function() {
    "use strict";

	function constructor(el) {
		if(!el[0].copyValToLink) {
			el[0].copyValToLink = this;
			el.on('change', function() {
	        	el.hiddenTag = el.hiddenTag || el.parent().find('.replace-with-value');
	        	el.hiddenTag.text(el.val());	
			})
    	}
	}

	return constructor;
});
