$(document).ready(function() {
    var input_values = {{values|safe}};
    if (input_values.length > 0) {
        document.getElementsByClassName("username")[0].value = input_values[0];
        document.getElementsByClassName("email")[0].value = input_values[1];
    }
    var input_fields = ["username", "email", "password", "confirm_password"];
    for (var n=0; n<input_fields.length; n++) {
        $("."+input_fields[n]).popover({
            trigger: "focus"
        });
    }
});