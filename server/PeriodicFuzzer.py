import copy
import logging
import subprocess as sp
import threading as th
import git
import sys
import os
import stat
import signal
import shutil


class PeriodiFuzzerError(Exception):
    def __init__(self, message):
        super().__init__(message)


class PeriodicFuzzer():
    def __init__(self, **kwargs):
        if self.__supportedFuzzBackend(kwargs['fuzzBackend']) == False:
            raise PeriodiFuzzerError(f"unsuported fuzzing beckend: {kwargs['fuzzBackend']}")
        self._flags = copy.deepcopy(kwargs)
        self._fuzzing_in_process = False
        self._fuzzer_list = []

    def __repr__(self):
        return f'PeriodicFuzzer({self._flags})'

    def __str__(self):
        return str(self._flags)

    @staticmethod
    def __supportedFuzzBackend(fuzzBackend):
        if fuzzBackend == 'AFL':
            return True
        else:
            return False

    def __update(self):
        if os.path.exists(self._flags['clonePath']) == False:
            logging.log(
                logging.INFO,
                f"Starting git clone from {self._flags['gitURL']} using branch {self._flags['clonePath']} to {self._flags['gitBranch']}")

            git.Repo.clone_from(self._flags['gitURL'], self._flags['clonePath'], branch=self._flags['gitBranch'])

            logging.log(logging.INFO, f"Finished git clone")

            return True

        repositry = git.Repo(self._flags['clonePath'])
        head_before_pull = repositry.head.commit

        repositry.remotes.origin.pull()
        if repositry.head.commit == head_before_pull:
            return False
        else:
            logging.log(logging.INFO, f"Pulled new chagnes from {self._flags['gitURL']} using branch {self._flags['clonePath']}")

            return True

    def __build(self):
        script_src_path = self._flags['buildScriptPath']
        scpirt_dest_path = self._flags['clonePath'] + '/' + os.path.basename(self._flags['buildScriptPath'])

        with open(script_src_path, 'r') as reader:
            with open(scpirt_dest_path, 'w') as writer:
                writer.write(reader.read())

        os.chmod(scpirt_dest_path, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC | stat.S_IRGRP | stat.S_IROTH)

        build_process = sp.Popen(scpirt_dest_path, cwd=self._flags['clonePath'],
                                 stdout=sys.stdout if self._flags['debug'] else sp.DEVNULL,
                                 stderr=sys.stderr if self._flags['debug'] else sp.DEVNULL)
        build_process.wait()
        if build_process.returncode != 0:
            raise PeriodiFuzzerError(f"Script {scpirt_dest_path} error: {build_process.returncode}")

    def __fuzz(self):
        if self._fuzzing_in_process:
            return

        logging.log(logging.INFO, f"Starting up fuzzing {self._flags['clonePath']}")

        fuzz_used = self._flags['fuzzBackend']

        if fuzz_used == 'AFL':
            self.__fuzz_afl()
        elif fuzz_used == 'yang-imp-fuzzer':
            self.__fuzz_yang_imp()

        self._fuzzing_in_process = True

    def __fuzz_afl(self):
        fuzz_path = shutil.which('afl-fuzz')
        if fuzz_path is None:
            raise PeriodiFuzzerError(f"Couldn't find afl-fuzz")

        for i in range(self._flags['numberOfCPUs']):
            inputs = self._flags['inputsDirPath']
            fuzz_type = '-S' if i == 0 else '-M'
            output_path = self._flags['workDirPath'] + '/output'
            command = self._flags['clonePath'] + '/' + self._flags['fuzzTarget']
            fuzz_name = 'fuzzer' + str(i)
            flags = self._flags['fuzzFlags']

            logging.log(logging.INFO, f"Starting fuzzer with ID {i}")

            fuzz_process = sp.Popen([fuzz_path, '-i', inputs, '-o', output_path, fuzz_type, fuzz_name, flags, '--', command],
                                    cwd=self._flags['workDirPath'],
                                    stdout=sys.stdout if self._flags['debug'] else sp.DEVNULL,
                                    stderr=sys.stderr if self._flags['debug'] else sp.DEVNULL)
            self._fuzzer_list.insert(i, fuzz_process)

    def __fuzz_yang_imp(self):
        fuzz_path = shutil.which('yang-imp-fuzzer')
        if fuzz_path is None:
            raise PeriodiFuzzerError(f"Couldn't find yang-imp-fuzzer")

        for i in range(self._flags['numberOfCPUs']):
            output_path = self._flags['workDirPath'] + '/output'
            flags = self._flags['fuzzFlags']

            logging.log(logging.INFO, f"Starting fuzzer with ID {i}")
            fuzz_process = sp.Popen([fuzz_path, flags],
                                    cwd=self._flags['workDirPath'],
                                    stdout=sys.stdout if self._flags['debug'] else sp.DEVNULL,
                                    stderr=sys.stderr if self._flags['debug'] else sp.DEVNULL)
            self._fuzzer_list.insert(i, fuzz_process)


    def __stopFuzzing(self):
        if self._fuzzing_in_process == False:
            return

        logging.log(logging.INFO, f"Stopping fuzzing")

        for fuzz_proccess in self._fuzzer_list:
            fuzz_proccess.send_signal(signal.SIGINT)

        self._fuzzer_list.clear()
        self._fuzzing_in_process = False

        self.__syncInputs()

    def __syncInputs(self):
        if os.path.exists(self._flags['inputsDirPath']) == False:
            raise PeriodiFuzzerError(f"directory {self._flags['inputsDirPath']} doesn't exist")

        for i in range(self._flags['numberOfCPUs']):
            logging.log(logging.INFO, f"Syncing inpout from old fuzzer with ID {i}")
            old_inputs_dir = self._flags['workDirPath'] + '/output/fuzzer' + str(i) + '/queue'
            if os.path.exists(old_inputs_dir) == False:
                raise PeriodiFuzzerError(f"directory {old_inputs_dir} doesn't exist")

            for dir_path, dir_names, file_names in os.walk(old_inputs_dir):
                for file_name in file_names:
                    src_file_path = dir_path + '/' + file_name
                    dest_file_path = self._flags['inputsDirPath'] + '/' + file_name

                    with open(src_file_path, 'rb') as reader:
                        with open(dest_file_path, 'wb') as writer:
                            writer.write(reader.read())

                    os.chmod(dest_file_path, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IROTH)

    def start(self):
        logging.log(logging.INFO, f"Staring periodic fuzzing server")

        repeating_timer = th.Event()
        while True:
            try:
                is_updated = self.__update()
                if is_updated and self._fuzzing_in_process:
                    self.__stopFuzzing()
                    self.__build()
                    self.__fuzz()
                if self._fuzzing_in_process == False:
                    self.__build()
                    self.__fuzz()

                repeating_timer.wait(self._flags['updateInterval'])

            except git.InvalidGitRepositoryError as git_error:
                raise PeriodiFuzzerError(f"PeriodicFuzzer update error: {git_error}")

            except IOError as io_error:
                raise PeriodiFuzzerError(f"PeriodicFuzzer read write error: {io_error}")

    def stop(self):
        self.__stopFuzzing()
