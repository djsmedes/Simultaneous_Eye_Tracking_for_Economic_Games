"""
@author: djs
@revision history:
    *djs 05/14 - created
    *djs 04/16 - updating documentation
"""

from copy import deepcopy
import datetime


class Packet:
    CONTRIB_MODE = 0
    FEEDBACK_MODE = 1
    
    which_mode = CONTRIB_MODE
    which_round = 1

    def __init__(self, values=None):
        self.time = datetime.datetime.now().isoformat(' ')
        self.values = values
        if values is None:
            self.values = {}
        self.round = deepcopy(Packet.which_round)
        self.mode = deepcopy(Packet.which_mode)
        
    def getXY(self):
        return (self.values[u'frame'][u'avg'][u'x'],
                self.values[u'frame'][u'avg'][u'y'])
