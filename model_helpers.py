#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# imports

# standard
from collections import defaultdict

# extra
import numpy as np
import pandas as pd
from sklearn import metrics
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier


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


dtc = DecisionTreeClassifier(max_depth=None)
dtc_grid = {
    'criterion': ['gini'], # gini
    'class_weight': [None], # None
    'min_samples_split': [2, 10, 40], # 2-60
    'min_samples_leaf': [40, 60], # 40
} # best: smoothing=.6: 75.4

dtcabc = DecisionTreeClassifier(max_depth=1, criterion='gini', min_samples_split=2, min_samples_leaf=2, class_weight=None)
abc = AdaBoostClassifier(base_estimator=dtcabc)
abc_grid = {
    'n_estimators': [60], # 60
    'learning_rate': [.5] # .5
} # best: smoothing=.6: 69.4

rfc = RandomForestClassifier(max_depth=None, random_state=1)
rfc_grid = {
    'min_samples_split': [2], # 2
    'min_samples_leaf': [1], # 1
    'n_estimators': [100, 200, 400], # 200
    'class_weight': [None], # None
    'criterion': ['gini'] #
} # best: smoothing=.6: 78.1

xgc = XGBClassifier(seed=1, num_class=20)
xgc_grid = {
    'objective': ['reg:logistic'], # reg:logistic, multi:softmax
    'booster': ['dart'], # dart
    'max_depth': [10], # 5, 10, 20
    'lambda': [1], # 1, 2, 5
    'alpha': [0], # 0, 1
    'gamma': [0], # 0, 1
    'eta': [.3], # range: [0,1]
    'base_score': [.5], # .1, .5, .9
    'min_child_weight': [0], # 0, 1, 2
    'max_delta_step': [5], # 0, 1-10 larger
    'subsample': [1], # range: (0,1]
    'sample_type': ['uniform', 'weighted'], # uniform, weighted
    'normalize_type': ['tree', 'forest'], # tree, forest
    'rate_drop': [0] # 0-1
} # best: smoothing=.6: 80.7

lrc = LogisticRegression(random_state=1)
lrc_grid = {
    'C': [10, 50, 150], # 150
    'fit_intercept': [True], # True
    'solver': ['lbfgs'], # lbfgs
    'penalty': ['l2'], # l2 (l2 only: newton-cg, sag, lbfgs)
    'multi_class': ['multinomial'], # multinomial (multinomial: newton-cg, sag, saga, lbfgs)
    'class_weight': ['balanced'], # None
    'dual': [False], # False
    'max_iter': [500] # 500
} # best: smoothing=.6: 80.3

sgd = SGDClassifier(random_state=1, fit_intercept=True, penalty='l2')
sgd_grid = {
    'loss': ['log'], # log
    'alpha': [1e-6], # 1e-6
    'max_iter': [1100] # 1100
} # best: smoothing=.6: 79.5


# In[ ]:


answers = pd.read_csv('data/submission.csv', header=0, index_col=0)

