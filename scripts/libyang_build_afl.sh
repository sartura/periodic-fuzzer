#!/bin/bash
rm -rf build
mkdir build
cd build
cmake -DCMAKE_C_COMPILER=afl-clang-fast -DCMAKE_BUILD_TYPE=Debug -DENABLE_FUZZ_TARGETS=ON -DFUZZER=AFL ..
make -j
