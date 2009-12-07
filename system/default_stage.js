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
            "id" : "bottombar",
            "type" : "ClutterRectangle",
            "x" : -10, "y" : 370,
            "width" : 820, "height" : 80,
            "color" : "white",
            "border-color" : "#1a87a5",
            "border-width" : 8
        },
        {
            "id" : "message_box",
            "type" : "ClutterRectangle",
            "x" : 475, "y" : 15,
            "width" : 210, "height" : 280,
            "color" : "#1D96B8",
            "border-color" : "#1a87a5",
            "border-width" : 5
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
        {
            "id" : "icon1",
            "type" : "ClutterGroup",
            "x" : 100, "y" : 100
        },
        {
            "id" : "icon2",
            "type" : "ClutterGroup",
            "x" : 250, "y" : 100
        },
        {
            "id" : "icon3",
            "type" : "ClutterGroup",
            "x" : 100, "y" : 250
        },
        {
            "id" : "icon4",
            "type" : "ClutterGroup",
            "x" : 250, "y" : 250
        },
    ]
}
