# CI-fuzz
CI-fuzz is a python server that implements periodic fuzzing of git based projects. That is, it checks whether the project git had any updates in the set time period, and if so it rebuilds the fuzzing targets and restarts fuzzing with the new fuzz target versions, while keeping the previous corpus.


# TODO:
* use JSON file to specify command line arguments or use the argparse module
* use the logging module
* use the git module
