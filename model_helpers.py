#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# imports

# extra
import numpy as np
import pandas as pd
import parfit.parfit as pf
from sklearn.model_selection import ParameterGrid


# In[ ]:


def load_data():
    cuisine = pd.read_csv('data/cuisine.csv', names=['cuisine'], header=None, index_col=0)
    cuisine = cuisine.astype(np.unicode_)
    train_ings = pd.read_csv('data/temp_train.csv', header=0, index_col=0)
    train_ings = train_ings.astype(np.float64)
    train = pd.concat((cuisine, train_ings), axis=1)
    test = pd.read_csv('data/temp_test.csv', header=0, index_col=0)
    test = test.astype(np.float64)
    return (train, test)


# In[ ]:


def train_validate_split(data, val_size=.22, seed=1):
    samples = []
    for cuisine, group in data.groupby('cuisine'):
        samples.append(group.sample(frac=val_size, replace=False, random_state=seed, axis='index'))
    val = pd.concat(samples, axis='index')
    train = data.drop(index=val.index)
    X_train = train.drop('cuisine', axis=1)
    X_val = val.drop('cuisine', axis=1)
    y_train = train['cuisine']
    y_val = val['cuisine']
    return (X_train, y_train, X_val, y_val)


# In[ ]:


def test_hyperparams(clf, grid, metric, X_train, y_train, X_val, y_val):
    param_grid = ParameterGrid(grid)
    best_model, best_score, all_models, all_scores = pf.bestFit(
        clf, param_grid, X_train, y_train, X_val, y_val, metric=metric, greater_is_better=True)
    print(best_model, best_score)


# In[ ]:


pct = lambda v: int(v * 100)

def test(X, y, title, clf, sampler=None, splits=3):
    kfold = KFold(n_splits=splits, shuffle=True, random_state=1)
    for train_i, test_i in kfold.split(X):
        X_train, X_test = X.iloc[train_i], X.iloc[test_i]
        y_train, y_test = y.iloc[train_i], y.iloc[test_i]
        if sampler:
            X_train, y_train = sampler.fit_resample(X_train, y_train)
        model = clf.fit(X_train, y_train)
        preds = model.predict(X_test)
        print(metrics.accuracy_score(y_test, preds))
        print(metrics.classification_report(y_test, preds))

def get_errors(X, y, model, sort_col=None):
    errors = []
    preds = []
    for i in range(X.shape[0]):
        obs = X.iloc[i:i+1]
        real = y.iloc[i]
        y_pred = model.predict(obs)
        if y_pred != [real]:
            errors.append(i)
            preds.append(y_pred)
    errs = pd.concat([X.iloc[errors], y.iloc[errors]], axis=1)
    preds_df = pd.DataFrame(preds, index=errs.index, columns=['pred'])
    errs = pd.concat([errs, preds_df], axis=1)
    print('Errors:', errs.shape[0])
    if sort_col:
        errs.sort_values(sort_col, inplace=True)
    return errs


# In[ ]:


answers = pd.read_csv('data/submission.csv', header=0, index_col=0)

