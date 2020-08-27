define(['modules/helpers'], function(helpers) {
	var tpText = _.template('<label><%=title%></label><input type="text" name="<%=field%>" value="<%=obj[field]%>">');
	var tpArea = _.template('<label><%=title%></label><textarea name="<%=field%>"><%=obj[field]%></textarea>');
	var tpSelect = _.template('<label><%=title%></label><select name="<%=field%>" value="<%=obj[field]%>">\
		<option value="label" <% if(obj[field]=="label") { %> selected<%}%> >Label</option>\
		<option value="text" <% if(obj[field]=="text") { %> selected<%}%> >Text box</option>\
		<option value="textArea" <% if(obj[field]=="textArea") { %> selected<%}%> >Text area</option>\
		<option value="select" <% if(obj[field]=="select") { %> selected<%}%> >Select</option>\
		<option value="checkset" <% if(obj[field]=="checkset") { %> selected<%}%> >Checkboxes</option>\
		<option value="radioset" <% if(obj[field]=="radioset") { %> selected<%}%> >Radio buttons</option>\
		<option value="fileupload" <% if(obj[field]=="fileupload") { %> selected<%}%> >File upload(bucket)</option>\
		<option value="confidentialupload" <% if(obj[field]=="confidentialupload") { %> selected<%}%> >Confidential file upload</option>\
		<option value="fileuploadtemplate" <% if(obj[field]=="fileuploadtemplate") { %> selected<%}%> >File upload(template)</option>\
		<option value="filedownload" <% if(obj[field]=="filedownload") { %> selected<%}%> >File download</option>\
		<option value="date" <% if(obj[field]=="date") { %> selected<%}%> >Date</option>\
		<option value="typeahead" <% if(obj[field]=="typeahead") { %> selected<%}%> >Type-ahead</option>\
		<option value="table" <% if(obj[field]=="table") { %> selected<%}%> >Table(template)</option>\
		<option value="blockrepeat" <% if(obj[field]=="blockrepeat") { %> selected<%}%> >Block Repeat</option>\
		<option value="review" <% if(obj[field]=="review") { %> selected<%}%> >Review block</option>\
		<option value="submit" <% if(obj[field]=="submit") { %> selected<%}%> >Submit</option>\
		</select>');

	var tpCheckbox = _.template('<label><%=title%></label><div><div>Yes<input class="nofloat" type="radio" name="<%=field%>" <% if(obj[field]) { print(\'checked="checked"\') } %> value="True" ></div><div>No:<input type="radio" class="nofloat" name="<%=field%>" <% if(!obj[field]) { print(\'checked="checked"\') } %> value="False" ></div></div>')
	var tpRo = _.template('<label><%=title%></label><span><%=obj[field]%></span>');

	var tp = _.template('\
		<form>\
		<div class="column-one-half">\
			<div><%= tpSelect({title:"Field type",field:"fieldType",obj:obj}) %></div>\
			<div><%= tpText({title:"Field name",field:"fieldName",obj:obj}) %></div>\
			<div><%= tpText({title:"Short name",field:"name",obj:obj}) %></div>\
		</div>\
		<div class="column-one-half">\
			<div><%= tpText({title:"Order",field:"order",obj:obj}) %></div>\
			<div><%= tpText({title:"Option group",field:"optionGroup",obj:obj}) %></div>\
			<div><%= tpCheckbox({title:"Mandatory",field:"mandatory",obj:obj}) %></div>\
		</div>\
		<div class="clear"></div>\
		<div><%= tpArea({title:"Label",field:"label",obj:obj}) %></div>\
		<div><%= tpArea({title:"Hint",field:"hint",obj:obj}) %></div>\
		<div><%= tpArea({title:"Options",field:"options",obj:obj}) %></div>\
		<div><button type="button" class="button dlg-close" value="cut">Cut to clipboard</button></div>\
		</form>');

	var pageTemplate = _.template('\
		<form>\
		<div class="column-one-half">\
		<% if(obj.id) { %><div><%= tpRo({title:"Page id",field:"id",obj:obj}) %></div><% } %>\
		<div><%= tpText({title:"Page title",field:"title",obj:obj}) %></div>\
		<div><%= tpText({title:"Order",field:"order",obj:obj}) %></div>\
		<div><%= tpText({title:"Parent id",field:"parent_id",obj:obj}) %></div>\
		</div>\
		<% if(obj.id) { %>\
			<div class="column-one-half">\
			<div class="block-space"><button type="button" class="button dlg-close" value="createChild">Create child page</button></div>\
			<div class="block-space"><button type="button" class="button dlg-close" value="createSibling">Create sibling page</button></div>\
			<div class="block-space"><button type="button" class="button dlg-close" value="deletePage">Delete page</button></div></div>\
			</div>\
		<% } %>\
		<div class="column-full-width">\
		<div><%= tpArea({title:"Options",field:"options",obj:obj}) %></div>\
		</div>\
		</form>\
	')

	var form = $('form.dd-form');
	var editMode = localStorage.config == 'on';

	var menu; // the menu element
	var menuShowing;

	function clipboard(mode, action) {
		var details = getDetails();
		$.ajax({
			method: 'get',
			dataType: "json",
			url:'/formbuilder/page',
			data: {'clipboard':'count'}
		}).then(function(content) {
			var message = content.count > 0 ? "Are you sure you want to "+mode+" "+content.count+" clipboard items?" : "Your clipboard is empty";
			require(['modules/Lightbox'], function(Lightbox) {
				(new Lightbox({title:'Clipboard '+mode, message:message, buttons:{ok:1,cancel:1}}))
					.getContainer().find('button[value=ok]').on('click', function() {
						details.action = action;
							$.ajax({
							  method: 'post',
							  url:'/formbuilder/page',
							  data: helpers.map(details)
						  	}).then(function(content) {
						  		window.location.reload()
						  	})
					})
			});
		});		
	};

	function deletePage(details) {
		details.action="delete";
		require(['modules/Lightbox'], function(Lightbox) {
			(new Lightbox({title:'Delete', message:"Are you sure you want to delete this page?", buttons:{ok:1,cancel:1}}))
				.getContainer().find('button[value=ok]').on('click', function() {
					$.ajax({
					  method: 'post',
					  dataType: "json",
					  url:'/formbuilder/page',
					  data: details
				  	}).then(
				  		function(results) {
				  			window.location.reload()
				  		}
				  	)
				 })
		})
	}

	function editPageFull(section,details) {
		require(['modules/Lightbox'], function(Lightbox) {
			var lightbox = new Lightbox({title:(section && section.id ? 'Edit' : 'Create') +' page/section', message:""});
			var container = lightbox.getContainer();
			container.find('.outer .outer').html(pageTemplate({obj:section,tpRo:tpRo,tpText:tpText,tpArea:tpArea,tpSelect:tpSelect,tpCheckbox:tpCheckbox}));
			container.find('button[value=ok]').on('click', function() {
				var update = _.extend(helpers.unMap(container.find('form').serializeArray()),details);
				intify(update,'order');
				$.ajax({
				  method: 'post',
				  dataType: "json",
				  url:'/formbuilder/page',
				  data: helpers.map(update)
			  	}).then(
			  		function(results) {
			  			window.location.reload()
			  		}
			  	)		

			});
			container.find('button[value=createChild]').on('click', function() {
				delete details.page; 
				editPageFull({title:'<add title>',order:'10',parent_id:section.id},details)
			})
			container.find('button[value=createSibling]').on('click', function() {
				delete details.page; 
				editPageFull({title:'<add title>',order:1+(section.order || 0),parent_id:section.parent_id},details)
			})			
			container.find('button[value=deletePage]').on('click', function() {
				deletePage(details);
			})			

		})
	}
	function boolify(obj, field) {
		// make string 'True' and 'False' into boolean
		if(_.isString(obj[field])){
			obj[field] = obj[field] in {'true':1,'True':1}
		}
	}
	function intify(obj,field) {
		if(!parseInt(obj[field],10)) {
			obj[field] = 1;
		}
	}

	function editQuestionFull(question, details, questionContainer) {
		//  callled once questions details retrieved by ajax
		boolify(question,'mandatory');
		intify(question,'order');
		require(['modules/Lightbox'], function(Lightbox) {
			var lightbox = new Lightbox({title:'Edit Question', message:"Name : "+name});
			var container = lightbox.getContainer();
			container.find('.outer .outer').html(tp({obj:question,tpRo:tpRo,tpText:tpText,tpArea:tpArea,tpSelect:tpSelect,tpCheckbox:tpCheckbox}));
			container.find('button[value=ok]').on('click', function() {
				// save the result
				details = _.extend(details,helpers.unMap(container.find('form').serializeArray()));
				$.ajax({
				  method: 'post',
				  url:'/formbuilder/question',
				  data: helpers.map(details)
			  	}).then(function(content) {
			  		location.reload();
			  		//questionContainer.html($(content).html());
			  	})
			})
			container.find('button[value=cut]').on('click', function() {
				// move to clipboard
				details.action = 'cut';
				$.ajax({
				  method: 'post',
				  url:'/formbuilder/question',
				  data: helpers.map(details)
				}).then(function(content) {
					location.reload();
			  		//questionContainer.html($(content).html());
			  	})
			})
		})
	}

	function getDetails() {
		return {
			'csrfmiddlewaretoken': form.find('input[name=csrfmiddlewaretoken]').val(),
			'instance': form.find('input[name=instance]').val(),
			'page': form.find('input[name=page]').val()
		}
	}

	function editQuestion(container) {
		//var form = $(container).closest('form.dd-form');
		// get things from the form
		//var container = $(evt.target).closest('.form-group');  // if we are editing
		var details = getDetails();
		var id = container && container.attr('data-id');
		if(id) {
			details.id = id;
			$.ajax({
			  dataType: "json",
			  url:'/formbuilder/question',
			  data: helpers.map(details)
			}).then(
				function(questions) {
					editQuestionFull(questions[0],details,container)
				}
			)
		} 
		if(id = container && container.attr('data-section')) {
			// We are editing a page, not a question
			details.page=id;
			$.ajax({
			  dataType: "json",
			  url:'/formbuilder/page' ,
			  data: helpers.map(details)
			}).then(
				function(pageData) {
					editPageFull(pageData,details,container)
				}
			)
		}
	}
	
	// form editor
	var editEnabled = false;
	$(document.body).on('click', function(evt) {
		if(editEnabled) {
			editEnabled = false;
			var questionContainer = $(evt.target).closest('.form-group');
			if(questionContainer) {
				editQuestion(questionContainer);
			}
		}
	});

	function setForm(mode) {
		details = getDetails();
		details.action = mode;
		$.ajax({
			method: 'get',
			dataType: "json",
			url:'/toolbox',
			data: details
		}).then(function(content) {
			window.location.reload();
		})
	}

	function menuClick(evt) {
		var target = $(evt.target);
		switch(target.val()) {
			case 'toggle-edit':
				editMode = !editMode;
				localStorage.config = editMode ? 'on' : 'off';
				target.text(editMode? 'Stop edit mode':'Edit mode');
				break;
			case 'new-question':
				editQuestionFull({},getDetails());
				break;
			case 'new-page':
				editPageFull({},getDetails());
				break;
			case 'paste':
				clipboard('paste','paste');
				break;
			case 'empty-clip':
				clipboard('delete','empty-clip');
				break;
			case 'clear-form':
				setForm('clearform')
				break;
			case 'complete-form':
				setForm('completeform')
				break;
			case 'unsubmit-form':
				setForm('unsubmitform')
				break;	
		}
		showMenu(false);
	}

	function showMenu(state) {
		menu.setClass('hidden',!state);
		menuShowing = state;
	}

	function onClick(evt) {
		var target = $(evt.target);
		if(menuShowing && !target.closest('.menu-block').length) {
			showMenu(false);
		}
		if(highlightedQuestion && target.hasClass('question-edit-block')) {
			evt.preventDefault();
			evt.stopImmediatePropagation();
			editQuestion($(highlightedQuestion));
		}
	}

	var highlightedQuestion;

	var editBlock = $('<span class="question-edit-block"></span>');
	var nextTarget, hoverTimer;


	function editHover(evt) {
		//var target = $(evt.target);
		if(!editMode) return;
		var question = nextTarget.closest('.edit-item');
		if(question[0] != highlightedQuestion) {
			if(highlightedQuestion) {
				$(highlightedQuestion).removeClass('edit-highlight');
				editBlock.remove();
			}
			highlightedQuestion = question[0];
			question.addClass('edit-highlight');
			question.append(editBlock);
		}
	};
	function dbHover(evt) {
		nextTarget = $(evt.target); 
		clearTimeout(hoverTimer);
		hoverTimer = setTimeout(editHover,50);
	}


	function navClick(evt) {
		var target = $(evt.target).closest('li');
		if(target.length) {
			evt.preventDefault();
			evt.stopPropagation();
			var data = getDetails();
			data.page = parseInt(target.attr('data-page'),10);
			$.ajax({
				method: 'get',
				dataType: "json",
				url:'/formbuilder/page',
				data: helpers.map(data)
			}).then(function(content) {

			})
		}
	}



	function initialize() {
		/* form.find('.form-group').each(function() {
			$(this).append($('<img class="form-edit icon icon-pen">'));
		});*/
		var tp = _.template('\
			<div class="menu-block">\
			<span class="threeline-menu"></span>\
			<div class="config-menu hidden">\
				<button type="button" value="toggle-edit">'+(editMode? 'Stop edit mode':'Edit mode')+'</button>\
				<button type="button" value="new-question">New question</button>\
				<button type="button" value="new-page">New page</button>\
				<button type="button" value="paste">Paste</button>\
				<button type="button" value="empty-clip">Empty clipboard</button>\
				<button type="button" value="clear-form">Clear form</button>\
				<button type="button" value="complete-form">Complete form</button>\
				<button type="button" value="unsubmit-form">Un-submit form</button>\
			</div></div>\
		');
		menuBlock = $(tp());
		menu = menuBlock.find('.config-menu')
		menu.on('click',menuClick);
		$('#global-header').append(menuBlock);
		var icon = menuBlock.find('.threeline-menu');
		$(document.body).on('click',onClick);
		icon.on('click',function() {
			showMenu(true);
		})
		$(document.body).on('mouseover', dbHover);

		//$('ul.nav').on('click', navClick);
	}

	/* function keyDown(evt) {
		if(evt.which == 88 && evt.altKey) {
			initialize();
			$(document.body).off('keydown',keyDown);
		}
	}		
	$(document.body).on('keydown',keyDown ) */
	initialize();
});
