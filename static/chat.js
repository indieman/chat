$(document).ready(function() {

    $("#messageform").live("submit", function() {
        newMessage($(this));
        return false;
    });
    $("#messageform").live("keypress", function(e) {
        if (e.keyCode == 13) {
            newMessage($(this));
            return false;
        }
    });
    $("#message").select();
    updater.poll();
});

function newMessage(form) {
    var message = form.formToDict();
    var disabled = form.find("input[type=submit]");
    disabled.disable();
    $.post("/", message,
        function(response){
            if (response['status'] == 'error') {
                if (response['body']) {
                    $('#bodyError').text(response['body'][0]);
                }
                if (response['nickname']) {
                    $('#nicknameError').text(response['nickname'][0]);
                }
            } else {
                $('#bodyError').text('');
                $('#nicknameError').text('');
                updater.showMessage(response);
            }

        }, "json");
    form.find('input[type=text]').val('').select();
    disabled.enable();
}

jQuery.postJSON = function(url, args, callback) {
    $.ajax({url: url, data: $.param(args), dataType: "text", type: "POST",
            success: function(response) {
    }, error: function(response) {
        console.log("ERROR:", response)
    }});
};

jQuery.fn.formToDict = function() {
    var fields = this.serializeArray();
    var json = {}
    for (var i = 0; i < fields.length; i++) {
        json[fields[i].name] = fields[i].value;
    }
    if (json.next) delete json.next;
    return json;
};

jQuery.fn.disable = function() {
    this.enable(false);
    return this;
};

jQuery.fn.enable = function(opt_enable) {
    if (arguments.length && !opt_enable) {
        this.attr("disabled", "disabled");
    } else {
        this.removeAttr("disabled");
    }
    return this;
};

var updater = {
    errorSleepTime: 500,
    cursor: null,

    poll: function() {
        messages = $('.message');
        lastId = $(messages[messages.length - 1]).attr('id');
        var args = {'lastId': lastId};
        if (updater.cursor) args.cursor = updater.cursor;
        $.ajax({url: "/a/message/updates", type: "POST", dataType: "text",
                data: $.param(args), success: updater.onSuccess,
                error: updater.onError});

    },

    onSuccess: function(response) {
        try {
            updater.newMessages(eval("(" + response + ")"));
        } catch (e) {
            updater.onError();
            return;
        }
        updater.errorSleepTime = 500;
        window.setTimeout(updater.poll, 0);
    },

    onError: function(response) {
        updater.errorSleepTime *= 2;
        window.setTimeout(updater.poll, updater.errorSleepTime);
    },

    newMessages: function(response) {
        for (var i = 0; i < response.length; i++) {
            updater.showMessage(response[i]);
        }
    },

    showMessage: function(message) {
        var existing = $("#m" + message.id);
        if (existing.length > 0) return;
        var node = $(message.html);
        node.hide();
        $("#inbox").append(node);
        node.slideDown();
    }
};