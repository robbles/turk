import time

def log_method(m):
    def _logging_method(*args, **kwargs):
        print '[%s] %s called' % (time.ctime(), m.__name__)
        return m(*args, **kwargs)
    return _logging_method


