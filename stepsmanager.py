import sys
import util
import jobstep


class StepsManager(object):
  def __init__(self,_args):
    self.args = _args
    self.clear()

  def clear(self):
    self.steps = {}
    self.dependencies = {}

  def register(self,_className,_dependencies,pollInterval=0,timeout=0):
    if not _className in self.steps.keys():
      for _dependency in _dependencies:
        if not _dependency in self.steps.keys():
          print("Error: " + _className + " has unfullfilled dependency: " + _dependency)
          self.clear()
          return
      try:
        cls = self.importClass(_className)
        obj = cls(self.args)
        obj.setPollInterval(pollInterval)
        obj.setTimeout(timeout)
        self.steps[_className] = obj
        self.dependencies[_className] = _dependencies
      except:
        util.error("Error registering " + _className + ": " + util.exception2string())
        self.clear()
    else:
      util.warn("warning trying to re-register:" + _className)


  def show(self):
    if len(self.steps) == 0:
      util.info("0 steps")
      return
    for key,obj in self.steps.iteritems():
      util.info("object: " + key + " status:" + obj.getStatus().getName())
      
  def run(self):
    pending_steps = []

    # reset status to idle
    for key,obj in self.steps.iteritems():
      obj.setInactive()
      pending_steps.append(key)

    # run tasks with no dependencies first (in parallel)
    while len(pending_steps)>0:
      for key_idx in range(len(pending_steps)-1,-1,-1):
        key = pending_steps[key_idx]
        obj = self.steps[key]
        if obj.isComplete():
          del pending_steps[key_idx]
        elif obj.isInactive():
          all_dependencies_ok = True
          for dependency in self.dependencies[key]:
            dep_obj = self.steps[dependency]
            if dep_obj.getStatus() != JobStepStatus.COMPLETE:
              all_dependencies_ok = False
          if all_dependencies_ok:
            try:
              obj.runTask()
            except:
              util.error("Error running " + _className + ": " + util.exception2string())
              return
        elif obj.isRunning():
          # TODO: add polling interval
          if obj.isTimeoutExpired():
            util.error("Error expired timeout for " + key + " after " + str(obj.getElapsedStartTime()) + "s")
            return
          if obj.getElapsedLastCheckTime() > obj.getPollInterval():
            obj.updateProgress()
        elif obj.isError():
          util.error("An error happened in " + key + ": " + obj.getMessage())
          return
        else:
          util.error("Error unknown status of " + key +": " + obj.getStatus())
          return





  def importClass(self,name):
    # avoid repeating current package
    name = __package__ + "." + name
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


