import sys

import logging

import config.ConfigPeriodicFuzzer as cpf
import server.PeriodicFuzzer as pf


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    if len(sys.argv) != 2:
        logging.log(logging.ERROR, f"usage: {sys.argv[0]} JSON_config_file")
        exit(1)

    try:
        configPeriodicFuzzer = cpf.ConfigPeriodicFuzzer()
        configPeriodicFuzzer.parseJSON(sys.argv[1])
        configuration = configPeriodicFuzzer.getConfiguration()

        periodicFuzzer = pf.PeriodicFuzzer(**configuration)
        periodicFuzzer.start()

    except cpf.ConfigPeriodicFuzzerError as config_error:
        logging.log(logging.ERROR, f"main error: {config_error}")
    except pf.PeriodiFuzzerError as periodic_error:
        logging.log(logging.ERROR, f"main error: {periodic_error}")
    except KeyboardInterrupt:
        logging.log(logging.INFO, f"main: keyboard interrupt")

    periodicFuzzer.stop()
