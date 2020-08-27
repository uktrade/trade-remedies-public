define(function() {
    "use strict";
	var constructor = function(el) {
	this.parts = el.find('input[type="text"]');
	this.parts.on('keyup',_.bind(onKeyup,this))
		.on('keypress',_.bind(onKeypress,this))
		.on('focus',focus)
		.on('paste',_.bind(paste,this));
	}

	function paste(evt) {
		// allows pasting of dates in 
		var str = evt.originalEvent.clipboardData.getData('text/plain'),bits;
		if(str && (bits=/(\d\d)[\/\\.-]?(\d\d)[\/\\.-]?(\d\d\d\d)/.exec(str))) {
			this.parts.each(function(idx) {
				$(this).val(bits[idx+1]);
			})
			return false;
		}
	}	

	function focus() {
		$(this.select());
	};

	function onKeypressDef(e) {
		var el = e.target;
		var val;
		// find the target in our list
		for(var idx = 0; idx < this.parts.length; idx++) {
			if(this.parts[idx] === el) break;
		}
		if((val = $(el).val()).length == 2) {
			if(idx === (this.parts.length-1)) {
				if(!({'19':1,'20':1}[val])) {
					$(el).val(((val-0) < 30 ? '20' : '19')+ val); // years before 2030 are considered 20th cent
				}
			}
			if(idx < this.parts.length - 1) {
				this.parts[idx+1].select();
			}
		}
		if((idx > 0) && (val == '') && (e.which === 8)) { // backspace on empty field goes back one
			this.parts[idx-1].select()
		}
	}
	function onKeyup(e) { // needed to trap the backspace
		if(e.which === 8) {
			return false;
			//onKeypress.call(this,e);	
		}
	}

	function onKeypress(e) {
		var self = this;
		var evt = e;
		if((evt.which > 32) &&  (/\D/.test(String.fromCharCode(evt.which)))) return false; // only let numeric chars through
		_.defer(function(){
			onKeypressDef.call(self,evt);
		});
	}
	return constructor;
});
