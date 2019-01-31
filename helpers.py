#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# invert dicts
def invert_dict_singles(orig):
    new = {}
    for k, v in orig.items():
        new[v] = new.get(v, [])
        new[v].append(k)
    return new

def invert_dict_lists(orig):
    new = {}
    for k, vals in orig.items():
        for v in vals:
            new[v] = k
    return new


# In[ ]:


def remove_dupes(lst):
    seen = set()
    seen_add = seen.add
    return [x for x in lst if not (x in seen or seen_add(x))]


# In[ ]:


from csv import DictReader

lang_trans = {}
with open('data/lang_tags.csv', 'r', encoding='utf-8') as file:
    reader = DictReader(file, fieldnames=['word', 'lang'])
    for row in reader:
        lang_trans[row['word']] = row['lang']


# In[ ]:


# hack instead of bigger solution that didn't work
spellcheck = {
    'reduc': 'reduced',
    'jell o': 'gelatin',
    'jello': 'gelatin',
    'made with': 'with',
    'v': 'tomato juice',
    'e fu': 'yi mein',
    'miracle whip': 'mayonaise',
    'ragu': 'italian',
    'veget': 'vegetable',
    'vegeta': 'vegetable',
    'recip': 'recipe',
    'oliv': 'olive',
    'semi sweet': 'semisweet',
    'mellow yellow': 'soda',
    'mountain dew': 'soda',
    'budweiser': 'beer',
    'soi': 'soy'
}


# In[ ]:


stopwords = ['accompaniment', 'all', 'boil', 'bought', 'boston', 'boned', 'boneless', 'breast', 'breasts', 'broiler',
         'can', 'canned', 'chopped', 'crumbled', 'crumbles', 'crushed', 'cuisine', 'cuisines', 
         'cut', 'center', 'coarse', 'cook', 'cooking', 'dried', 'dry', 'diced', 'extra', 
         'fast', 'filled', 'fine', 'finely', 'fresh', 'freshly', 'frozen', 'fryer', 'full', 'grate', 'grated', 'grill', 'ground', 
         'half', 'halves', 'head', 'high', 'homestyl', 'homestyle', 'large', 'leaf', 'leftover', 'leg', 'legs', 'low',
         'master', 'medium', 'minced', 'natural',
         'original', 'ounc', 'oven', 'oz', 'part', 'plain', 'premium', 'purpose', 'ready',
         'real', 'reduce', 'refrigerated', 'rising', 'skinned', 'skinless', 'sodium',
         'seamless', 'sheet', 'shred', 'shredded', 'slice', 'sliced', 'small', 'standing', 'streaky', 'store', 'style', 'superior', 
         'thigh', 'thighs', 'torn', 'traditional', 'unsweetened', 'virgin', 'wedges']


# In[ ]:


word_sub_classes = {
    '': stopwords,
    'american': ['argo', 'bisquick', 'bragg', 'braggs', 'breakstone', 'breakstones', 'breyers', 'crisco',
              'campbells', 'diamond', 'frenchs', 'heinz', 'hellmanns', 'hellmann', 'hershey',
              'hurst', 'jif', 'jiffy', 'johnsonville', 'jonshonville', 'kerrygold', 'klondike', 'knorr', 'knudsen', 'kraft', 'lipton',
              'mazola', 'meyer', 'mccormick', 'nestle', 'pam', 'pace', 'philadelphia', 'pillsbury', 'pompeian', 'progresso', 'ritz', 'smithfield',
              'sargento', 'stonefire', 'swanson', 'triscuits', 'tyson',
              'wishbone', 'wondra', 'williams', 'yoplait', 'zatarains'],
    'italian': ['barilla', 'bertolli', 'classico', 'delallo'],
    'mexican': ['mission', 'goya', 'rotel', 'tostidos'],
    'healthy': ['diet', 'fatfree', 'glutenfree', 'light', 'lowfat',  'lowsodium', 'nonfat']
}

phrase_sub_classes = {
    '': ['firmly packed', 'flat leaf', 'free range', 'on the vine', 'rapid rise', 'vine ripened', 'whole kernel'],
    'american': ['artisan blends', 'best food', 'better than bouillon', 'betty crocker', 'bob evans', 'calcium plus vitamin d', 'country crock',
              'crystal farms', 'duncan hines', 'earth balance', 'egglands best', 'family harvest', 'farmhouse original', 
              'foster farms', 'franks redhot', 'gold medal', 'good seasons', 'gourmet garden',
              'green giant', 'hidden valley', 'hillshire farms', 'home originals', 'honeysuckle white',
              'i cant believe its not', 'i cant believe it not', 'i cant believ it not', 'jimmy dean', 'king arthur', 'land o lakes',
              'lea and perrins', 'mrs dash', 'nielsen massey', 'no stick', 'oscar mayer', 
              'pasta sides', 'pepperidge farm', 'pure wesson', 'ready rice', 'recipe creation', 'recipe secret', 'robert mondavi',
              'simply organic', 'skippy', 'special k', 'spice islands', 'a hint of', 'a touch of philadelphia', 
              'texas pete', 'uncle bens', 'wish bone', 'honey bunches of oats'],
    'asian': ['a taste of thai', 'conimex woksaus specials', 'soy vay', 'veri veri'],
    'italian': ['old world style'],
    'mexican': ['old el paso', 'ro tel', 'taco bell', 'thick and chunky'],
    'healthy': ['cholesterol free', 'fat free', 'gluten free', 'less sodium', 'low fat', 'low salt', 'low sodium', 'lower sodium', 
                'non fat', 'no salt added', 'reduced fat', 'reduce sodium', 'reduced sodium', 'sodium reduced', 'wheat free'],
    # ands
    'half-and-half': ['half and half'],
    'mac-and-cheese': ['macaroni and cheese'],
    'bread-and-butter': ['bread and butter'],
    'chocolates': ['m and ms'],
    'pork-and-beans': ['pork and beans'],
    'sweet-and-sour': ['sweet and sour'],
    # synonyms
    'pepper': ['black pepper'],
    'garlic': ['garlic clove', 'garlic cloves'],
    'sugar': ['white sugar', 'granulated sugar'],
    'cream': ['whipping cream', 'heavy cream', 'heavy whipping cream'],
    'cumin': ['cumin seed', 'cumin seeds']
}
words_to_segment = {
 'alfredostyle',
 'almondmilk',
 'applesauce',
 'beetroot',
 'bellpepper',
 'blackcurrant',
 'blackpepper',
 'bluefish',
 'boysenberries',
 'breadcrumb',
 'breadcrumbs',
 'breadstick',
 'cauliflowerets',
 'chilegarlic',
 'chocolatecovered',
 'cornbread',
 'corncobs',
 'cornflour',
 'cornstarch',
 'crabapples',
 'crawfish',
 'crayfish',
 'cuttlefish',
 'ducklings',
 'fruitcake',
 'huckleberries',
 'kingfish',
 'kiwifruit',
 'mexicorn',
 'milkfish',
 'monkfish',
 'poppyseeds',
 'poundcake',
 'quickcooking',
 'redcurrant',
 'rockfish',
 'sablefish',
 'sheepshead',
 'shellfish',
 'sweetbreads',
 'swordfish',
 'wheatberries',
 'whitefish',
 'wolfberries'
}


# In[ ]:


words_to_sub = invert_dict_lists(word_sub_classes)
phrases_to_sub = invert_dict_lists(phrase_sub_classes)


# In[ ]:


import re

char_pattern = re.compile(r'[®™’â€/\!\'%\(\)\.\d]')
of_pattern = re.compile(r' of (?:the )?')

spellcheck_compiled = []
for k, v in sorted(spellcheck.items()):
    k = re.compile(r'(\b)' + k + r'(\b)')
    v = r'\1' + v + r'\2'
    spellcheck_compiled.append((k, v))


# In[ ]:


from operator import itemgetter

def make_freq_dict(word_counts):
    lines = []
    for word, freq in sorted(word_counts.items(), key=itemgetter(1), reverse=True):
        if freq > 4 and len(word) > 3:
            lines.append('{0} {1}\n'.format(word, freq))
    with open('data/frequency_dictionary.txt', 'w+', encoding='utf-8') as file:
        for line in lines:
            file.write(line)


# In[ ]:


from symspellpy.symspellpy import SymSpell, Verbosity

sym_spell = SymSpell(83000, 1, 7)
dictionary_path = 'data/frequency_dictionary.txt'
if not sym_spell.load_dictionary(dictionary_path, 0, 1):
    print("Dictionary file not found")

def correct_spelling(word):
    suggestions = sym_spell.lookup(word, Verbosity.TOP, 1)
    if not suggestions:
        return word
    return suggestions[0].term

sym_seg = SymSpell(83000, 1, 8)
dictionary_path = 'data/segment_dictionary.txt'
if not sym_seg.load_dictionary(dictionary_path, 0, 1):
    print("Dictionary file not found")

def segment_word(word):
    res = sym_seg.word_segmentation(word)
    return res.segmented_string


# In[ ]:


import en_core_web_lg
from functools import lru_cache
import spacy

parse = spacy.load('en_core_web_lg', disable=['parser', 'ner'])

for word in parse.Defaults.stop_words:
    lex = parse.vocab[word]
    lex.is_stop = True

@lru_cache(maxsize=4096)
def lemmatize(phrase):
    return [token.lemma_ for token in parse(phrase) if not (token.is_stop or token.text in stopwords)]


# In[ ]:


import pandas as pd

counts = lambda df: df.apply(pd.Series.value_counts, axis=0)

def get_errors(X, y, model, sort_col=None):
    errors = []
    for i in range(X.shape[0]):
        obs = X.iloc[i:i+1]
        real = y.iloc[i]
        y_pred = model.predict(obs)
        if y_pred != [real]:
            errors.append(i)
    errs = pd.concat([X.iloc[errors], y.iloc[errors]], axis=1)
    print('Errors:', errs.shape[0])
    if sort_col:
        errs.sort_values(sort_col, inplace=True)
    return errs

