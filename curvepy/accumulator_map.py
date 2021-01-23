from .accumulator import Accumulator
from .curve import MIN_STEP
from intervalpy import Interval


class AccumulatorMap(Accumulator):

    def __init__(
            self,
            func,
            tfm,
            degree,
            is_period=True,
            interpolation=None,
            uniform=True,
            min_step=MIN_STEP):
        super().__init__(
            func,
            self._accumulator_map_scan,
            interpolation=interpolation,
            uniform=uniform,
            min_step=min_step
        )

        tfm_ags = type(self).count_positional_args(tfm)
        if tfm_ags == 0 or tfm_ags > 2:
            raise Exception('Unable to adapt function')
        self._accumulator_map_tfm_with_x = tfm_ags > 1
        self.accumulator_map_tfm = tfm

        self.degree = None
        self.period = None
        if is_period:
            self.period = degree
            if self.period is None or self.period <= 0:
                raise Exception('Min period must be a positive number')
        else:
            self.degree = int(degree)
            if self.degree <= 0:
                raise Exception('Min degree must be a positive integer')

    def _accumulator_map_scan(self, x, y, _):
        points = [[x, y]]
        if self.degree is not None:
            if self.degree != 1:
                points += self.curve.sample_points_from_x(
                    x,
                    self.degree - 1,
                    backward=True,
                    open=True,
                    min_step=self.min_step
                )
        elif self.period is not None:
            points += reversed(self.curve.sample_points(
                domain=Interval.closed_open(x - self.period, x),
                min_step=self.min_step
            ))
        else:
            raise Exception('Bad config')

        ys = [p[1] for p in points]
        return self._accumulator_map(x, ys)

    def _accumulator_map(self, x, ys):
        if self._accumulator_map_tfm_with_x:
            return self.accumulator_map_tfm(x, ys)
        else:
            return self.accumulator_map_tfm(ys)
