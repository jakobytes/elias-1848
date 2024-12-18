#!/bin/bash
#SBATCH --job-name=verse_sim
#SBATCH --time=12:00:00
#SBATCH --mem-per-cpu=32G
#SBATCH --cpus-per-task=1
#SBATCH --partition=gpu
#SBATCH --ntasks=1
#SBATCH --gres=gpu:v100:1

srun -D .. env DATA_DIR=$PROJSCRATCH/filter-data \
	make $PROJSCRATCH/filter-data/v_sim.tsv -o ../filter-data/verses_cl.csv
srun -D .. env DATA_DIR=$PROJSCRATCH/filter-data \
	make data/work/v_sim.sqrt.tsv -o $PROJSCRATCH/filter-data/verses_cl.csv
srun -D .. env DATA_DIR=$PROJSCRATCH/filter-data \
	make data/work/v_sim.binary.tsv -o $PROJSCRATCH/filter-data/verses_cl.csv
srun -D .. env DATA_DIR=$PROJSCRATCH/filter-data \
	make $PROJSCRATCH/filter-data/v_clust.tsv \
	-o $PROJSCRATCH/filter-data/v_sim.tsv \
	-o data/work/v_sim.sqrt.tsv \
	-o data/work/v_sim.binary.tsv

