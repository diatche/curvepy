from .extension import Extension
from ..constant import Constant
from intervalpy import Interval

class ConstantExtension(Extension):

    """
    Extends an end of a function with a line using its edge values.
    """

    name = "constant"

    def update_extension(self):
        if self.curve.domain.is_empty:
            self.start_func.value = None
            self.end_func.value = None
            return

        if self.start:
            x = self.curve.domain.start
            y = self.curve.y(x)
            self.start_func.value = y

        if self.end:
            x = self.curve.domain.end
            y = self.curve.y(x)
            self.end_func.value = y

    def create_extension_func(self, start=False):
        return Constant(0)
