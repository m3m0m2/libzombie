from __future__ import print_function
import paramiko
import os
import getpass
import select
import socket
      


class SshShell(object):
  def __init__(self, _host):
    self.host = _host
    self.setRecvTimeout(0)
    self.setLineSep("\r\n")
    self.recvbufsize = 4000


  def __del__(self):
    if self.client is not None:
      self.client.close()
      self.client = None

  """
    None disables timeout
  """
  def setRecvTimeout(self, _recvTimeout):
    self.recvTimeout = _recvTimeout
    if hasattr(self,'channel'):
      self.channel.settimeout(_recvTimeout)

  def setLineSep(self, _sep):
    self.linesep = _sep

  def connect(self, use_passwd = True, use_rsa_key = True, use_dsa_key = True):
    valid_key = False
    use_config = True
    has_config_host = False
    rsa_key_file = None
    dsa_key_file = None
    key = None
    host = None
    user = None
    password = None
    proxy = None
    args = { }

    try:
      if use_config:
        try:
          config = paramiko.SSHConfig()
          config.parse(open(os.path.expanduser('~/.ssh/config')))
          confighost = config.lookup(self.host)
          if self.host in confighost:
            print("Using ssh_config")
            has_config_host = True
            host = confighost['hostname']
            user = confighost['user']
            if 'proxycommand' in confighost:
              proxy = paramiko.ProxyCommand(
                subprocess.check_output(
                  [os.environ['SHELL'], '-c', 'echo %s' % confighost['proxycommand']]
                ).strip()
              )
            if 'identityfile' in confighost:
              rsa_key_file = os.path.expanduser(confighost['identityfile'])
              dsa_key_file = os.path.expanduser(confighost['identityfile'])
        except:
          pass
      # no ssh_config
      if host is None:
        host = self.host

      if user is None:
        user = getpass.getuser()

      # Attempt RSA validation without passwd
      if use_rsa_key:
        if rsa_key_file is None:
          try:
            rsa_key_file = os.path.join(os.environ['HOME'], '.ssh', 'id_rsa')
            key = paramiko.RSAKey.from_private_key_file(rsa_key_file)
            valid_key = True
            print("Using RSA Key")
          #except paramiko.PasswordRequiredException:
          except:
            pass
            #password = getpass.getpass('RSA key password: ')
            #key = paramiko.RSAKey.from_private_key_file(path, password)
      if not valid_key and use_dsa_key:
        if dsa_key_file is None:
          try:
            dsa_key_file = os.path.join(os.environ['HOME'], '.ssh', 'id_dsa')
            key = paramiko.DSSKey.from_private_key_file(dsa_key_file)
            print("Using DSA Key")
            valid_key = True
          except:
            pass

      if not valid_key and use_passwd:
        print("Using Password")
        password = getpass.getpass('Enter SSH password: ')

      client = paramiko.SSHClient()
      client.load_system_host_keys()
      client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      args['username'] = user
      if password is not None:
        args['password'] = password
      if valid_key:
        args['pkey'] = key
      if proxy:
        args['sock'] = proxy

      client.connect(host, **args)
      #client.connect(host, username=user, password=password, key_filename=key_filename,look_for_keys=True, sock=proxy)
      self.client = client
      self.setinteractive()
    except Exception as e:
      msg = "Connection failed  to %s with error %s" % (host, e.args)
      print(msg)
      raise Exception("Connection Failed")


  def setinteractive(self):
    self.channel = self.client.invoke_shell()
    #self.channel.makefile('wb')
    #self.channel.makefile('rb')
    #self.channel.makefile_stderr('rb')
    self.channel.setblocking(0)
    self.stdoutbuf = ''
    self.stderrbuf = ''


  def execute(self, _cmd):
    self.channel.send(_cmd + "\n")

  
  def hasStdout(self):
    if len(self.stdoutbuf) > 0:
      return True
    return self.channel.recv_ready() 

  def hasStderr(self):
    if len(self.stderrbuf) > 0:
      return True
    return self.channel.recv_stderr_ready()


  """
    Ignore last line if it doesn't have line sep at the end
  """
  def getStdoutLine(self, blocking = True, incompleteLine = False):
    # already buffered
    lineend = self.stdoutbuf.find(self.linesep)
    if lineend >= 0:
      _txt = self.stdoutbuf[ 0 : lineend ]
      self.stdoutbuf = self.stdoutbuf[ lineend + len(self.linesep) : ]
      return _txt

    if self.channel.recv_ready() or (blocking and not self.isClosed()):
      try:
        self.stdoutbuf += self.channel.recv(self.recvbufsize)
      except socket.timeout:
        return None

    lineend = self.stdoutbuf.find(self.linesep)
    if lineend >= 0:
      _txt = self.stdoutbuf[ 0 : lineend ]
      self.stdoutbuf = self.stdoutbuf[ lineend + len(self.linesep) : ]
      return _txt

    if incompleteLine and len(self.stdoutbuf) > 0:
      _txt = self.stdoutbuf
      self.stdoutbuf = ''
      return _txt

    return None

  def getStderrLine(self, blocking = True, incompleteLine = False):
    # already buffered
    lineend = self.stderrbuf.find(self.linesep)
    if lineend >= 0:
      _txt = self.stderrbuf[ 0 : lineend ]
      self.stderrbuf = self.stderrbuf[ lineend + len(self.linesep) : ]
      return _txt

    if self.channel.recv_stderr_ready() or (blocking and not self.isClosed()):
      try:
        self.stderrbuf += self.channel.recv_stderr(self.recvbufsize)
      except socket.timeout:
        return None

    lineend = self.stderrbuf.find(self.linesep)
    if lineend >= 0:
      _txt = self.stderrbuf[ 0 : lineend ]
      self.stderrbuf = self.stderrbuf[ lineend + len(self.linesep) : ]
      return _txt

    if incompleteLine and len(self.stderrbuf) > 0:
      _txt = self.stderrbuf
      self.stderrbuf = ''
      return _txt

    return None

  def isClosed(self):
    return self.channel.closed

