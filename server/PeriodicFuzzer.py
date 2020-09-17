import copy


class PeriodiFuzzerError(Exception):
    pass


class PeriodicFuzzer():
    def __init__(self, **kwargs):
        self.flags = copy.deepcopy(kwargs)

    def __repr__(self):
        return f'PeriodicFuzzer({self.flags})'

    def __str__(self):
        return str(self.flags)

    def __clone(self):
        pass

    def __update(self):
        pass

    def __build(self):
        pass

    def __syncInputs(self):
        pass

    def __fuzz(self):
        pass

    def __stopFuzzing(self):
        pass

    def supportedFuzzBeckend(self, fuzzBeckend):
        pass

    def start(self):
        pass
