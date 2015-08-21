
from flap.lexer import FragmentKind

class State:

    def onCommand(self, event, context):
        self.default(event, context)
    
    def onOpenOptions(self, event, context):
        self.default(event, context)
   
    def onCloseOptions(self, event, context):
        self.default(event, context)
        
    def onOpenParameter(self, event, context):
        self.default(event, context)
        
    def onCloseParameter(self, event, context):
        self.default(event, context)
        
    def default(self, event, context):
        context.restartFrom(event)


class InitialState(State):
    
    def default(self, event, context):
        context.reset()


class Ready(InitialState):
    
    def onCommand(self, event, context):
        context.record(event)
        context.activate(COMMAND_DETECTED)


class SuccessState(State):
    
    def default(self, event, context):
        context.match()
        context.restartFrom(event)       
        
        
class CommandDetected(SuccessState):
    
    def onOpenOptions(self, event, context):
        context.record(event)
        context.activate(OPTIONS_OPENED)
        
        
class OptionsOpened(State):
    
    def default(self, event, context):
        context.record(event)
        context.activate(OPTIONS_READ)


class OptionsRead(State):
    
    def onCloseOptions(self, event, context):
        context.record(event)
        context.activate(COMMAND_DETECTED)


class ParameterOpened(State):
    
    def default(self, event, context):
        context.record(event)
        context.activate(PARAMETER_READ)


class ParameterRead(State):
    
    def onCloseParameter(self, event, context):
        context.record(event)
        context.activate(PARAMETER_CLOSED)
        
        
class ParameterClosed(SuccessState):
    
    def onOpenParameter(self, event, context):
        context.record(event)
        context.parameterOpened()

READY = Ready()
COMMAND_DETECTED = CommandDetected()        
OPTIONS_OPENED = OptionsOpened()
OPTIONS_READ = OptionsRead()
PARAMETER_OPENED = ParameterOpened()
PARAMETER_READ = ParameterRead()
PARAMETER_CLOSED = ParameterClosed()


class Automaton:
           
    def __init__(self):
        self._state = READY
        self._buffer = []
        self._matches = []
    
    def activate(self, state):
        self._state = state
            
    def record(self, event):
        self._buffer.append(event)
        
    def match(self):
        self._matches.append(self._buffer)

    def restartFrom(self, event):
        self.reset()
        self.accept(event)
            
    def reset(self):
        self._state = Ready()
        self._buffer = []
    
    def acceptAll(self, fragments):
        for eachFragment in fragments:
            self.accept(eachFragment)
        if isinstance(self._state, SuccessState):
            self.match()
                
    def accept(self, fragment):
        if self.ignore(fragment):
            self.record(fragment)
            
        else:
            if fragment.isACommand():
                self._state.onCommand(fragment, self)
            
            elif fragment.text() == "[":
                self._state.onOpenOptions(fragment, self)
            
            elif fragment.text() == "]":
                self._state.onCloseOptions(fragment, self)
            
            elif fragment.text() == "{":
                self._state.onOpenParameter(fragment, self)
                
            elif fragment.text() == "}":
                self._state.onCloseParameter(fragment, self)
                        
            else:
                self._state.default(fragment, self)
    
    def ignore(self, fragment):
        return fragment.isAComment() or fragment.isAWhiteSpace() 
        
    def matches(self):
        return self._matches

