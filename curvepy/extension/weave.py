from .extension import Extension
from intervalpy import Interval
from ..const import GOLD

class WeaveExtension(Extension):

    """
    Extends an end of a function with a line using its edge tangents.
    """

    name = "weave"

    def __init__(self, func, period=None, degree=3, tolerance=1e-3, **kwargs):
        super().__init__(func, **kwargs)
        if self.start:
            raise Exception('Weave extension currently only supports extending the end')
        self.period = float(period)
        self.degree = int(degree)
        self.tolerance = float(tolerance)
        assert self.period > 0
        assert self.degree > 1
        assert self.tolerance > 0
        if self.end:
            self.setup()

    def y_extension(self, x):
        if self.end and x >= self.curve.domain.end:
            self.accumulate(x)
            return self.extension.y(x)
        return None

    def update_extension(self):
        if self.end:
            self.extension.reset()
            self.extension_interval = self.get_extension_interval()

    def get_extension_interval(self):
        if self.end and not self.curve.domain.is_empty:
            smas = list(map(lambda sma: sma.y(self.curve.domain.end), self.smas))
            if len(list(filter(None, smas))) == len(smas):
                return Interval.gte(self.curve.domain.end)
        # Not enough data
        return Interval.empty()

    def accumulate(self, x):
        x0 = self.layers.domain.end
        while True:
            if x0 is None or x0 >= x:
                break
            x1 = self.accumulate_next(x0)
            assert x1 > x0
            x0 = x1

    def setup(self):
        self.periods = []
        self.sma_tangents = []
        self.smas = []
        self.macs = []
        mac_period_coef = 2.5
        for i in range(self.price_degree):
            period = self.quote_period * GOLD ** float(i * 2)
            period = round(period / self.quote_period) * self.quote_period
            self.periods.insert(0, period)

        for i in range(self.price_degree):
            period = self.periods[i]
            sma = self.market.quote_func.ohlc.sma(period, is_period=True)
            sma = sma.offset(period * -0.5)
            sma_tangent = sma.extension('tangent', start=False, end=True)
            self.sma_tangents.append(sma_tangent)
            if i == 0:
                sma = sma_tangent
            if i != 0:
                mac = (sma - self.sma_tangents[i - 1]).extension('sin', period=period * mac_period_coef, start=False, end=True)
                sma = self.sma_tangents[i - 1] + mac
                self.smas.append(sma)
                self.macs.append(mac)
            self.smas.append(sma)

    def accumulate_next(self, x):
        from scipy.optimize import minimize
        
        x0 = self.layers.x_previous(x, min_step=self.min_step)
        if x0 is None:
            return None
        y = self.layers.y(x)
        step = x - x0
        x1 = x + step

        def get_values():
            # return list(map(lambda mac: (mac.y(x1) - mac.y(x)) / step, self.macs))
            # return list(map(lambda mac: mac.y(x1), self.macs)) + list(map(lambda sma: sma.y(x1), self.smas))
            # return list(map(lambda sma: sma.y(x1), self.smas))
            return list(map(lambda mac: mac.y(x1), self.macs))
            # return list(map(lambda mac: (mac.y(x1) - mac.y(x)) / step, self.macs))

        start_values = get_values()
        start_values = list(map(lambda y: y * 0.9, start_values))
        values_len = len(start_values)

        smas = list(map(lambda sma: sma.y(x1), self.smas))
        sma_len = len(smas)

        def error_func(params):
            y_coef = params[0]
            y1 = y * (1 + y_coef)
            self.extension.replace((x1, y1), or_append=True)

            error_sum = 0

            values = get_values()
            for i in range(values_len):
                error_sum += (start_values[i] - values[i]) ** 2
                # error_sum += (values[i]) ** 2

            # for i in range(sma_len):
            #     error_sum += (y1 - smas[i]) ** 2
            #     # error_sum += (values[i]) ** 2

            return error_sum

        # docs: https://docs.scipy.org/doc/scipy-0.18.1/reference/generated/scipy.optimize.minimize.html#scipy.optimize.minimize
        params = [0]
        method = 'Nelder-Mead'
        result = minimize(error_func, params, method=method, tol=self.tolerance)
        
        y_coef = result.x[0]
        y1 = y * (1 + y_coef)
        self.extension.replace((x1, y1), or_append=True)

        return x1

    # def setup(self):
    #     self.extension = Points([])
    #     self.layers = Curve.first([self.curve, self.extension])
    #     self.periods = []
    #     self.smas = []
    #     self.macs = []
    #     mac_period_coef = 2.5
    #     for i in range(self.degree):
    #         period = self.period * GOLD ** float(i * 2)
    #         period = round(period / self.period) * self.period
    #         self.periods.insert(0, period)

    #     for i in range(self.degree):
    #         period = self.periods[i]
    #         sma = self.layers.sma(period, is_period=True)
    #         sma = sma.offset(period * -0.5)
    #         if i == 0:
    #             sma = sma.extension('tangent', start=False, end=True)
    #         else:
    #             mac = (sma - self.smas[i - 1]).extension('sin', period=period * mac_period_coef, start=False, end=True)
    #             sma = self.smas[i - 1] + mac
    #             self.macs.append(mac)
    #         self.smas.append(sma)

    # def accumulate_next(self, x):
    #     x0 = self.layers.x_previous(x, min_step=self.min_step)
    #     if x0 is None:
    #         return None
    #     y = self.layers.y(x)
    #     step = x - x0
    #     x1 = x + step

    #     def get_values():
    #         # return list(map(lambda mac: (mac.y(x1) - mac.y(x)) / step, self.macs))
    #         # return list(map(lambda mac: mac.y(x1), self.macs)) + list(map(lambda sma: sma.y(x1), self.smas))
    #         # return list(map(lambda sma: sma.y(x1), self.smas))
    #         return list(map(lambda mac: mac.y(x1), self.macs))
    #         # return list(map(lambda mac: (mac.y(x1) - mac.y(x)) / step, self.macs))

    #     start_values = get_values()
    #     start_values = list(map(lambda y: y * 0.9, start_values))
    #     values_len = len(start_values)

    #     smas = list(map(lambda sma: sma.y(x1), self.smas))
    #     sma_len = len(smas)

    #     def error_func(params):
    #         y_coef = params[0]
    #         y1 = y * (1 + y_coef)
    #         self.extension.replace((x1, y1), or_append=True)

    #         error_sum = 0

    #         values = get_values()
    #         for i in range(values_len):
    #             error_sum += (start_values[i] - values[i]) ** 2
    #             # error_sum += (values[i]) ** 2

    #         # for i in range(sma_len):
    #         #     error_sum += (y1 - smas[i]) ** 2
    #         #     # error_sum += (values[i]) ** 2

    #         return error_sum

    #     # docs: https://docs.scipy.org/doc/scipy-0.18.1/reference/generated/scipy.optimize.minimize.html#scipy.optimize.minimize
    #     params = [0]
    #     method = 'Nelder-Mead'
    #     result = minimize(error_func, params, method=method, tol=self.tolerance)
        
    #     y_coef = result.x[0]
    #     y1 = y * (1 + y_coef)
    #     self.extension.replace((x1, y1), or_append=True)

    #     return x1
