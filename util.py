import traceback


def exception2string():
  return traceback.format_exc()

def error(msg):
  print(msg)

def warn(msg):
  print(msg)

def info(msg):
  print(msg)
