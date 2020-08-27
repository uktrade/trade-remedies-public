define([], function() {
    "use strict";
	var constructor = function(el) {
		// el is the outer div, so find the input
		var self = this;
		this.el = el;
		$(el).on('click', _.bind(onClick, this));
	}
	function showUploader(el) {
	// Pass the file panel of the el to expand the uploader panel of
		$('.file-panel.expanded').removeClass('expanded').closest('.ulpoad-row').removeClass('expanded');
		el.addClass('expanded').closest('.upload-row').addClass('expanded');
	}

	function onClick(evt) {
		var target = $(evt.target);
		if(target.val() == 'btn-add-another') {
			this.btn_add_another = target;
			showUploader($('.new-file-uploader .file-panel'));
			this.btn_add_another.hide();
		}
		if(target.val()=='btn-upload') {
			showUploader(target.closest('.file-panel'));
			this.btn_add_another && this.btn_add_another.show();
		}

	}

	return constructor;
});
