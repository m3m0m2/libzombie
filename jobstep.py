import inspect
import enum
import time


class JobStepArgs(object):

  def __init__(self):
    self.clear()

  def get(self,_key):
    if _key in self.data.keys():
      return self.data[_key]
    return None

  def set(self,_key,_value):
    self.data[_key] = _value

  def clear(self):
    self.data = { }



class JobStepStatus(enum.Enum):
  INACTIVE = 1
  ERROR = 2
  RUNNING = 3
  COMPLETE = 4

  def getName(self):
    return self.name



class JobStep(object):

  #TODO: add optional args: poll_interval, started_time
  def __init__(self, _args=None):
    self.setStatus(JobStepStatus.INACTIVE)
    self.setArgs(_args)
    self.setProgress(0)
    self.setMessage('')
    self.setPollInterval(5)
    self.setTimeout(0)
    self.lastCheckTime = 0
    print('JobStep constructor')

  def getArgs(self):
    return self.args

  def setArgs(self,_args):
    self.args=_args

  def getStatus(self):
    return self.status

  def setStatus(self,_status):
    self.status = _status

  # Manage running time, poll interval and timeout

  def getTimeout(self):
    return self.timeout

  def setTimeout(self,_timeout):
    self.timeout = _timeout

  def isTimeoutExpired(self):
    if self.timeout == 0:
      return False
    return (self.getStartTime() + self.timeout) <= time.time()

  def getPollInterval(self):
    return self.pollInterval

  def setPollInterval(self,_pollInterval):
    self.pollInterval = _pollInterval

  def getStartTime(self):
    return self.startTime

  def setStartTimeNow(self):
    self.startTime = time.time()

  # Only valid if in running status
  def getElapsedStartTime(self):
    return time.time() - self.startTime

  def getLastCheckTime(self):
    return self.lastCheckTime

  def setLastCheckTimeNow(self):
    self.lastCheckTime = time.time()

  def getElapsedLastCheckTime(self):
    return time.time() - self.lastCheckTime

  # Override this to run the task
  def run(self):
    raise NotImplementedError("Class %s doesn't implement method %s" % (self.__class__.__name__,inspect.stack()[0][3]))

  # Wrapper around run
  def runTask(self):
    self.setStartTimeNow()
    self.setRunning()
    self.run()



  """
  # Override this to check the task progress
  return [progress, msg] where progress is between 0-100 (0=just started, 100=complete) or <0 for fatal errors
  """
  def checkProgress(self):
    raise NotImplementedError("Class %s doesn't implement method %s" % (self.__class__.__name__,inspect.stack()[0][3]))

  # Wrapper around checkProgress
  def updateProgress(self):
    self.setLastCheckTimeNow()
    _progress, _msg = self.checkProgress()
    self.setProgress(_progress)
    self.setMessage(_msg)
    if self.getProgress() == 100:
      self.setComplete()

  # for progress logging
  def getProgress(self):
    return self.progress
  
  def setProgress(self,_progress):
    self.progress = _progress

  def getMessage(self):
    return self.msg

  def setMessage(self,_msg):
    self.msg = _msg


  # Status related
  def isComplete(self):
    return self.getStatus() == JobStepStatus.COMPLETE

  def setComplete(self):
    self.setStatus(JobStepStatus.COMPLETE)

  def isInactive(self):
    return self.getStatus() == JobStepStatus.INACTIVE

  def setInactive(self):
    self.setStatus(JobStepStatus.INACTIVE)

  def isRunning(self):
    return self.getStatus() == JobStepStatus.RUNNING

  def setRunning(self):
    self.setStatus(JobStepStatus.RUNNING)

  def isError(self):
    return self.getStatus() == JobStepStatus.ERROR

  def setError(self):
    self.setStatus(JobStepStatus.ERROR)


