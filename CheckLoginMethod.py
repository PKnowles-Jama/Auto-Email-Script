from ClearLayout import clearLayout

def CheckLoginMethod(basic_oauth):
    
    clearLayout(dynamic_content_layout) # Clear only the dynamic content layout
    
    if basic_oauth == 'basic':
        LoginForm("Username","Password")
    else
        LoginForm("Client ID","Client Secret")