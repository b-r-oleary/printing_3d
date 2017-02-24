from __future__ import division, print_function

from time import time
import inspect
import textwrap

def verbosify(function,
              keyword='announce',
              line_length=50,
              time_precision=4,
              show_time=True,
              bullet_point='- '):
    """
    verbosify is a decorator that should be
    applied to class methods for classes
    that have a self.verbose = True/False
    field.

    If self.verbose is True, then inserting a keyword argument announce="<some string>"
    which result in printing:

    <some string>:          <time taken by the method to complete in seconds>

    this is used to monitor the progress of class methods and their timing.
    
    *inputs*
    function (function) the function to modify
    keyword (str) the keyword used to contain the announcement
    line_length (int) the position in the line at which to try to put the 
            time required for the function to run.
    time_precision (int) the number of digits requested for reporting the time
            required for the function to run
    show_time (bool) whether or not to show the time required for the function
            to run.
    """
    
    # using a keyword argument 'announce', we can specify a default message
    # for a verbose method, but it should be possible to overwrite this default
    # message with the method:
    
    args = inspect.getargspec(function)
    if args.defaults is not None:
        defaults = {key: value for key, value 
                    in zip(args.args[-len(args.defaults):],
                           args.defaults)}
        default_value = (defaults[keyword] if keyword in defaults else None)
    else:
        defaults = {}
        default_value = None
    
    
    time_format = '%.' + str(time_precision) + 'fs'

    
    def verbose_function(self, *args, **kwargs):
        if self.verbose:
            announce = True
            if keyword in kwargs:
                announcement = kwargs[keyword]
                del kwargs[keyword]
            elif default_value is not None:
                announcement = default_value
            else:
                announce = False

        if announce:
            announcement = bullet_point + ('\n' + ' ' * len(bullet_point)).join(textwrap.wrap(announcement, line_length))
            print(announcement, end=(":" + ' ' * (line_length - len(announcement.split('\n')[-1]) 
                                                 if line_length > len(announcement.split('\n')[-1]) 
                                                 else 1)))
            
        t0 = time()
        output = function(self, *args, **kwargs)
        dt = time() - t0
        
        if announce and show_time: print(time_format % dt)
        return output
    
    return verbose_function
