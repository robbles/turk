{
    "id" : "stage",
    "type" : "ClutterStage",
    "width" : 700, "height" : 450,
    "x" : 200, "y" : 200,
    "color" : "#1D96B8",
    "visible" : true,
    "reactive" : true,
    "signals" : [
    ],
    "children" : [
        {
            "id" : "icon1",
            "type" : "ClutterGroup",
            "anchor-x" : 64, "anchor-y" : 64,
            "x" : 160, "y" : 104,
            "children" : [
                {
                    "type" : "ClutterRectangle",
                    "color" : "black",
                    "x" : -10, "y" : -10,
                    "width" : 148, "height" : 148,
                    "opacity" : 0,
                },
                {
                    "type" : "ClutterTexture",
                    "filename" : "lamp.png",
		    "width" : 128, "height" : 128,
                }
            ]
        },
        {
            "id" : "icon2",
            "type" : "ClutterGroup",
            "anchor-x" : 64, "anchor-y" : 64,
            "x" : 350, "y" : 104,
            "children" : [
                {
                    "type" : "ClutterRectangle",
                    "color" : "black",
                    "x" : -10, "y" : -10,
                    "width" : 148, "height" : 148,
                    "opacity" : 0,
                },
                {
                    "type" : "ClutterTexture",
                    "filename" : "display.png"
                }
            ]
        },
        {
            "id" : "icon3",
            "type" : "ClutterGroup",
            "anchor-x" : 64, "anchor-y" : 64,
            "x" : 160, "y" : 292,
            "children" : [
                {
                    "type" : "ClutterRectangle",
                    "color" : "black",
                    "x" : -10, "y" : -10,
                    "width" : 148, "height" : 148,
                    "opacity" : 0,
                },
                {
                    "type" : "ClutterTexture",
                    "filename" : "hardware.png"
                }
            ]
        },
        {
            "id" : "icon4",
            "type" : "ClutterGroup",
            "anchor-x" : 64, "anchor-y" : 64,
            "x" : 350, "y" : 292,
            "children" : [
                {
                    "type" : "ClutterRectangle",
                    "color" : "black",
                    "x" : -10, "y" : -10,
                    "width" : 148, "height" : 148,
                    "opacity" : 0,
                },
                {
                    "type" : "ClutterTexture",
                    "filename" : "sound.png"
                }
            ]
        },
        {  
            "id" : "bottombar",
            "type" : "ClutterRectangle",
            "x" : -10, "y" : 370,
            "width" : 820, "height" : 80,
            "color" : "white",
            "border-color" : "#1a87a5",
            "border-width" : 8
        },
        {
            "id" : "title",
            "type" : "ClutterLabel",
            "text" : "Turk Control Panel",
            "color" : "#222222",
	    "font-name" : "Sans 18",
            "x" : 100, "y" : 390,
        },
        {
            "id" : "knight",
            "type" : "ClutterTexture",
            "filename" : "turkknight3.png",
            "x" : 520, "y" : 270,
        },
    ]
}
