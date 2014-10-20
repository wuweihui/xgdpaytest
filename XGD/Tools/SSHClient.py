#/usr/bin/python27
#-*- coding: utf-8 -*-
#  Copyright 2011-2013 wuweihui@cn.ibm.com
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os, re, time
import stat, sys
import paramiko
__DEBUG__ = False

def _start_client(self, event=None):
    self.banner_timeout = 120
    self._orig_start_client(event)

paramiko.transport.Transport._orig_start_client = paramiko.transport.Transport.start_client
paramiko.transport.Transport.start_client = _start_client

EOF = chr(5)

class SSHClient(object):

    enable_ssh_logging = staticmethod(lambda path: paramiko.util.log_to_file(path))

    def __init__(self, host, port=22, timeout=10.0, newline='\n', prompt=None, promptlen=50):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.host = host
        self.port = int(port)
        self.shell = None
        self.set_prompt(prompt, promptlen)
        self._default_log_level = 'INFO'
        self.set_timeout(timeout or 10)
        self.set_newline(newline)
        self.ptywidth = 80
        self.buf = ''
        self.rawno = -1

    def set_timeout(self, timeout):
        old = getattr(self, '_timeout', 10.0)
        self._timeout = timeout
        return old
    
    def set_newline(self, newline):
      old = getattr(self, '_newline', '\n')
      self._newline = newline
      return old
    
    def set_prompt(self, prompt, promptlen=50):
      old = getattr(self, '_prompt', (None, 0))
      self._prompt = (prompt, promptlen)
      return old
   
    def set_prompt_length(self, length):
       old = getattr(self, '_prompt', (None, 50))
       self._prompt = (old[0], length)
       return old[1]
  
    def _prompt_is_set(self):
      return self._prompt[0] is not None
  
    def set_default_log_level(self, level):
      self._is_valid_log_level(level, raise_if_invalid=True)
      old = self._default_log_level
      self._default_log_level = level.upper()
      return old
    
    def login(self, username, password):
        self.client.connect(self.host, self.port, username, password)

    def login_with_public_key(self, username, keyfile, password):
        self.client.connect(self.host, self.port, username, password,
                            key_filename=keyfile)

    def close(self):
        self.client.close()
        
    def close_connection(self):
        self.close()

    def execute_command(self, command, ret_mode='stdout'):
        _, stdout, stderr = self.client.exec_command(command)
        return self._read_command_output(stdout, stderr, ret_mode)

    def start_command(self, command):
        _, self.stdout, self.stderr = self.client.exec_command(command)

    def read_command_output(self, ret_mode='stdout'):
        return self._read_command_output(self.stdout, self.stderr, ret_mode)

    def _read_command_output(self, stdout, stderr, ret_mode):
        if ret_mode.lower() == 'both':
            return stdout.read(), stderr.read()
        if ret_mode.lower() == 'stderr':
            return stderr.read()
        return stdout.read()

    def open_shell(self):
        self.shell = self.client.invoke_shell(width=self.ptywidth)

    def _write(self, text):
        self.shell.sendall(text)

    def _read(self):
        data = ''
        while self.shell.recv_ready():
            data += self.shell.recv(100000)
        return data
    
    def readex(self, length):
       ret = ''
       while self.buf and length > 0:
          ret += self.buf[0]
          self.buf = self.buf[1:]
          length -= 1
       if length > 0:
          if self.shell.recv_ready():
               ret += self.shell.recv(length)
       return ret
    
    def _read_char(self):
       ret = self.readex(1)
       if ret == '':
            next = self.readex(1)
            ret += next
            if next == '[':
                next = self.readex(1)
                ret += next
                while not next.isalpha():
                    next = self.readex(1)
                    ret += next
                ret += self._read_char()
       if ret == '':
          ret = EOF
       return ret
    
    def write(self, text, loglevel=None):
        self.write_bare(text + self._newline)
        #patch for windows
        if self._newline == '\r':
            data = self.read_until('\n', 1, loglevel)
        else:
            data = self.read_until(self._newline, 2, loglevel)
        return data

    def write_bare(self, text):
        try:
            text = str(text)
        except UnicodeError:
            raise ValueError('Only ascii characters are allowed in SSH.'
                             'Got: %s' % text)
        if not self._prompt_is_set():
            msg = ("Using 'Write' or 'Write Bare' keyword requires setting "
                   "prompt first. Prompt can be set either when taking library "
                   "into use or when using 'Open Connection' keyword.")
            raise RuntimeError(msg)
        if self.shell is None:
            self.open_shell()
            self.read_until_prompt('INFO')
        self._info("Writing %s" % repr(text))
        self._write(text)
    
    def read(self, loglevel=None):
        if self.shell is None:
            self.open_shell()
        ret = self._read()
        self._log(ret, loglevel)
        return ret

    
    def read_char(self):
        """
        wrap read_char, remove the linux output style flags
        """
        if __DEBUG__:
            return self.readex(1)
        
        re_linux_style = re.compile(r'\\[\d+[\;\d+]*m')
        
        tmp = self._read_char()
        if len(tmp) > 2:
           stylematch = re_linux_style.match(tmp)
           if stylematch:           
              ret = tmp.replace(stylematch.group(), '')
              self.buf += ret[1:]
              return ret[0] != EOF and ret[0] or ''
           
        return tmp.replace(EOF, '')

    def read_until(self, expected, length=50, loglevel=None):
        if self.shell is None:
            self.open_shell()
        ret = ''    
        self.rawno = -1
        start_time = time.time()
        while time.time() < float(self._timeout) + start_time:
            next = self.read_char()
            if not next:
               time.sleep(0.1)
               continue
            ret += next
            if (isinstance(expected, basestring) and expected in ret[-length:]) or \
               (not isinstance(expected, basestring) and expected.search(ret[-length:])):
                self._log(ret, loglevel)
                return ret
        self._log(repr(ret), loglevel)
        if not isinstance(expected, basestring):
            expected = expected.pattern
        raise AssertionError("No match found for '%s' in %s"
                                 % (expected, str(self._timeout)))

    def read_until_prompt(self, loglevel=None):
        if not self._prompt_is_set():
           raise RuntimeError('Prompt is not set')
        prompt, promptlen = self._prompt
        return self.read_until(prompt, promptlen, loglevel)

    def write_until_expected_output(self, text, expected, timeout,
                                    retry_interval, loglevel=None):
        timeout = float(timeout)
        retry_interval = float(retry_interval)
        old_timeout = self.set_timeout(retry_interval)
        starttime = time.time()
        while time.time() - starttime < timeout:
            self.write_bare(text)
            try:
                ret = self.read_until(expected, loglevel=loglevel)
                self.set_timeout(old_timeout)
                return ret
            except AssertionError:
                pass
        self.set_timeout(old_timeout)
        raise AssertionError("No match found for '%s' in %s"
                             % (expected, str(timeout)))
    
    def close_log(self):
       def _closed_log(msg, level=None):
          pass
       self._log = _closed_log
    
    def _info(self, msg):
        self._log(msg, 'INFO')

    def _debug(self, msg):
        self._log(msg, 'DEBUG')
        
    def _log(self, msg, level=None):
        self._is_valid_log_level(level, raise_if_invalid=True)
        msg = msg.strip()
        if level is None:
            level = self._default_log_level
        if msg != '':
            print('*%s* %s' % (level.upper(), msg))

    def _is_valid_log_level(self, level, raise_if_invalid=False):
        if level is None:
            return True
        if isinstance(level, basestring) and \
                level.upper() in ['TRACE', 'DEBUG', 'INFO', 'WARN', 'HTML']:
            return True
        if not raise_if_invalid:
            return False
        raise AssertionError("Invalid log level '%s'" % level)

if __name__ == '__main__':
    host = '172.20.5.200'
    ts = SSHClient(host)
    ts.login('root', 'root200')
    print ts.execute_command('ls', 'stdout')
    print '==========='
    print ts.execute_command('ls -l /etc', 'stdout')
    print '==========='
    #time.sleep(20)