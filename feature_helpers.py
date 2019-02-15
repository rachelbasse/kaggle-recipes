#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# imports
from collections import Counter, defaultdict, namedtuple

#extra
import numpy as np
import pandas as pd


# In[ ]:


percent = lambda x, y: round(100 * x / y)
flatten = lambda lists: [item for lst in lists for item in lst]


# In[ ]:


Ing = namedtuple('Ing', ['head', 'mods', 'states', 'brands', 'langs', 'cuisine', 'rcpid'])

def load_clean_data():
    recipes = pd.read_csv('data/cleaned_data.csv', header=0, index_col=0, encoding='utf-8',
                          # convert named tuple literals to Ings
                          converters={'ingredients': lambda x: eval(x)})
    print('{:,} recipes'.format(recipes.shape[0]))
    return recipes


# In[ ]:


def group_by(ings, attribute):
    groups = defaultdict(list)
    for ing in ings:
        groups[getattr(ing, attribute)].append(ing)
    return groups


# In[ ]:


def make_metrics(recipes):
    columns = []
    recipe_count = []
    recipe_mean_length = []
    head_count = []
    unique_count = []
    rare_count = []
    for cuisine, group in recipes.groupby('cuisine'):
        columns.append(cuisine)
        recipe_count.append(group.shape[0])
        recipe_mean_length.append(round(group.ingredients.apply(len).mean()))
        head_list = [ing.heads[0] for ings in group.ingredients for ing in ings]
        head_count.append(len(head_list))
        head_counts = Counter(head_list)
        unique_count.append(len(head_counts))
        rare_head = 0
        for head, count in head_counts.items():
            if count < 4:
                rare_head += 1
        rare_count.append(rare_head)
    rare_pct = [percent(rare, total) for rare, total in zip(rare_count, unique_count)]
    index = ['recipe_count', 'recipe_length', 'unique_count', 'head_count', 'rare_count', 'rare_pct', 'cuisine']
    metrics = pd.DataFrame([recipe_count, recipe_mean_length, unique_count, head_count, rare_count, rare_pct, columns],
                           index=index, columns=columns, dtype=np.uint32)
    return metrics.transpose()


# In[ ]:


def make_attribute_counts(ings, attribute, categories):
    atts = defaultdict(list)
    for ing in iter(ings):
        for att in getattr(ing, attribute):
            atts[att].append(ing.cuisine)
    att_counts = {}
    for att, cuisine_list in atts.items():
        att_counts[att] = Counter(cuisine_list)
    counts = pd.DataFrame.from_dict(att_counts, orient='index', columns=categories, dtype=np.float64)
    counts.fillna(0.0, inplace=True)
    return counts


# In[ ]:


def normalize_counts(counts, weights=None):
    if weights:
        counts = counts.apply(lambda col: col.map(lambda x: x / weights[col.name]), axis='index')
    count_min = counts.values.min()
    count_range = counts.values.max() - count_min
    counts = counts.applymap(lambda x: (x - count_min) / count_range)
    return counts


# In[ ]:


def equalize_counts(counts, smoothing=.6):
    proportions = counts.T / counts.sum(axis='columns')
    smooth_tails = lambda x: x / (smoothing + x)
    if smoothing:
        proportions = proportions.applymap(smooth_tails)
    return proportions.T


# In[ ]:


def make_scores(recipe, counts):
    def get_scores(ings):
        features = flatten([getattr(ing, att) for ing in ings])
        scores = counts.loc[features].drop(columns=['test'])
        if not features:
            return scores.sum(axis='index')
        return scores.sum(axis='index') / len(features)
    att_scores = []
    for att in ['mods', 'states', 'brands', 'langs']:
        recipe_scores = get_scores(recipe.ingredients)
        att_scores.append(recipe_scores.add_prefix('{}_'.format(att)))
    return pd.concat(att_scores, axis='index')


# In[ ]:


def replace_rare_name(name):
    parts = name.split('-')
    parts[-1] = 'raretype'
    return '-'.join(parts)


# In[ ]:


def make_indicators(recipes, rare_cutoff=0, common_cutoff=None):
    get_ing_attributes = lambda ings: flatten([ing.mods + ing.states + ing.brands + ing.langs for ing in ings])
    recipe_features = recipes.ingredients.map(get_ing_attributes)
    all_features = sorted(set(flatten(recipe_features)))
    feature_array = np.zeros([len(recipe_features), len(all_features)], dtype=np.uint8)
    feature_index = {feature: i for i, feature in enumerate(all_features)}
    for row_i, features in enumerate(recipe_features):
        for feature in features:
            feature_array[row_i, feature_index[feature]] = 1
    features = pd.DataFrame(feature_array, index=recipe_features.index, columns=all_features)
    feature_counts = features.sum(axis='index')
    if common_cutoff:
        common_value = feature_counts.quantile(q=common_cutoff)
        common_features = feature_counts[feature_counts >= common_value].index
        features = features.drop(columns=common_features)
        print('dropped {} common features >= count {}'.format(len(common_features), int(common_value)))
    rare_value = feature_counts.quantile(q=rare_cutoff)
    rare_features = feature_counts[feature_counts <= rare_value].index
    for rare_feature in rare_features:
        super_feature = replace_rare_name(rare_feature)
        if super_feature in features:
            features[super_feature] += features[rare_feature]
            continue
        features[super_feature] = features[rare_feature]
    features = features.drop(columns=rare_features)
    print('merged {} rare features <= count {}'.format(len(rare_features), int(rare_value)))
    return features


# In[ ]:


def save_output(output):
    output = output.drop(columns=['ingredients'])
    
    train = output.query('cuisine != "test"')
    test = output.query('cuisine == "test"')
    
    train.cuisine.to_csv('data/cuisine.csv', header=False, encoding='utf-8')
    
    train = train.drop(columns=['cuisine'])
    test = test.drop(columns=['cuisine'])
    
    train.to_csv('data/temp_train.csv', header=True, encoding='utf-8') 
    test.to_csv('data/temp_test.csv', header=True, encoding='utf-8')

