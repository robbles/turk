
// Currently selected input or output
// Dropped by clicking on the body or a device div
var selectedInput = null;
var selectedOutput = null;

// A list of input->output, output->input mappings,
// replaced by every '/mappings' query result to bridge.
// Basically, it tries to mimic the current state of the platform,
// rather than keep track of what's going on itself
var mappings = {};

// Initialize mappings with fake values, for demo purposes
//var mappings = [{"input_id":"2","input_name":"input1","output_id":"1","output_name":"output1"},
//                {"input_id":"5","input_name":"z_button","output_id":"1","output_name":"output1"}];


// Wrapper to provide separate namespace
(function(){


var init = function() {

    // Load the device list from Turk CloudBridge
    $("#devicelist").load("devices", {'format':'xhtml', 'limitnum':'10'}, deviceSetup);

    // Load the current mappings from CloudBridge
    $.post("mappings", {'format':'xml'}, parseMappings, 'xml');
    
    // Slide the help panel in when clicking on the '?' button, out when clicking on help panel
    $("#helpq").click(function() { $("#help").animate({'left':'0px'}, 'fast'); });
    $("#help").click(function() { $("#help").animate({'left':'-435px'}, 'fast'); });

    // Show the canvas and draw mappings when clicking the '#' button
    $("#showmap").click(function() { $("#canvas").css('visibility', 'visible'); showMappings(); });
    $("#canvas").click(function() { $("#canvas").css('visibility', 'hidden'); });

}

// Reloads mappings and data from bridge with AJAX
function refreshData() {
 
    //TODO: figure out how to refresh device list while in-use
    // Load the device list from Turk CloudBridge
//    $("#devicelist").load("devices", {'format':'xhtml', 'limitnum':'10'}, deviceSetup);

    // Load the current mappings from CloudBridge
    debug('reloading mappings');
    $.post("mappings", {'format':'xml'}, parseMappings, 'xml');
}

// Convert XML received from bridge into JSON
function parseMappings(responseXML) {
    debug('parseMappings called');
    mappings = $(responseXML).find('mapping').map(function() { input = $(this).children('input');
                                                               output = $(this).children('output');

                                                               mapping = {'input_id':input.attr('id'),
                                                                          'input_name':input.attr('name'),
                                                                          'output_id':output.attr('id'),
                                                                          'output_name':output.attr('name')};
                                                               return mapping; });
    debug(mappings);

    setTimeout(refreshData, 3000);
}

// Sets up dom elements that represent connected devices
function deviceSetup() {
    // Add a clear element after every third device div, to make them wrap properly
    $("#devicelist .device:nth-child(3n)").after("<div class=\"deviceclear\"></div>");

    //Attach events for inputs and outputs
    $(".deviceinput").click(inputClick).append("<div class=\"deviceshader\"></div>").qtip( {
        show: { delay:1000, when:{event:'mouseover'} },
        hide: { delay:2000, when:{event:'mouseout'} },
        api: { beforeShow: function() {
            this.updateContent('Device Input<br />' + getAssociated(this.elements.target), true);
            }, onShow: addToolTipLinks}
        }).mousedown(function() { return false; });

    $(".deviceoutput").click(outputClick).append("<div class=\"deviceshader\"></div>").qtip( {
        show: { delay:1000, when:{event:'mouseover'} },
        hide: { delay:2000, when:{event:'mouseout'} },
        api: { beforeShow: function() {
            this.updateContent('Device Output<br />' + getAssociated(this.elements.target), true);
            }, onShow: addToolTipLinks}
        }).mousedown(function() { return false; });
    
    //Attach function to drop selected when clicking on body or device
    $("body,.device").click(dropSelected);

    //Fade out deviceshaders
    $(".deviceshader").fadeOut("fast");

}

function addToolTipLinks() {
    elementid = $(this.elements.target).parent().parent().attr('id');
    elementname = $(this.elements.target).children('.inputname, .outputname').text();

    // Store id and name in disconnect link object, and add disconnect action
    var content = $(this.elements.content).children('.disconnectall');

    content.css('color', '#0000FF');
    content.get(0).element_ref = [elementid, elementname];
    content.click(function() {
        disconnectAll(this.element_ref[0], this.element_ref[1]);
    });
}

function disconnectAll(id, name) {
    $.post('unmap', 'device=' + id + '&name=' + name);
}


function inputClick(event) {
    // If user clicked on the same input twice, de-select it
    if(selectedInput == this) {
        $(selectedInput).removeClass("devicehl");
        selectedInput = null;
    } else {
        // Un-select previously selected Input, and select this one
        $(selectedInput).removeClass("devicehl");
        $(this).addClass("devicehl");
        selectedInput = this;
    }
    // Connect to the selected Output
    if(selectedOutput) {
        connectify();
    }
    return false;
}

function outputClick(event) {
    // If user clicked on the same output twice, de-select it
    if(selectedOutput == this) {
        $(selectedOutput).removeClass("devicehl");
        selectedOutput = null;
    } else {
        // Un-select previously selected Output, and select this one
        $(selectedOutput).removeClass("devicehl");
        $(this).addClass("devicehl");
        selectedOutput = this;
    }
    // Connect to the selected Input
    if(selectedInput) {
        connectify();
    }
    return false;
}


function connectify() {
    debug('connectifying: ' + selectedInput + ', ' + selectedOutput);
    // Flash Input/Output
    $(selectedInput).children(".deviceshader").fadeIn("fast", function() { $(this).fadeOut("slow") }).parent().removeClass("devicehl");
    $(selectedOutput).children(".deviceshader").fadeIn("fast", function() { $(this).fadeOut("slow") }).parent().removeClass("devicehl");

    input_device = $(selectedInput).parent().prev().children('.device_id').text();
    input_name = $(selectedInput).children('.inputname').text()
    output_device = $(selectedOutput).parent().prev().children('.device_id').text();
    output_name = $(selectedOutput).children('.outputname').text()

    $.post('map', 'input_device=' + input_device + '&input_name=' + input_name + "&output_device=" + output_device + "&output_name=" + output_name)
    
    selectedInput = selectedOutput = null;
}

function dropSelected() {
	$(selectedInput).removeClass("devicehl");
	$(selectedOutput).removeClass("devicehl");
	selectedInput = null;
	selectedOutput = null;	
}

// Get all mappings associated with this element
function getAssociated(element) {
    elementid = element.parent().parent().attr('id');
    elementname = element.children('.inputname, .outputname').text();
    //debug('looking for elements associated to ' + elementid + '.' + elementname);
    var returnstring = '';

    // Look through mappings table for anything that matches this input/output
    for(var i=0; i<mappings.length; i++) {
        if(elementid == mappings[i]['input_id'] && elementname == mappings[i]['input_name']) {
            returnstring = returnstring + mappings[i]['output_id'] + '.' + mappings[i]['output_name'] + '<br />';
        }
        else if(elementid == mappings[i]['output_id'] && elementname == mappings[i]['output_name']) {
            returnstring = returnstring + mappings[i]['input_id'] + '.' + mappings[i]['input_name'] + '<br />';
        }
    }

    // Add 'Disconnect All' link at bottom
    returnstring = returnstring + '<div class="disconnectall">Disconnect All</div>';

    return returnstring;
}

function showMappings() {
    // Get the reference to the canvas element and drawing context
    var canvasElement = document.getElementById("canvas");
    var canvas = canvasElement.getContext('2d');

    // Reset the canvas dimensions (canvas doesn't play nice with CSS fluid layouts)
    canvasElement.width = canvasElement.offsetWidth;
    canvasElement.height = canvasElement.offsetHeight;

    // Setup fill and stroke colors/options
    canvas.fillStyle = "rgba(255,255,255,0.5)";
    canvas.lineCap = 'round';

    // Clear canvas and fade out UI slightly
    canvas.clearRect(0, 0, canvasElement.width, canvasElement.height);
    canvas.fillRect(0, 0, canvasElement.width, canvasElement.height);

    for(var i=0; i<mappings.length; i++) {
        var input = $('#' + mappings[i]['input_id']).find('.' + mappings[i]['input_name']).get(0);
        var output = $('#' + mappings[i]['output_id']).find('.' + mappings[i]['output_name']).get(0);

        if(input && output) {
            drawConnection(canvas, getX(input) + input.offsetWidth + 20, getY(input), getX(output) - 20, getY(output));

        } else {
            debug('mapping elements are missing in DOM!');
        }
    }
}


function drawConnection(canvas, ax, ay, bx, by) {
    canvas.strokeStyle = "#000000";
    canvas.lineWidth = 5.0;
    canvas.beginPath();
    canvas.moveTo(ax, ay);
    canvas.quadraticCurveTo((bx + ax) / 2, by + 100, bx, by);
    canvas.stroke();

    canvas.strokeStyle = "#76C5DC";
    canvas.lineWidth = 3.0;
    canvas.beginPath();
    canvas.moveTo(ax, ay);
    canvas.quadraticCurveTo((bx + ax) / 2, by + 100, bx, by);
    canvas.stroke();
}


function debug(message) {
    if(typeof(console) != "undefined") {
        console.log(message);
    }
}

function getY( oElement )
{
    var iReturnValue = 0;
    while( oElement != null ) {
        iReturnValue += oElement.offsetTop;
        oElement = oElement.offsetParent;
    }
    return iReturnValue;
}

function getX( oElement )
{
    var iReturnValue = 0;
    while( oElement != null ) {
        iReturnValue += oElement.offsetLeft;
        oElement = oElement.offsetParent;
    }
    return iReturnValue;
}

document.addEventListener("DOMContentLoaded",init,false);
})();

