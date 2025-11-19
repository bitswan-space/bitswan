# WebChat - From Notebook to Chatbot: Turn code into conversations

WebChat 
WebChat is a brand new component in BSPump library that provides an interactive web-based chat interface with real-time communication, 
form handling, and dynamic flow management. It allows you to build your own chatbot using just Jupyter notebooks. 

You dont know much about ai or chatbots? Dont worry, with WebChat it is as easy as to build any other bitswan pipeline. 

How it works? 
With webchat you can create pipeline without actually creating a pipeline - everything is set up for you. The only thing you need to create yourself
is the flow.

Flow is created using the create command. 
initial_flow = create_webchat_flow("initial_flow")
This command returns a WebChat object, that you will use for calling of other methods. 
Now everything that is under this command will be part of this flow until create function is called again.

There are three Webchat methods you can use: 
set_welcome_message: 
await initial_flow.set_welcome_message(welcome_text="This is the welcome message that is always visible on the top.")
that sets the topmost response from webchat that is visible all time.

then set_prompt that sets the prompt form and returns the input data from user as dictionary.
form_response = await initial_flow.set_prompt(
    [
        IntField(name="fund_id", display="Fond", required=True),
        IntField("n"),
        TextField("le", hidden=True),
        ChoiceField("lol", choices=["a", "b", "c"]),
        CheckboxField("checkbox", required=False)
    ]
)

fond_value = form_response["fund_id"]


and tell_user that sets the response. 
await initial_flow.tell_user("This is your first message.")

All of them can take as arguments plain text or html code. You can pass it even an image tag and render an image:
TODO: Add examplea

Markdown blogs 
Now since we use Jupyter notebooks apart from code cells you can have markdown cells there. These are in webchat rendered on frontend as response. 
And again you can insert there image and an image will be then rendered as response. 
