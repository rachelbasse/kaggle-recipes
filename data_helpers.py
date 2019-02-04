#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# imports

# standard
from csv import DictReader
from operator import itemgetter
import re

# extra
from funcy import memoize
import spacy
from symspellpy.symspellpy import SymSpell, Verbosity


# In[ ]:


# quick hack instead of more complicated solution
spellcheck = {
    'reduc': 'reduced',
    'jell o': 'gelatin',
    'jello': 'gelatin',
    'made with': 'with',
    'v': 'tomato juice',
    'e fu': 'yi mein',
    'miracle whip': 'mayonaise',
    'veget': 'vegetable',
    'vegeta': 'vegetable',
    'recip': 'recipe',
    'oliv': 'olive',
    'semi sweet': 'semisweet',
    'mellow yellow': 'cola',
    'mountain dew': 'cola',
    'coke': 'cola',
    'soi': 'soy',
    'sauc': 'sauce',
    'ground pepper': 'bpepper',
    'black pepper': 'bpepper',
    'of beef': 'beef',
    'of veal': 'veal',
    'of round': 'beef',
    'abalone': 'snail',
    'rosemari': 'rosemary',
    'old bay seasoning': 'obseasoning',
    'half and half': 'andhalfhalf'
}


# In[ ]:


stopwords = ['s', 't', 'n', 'l', 'lb',
         'accompaniment', 'all', 'boil', 'bought', 'boston', 'boned', 'boneless', 'breast', 'breasts', 'broiler',
         'can', 'canned', 'chopped', 'cracked', 'crumbled', 'crumbles', 'crushed', 'cubed', 'cuisine', 'cuisines', 
         'cut', 'center', 'coarse', 'cook', 'cooking', 'dried', 'dry', 'diced', 'extra', 'eye',
         'fast', 'filled', 'fine', 'finely', 'flat', 'fresh', 'freshly', 'frozen', 'fryer', 'full', 'fully', 
         'granulate', 'granulated', 'grate', 'grated', 'great', 'grill', 'ground', 
         'half', 'halves', 'head', 'high', 'homestyl', 'homestyle', 'kernel', 'kitchen', 
         'large', 'leaf', 'leave', 'leftover', 'leg', 'legs', 'low',
         'master', 'medium', 'mild', 'minced', 'mini', 'minicub', 'natural',
         'original', 'ounc', 'oven', 'oz', 'part', 'plain', 'pod', 'premium', 'purpose', 
         'rack', 'ready', 'real', 'reduce', 'refrigerated', 'rising', 'round', 'seasoning', 'skinned', 'skinless', 'sodium',
         'seamless', 'sheet', 'shred', 'shredded', 'slice', 'sliced', 'small', 'standing', 'streaky', 'store', 'style', 'superior', 
         'thigh', 'thighs', 'torn', 'traditional', 'unsweetened', 'wedges']


# In[ ]:


word_sub_classes = {
    '': stopwords,
    'alcohol': ['bénédictine', 'budweiser', 'cordial', 'jagermeister', 'kirschenliqueur', 'kirschwasser', 'lambic', 
                'mixer', 'moonshine'],
    'bird': ['pheasant'],
    'fish': ['amberjack', 'bream', 'brill', 'carp', 'hamachi', 'lingcod', 'perch', 'pike', 'scrod', 'sockeye'],
    'game': ['bear', 'bison', 'moose', 'rooster'],
    'meat': ['bratwurst', 'chateaubriand', 'chopmeat', 'frankfurter', 'frog', 'jambon', 'knuckle', 'ribeye', 'riblet', 'wiener'],
    'sweetener': ['sucralose', 'stevia', 'swerve', 'truvía'],
    'tea': ['ceylon', 'pekoe', 'souchong'],
    'american': ['argo', 'bisquick', 'bragg', 'braggs', 'breakstone', 'breakstones', 'breyers', 'crisco',
              'campbells', 'diamond', 'frenchs', 'heinz', 'hellmanns', 'hellmann', 'hershey',
              'hurst', 'jif', 'jiffy', 'johnsonville', 'jonshonville', 'kerrygold', 'klondike', 'knorr', 'knudsen', 'kraft', 'lipton',
              'mazola', 'meyer', 'mccormick', 'nestle', 'pam', 'pace', 'philadelphia', 'pillsbury', 'pompeian', 'progresso',
              'ragu', 'ritz', 'smithfield', 'sargento', 'stonefire', 'swanson', 'triscuits', 'tyson',
              'wishbone', 'wondra', 'williams', 'yoplait', 'zatarains'],
    'italian': ['barilla', 'bertolli', 'classico', 'delallo'],
    'mexican': ['mission', 'goya', 'rotel', 'tostidos'],
    'healthy': ['diet', 'fatfree', 'glutenfree', 'grassfed', 'light', 'lean', 'lowfat',  'lowsodium', 'nonfat']
}

# WARNING: these will not be surrounded by word boundaries
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
    'andmaccheese': ['macaroni and cheese'],
    'andbreadbutter': ['bread and butter'],
    'chocolates': ['m and ms'],
    'andporkbeans': ['pork and beans'],
    'andsweetsour': ['sweet and sour'],
    # synonyms
    'bpepper': ['black pepper', 'ground pepper'],
    'garlic': ['garlic clove', 'garlic cloves'],
    'sugar': ['white sugar', 'granulated sugar'],
    'cream': ['whipping cream', 'heavy cream', 'heavy whipping cream'],
    'cumin': ['cumin seed', 'cumin seeds']
}


# In[2]:


words_to_segment = {
    'rockfish', 'cuttlefish', 'blackcurrant', 'pumpkinseed', 'breadcrumbs', 'crayfish', 'cauliflowerets', 'beetroot', 'chilegarlic', 
    'cornflour', 'almondmilk', 'crawfish', 'poundcake', 'wheatberries', 'kiwifruit', 'corncobs', 'applesauce', 'alfredostyle', 
    'chocolatecovered', 'sablefish', 'ducklings', 'sheepshead', 'sweetbreads', 'bellpepper', 'redcurrant', 'wolfberries', 'poppyseeds', 
    'crabapples', 'breadstick', 'milkfish', 'breadcrumb', 'blackpepper', 'cornbread', 'mexicorn', 'fruitcake', 'boysenberries', 'monkfish', 
    'huckleberries', 'swordfish', 'whitefish', 'shellfish', 'cornstarch', 'quickcooking', 'bluefish', 'kingfish'}


# In[ ]:


# invert dict of {k1: v1, k2: v1, k3: v2} to {v1: [k1, k2], v2: k3}
def invert_dict_singles(orig):
    new = {}
    for k, v in orig.items():
        new[v] = new.get(v, [])
        new[v].append(k)
    return new

# invert dict of {k1: v1, k2: v1, k3: v2} to {v1: [k1, k2], v2: k3}
def invert_dict_lists(orig):
    new = {}
    for k, vals in orig.items():
        for v in vals:
            new[v] = k
    return new

# remove first dupes and keep order: [3, 1, 3, 2, 3] => [1, 2, 3]
def remove_first_dupes(lst):
    seen = set()
    seen_add = seen.add
    res = [x for x in reversed(lst) if not (x in seen or seen_add(x))]
    res = res[::-1]
    return res


# In[ ]:


char_pattern = re.compile(r'[®™’â€/\!\'%\(\)\.\d]')
of_pattern = re.compile(r'(\w) of (?:the )?')
words_to_sub = invert_dict_lists(word_sub_classes)
phrases_to_sub = invert_dict_lists(phrase_sub_classes)

spellcheck_compiled = []
for k, v in sorted(spellcheck.items()):
    k = re.compile(r'(\b)' + k + r'(\b)')
    v = r'\1' + v + r'\2'
    spellcheck_compiled.append((k, v))


# In[ ]:


# detected language strings to add as ingredients
lang_trans = {}
with open('data/lang_tags.csv', 'r', encoding='utf-8') as file:
    reader = DictReader(file, fieldnames=['word', 'lang'])
    for row in reader:
        lang_trans[row['word']] = row['lang']


# In[ ]:


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


parse = spacy.load('en_core_web_lg', disable=['parser', 'ner'])

# workaround for 'en_core_web_lg' stop_words bug
for word in parse.Defaults.stop_words:
    lex = parse.vocab[word]
    lex.is_stop = True

@memoize
def lemmatize(phrase):
    is_stopword = lambda token: (token.is_stop or token.lemma_ in stopwords)
    return [token.lemma_ for token in parse(phrase) if not is_stopword(token)]


# In[ ]:


# WARNING: don't overwrite the existing manually tweaked dictionary!!!
def make_freq_dict(word_counts):
    lines = []
    for word, freq in sorted(word_counts.items(), key=itemgetter(1), reverse=True):
        if freq > 4 and len(word) > 3:
            lines.append('{0} {1}\n'.format(word, freq))
    with open('data/new_frequency_dictionary.txt', 'w+', encoding='utf-8') as file:
        file.write(lines)

