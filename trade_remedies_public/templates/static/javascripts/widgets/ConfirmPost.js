define(['modules/helpers'], function(helpers) {
    "use strict";
    // Intercept a form post and put up a confirmation pop-up
	var constructor = function(el) {
		// el is the outer div, so find the input
		var self = this;
		this.el = el;
		this.message = this.el.find('.confirmation-message').html();
		this.title = this.el.find('.confirmation-title').html();
		this.el.on('submit',_.bind(formSubmit,this));
	}

	function formSubmit(evt) {
		var self = this;
		if(!self.allowSubmit) {
			evt.preventDefault();
			require(['modules/Lightbox'], function(Lightbox) {
				self.lightbox = new Lightbox({title:self.title || 'Confirmation', message: self.message || 'Are you sure?', buttons:{yes:1,no:1}})
				self.lightbox.getContainer().find('button[value="yes"]').on('click', function() {
					self.allowSubmit = true;
					self.el.submit();
					delete self.allowSubmit;
	   			});
	   		});
	   		return false;
		}
	}

	return constructor;
});
