import copy
import time
import logging
import subprocess as sp
import threading as th

import datetime


class PeriodiFuzzerError(Exception):
    def __init__(self, message):
        super().__init__(message)


class PeriodicFuzzer():
    def __init__(self, **kwargs):
        if self.__supportedFuzzBeckend(kwargs['fuzzBeckend']) == False:
            raise PeriodiFuzzerError(f"unsuported fuzzing beckend: {kwargs['fuzzBeckend']}")
        self._flags = copy.deepcopy(kwargs)
        self._fuzzing_in_process = False
        self._fuzzer_list = []

    def __repr__(self):
        return f'PeriodicFuzzer({self._flags})'

    def __str__(self):
        return str(self._flags)

    @staticmethod
    def __supportedFuzzBeckend(fuzzBeckend):
        if fuzzBeckend == 'AFL':
            return True
        else:
            return False

    def __clone(self):
        pass

    def __checkUpdate(self):
        pass

    def __update(self):
        pass

    def __build(self):
        pass

    def __syncInputs(self):
        pass

    def __fuzz(self):
        self._fuzzing_in_process

    def __stopFuzzing(self):
        logging.log(logging.INFO, f"stopping fuzzing")
        self._fuzzing_in_process = False

    def start(self):
        logging.log(logging.INFO, f"staring fuzzing")

        repeating_timer = th.Event()
        while True:
            logging.log(logging.INFO, datetime.datetime.now())
            is_updated = self.__checkUpdate()
            if is_updated and self._fuzzing_in_process:
                self.__stopFuzzing()
                self.__update()
            self.__build()
            self.__fuzz()
            repeating_timer.wait(self._flags['updateInterval'])

    def stop(self):
        self.__stopFuzzing()