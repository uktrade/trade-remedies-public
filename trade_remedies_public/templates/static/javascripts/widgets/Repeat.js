define(['modules/helpers'], function(helpers) {
    "use strict";
    // A repeat block has a list of block ids as a parameter, then copies them 
	var constructor = function(el) {
		// el is the outer div, so find the input
		var self = this;
		this.blockCount = 0;
		this.el = el;
		this.button = el.find('button').first();
		this.repeatIds = (this.button.attr('data-repeats') || '').split(':');
		this.form = this.el.parents('form');

		var repeatMap = {};
		_.each(this.repeatIds, function(id) {
			repeatMap[id] = 1;
		});
		this.blocks = [];

		el.siblings('.form-group').each(function() {
			var testEl = $(this);
			var fieldName = testEl.attr('data-fieldname');
			if(fieldName in repeatMap) {
				var blockId = repeatMap[fieldName]-1;
				var block = self.blocks[blockId] = (self.blocks[blockId] || []);
				block.push(testEl);
				repeatMap[fieldName]++;
			}
		});
		// Now, re-render the fields into blocks
		self.container = $('<dev></div>');
		self.el.before(self.container);

		_.each(this.blocks, function(block, index) {
			self.container.append(self.buildBlock(block));
		});
		this.container[this.blockCount == 1 ? 'addClass' : 'removeClass']('hide-remove-buttons');
		this.button.on('click',_.bind(onClick,this));
	}

	function onClick() {
		var self = this;
		var block = [];
		_.each(this.blocks[0], function(el) {
			var clone = el.clone();
			clone.find('input,select,textarea').val('');
			block.push(clone);
			//self.button.before(clone);
		})
		self.container.append(self.buildBlock(block));
		setButtons.call(this);
	}

	function removeClick(el) {
		if(this.blockCount > 1) {
			this.blockCount--;
			$(el).parents('.repeat-block').remove();
		}
		setButtons.call(this);
	}

	function setButtons() {
		this.container[this.blockCount == 1 ? 'addClass' : 'removeClass']('hide-remove-buttons');
	}

	function buildBlock(block) {
		var self = this;
		var container = $('<div class="repeat-block"><div class="inner"><div class="question-list"></div><button class="button pull-right btn-remove" type="button">Remove</button></div></div>');
		_.each(block, function(el) { 
			container.find('.inner .question-list').append(el);
		})
		container.find('button.btn-remove').on('click',function() {removeClick.call(self,this)});
		self.blockCount++;
		return container;
	}

	constructor.prototype = {
		buildBlock: buildBlock
	}

	return constructor;
});
