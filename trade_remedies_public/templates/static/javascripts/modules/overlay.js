
define([], function() {
	var stack = [];
	var baseZIndex = 100;

	function createOverlay(options) {
		// create a new overlay, higher than any previous ones
		var self = this;
		var overlay = $('<div><div class="semi-transparent '+(options && options.opacity ? options.opacity : 'op66')+'"></div></div>');
		//var overlay = $(document.createElement('div'));
		overlay.addClass('overlay').prependTo(document.body);

		overlay.css({zIndex:baseZIndex+stack.length}).addClass('active');		
		var top = stack[stack.length-1];
		if(top) {
			top.removeClass('active');
		} else {
			overlay.find('.semi-transparent').hide().fadeIn(200);
		}
		stack.push(overlay);
		return overlay;
	}

	function destroyOverlay(overlay) {
		var thisOverlay = overlay;
		// find the overlay in the stack
		var idx = stack.length-1;
		while(idx > 0 && stack[idx] != overlay) {
			idx--;
		}
		if(stack[idx] === overlay) {
			stack.splice(idx,1);
			var top = stack[stack.length-1];
			if(top) {
				top.addClass('active');
					overlay.remove();
			} else {
				overlay/*.find('.semi-transparent')*/.fadeOut(200,function() {
					thisOverlay.remove();
				});
			}
		} else {
			console.error('Attempt to clear overlays out of sequence')
		}
	}
	return {
		createOverlay:createOverlay,
		destroyOverlay: destroyOverlay
	}
})

