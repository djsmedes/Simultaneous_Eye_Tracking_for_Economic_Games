"""
@author: djs
@revision history:
    *djs 06/14 - created
    *djs 04/16 - updating documentation
"""

from psychopy import visual


class Button(object):
    """ A button that can have text on it. Also has a "clickable" property, but relies on external code to check it to
        determine what should happen on a click.
    """

    def __init__(
            self,
            window,
            pos=(0, 0),
            text='Weiter',
            font_size=20,
            width=85,
            height=35,
            margin=10,
            line_color=None,
            clickable_color='green',
            not_clickable_color='lightgrey',
            is_clickable=False,
            text_color='white'
            ):
        self.window = window
        self._frame = visual.Rect(
                self.window,
                width=width,
                height=height,
                lineColor=line_color,
                pos=pos
                )
        self._text_stim = visual.TextStim(
                self.window,
                text=text,
                pos=pos,
                height=font_size,
                wrapWidth=width-2*margin,
                color=text_color
                )
        self._clickable = is_clickable
        self.clickable_color = clickable_color
        self.not_clickable_color = not_clickable_color
        if is_clickable:
            self._frame.fillColor = self.clickable_color
        else:
            self._frame.fillColor = self.not_clickable_color
        
    @property
    def text(self):
        return self._text_stim.text

    @text.setter
    def text(self, new_text):
        self._text_stim.setText(new_text)
        
    @property
    def pos(self):
        return self._frame.pos

    @pos.setter
    def pos(self, new_pos):
        self._frame.pos = new_pos
        self._text_stim.pos = new_pos
        
    @property
    def clickable(self):
        return self._clickable

    @clickable.setter
    def clickable(self, bool_):
        self._clickable = bool_
        if bool_:
            self._frame.fillColor = self.clickable_color
        else:
            self._frame.fillColor = self.not_clickable_color

    @property
    def frame(self):
        return self._frame

    @property
    def color(self):
        return self._frame.fillColor

    @color.setter
    def color(self, new_color):
        self._frame.fillColor = new_color

    def draw(self):
        self._frame.draw()
        self._text_stim.draw()
    
    def setPos(self, pos):
        """ For PsychoPy compatibility (can easily use the .setPos method of every object in a list)
        :param pos: tuple with the position you wish to set
        """
        self._frame.pos = pos
        self._text_stim.pos = pos
        
    def setText(self, text):
        """ For PsychoPy compatibility
        :param text: the text to set
        """
        self._text_stim.setText(text)
