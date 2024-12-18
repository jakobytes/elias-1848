#!/bin/bash
#SBATCH --job-name=poem_sim
#SBATCH --time=12:00:00
#SBATCH --mem-per-cpu=32G
#SBATCH --cpus-per-task=1
#SBATCH --partition=gpu
#SBATCH --ntasks=1
#SBATCH --gres=gpu:v100:1

srun -D .. env DATA_DIR=$PROJSCRATCH/filter-data \
	make $PROJSCRATCH/filter-data/p_sim.csv \
	     $PROJSCRATCH/filter-data/p_clust.tsv \
	     -o $PROJSCRATCH/filter-data/verses_cl.csv

