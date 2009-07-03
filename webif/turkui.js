
var selectedInput = null;
var selectedOutput = null;

(function(){


var init = function() {

    // Load the device list from Turk CloudBridge
    $("#devicelist").load("devices", {'format':'xhtml', 'limitnum':'10', 'styling':'0'}, deviceSetup);

}

function deviceSetup() {
    // Add a clear element after every third device div, to make them wrap properly
    $("#devicelist .device:nth-child(3n)").after("<div class=\"deviceclear\"></div>");

    //Attach click for inputs and outputs
    $(".deviceinput").click(inputClick).append("<div class=\"deviceshader\"></div>");
    $(".deviceoutput").click(outputClick).append("<div class=\"deviceshader\"></div>").each(function() { this.associatedInputs = []; });
    
    //Attach function to drop selected when clicking on body or device
    $("body,.device").click(dropSelected);

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
    } else {
    	showConnected(this);
    }
    return false;
}

function outputClick(event) {
    // Un-select previously selected Output, and select this one
    $(selectedOutput).removeClass("devicehl");
    $(this).addClass("devicehl");
    selectedOutput = this;

    // Connect to the selected Input
    if(selectedInput) {
        connectify();
    } else {
    	showConnected(this);
    }
    return false;
}

function showConnected(element) {	
	if(element.associatedInputs) {
	    if(element.associatedInputs.length) {
	        $.each(element.associatedInputs, function() {
			    $(this).children(".deviceshader").fadeIn("fast",
					function() { $(this).fadeOut("slow") }).parent().removeClass("devicehl");
	        });
	    }
    }
    if(element.associatedOutput) {
        $(element.associatedOutput).children(".deviceshader").fadeIn("fast",
			function() { $(this).fadeOut("slow") }).parent().removeClass("devicehl");
    }
}


function connectify() {
    // Flash Input/Output
    $(selectedInput).children(".deviceshader").fadeIn("fast", function() { $(this).fadeOut("slow") }).parent().removeClass("devicehl");
    $(selectedOutput).children(".deviceshader").fadeIn("fast", function() { $(this).fadeOut("slow") }).parent().removeClass("devicehl");

	//Clear old associations
	if(selectedInput.associatedOutput) {
		selectedInput.associatedOutput.associatedInputs.splice($.inArray(selectedInput, selectedInput.associatedOutput.associatedInputs), 1);
	}
	
	
    // Associate
    selectedInput.associatedOutput = selectedOutput;
    selectedOutput.associatedInputs.push(selectedInput);

    $.post('http://localhost:8080', 'request=associate&device="&input=' + $(selectedInput).attr('inputname') + "&output=" + $(selectedOutput).attr('outputname'))
    
    // Remove duplicate registrations of input from output
    $.unique(selectedOutput.associatedInputs);

    selectedInput = selectedOutput = null;
}

function dropSelected() {
	$(selectedInput).removeClass("devicehl");
	$(selectedOutput).removeClass("devicehl");
	selectedInput = null;
	selectedOutput = null;	
}


document.addEventListener("DOMContentLoaded",init,false);
})();
