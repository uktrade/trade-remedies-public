define(['modules/helpers'],function(helpers) {
    "use strict";

    var notesTemplate = _.template('\
        <h2 class="heading-medium">Notes<span class="edit-block" title="Add note"></span></h2>\
        <div class="add-note"><form>\
            <label><div class="heading-small">Note title</div><input type="text" name="noteTitle"></label>\
            <label><div class="heading-small">Tags</div><input type="text" name="tags"></label>\
            <label><div class="heading-small">Note</div><textArea name="note"></textArea></label>\
            <div class="button-container margin-top-1 margin-bottom-1"><button type="button" class="button small pull-right" value="addNote" name="btnAction">Add note</button><button type="button" class="button small secondary" value="cancelNote" name="btnAction">Cancel</button></div>\
        </form></div>\
    ');

    var noteTemplate = _.template('\
        <div class="note-outer" data-noteid="<%- note.id %>">\
            <span class="edit-block"><div class="icon icon-cross btn-delete" title="Delete"></div><div class="icon icon-pen btn-edit" title="Edit"></div></span>\
            <h2 class="note-title heading-small"><%- note.title %></h2>\
            <div note-text><%= _.escape(note.text || "").replace(/\\n/g,"<br>") %></div>\
            <div class="note-footer" ><% print( note.user && ((note.user.firstName && (note.user.firstName + " " + note.user.lastName)) || note.user.name) || "anonymous") %> <span class="date pull-right"><%- new Date(note.date).format("dd mon yyyy HH:MM") %></span></div><div></div>\
        </div>\
    ');

    function constructor(container, instance, questionsContainer) {
        this.questionsContainer = questionsContainer;
        this.instance = instance;
        this.container = container;
        this.container.prepend($('<div class="loader"></div>'))
        questionsContainer.on('click',_.bind(noteClick,this))
        getNotes.call(this);
    }

    function renderNotes(container) {
        var self = this;
        if(this.noteData) {
            this.container.addClass('note-container');
            this.container.html(notesTemplate({list:this.noteData}));
            this.addNoteFm = this.container.find('.add-note');
        }
        if(this.questionsContainer && this.fieldNotes) {
            var notesBlocks = this.questionsContainer.find('.notes-block');
            notesBlocks.each(function(notesBlock) {
                var block = $(this);
                block.html('<div class="note-block-head"><button type="button" class="btn-add-note pull-right">Add note</button></div>'); // clear the custard
                var fieldId = block.attr('data-field');
                var notes = (self.fieldNotes[fieldId] || []);
                _.each(notes,function(note) {
                    block.append($(noteTemplate({note:note})));
                })
            });
        }
    }

    function noteClick(evt) {
        var target = $(evt.target);
        if(target.hasClass('btn-delete')) {
            deleteNote.call(this,target);
        }
        if(target.val()=='addNote') { // it's the add button
            addNote.call(this,evt);
        }
        if(target.val()=='cancelNote') { 
            this.addNoteFm.remove();
        }
        if(target.closest('.btn-add-note').length) {
            addNoteDialogue.call(this,(target).closest('.btn-add-note'))
        }
    }

    function addNote(evt) {
        var self = this;
        evt.preventDefault();
        evt.stopPropagation();
        var data = (this.addNoteFm.find('form').serializeArray()).concat([
            {name:'csrfmiddlewaretoken',value:dit.csrf_token},
            {name:'instance',value:this.instance},
            {name:'question',value:this.questionId}
        ]);
        $.ajax({
            url: 'note',
            type: 'POST',
            data: data
        }).then(function(result) {
            self.addNoteFm.remove();
            getNotes.call(self);
        }, function() {
            self.addNoteFm.remove();
        });
    }

    function deleteNote(btn) {
        var self = this;

        require(['modules/Lightbox'], function(Lightbox) {
            var lightbox = new Lightbox({title:'Delete', message:"Are you sure you want to delete this note?", buttons:{ok:1,cancel:1}});
            lightbox.getContainer().find('button[value=ok]').on('click', function() {
                var outer = btn.closest('.note-outer');
                var noteId = outer.attr('data-noteid');
                var data = helpers.map({
                    id:noteId,
                    action:'delete',
                    csrfmiddlewaretoken:dit.csrf_token
                });
                $.ajax({
                    url: 'note',
                    type: 'POST',
                    data: data
                }).then(function(result) {
                    getNotes.call(self);
                }, function() {
                    // made of fail
                });
            })
        });
    }

    function getNotes() {
    // Reloads the notes and renders
        var self = this;
        $.ajax({
            url: 'note',
            type: 'GET',
            dataType: "json",
            data: {instance: self.instance}
        }).then(function(result) {
            self.noteData = result.notes.sort(function(a,b) {return a.date < b.date ? 1:-1});
            self.fieldNotes = {};
            self.pageNotes = [];
            _.each(self.noteData, function(note) {
                if(note.fieldId) {
                    (self.fieldNotes[note.fieldId] = self.fieldNotes[note.fieldId] || []).push(note);
                } else {
                    self.pageNotes.push(note);
                }
            })
            renderNotes.call(self)
        });
    }
    
    function addNoteDialogue(button) {
        var self=this;
        var container = button.closest('.notes-block');
        this.questionId = container.attr('data-field');
        this.addNoteFm.css({height:0});
        button.closest('.note-block-head').after(this.addNoteFm);
        this.addNoteFm.css({height:this.addNoteFm.prop('scrollHeight')});
        setTimeout(function(){self.addNoteFm.css({height:'auto'})},300);
    }

    constructor.prototype = {
        refresh: function() {
            renderNotes.call(this);
        }
    }
    return constructor;
})
