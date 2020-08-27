define(function() {
    "use strict";
	var constructor = function(el) {
		this.el = el;
		el.addClass('sortable');
		this.header = this.el.find('th').first().closest('tr');
		this.header.on('click', _.bind(onClick, this));
		this.tbody = this.el.find('tbody').first();
		if(!this.header.find('.sort-indicator').length) {
			decorateColumns.call(this);
		}
		getRows.call(this);
	}

	function onClick(evt) {
		(this.selectedHeader || this.header.find('.sort-active')).removeClass('sort-active');
		this.selectedHeader =  $(evt.target).closest('th');
		this.selectedHeader.addClass('sort-active');
		var isAscending = this.selectedHeader.hasClass('asc');
		this.selectedHeader.toggleClass('asc');
		var selectedHeaderIndex = this.header.find('th').index(this.selectedHeader);

		sortTable.call(this, selectedHeaderIndex, isAscending ? -1 : 1);
	}

	function decorateColumns() {
		this.header.find('th').each(function() {
			var target = $(this);
			if(!target.hasClass('no-sort')) {
				var sortIndicator = $('<a class="sort-indicator pull-left" href="javascript:void(0)"><span class="visually-hidden">Sort by '+$(this).text()+'</span></a>');
				target.append(sortIndicator);
			}
		})
	}

	function getRows() {
		var rows = this.rows = [];
		this.el.find('tbody tr').each(function(tr) {
			rows.push({tr:this, cols:$(this).find('td')});
		});
	}

	function sortTable(colIndex, direction) {
		var self = this;

		self.rows = self.rows.sort(function(rowA,rowB) {
			var ea = rowA.cols[colIndex], eb = rowB.cols[colIndex];
			ea.sortval = ea.sortval || $(ea).attr('sortval') || $(ea).text();
			eb.sortval = eb.sortval || $(eb).attr('sortval') || $(eb).text();
			var ca = ea.sortval, cb = eb.sortval;
			return (ca > cb ? 1 : (ca < cb ? -1 : 0)) * direction;
		});
		_.each(self.rows, function(row, idx) {
			self.tbody.prepend(row.tr);
			// $(row.tr).setClass('odd-row', !(idx % 2)); for zebra stripes
		}); 
	}

	return constructor;
});
