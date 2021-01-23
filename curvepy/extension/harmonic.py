import warnings
from .extension import Extension
from ..constant import Constant
from ..empty import Empty
from ..curve import Curve

class HarmonicExtension(Extension):

    """
    Extends an end of a function with a series of sine wave using its edge tangents.
    """

    name = "harmonic"

    def __init__(self, func, period=None, degree=3, regression_degree=5, **kwargs):
        self.period = float(period)
        self.degree = int(degree)
        self.regression_degree = int(regression_degree)
        self.regression = 0.1
        assert self.period > 0
        assert self.degree > 1
        assert self.regression_degree > 1
        self._fast_sma = Empty()
        self._extension_offset = Constant(0)
        self.smas = []
        self.macs = []
        super().__init__(func, **kwargs)
        if self.start:
            raise Exception('Weave extension currently only supports extending the end')

    def update_extension(self):
        x = self.curve.domain.end
        y = self._fast_sma.y(x)
        y_ext = self.end_func.y(x)
        
        if y_ext is None:
            return

        y_offset = y - y_ext
        if y_offset != 0:
            self._extension_offset.value = self._extension_offset.value + y_offset

    def create_extension_func(self, start=False):
        base_line = Constant(0)
        hsmas = reversed(self.curve.harmonic_smas(
            self.period,
            self.degree,
            stride=1,
            is_period=True
        ))
        sma_tangents = []
        smas = []
        macs = []
        mac_period_coef = 2.5

        for hsma in hsmas:
            sma = hsma.offset(hsma.period * -0.5)
            sma_tangent = sma.extension(
                'tangent',
                regression_period=hsma.period * self.regression,
                start=False,
                end=True
            )
            if not sma_tangent.domain.is_positive_infinite:
                # Not enough data for this period
                warnings.warn('Not enough data to extend with all degrees of harmonic')
                continue
            sma_tangents.append(sma_tangent)
            if len(sma_tangents) == 1:
                base_line = sma_tangent
                smas.append(sma_tangent)
            else:
                mac_period = hsma.period * mac_period_coef
                ref_sma = smas[-1]
                mac = (sma - ref_sma).extension(
                    'sin',
                    period=mac_period,
                    regression_period=hsma.period * self.regression,
                    start=False,
                    end=True
                )
                macs.append(mac)

                sma_ext = type(self).first([sma, ref_sma + mac])
                smas.append(sma_ext)

        # Save extension
        self._fast_sma = sma_tangents[-2] + macs[-1]
        self.macs = macs
        self.smas = smas

        return Curve.add_many([self._extension_offset, base_line] + macs)
