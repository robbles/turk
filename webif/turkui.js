
(function(){

var selectedInput = null;
var selectedOutput = null;

var init = function() {

    // Load the device list from Turk DataFetcher
    $("#devicelist").load("devicecontent.html", {}, deviceSetup);

}

function deviceSetup() {
    // Add a clear element after every third device div, to make them wrap properly
    $("#devicelist .device:nth-child(3n)").after("<div class=\"deviceclear\"></div>");

    //Attach click and mouseenter events for inputs and outputs
    $(".deviceinput").click(inputClick).mouseenter(showConnected).mouseleave(hideConnected).append("<div class=\"deviceshader\"></div>").associatedOutput = null;
    $(".deviceoutput").click(outputClick).mouseenter(showConnected).mouseleave(hideConnected).append("<div class=\"deviceshader\"></div>").associatedInput = null;

    //Fade out deviceshaders
    $(".deviceshader").fadeOut("fast");

}

function inputClick(event) {
    // Un-select previously selected Input, and select this one
    $(selectedInput).removeClass("devicehl");
    $(this).addClass("devicehl");
    selectedInput = this;

    // Connect to the selected Output
    if(selectedOutput) {
        connectify();
    } 
}

function outputClick(event) {
    // Un-select previously selected Output, and select this one
    $(selectedOutput).removeClass("devicehl");
    $(this).addClass("devicehl");
    selectedOutput = this;

    // Connect to the selected Input
    if(selectedInput) {
        connectify();
    } 
}

function showConnected(event) {
    if(this.associatedInput || this.associatedOutput) {
        $(this.associatedInput).addClass("deviceassociated");
        $(this.associatedOutput).addClass("deviceassociated");
    }
}

function hideConnected(event) {
    if(this.associatedInput || this.associatedOutput) {
        $(this.associatedInput).removeClass("deviceassociated");
        $(this.associatedOutput).removeClass("deviceassociated");
    }
}

function connectify() {
    // Flash Input/Output
    $(selectedInput).children(".deviceshader").fadeIn("fast", function() { $(this).fadeOut("slow") }).parent().removeClass("devicehl");
    $(selectedOutput).children(".deviceshader").fadeIn("fast", function() { $(this).fadeOut("slow") }).parent().removeClass("devicehl");

    // Associate
    selectedInput.associatedOutput = selectedOutput;
    selectedOutput.associatedInput = selectedInput;

    selectedInput = selectedOutput = null;
}




document.addEventListener("DOMContentLoaded",init,false);
})();
