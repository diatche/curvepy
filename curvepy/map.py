from .curve import Curve, MIN_STEP
from intervalpy import Interval

class Map(Curve):

    def get_domain(self):
        return self.curve.domain

    def __init__(self, func, tfm, skip_none=False, min_step=MIN_STEP, name=None):
        if bool(func.min_step) and func.min_step > min_step:
            min_step = func.min_step
        super().__init__(min_step=min_step)
        self.curve = Curve.parse(func)
        self.skip_none = skip_none
        self.name = name

        tfm_ags = type(self).count_positional_args(tfm)
        if tfm_ags == 0 or tfm_ags > 2:
            raise Exception('Unable to adapt function')
        self._map_tfm_with_x = tfm_ags > 1
        self.map_tfm = tfm

        self._observer_token = self.curve.add_observer(begin=self.begin_update, end=self.end_update, prioritize=True)
    
    def __repr__(self):
        try:
            name = self.name or f'map({self.map_tfm.__name__})'
            return f'{self.curve}.{name}'
        except Exception as e:
            return super().__repr__() + f'({e})'

    def __del__(self):
        self.curve.remove_observer(self._observer_token)

    def y(self, x):
        y = self.curve.y(x)
        if y is None and self.skip_none:
            return None
        return self._map(x, y)

    def x_previous(self, x, min_step=MIN_STEP, limit=None):
        min_step = self.resolve_min_step(min_step)
        return self.curve.x_previous(x, min_step=min_step, limit=limit)

    def x_next(self, x, min_step=MIN_STEP, limit=None):
        min_step = self.resolve_min_step(min_step)
        return self.curve.x_next(x, min_step=min_step, limit=limit)

    def _map(self, x, y):
        if self._map_tfm_with_x:
            return self.map_tfm(x, y)
        else:
            return self.map_tfm(y)