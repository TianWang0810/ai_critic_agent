#!/bin/bash

# Mac M4 安全启动脚本
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

python main.py "$@"