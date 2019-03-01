#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# imports

# standard
from collections import Counter, defaultdict
from itertools import combinations, product
from math import log

#extra
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# In[ ]:


new_features = {
    'east': ['chinese', 'filipino', 'indian', 'japanese', 'korean', 'thai', 'vietnamese'],
    'west': ['russian', 'british', 'irish', 'french', 'italian', 'greek', 'spanish', 'cajun_creole',
             'moroccan', 'southern_us', 'mexican', 'jamaican', 'brazilian'],
    'britishlike': ['british', 'french', 'irish'],
    'chineselike': ['chinese', 'filipino', 'japanese', 'korean', 'thai', 'vietnamese'],
    'italianlike': ['greek', 'italian', 'mexican', 'spanish'],
    'indianlike': ['indian', 'japanese', 'mexican', 'moroccan', 'southern_us', 'thai'],
    'southern_uslike': ['brazilian', 'cajun_creole', 'filipino', 'jamaican', 'indian', 'mexican', 'southern_us']
}


# In[ ]:


def load_clean_data():
    recipes = pd.read_csv('data/cleaned_data.csv', header=0, index_col=0, encoding='utf-8',
                          # convert list literals to lists
                          converters={'ingredients': lambda x: eval(x)})
    print('{:,} recipes'.format(recipes.shape[0]))
    return recipes


# In[ ]:


flatten = lambda lists: [item for lst in lists for item in lst]


# In[ ]:


def remove_states(ings):
    return ings.map(lambda lst: [ing for ing in flatten(lst) if '_state' not in ing])


# In[ ]:


def remove_dupes(ings):
    return ings.map(set).map(list)


# In[ ]:


def add_combos(ings):
    combos = lambda lst: lst + list(map('+'.join, combinations(sorted(lst), 2)))
    return ings.map(combos)


# In[ ]:


def update_names(ings, renamed):
    return [renamed[feature] if feature in renamed else feature for feature in ings]


# In[ ]:


def make_counts(recipes):
    counts = {}
    for cuisine, group in recipes.groupby('cuisine'):
        all_ings = flatten(group.ingredients.to_list())
        counts[cuisine] = Counter(all_ings)
    counts = pd.DataFrame.from_dict(counts, orient='columns', dtype=np.float64)
    counts.fillna(0.0, inplace=True)
    counts.test = 0.0
    print('{} features'.format(counts.shape[0]))
    return counts


# In[ ]:


def scale_counts(counts, scales):
    counts = counts.apply(lambda col: col.map(lambda x: x / scales[col.name]), axis='index')
    return counts


# In[ ]:


def merge_arrows(arrows, update):
    arrows.update(update)
    for origin, target in arrows.items():
        if target in arrows:
            arrows[origin] = arrows[target]
    return arrows

def get_target_feature(feature, bad_features, catchall):
    parts = feature.split('-')
    if parts[-1] == catchall:
        target = parts[0]
    else:
        parts[-1] = catchall
        target = '-'.join(parts)
    if target in bad_features:
        target = get_target_feature(target, bad_features, catchall)
    return target

def merge_features(counts, features_to_merge, catchall):
    renamed_features = {}
    counts = counts.copy()
    if catchall in features_to_merge:
        features_to_merge = features_to_merge.copy()
        features_to_merge.remove(catchall)
    features_to_keep = set(counts.index) - set(features_to_merge)
    for feature in features_to_merge:
        target = get_target_feature(feature, features_to_merge, catchall)
        renamed_features[feature] = target
        if target in features_to_keep:
            counts.loc[target] += counts.loc[feature]
            continue
        counts.loc[target] = counts.loc[feature]
    counts = counts.drop(index=features_to_merge)
    print('{} merged, {} features left'.format(len(renamed_features), len(counts)))
    return (counts, renamed_features)


# In[ ]:


def merge_rare_features(counts, single_cutoff, combo_cutoff, catchall):
    totals = counts.max(axis='columns')
    rare_combo_features = totals[totals <= combo_cutoff].index.to_list()
    combo_features = [feature for feature in rare_combo_features if '+' in feature]
    merged = counts.drop(index=combo_features)
    print('{} combo features dropped'.format(len(combo_features)))
    renamed = {old: 'rarecombotype' for old in combo_features}

    totals = merged.max(axis='columns')
    rare_features = totals[totals <= single_cutoff].index.to_list()
    long_features = [feature for feature in rare_features if len(feature.split('-')) > 1]
    merged, renamed_update = merge_features(merged, long_features, catchall)
    renamed = merge_arrows(renamed, renamed_update)
    
    totals = merged.max(axis='columns')
    rare_features = totals[totals <= single_cutoff].index.to_list()
    raretype_features = [feature for feature in rare_features if len(feature.split('-')) > 1]
    merged, renamed_update = merge_features(merged, raretype_features, catchall)
    renamed = merge_arrows(renamed, renamed_update)
    
    totals = merged.max(axis='columns')
    rare_features = totals[totals <= single_cutoff].index.to_list()
    merged, renamed_update = merge_features(merged, rare_features, catchall)
    renamed = merge_arrows(renamed, renamed_update)
    
    return (merged, renamed)


# In[ ]:


def get_proportions(counts):
    total = counts.sum(axis='columns')
    inverse_total = total.map(lambda x: 1 / x if x else 0)
    proportions = counts.T * inverse_total
    return proportions.T


# In[ ]:


def make_indicators(recipes, features):
    indicators = np.zeros([recipes.shape[0], len(features)], dtype=np.uint8)
    feature_index = {feature: i for i, feature in enumerate(features)}
    for row_i, ings in enumerate(recipes.ingredients):
        for feature in ings:
            indicators[row_i, feature_index[feature]] = 1
    indicators = pd.DataFrame(indicators, index=recipes.index, columns=features)
    return indicators


# In[ ]:


def make_points(props, adj=True):
    smooth = lambda data, i: data.applymap(lambda x: log(1.01 + (x / (i + x))) if x else 0)
    points = smooth(props, .2)
    weights = {
        # drop
        'british': .905,
        'cajun_creole': .85,
        #'chinese': .99,
        'greek': .99,
        'indian': .94,
        'irish': .96,
        'jamaican': .915,
        'korean': .98,
        'moroccan': .87,
        'russian': .9,
        'spanish': .99,
        'thai': .96,
        'vietnamese': .94,
        # boost
        'brazilian': 1.02,
        'filipino': 1.02,
        'french': 1.04,
        'italian': 1.16,
        'japanese': 1.155,
        'mexican': 1.05,
        'southern_us': 1.045
    }
    if adj:
        for cuisine, weight in weights.items():
            points[cuisine] = weight * points[cuisine]
    return points


# In[ ]:


def make_scores(recipe, points):
    return points.loc[recipe.ingredients].mean()


# In[ ]:


def add_score_features(scores):
    to_add = []
    for name, cats in new_features.items():
        series = scores[cats].mean(axis='columns')
        series.name = name
        to_add.append(series)
    scores = pd.concat([scores] + to_add, axis='columns')
    return scores


# In[ ]:


def plot_cnf(cm, classes):
    plt.figure(figsize=(9,9))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=80)
    plt.yticks(tick_marks, classes)
    thresh = cm.max() / 2.
    for i, j in product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], 'd'),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.tight_layout()
    plt.grid(False)


# In[ ]:


def save_output(output, prefix='temp_'):
    output = output.drop(columns=['ingredients'])
    
    train = output.query('cuisine != "test"')
    test = output.query('cuisine == "test"')
    
    train.cuisine.to_csv('data/cuisine.csv', header=False, encoding='utf-8')
    
    train = train.drop(columns=['cuisine'])
    test = test.drop(columns=['cuisine'])
    
    train.to_csv('data/' + prefix + 'train.csv', header=True, encoding='utf-8') 
    test.to_csv('data/' + prefix + 'test.csv', header=True, encoding='utf-8')

