function send_action(post_data) {
    post_data.csrfmiddlewaretoken = csrf_token;
    post_data.keep_variables = keep_variables;

    $.ajax({
        type: 'POST',
        url: window.location.href,
        data: post_data,
        dataType: 'json',

        success: function(data, status) {
            eval(data.javascript);
            bind_forms();
        }
    });
}

function do_action(action, post_data) {
    post_data.action = action;
    send_action(post_data);
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function bind_forms() {
    // Send form data as AJAX
    $('form[data-async]').on('submit', function(event) {
        $.ajax( {
            url: window.location.href,
            type: 'POST',
            data: new FormData( this ),
            processData: false,
            contentType: false,
            success: function(data, status) {
                eval(data.javascript);
                bind_forms();
            }
        } );
        event.preventDefault();
    });

    $('form[data-async]').each(function() {
        $('<input type="hidden" name="keep_variables">').attr('value', keep_variables).appendTo(this);
        $('<input type="hidden" name="csrfmiddlewaretoken">').attr('value', csrf_token).appendTo(this)
        $(this).removeAttr('data-async')
    })
}

$(document).ready(function() {
    // Autofocus the first element with data-autofocus on a modal
    $(".modal").on('shown.bs.modal', function() {
        $(this).find("[data-autofocus]:first").focus();
    });

    // Autofocus
    $("[data-autofocus]:first").focus();

    // Turn forms into AJAX forms
    bind_forms();

    // Make table rows with links on the entire row clickable
    $('.table tr[data-href]').each(function(){
        $(this).css('cursor','pointer').click( function(){
                document.location = $(this).attr('data-href');
            }
        );
    });
});
