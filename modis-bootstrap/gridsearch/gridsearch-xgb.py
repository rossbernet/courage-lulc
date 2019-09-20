#!/usr/bin/env python3

import sys
import os
import argparse
import math
import multiprocessing as mp

import numpy as np
import rasterio as rio
import h5py
from sklearn.model_selection import RandomizedSearchCV
from sklearn.utils.class_weight import compute_class_weight
from xgboost import XGBClassifier

'''
Randomly search through the parameter space to evaluate extreme gradient boosting
performance under various conditions
'''

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--h5-file', required=True)
    parser.add_argument('--n-jobs', type=int, default=-1)
    parser.add_argument('--n-iter', type=int, default=20)
    parser.add_argument('--no-water', action='store_true')
    args = parser.parse_args()

    def all_water(np_arr):
        return np_arr[:,0] == 17

    with h5py.File(args.h5_file, 'r') as h5:
        data = np.array(h5['modis_training'])
    np.random.shuffle(data)

    if args.no_water:
        data = data[~all_water(data)]

    half = data[:data.shape[0] // 2].copy()
    print(half.shape)
    del data
    xs = half[:,1:]
    ys = half[:,0].astype(np.uint8)
    unique_ys = np.unique(ys)
    weights = compute_class_weight('balanced', unique_ys, ys)

    weight_dict = {}
    for i in range(weights.size):
        weight_dict[unique_ys[i]] = weights[i]


    param_grid = {
        'n_jobs': [args.n_jobs],
        'silent': [False],
        'max_depth': [6, 10, 15, 20, 30],
        'learning_rate': [0.001, 0.01, 0.1, 0.2, 0,3],
        'subsample': [0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        'colsample_bytree': [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        'colsample_bylevel': [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        'min_child_weight': [0.5, 1.0, 3.0, 5.0, 7.0, 10.0],
        'gamma': [0, 0.25, 0.5, 1.0],
        'reg_lambda': [0.1, 1.0, 5.0, 10.0, 50.0, 100.0],
        'n_estimators': [100, 200, 400, 800, 1600]}

    print(param_grid)

    # Use the random grid to search for best hyperparameters
    # First create the base model to tune
    rf = XGBClassifier()
    # Random search of parameters, using 3 fold cross validation, 
    # search across 100 different combinations, and use all available cores
    rf_random = RandomizedSearchCV(scoring = 'f1_macro', estimator = rf, param_distributions = param_grid, n_iter = args.n_iter, cv = 2, verbose=10, random_state=42, n_jobs=1)
    # Fit the random search model
    rf_random.fit(xs, ys)

    print("FINISHING")
    print(rf_random.cv_results_)

    print("BEST PARAMS")
    print(rf_random.best_params_)