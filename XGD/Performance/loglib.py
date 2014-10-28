#-*- coding:utf-8 -*-

import threading
import sys, os
import traceback

loglib_prlock = threading.RLock()
loglib_loglock = threading.RLock()
loglib_errlock = threading.RLock()

__DEBUG__ = 0

def debug_print(level, *args, **kws):
    '''
    optional keyword:  level
    usage example:
        debugprint(2, 'test message', 'something else', 'some values')
        debugprint(1, 'function name', 'args', 'kws')
    '''
    if level == None:
        level = 0
    if level <= __DEBUG__:
        with loglib_prlock:
            print level, 
            for arg in args:
                print arg,
            for key, val in kws.items():
                print key, "=", val,
            print ''
        

def set_debug_level(level):
    global __DEBUG__
    __DEBUG__ = level
    
loglib_out = sys.stdout
loglib_err = sys.stderr
loglib_LOG_FLAG = True

def log(*args, **kws):
    """
    The log message is write to sys.stdout window by default
    please use set_log_path(path) to change this setting.
    """
    if loglib_LOG_FLAG and loglib_out:
        with loglib_loglock:
            for arg in args:
                loglib_out.write(str(arg) + " ")   
            if args:         
                loglib_out.write("\n")
            for key, val in kws.items():
                loglib_out.write(str(key) + "=" + str(val) + "\n")

def logerr(*args, **kws):
    """
    The log message is write to sys.stderr window by default
    please use set_log_path(path) to change this setting.
    """
    if loglib_err:
        with loglib_errlock:
            for arg in args:
                loglib_err.write(str(arg) + " ")   
            if args:         
                loglib_err.write("\n")
            for key, val in kws.items():
                loglib_err.write(str(key) + "=" + str(val) + "\n")


def set_log_path(out=None, err=None):
    """
    log path could be a file path string or a file type instance
    the file type instance must have 'write' method
    you can also set the path to None to stop logging
    """
    global loglib_out, loglib_err
    org_out, org_err = loglib_out, loglib_err
    if isinstance(out, str):
        if os.path.exists(out):
            print "Log file already exists, it will be over written!"
        try:
            loglib_out = open(out, 'wb')
        except:
            print "Log file open failed! Default setting will be used!"
    elif out:
        loglib_out = out
        
    if isinstance(err, str):
        if out == err and out:  #file already open for out
            loglib_err = loglib_out
            return True
        if os.path.exists(out):
            print "Log file already exists, it will be over written!"
        try:
            loglib_err = open(err, 'wb')
        except:
            print "Log file open failed! Default setting will be used!"
    elif err:
        loglib_err = err
    
    return org_out, org_err

def log_end():
    if isinstance(loglib_out, file):
        loglib_out.close()
        
    if isinstance(loglib_err, file):
        loglib_err.close()
        
def pause_logging():
    """
    In some case the logging process should be stopped, like in the performance testing.
    """
    global loglib_LOG_FLAG
    try:
        loglib_out.flush()
    except:
        pass
    loglib_LOG_FLAG = False

def resume_logging():
    global loglib_LOG_FLAG
    loglib_LOG_FLAG = True