"""
@author: djs
@revision history:
    *djs 07/14 - created
    *djs 04/16 - updating documentation
"""


class EscPressedException(Exception):

    def __init__(self):
        pass
        
    def __str__(self):
        return 'Escape key pressed.'


class HandlerException(Exception):

    def __init__(self, err):
        self.err = err
    
    def __str__(self):
        return 'Handler error: {}'.format(self.err)
    

class EyeTribeException(Exception):

    def __init__(self):
        pass
    
    def __str__(self):
        return 'EyeTribe error.'
