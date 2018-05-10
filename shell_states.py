import re
import time

class ShellStateLink:
  def __init__(self, pattern, toState):
    self.toState = toState
    self.pattern = pattern 

  def match(self, line):
    return re.match(self.pattern, line)
    

class ShellStateTrigger:
  def __init__(self, trigger, text):
    self.text = text
    self.trigger = trigger

  def perform(self):
    self.trigger(self.text)



class ShellState:
  def __init__(self, sid, timeout = 0, incompleteLine = False, note = ''):
    self.sid = sid
    self.timeout = timeout
    self.incompleteLine = incompleteLine
    self.links = []
    self.triggers = []
    self.note = note


  def setNote(self, note):
    self.note = note

  def setTimeout(self, timeout = 0):
    self.timeout = timeout

  def setIncompleteLine(self, incompleteLine = False):
    self.incompleteLine = incompleteLine

  def addLink(self, link):
    self.links.append(link)

  def addTrigger(self, trigger):
    self.triggers.append(trigger)


class StateTransitionLog:
  def __init__(self, fromId, toId, line, match):
    self.fromId = fromId
    self.toId = toId 
    self.line = line 
    self.match = match



class ShellStates:
  def __init__(self, shell):
    self.shell = shell
    self.states = []
    s = self.addState()
    s.setNote("Error")
    s = self.addState()
    s.setNote("Begin")
    self.transitions = []


  def begin(self):
    return self.states[1]

  def error(self):
    return self.states[0]

  def addState(self):
    sid = len(self.states) 
    s = ShellState(sid)
    self.states.append(s)
    return s

  def summary(self):
    s = 'Transitions Summary:\n'
    for transition in self.transitions:
      s +=  "transition %d (%s) -> %d (%s), line:'%s', matched:'%s'\n" % (transition.fromId, self.states[transition.fromId].note, transition.toId, self.states[transition.toId].note, transition.line, transition.match.group())
    return s


  """
    Returns when last state has no links
  """
  def run(self):
    state = self.begin()
    expirytime = None
    curtime = None
    expired = False
    

    while not expired:
      for trigger in state.triggers:
        trigger.perform()
      self.shell.setRecvTimeout(state.timeout)

      if state.timeout is not None:
        curtime = time.time()
        expirytime = curtime + state.timeout
      else:
        expirytime = None

      # last node
      if len(state.links) == 0:
        break

      match = None
      while True:
        line = self.shell.getStdoutLine(incompleteLine=state.incompleteLine)
        if line is None:
          if expirytime is not None:
            curtime = time.time()
            if curtime > expirytime:
              expired = True
              break
          continue

        print("DBG got: " + line)

        for link in state.links:
          match = link.match(line)
          if match:
            print("DBG change state from %d to %d, line:'%s', matched:'%s'" % (state.sid, link.toState.sid, line, match.group()))
            self.transitions.append(StateTransitionLog(state.sid, link.toState.sid, line, match))
            #state.matches = matches
            #state.line = line 
            state = link.toState
            break
        if match:
          break

        # look for next line until timeout
        curtime = time.time()
        if expirytime is not None and curtime > expirytime:
          expired = True
          break
       


      






  


