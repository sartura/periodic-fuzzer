import copy
import logging
import subprocess as sp
import threading as th
import git
import os
import stat
import signal
import shutil


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

        st = os.stat(scpirt_dest_path)
        os.chmod(scpirt_dest_path, st.st_mode | stat.S_IEXEC)

        build_process = sp.Popen(scpirt_dest_path, cwd=self._flags['clonePath'])
        build_process.wait()
        if build_process.returncode != 0:
            raise PeriodiFuzzerError(f"Script {scpirt_dest_path} error: {build_process.returncode}")

    def __fuzz(self):
        if self._fuzzing_in_process:
            return

        self._fuzzing_in_process = True
        logging.log(logging.INFO, f"Starting up fuzzing {self._flags['clonePath']}")

        fuzz_used = 'afl-fuzz'
        fuzz_path = shutil.which(fuzz_used)
        if fuzz_path is None:
            raise PeriodiFuzzerError(f"Couldn't find {fuzz_used}")

        for i in range(self._flags['numberOfCPUs']):
            inputs = self._flags['inputsDirPath']
            fuzz_type = '-S' if i == 0 else '-M'
            output_path = self._flags['workDirPath'] + '/output'
            command = self._flags['clonePath'] + '/' + self._flags['fuzzTarget']
            fuzz_name = 'fuzzer' + str(i)

            logging.log(logging.INFO, f"Starting fuzzer with ID {i}")

            fuzz_process = sp.Popen([fuzz_path, '-i', inputs, '-o', output_path, fuzz_type, fuzzer_name, '--', command], cwd=self._flags['workDirPath'])
            self._fuzzer_list[i] = fuzz_process

    def __stopFuzzing(self):
        if self._fuzzing_in_process == False:
            return

        logging.log(logging.INFO, f"Stopping fuzzing")
        self._fuzzing_in_process = False

        for fuzz_proccess in self._fuzzer_list:
            fuzz_proccess.send_signal(signal.SIGINT)
        self._fuzzer_list = []

        self.__syncInputs()

    def __syncInputs(self):
        if os.path.exists(self._flags['inputsDirPath']) == False:
            raise PeriodiFuzzerError(f"directory {self._flags['inputsDirPath']} doesn't exist")

        for i in range(self._flags['numberOfCPUs']):
            logging.log(logging.INFO, f"Syncing inpout from old fuzzer with ID {i}")
            old_inputs_dir = self._flags['workDirPath'] + 'output/fuzzer' + str(i) + '/queue'
            if os.path.exists(old_inputs_dir) == False:
                raise PeriodiFuzzerError(f"directory {old_inputs_dir} doesn't exist")

            for dir_path, dir_names, file_names in os.walk(old_inputs_dir):
                for file_name in file_names:
                    src_file_path = dir_path + '/' + file_name
                    dest_file_path = self._flags['inputDirPath'] + '/' + file_name

                    with open(src_file_path, 'r') as reader:
                        with open(dest_file_path, 'w') as writer:
                            writer.write(reader.read())
                            # TODO: chane file mode after writing

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
                repeating_timer.wait(self._flags['updateInterval'])

            except git.InvalidGitRepositoryError as git_error:
                raise PeriodiFuzzerError(f"PeriodicFuzzer update error: {git_error}")

            except IOError as io_error:
                raise PeriodiFuzzerError(f"PeriodicFuzzer read write error: {io_error}")

    def stop(self):
        self.__stopFuzzing()
