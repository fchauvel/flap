

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
        context.record("name", event)
        context.activate(COMMAND_DETECTED)


class SuccessState(State):
    
    def default(self, event, context):
        context.match()
        context.restartFrom(event)       
        
        
class CommandDetected(SuccessState):
    
    def onOpenOptions(self, event, context):
        context.record("ignored", event)
        context.activate(OPTIONS_OPENED)
        
    def onOpenParameter(self, event, context):
        context.record("ignored", event)
        context.activate(PARAMETER_OPENED)
        
        
class OptionsOpened(State):
    
    def default(self, event, context):
        context.record("options", event)
        context.activate(OPTIONS_READ)


class OptionsRead(State):
    
    def onCloseOptions(self, event, context):
        context.record("ignored", event)
        context.activate(COMMAND_DETECTED)


class ParameterOpened(State):
    
    def default(self, event, context):
        context.record("parameters", event)
        context.activate(PARAMETER_READ)


class ParameterRead(State):
    
    def onCloseParameter(self, event, context):
        context.record("ignored", event)
        context.activate(PARAMETER_CLOSED)
        
        
class ParameterClosed(SuccessState):
    
    def onOpenParameter(self, event, context):
        context.record("ignored", event)
        context.parameterOpened()


READY = Ready()
COMMAND_DETECTED = CommandDetected()        
OPTIONS_OPENED = OptionsOpened()
OPTIONS_READ = OptionsRead()
PARAMETER_OPENED = ParameterOpened()
PARAMETER_READ = ParameterRead()
PARAMETER_CLOSED = ParameterClosed()


class Match:
    
    def __init__(self, name, options, parameters):
        self._name = name
        self._options = options
        self._parameters = parameters
        
    def name(self):
        return self._name.text()
    
    def options(self):
        texts = [ fragment.text() for fragment in self._options ]
        return texts
    
    def parameters(self):
        texts = [ fragment.text() for fragment in self._parameters ]
        return texts



class Automaton:
           
    def __init__(self):
        self._state = READY
        self._buffer = {}
        self._matches = []
    
    def activate(self, state):
        self._state = state
            
    def record(self, key, event):
        if key not in self._buffer.keys():
            self._buffer[key] = [event] 
        else:
            self._buffer[key].append(event)
        
    def match(self):
        name = self._buffer.get("name", [None])[0]
        options = self._buffer.get("options", [])
        parameters = self._buffer.get("parameters", [])
        match = Match(name, options, parameters)
        self._matches.append(match)

    def restartFrom(self, event):
        self.reset()
        self.accept(event)
            
    def reset(self):
        self._state = Ready()
        self._buffer = {}
    
    def acceptAll(self, fragments):
        for eachFragment in fragments:
            self.accept(eachFragment)
        if isinstance(self._state, SuccessState):
            self.match()
                
    def accept(self, fragment):
        if self.ignore(fragment):
            self.record("ignored", fragment)
            
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
