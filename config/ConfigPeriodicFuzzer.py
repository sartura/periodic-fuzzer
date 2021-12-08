import json
import copy


class ConfigPeriodicFuzzerError(Exception):
    def __init__(self, message):
        super().__init__(message)


class ConfigPeriodicFuzzer():
    def __init__(self):
        self._configuration = {}

    def __repr__(self):
        return f'ConfigPeriodicFuzzer({self._configuration})'

    def __str__(self):
        return str(self._configuration)

    def parseJSON(self, configuration_file_path):
        expected_configuration_dict = {
            'gitURL': {'defaultValue': None, 'typeTransform': str},
            'inputsDirPath': {'defaultValue': '/tmp/ci-fuzz/inputs', 'typeTransform': str},
            'clonePath': {'defaultValue': '/tmp/ci-fuzz/repo', 'typeTransform': str},
            'workDirPath': {'defaultValue': '/tmp/ci-fuzz', 'typeTransform': str},
            'gitBranch': {'defaultValue': 'master', 'typeTransform': str},
            'buildScriptPath': {'defaultValue': '/tmp/ci-fuzz/build.sh', 'typeTransform': str},
            'fuzzBackend': {'defaultValue': 'AFL', 'typeTransform': str},
            'fuzzFlags': {'defaultValue': '', 'typeTransform': str},
            'fuzzTarget': {'defaultValue': None, 'typeTransform': str},
            'updateInterval': {'defaultValue': 300, 'typeTransform': int},
            'numberOfCPUs': {'defaultValue': 1, 'typeTransform': int},
            'debug': {'defaultValue': False, 'typeTransform': bool},
        }

        try:
            with open(configuration_file_path) as configuration_file:
                configuration = json.load(configuration_file)

            for config_key in expected_configuration_dict.keys():
                if config_key not in configuration:
                    raise ConfigPeriodicFuzzerError(f"missing key {config_key}")
                if configuration[config_key] is None and expected_configuration_dict[config_key]['defaultValue'] is None:
                    raise ConfigPeriodicFuzzerError(f"value for key {config_key} needs to be specified")

                if configuration[config_key] is None:
                    self._configuration[config_key] = expected_configuration_dict[config_key]['defaultValue']
                else:
                    self._configuration[config_key] = expected_configuration_dict[config_key]['typeTransform'](configuration[config_key])

        except json.JSONDecodeError as json_error:
            raise ConfigPeriodicFuzzerError('error parsing JSON file')
        except ValueError as val_error:
            raise ConfigPeriodicFuzzerError(f"invalid JSON value for key {config_key}")

    def getConfiguration(self):
        return self._configuration
