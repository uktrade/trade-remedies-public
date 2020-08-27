// Progressive enhancement produces lightbox with list of organisations
define(function() {
    "use strict";
	var constructor = function(el) {
        // Called on the main
        el.on('click', _.bind(onClick,this));
	}

    function onClick(evt) {
        var target = $(evt.target);
        if(target.hasClass('no-debounce')) return;
        var tag = (target.prop('tagName') || '').toLowerCase();
        var type = (target.prop('type') || '').toLowerCase();
        var check = (type == 'submit') || (tag == 'a' && target.hasClass('button'));
        if(check) {
            if(target.attr('disabled')) {
                evt.preventDefault();
            }
            if(check) {
                setTimeout(function() {
                    target.attr('disabled','disabled')
                },0);
            }
        }
    }

    return constructor;
});
