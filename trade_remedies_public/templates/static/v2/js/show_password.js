$('#show_password').click(function () {
  if ($(this).attr('aria-checked') === 'false') {
    $(this).attr('aria-checked', 'true')
    $('#password').attr('type', 'text')
    $(this).find('span').text('Hide')
    $("#password-text").html("Password shown.")
  } else {
    $(this).attr('aria-checked', 'false')
    $('#password').attr('type', 'password')
    $(this).find('span').text('Show')
    $("#password-text").html("Password hidden.")
  }
})
