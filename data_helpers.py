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
from spacy.lemmatizer import Lemmatizer
from spacy.lang.en import LEMMA_INDEX, LEMMA_EXC, LEMMA_RULES
from symspellpy.symspellpy import SymSpell, Verbosity


# In[ ]:


# WARNING: words of length <= 4 will not get spelling correction
special_spelling = {
    'believ': 'believe', 'bbq': 'barbecue', 'cauliflowerets': 'cauliflower', "chik''n": 'chicken',
    'chillies': 'chile', 'coco': 'cocoa', 'creamer': 'cream', 'cummin': 'cumin', 'dress': 'dressing', 'dri': 'dried',
    'evapor': 'evaporated', 'filo': 'phyllo', 'fri': 'fries', 'grained': 'grain',
    'haas': 'hass', 'half half': 'halfandhalf', 'ic': 'ice',
    'jalape': 'jalapeno', 'jell o': 'jello', 'lb': '', 'leav': 'leaf', 'leaves': 'leaf', 'liquorice': 'licorice', 
    'marin': 'marinade', 'mayonnai': 'mayonaise', 'min': 'mint', 'minicub': 'minicube',
    'nuts': 'nut', 'oats': 'oat', 'oliv': 'olive', 'pâté': 'pate',
    'penn': 'penne', 'purée': 'puree', 'dress russian': 'russian dressing', 'rom': 'roma',
    'saki': 'sake', 'sauc': 'sauce', 'season': 'seasoning', 'soi': 'soy', 'tradit': 'traditional', 'v 8': 'v8',
    'veget': 'vegetable', 'vegeta': 'vegetable', 'veggie': 'vegetable', 'veggies': 'vegetable',
    'wrapper': 'wrap', 'wrappers': 'wrap', 'yuca': 'yucca'
}

exceptions = {
    # commas
    'boneless, skinless chicken breast': 'boneless skinless chicken breast', 'red vinegar white white, wine,': 'red vinegar and white wine',
    # dashes
    'all-purpose': 'allpurpose', 'bone-in': 'bonein', 'cho-cho': 'chocho', 'coca-cola': 'coke',
    'corn-on-the-cob': 'corn', 'demi-glace': 'demiglace', 'e-fu': 'yi mein', 'five-spice': 'fivespice',
    'free-range': 'freerange', 'grass-fed': 'grassfed', 'half-and-half': 'halfandhalf', 'jell-o': 'jello',
    'multi-grain': 'multigrain', 'ogura-an': 'oguraan', 'piri-piri': 'piripiri',
    'ro-tel': 'rotel', 'shell-on': 'shellon', 'skin-on': 'skinon', 't-bone': 'tbone', 'tex-mex': 'texmex',
    'wish-bone': 'wishbone', 'yaki-nori': 'yakinori',
    # special
    'abura age': 'aburaage', 'bake soda': 'bakingsoda', 'baking soda': 'bakingsoda', 'bun': 'roll', 'buns': 'roll',
    'color': 'coloring', 'di parma': '', 'free range': 'freerange',
    'garlic clove': 'garlic', 'garlic cloves': 'garlic', 'hot dog': 'hotdog', 'hot dogs': 'hotdog', 'ice cream': 'icecream', 
    'rib eye': 'ribeye', 'slice thinli': '', 'soft drink': 'soda', 'wish bone': 'wishbone', 'or white yellow': '',
    # stopwords
    'all purpose': 'allpurpose', 'multi purpose': 'multipurpose',
    'bone in': 'bonein',
    'head on': 'headon', 'shell on': 'shellon', 'skin on': 'skinon', 'on the vine': '',
    'baby back': 'babyback',
    'packed in': 'in',
    'made with': 'with',
    'italian with herbs dressing': 'italian herbs dressing',
    'cold cut': 'coldcut', 'cold cuts': 'coldcuts',
    'do chua': 'pickled carrot daikon',
    'ear of': '', 'leg of': '', 'breast of': '', 'eye of ': 'eyeof', 'fillet of': '', 'rack of': '',
    'a touch of': '', 'a hint of': '',
    'five spice': 'fivespice',
    'bread and butter': 'breadandbutter', 'half and half': 'halfandhalf', 'macaroni and cheese': 'macaroniandcheese', 
    'pork and beans': 'porkandbeans', 'sweet and sour': 'sweetandsour'
}


# In[ ]:


brands_to_sub_lists = { 
    'baking mix': ['bisquick'],
    'beer': ['budweiser'],
    'bouillon': ['better than bouillon'],
    'brandy': ['poire williams'],
    'bread': ['wondra'],
    'butter': ['country crock calcium plus vitamin d', 'flora buttery',
               'i cant believe it not butter', 'i cant believe its not butter'],
    'cake': ['yodel'],
    'candy': ['m and ms'],
    'cereal': ['chex', 'corn flakes', 'fiber one'],
    'cheese spread': ['velveeta'],
    'chocolate': ['hershey', 'ibarra'],
    'chip': ['tostitos'],
    'corn': ['green giant steamers niblets', 'green giant steamers niblet'],
    'cracker': ['triscuit', 'triscuits'],
    'cream': ['elmlea single', ],
    'dairy': ['daiya', 'flora cuisine', 'flora original'],
    'dressing': ['wishbone'],
    'gelatin': ['jello'],
    'gravy': ['gravy master'],
    'hazelnut spread': ['nutella'],
    'hot pepper': ['peppadew', 'peppadews', 'piment despelette'],
    'hot sauce': ['franks', 'harissa', 'louisiana hot sauce', 'pickapeppa'],
    'liqueur': ['chambord', 'crème de cassis', 'creme de cassis', 'cointreau', 'frangelico', 'galliano',
                'gran marnier', 'grand marnier',
                'kahlua', 'kahlúa', 'licor 43', 'madeira', 'praline liqueur', 'pernod', 'tuaca'],
    'liquor': ['southern comfort'],
    'meat substitute': ['quorn'],
    'milk': ['carnation'],
    'pasta': ['knorr pasta sides', 'barilla'],
    'rice': ['uncle bens', 'knorr fiesta sides'],
    'rice flour': ['mochiko'],
    'rum': ['bacardi'],
    'seasoning': ['accent', 'maggi', 'mrs dash', 'taco bell home originals'],
    'shortening': ['crisco'],
    'soda': ['7 up', 'coke', 'dr pepper', 'la casera', 'sprite', 'squirt'],
    'stout': ['guinness'],
    'sugar': ['sugar in the raw'],
    'sweetener': ['splenda', 'splenda granular', 'splenda granulated', 'swerve', 'truvía', 'truvía baking blend'],
    'syrup': ['karo'],
    'tequila': ['jose cuervo'],
    'tomato': ['rotel'],
    'tomato juice': ['v8'],
    'tomato sauce': ['ragu'],
    'tortilla chip': ['doritos'],
    'whiskey': ['george dickel', 'jack daniels'],
    'yogurt': ['flora proactiv', 'yoplait']
}

brands_to_pull = {
    'a taste of thai', 'alexia', 'angostura', 'argo', 'azteca', 'baileys', 'barilla ovenready',
    'barilla plus', 'bertolli', 'bertolli classico', 'best food', 'best foods', 'betty crocker', 'bob evans',
    'bragg', 'braggs', 'breakstones', 'breyers', 'camellia', 'campbells', 'cavenders', 'challenge',
    'chartreuse', 'chobani', 'cholula', 'cinnamon toast crunch', 'colmans', 'conimex wok',
    'conimex woksaus specials', 'country crock', 'crisco', 'crisco pure', 'crystal', 'crystal farms', 'cumberland',
    'curry guy', 'daisy', 'daisy brand', 'del monte', 'delallo', 'diamond crystal', 'dole', 'domaine de canton',
    'domino', 'dream', 'dreamfields', 'duncan hines', 'earth balance', 'egglands best', 'equal', 'estancia',
    'everglades', 'fisher', 'foster farms', 'franks', 'franks redhot original', 'frenchs', 
    'gebhardt', 'godiva', 'gold medal', 'good seasons', 'gourmet garden', 'goya', 'green giant',
    'grey poupon', 'hatch', 'heath', 'heinz', 'hellmann', 'hellmanns', 'herdez',
    'hidden valley', 'hidden valley farmhouse originals', 'hogue', 'holland house', 'honey bunches of oat',
    'honeysuckle white', 'hurst family harvest', 'imperial',
    'jack daniels', 'jagermeister', 'jameson', 'jello', 'jif', 'jiffy', 'jimmy dean', 'johnsonville',
    'kahlua', 'kahlúa', 'kerrygold', 'kewpie', 'kikkoman', 'kim crawford', 'king arthur',
    'klondike gourmet', 'klondike rose', 'knorr', 'knox', 'knudsen', 'kraft', 'kraft big slice', 'kraft classic',
    'kraft mexican style', 'kraft original', 'kraft slim cut', 'kroger', 'la victoria', 'land o lakes',
    'lea and perrins', 'lipton', 'lipton cup size', 'lipton iced tea brew family size', 'lipton recipe secrets',
    'madras', 'mae ploy', 'makers mark', 'maldon', 'manischewitz', 'martha white', 'mazola', 'mccormick',
    'mccormick original', 'mccormick perfect pinch', 'meyer', 'mezzetta', 'minute',
    'mission', 'mizkan', 'morton', 'mountain dew', 'mountain high',
    'nakano', 'nestle', 'new york style panetini', 'nido', 'nielsenmassey', 'nielsen massey', 'nilla', 'nusalt', 'nu salt',
    'old bay', 'old el paso',
    'old el paso thick n chunky', 'oreo', 'ortega', 'oscar mayer', 'oscar mayer deli fresh', 'pace', 'pam', 
    'pam nostick', 'pepperidge farm', 'philadelphia', 'pillsbury', 'pillsbury classic', 
    'pillsbury crescent recipe creations', 'pompeian', 'progresso', 'pure wesson', 'ragu classic',
    'ragu robusto', 'ragu traditional', 'red gold', 'rice krispies', 'ritz', 'robert mondavi', 'ronzoni',
    'royal', 'saffron road', 'sargento', 'sargento artisan blends', 'sargento traditional cut', 'silk', 'simply organic',
    'skippy', 'smart balance', 'smithfield', 'southern comfort', 'soy vay', 'soy vay veri veri teriyaki', 'special k',
    'spice islands', 'spike', 'st germain', 'stonefire', 'success', 'swanson',
    'syd', 'tabasco', 'taco bell', 'taco bell thick and chunky', 'tapatio', 'texas pete',
    'thai kitchen', 'tipo ', 'toulouse', 'tuttorosso',
    'tyson', 'uncle bens original converted brand', 'uncle bens ready rice', 'velveeta', 'white lily',
    'wholesome sweeteners', 'wolf brand', 'yoplait', 'zatarains'   
}


# In[ ]:


words_to_segment = {
    'alfredostyle': 'alfredo style', 'almondmilk': 'almond milk', 'applesauce': 'apple sauce',
    'arrowroot': 'arrow root', 'beetroot': 'beet root',
    'bellpepper': 'bell pepper', 'blackcurrant': 'black currant', 'blackpepper': 'black pepper', 'bluefish': 'blue fish',
    'breadcrumb': 'bread crumb', 'breadcrumbs': 'bread crumbs', 'breadstick': 'bread stick', 'brinecured': 'brine cured',
    'broilerfryer': 'broiler fryer', 'broilerfryers': 'broiler fryer', 'butterflavored': 'butter flavored',
    'buttermargarine': 'butter margarine', 'chickenapple': 'chicken apple', 'chilegarlic': 'chile garlic', 
    'chocolatecovered': 'chocolate covered', 'chocolatehazelnut': 'chocolate hazelnut', 'coarsegrain': 'coarse grain',
    'coconutmilk': 'coconut milk', 'countrystyle': 'country style', 'cornbread': 'corn bread', 'corncobs': 'corn cobs', 
    'cornflour': 'corn flour', 'cornmeal': 'corn meal', 'cornstarch': 'corn starch',
    'crabapples': 'crab apples', 'cuminseed': 'cumin seed', 'dillweed': 'dill weed', 'dutchprocessed': 'dutch processed',
    'extralean': 'extra lean', 'extravirgin': 'extra virgin', 'flaxseed': 'flax seed', 'freezedried': 'freeze dried',
    'fruitcake': 'fruit cake', 'gingerroot': 'ginger root', 'greekstyle': 'greek style', 
    'hardboiled': 'hard boiled', 'honeyflavored': 'honey flavored', 'italianstyle': 'italian style',
    'kiwifruit': 'kiwi fruit', 'kongstyle': 'kong style', 'lemonlime': 'lemon lime', 'longgrain': 'long grain',
    'meatfilled': 'meat filled', 'mediumgrain': 'medium grain', 'ovenready': 'oven ready',
    'parmigianareggiano': 'parmigiana reggiano', 'parmigianoreggiano': 'parmigiano reggiano', 'pinenut': 'pine nut',
    'poppyseeds': 'poppy seeds', 'poundcake': 'pound cake', 'pumpkinseed': 'pumpkin seed', 'pumpkinseeds': 'pumpkin seed',
    'quickcooking': 'quick cooking', 'redcurrant': 'red currant', 'sesameginger': 'sesame ginger', 'shanghaistyle': 'shanghai style',
    'sheepshead': 'sheeps head', 'shiromiso': 'shiro miso', 'shortgrain': 'short grain', 'softboiled': 'soft boiled',
    'soybean': 'soy bean', 'soybeans': 'soy bean', 'soymilk': 'soy milk', 'sparerib': 'spare rib', 'stoneground': 'stone ground',
    'sugarcane': 'sugar cane', 'superfine': 'super fine', 
    'sweetbreads': 'sweet breads', 'vegetablefilled': 'vegetable filled', 'wholemilk': 'whole milk'
}

state_words = {
    # prep
    'beaten', 'blackened', 'blanched', 'bleached', 'blend', 'blended', 'boiled', 'bonein', 'boneles',
    'bottled', 'braised', 'breaded', 'brewed', 
    'candied', 'canned', 'centercut', 'chiffonade', 'chilled', 'chopped',
    'clotted', 'coarse', 'cold', 'coldsmoked', 'compressed',
    'condensed', 'cook', 'cooked', 'cool', 'cracked', 'creamed', 'crumble', 'crumbled', 'crushed', 'cube',
    'cubed', 'cured', 'cut', 'diced', 'drained', 'dried', 'flaked', 'fleshed', 'fried', 'frozen',
    'granular', 'granulate', 'granulated', 'grate', 'grated', 'grill', 'grilled', 'ground', 'headon', 
    'iced', 'iodized', 'mashed', 'melted', 'minced', 'mixed', 'natural', 'parboiled', 'pack', 'packed',
    'peeled', 'pickled', 'pitted', 'pointed', 'popped',
    'powdered', 'prepare', 'prepared', 'pressed', 'raw', 'reduce', 'reduced', 'refined',
    'refrigerated', 'ripe', 'ripened', 'roasted',
    'rolled', 'rubbed', 'salted', 'section', 'segment', 'shaped', 'shaved', 'shelled', 'shellon', 'shred', 'shredded',
    'shuck', 'shucked', 'skinles', 'skinon', 'slice', 'sliced',
    'slivered', 'smoked', 'softened','steamed', 'stewed', 'strained', 'sweeten', 'sweetened', 'toasted',
    'uncook', 'unsalt', 'unbleached', 'uncooked', 'unsalted', 'unsmoked', 'unsulphured',
    'warm', 'whipped', 'whisked', 'whole',
    # quality
    'added', 'allpurpose', 'artificial', 'best', 'blend', 'bought',
    'crispy', 'dry', 'extra', 'fancy', 'fine', 'finely', 'firm', 'firmli', 'firmly', 'flavor',
    'flavored', 'freerange', 'fresh', 'freshly', 'fully', 'grassfed', 'homemade', 'imitation', 'large',
    'leftover', 'loosely', 'natural', 'medium', 'mini',
    'multipurpose', 'oldfashioned', 'organic', 'petite', 'plain', 'prime', 'pure', 
    'regular', 'seasoned', 'seedless', 'size', 'small', 'spare', 'style', 'super', 'superior',
    'table', 'tightly', 'tradicional', 'traditional', 'unflavored', 'virgin',
}

heads_to_drop = {
    'accompaniment', 'bag', 'baking', 'ball', 'bar', 'base', 'black', 'bowl',  'cap',
    'crosswise',  'cube', 'cup', 'dessert', 'dinner', 'fillet', 'flake', 'food', 'free', 'frozen', 
    'half', 'kiss', 'layer', 'lowfat', 'mixers', 'pad', 'pod', 'pot', 'purpose', 'quick',
    'recipe', 'shape', 'side', 'spanish', 'spiral', 'split', 'sprig', 'steak', 'weed', 'zero'
}

head_subs = {
    'meat': ['fillet', 'steak']
}


# In[ ]:


supertypes = {
    'apple': ['pippin'],
    'bakingsoda': ['bicarbonate'],
    'ball': ['falafel'],
    'bean': ['cannelloni', 'garbanzo', 'legume'],
    'beer': ['ale', 'lambic', 'pilsner', 'porter', 'stout'],
    'bouillon': ['minicube'],
    'bread': ['bagel', 'baguette',  'brioche', 'bun', 'ciabatta', 'grissini',
             'pumpernickel', 'roll', 'sourdough'],
    'butter': ['oleo', 'margarine', 'shortening'],
    'cake': ['crepe', 'cupcake', 'genoise', 'pancake', 'shortcake', 'waffle'],
    'candy': ['brittle', 'dragee', 'gumdrop', 'meringue', 'praline', 'toffee'],
    'cereal': ['amaranth', 'barley', 'buckwheat', 'bran', 'bulgur', 'groat', 'malt', 'millet', 'oat', 'oatmeal',
               'sorghum', 'spelt', 'triticale', 'wheat', 'wheatberry', 'wheatberrie'],
    'cheese': ['asiago', 'boursin', 'brie', 'cantal', 'cheddar', 'chevre', 'colby', 'dolce', 'dubliner', 'feta', 
               'fontina', 'gorgonzola', 'gouda', 'gruyere', 'gruyère', 'halloumi', 'havarti', 'jack',
               'jarlsberg', 'manchego', 'mascarpone', 'mozzarella', 'muenster', 'neufchtel',
               'paneer', 'parmesan', 'parmigiano', 'pecorino', 'provolone', 
               'reblochon', 'reggiano', 'ricotta', 'romano', 'roquefort',
               'stilton', 'swis', 'taleggio', 'wensleydale'],
    'cherry': ['maraschino'],
    'coffee': ['cappuccino'],
    'cookie': ['amaretti', 'biscotti', 'cone', 'gingersnap', 'macaron', 'shortbread', 'snap', 'tart'],
    'cracker': ['biscuit', 'pretzel', 'saltine'],
    'custard': ['flan'],
    'dressing': ['russian', 'vinaigrette'], 
    'drink': ['beverage', 'carbonated', 'eggnog', 'limeade', 'seltzer', 'tonic', 'verjuice', 'zabaglione'],
    'egg': ['white', 'yolk'],
    'fish': ['abalone', 'ahi', 'albacore', 'amberjack', 'anchovy', 'barramundi', 'bas', 'basa', 'branzino', 'bream', 'brill',
             'carp', 'catfish', 'claw', 'cod' 'conch', 'cuttlefish', 'dogfish', 'eel', 'escargot', 'fishcake', 'grouper', 
             'haddock', 'hake', 'halibut', 'hamachi', 'herring', 'kamaboko',
             'kingfish', 'kipper', 'lingcod', 'mackerel', 'mahi', 'mahimahi', 'merluza', 'milkfish', 'monkfish', 'mullet',
             'octopu', 'perch', 'pike', 'pollock', 'pompano', 'octopus', 'redfish', 'rockfish', 'roughy', 'sablefish', 'salmon',
             'sashimi', 'scrod', 'shad', 'shark', 'shellfish', 'snapper', 'sockeye', 'sole', 'sturgeon', 'swordfish',
             'tentacle', 'tilapia', 'tobiko', 'trout',
             'tuna', 'turbot', 'turtle', 'unagi', 'whitefish', 'yellowfin', 'yellowtail'],
    'flatbread': ['appam', 'arepa', 'bakarkhani', 'bammy', 'bannock', 'barbari', 'bataw', 'bazlama', 'beiju', 'bhakri', 'bhatura',
                  'bindaeddeok', 'bolani', 'borlengo', 'bánh', 'casabe', 'chapati', 'chepati', 'chikkolee', 'dhebra', 'dosa',
                  'farl', 'flatbrød', 'flatkaka', 'focaccia', 'frybread', 'ftira', 'gurassa', 'gözleme', 'harsha', 'hoggan',
                  'injera', 'johnnycake', 'kaak', 'kachori', 'khebz', 'khubz', 'kulcha', 'lagana', 'lahoh', 'laobing', 'lavash', 'lefse',
                  'lepyoshka', 'luchi', 'malooga', 'markook', 'matnakash', 'matzah', 'matzo', 'murr', 'muufo', 'naan', 'ngome', 'oatcake',
                  'obi non', 'opłatek', 'paan', 'pappadam', 'paratha', 'parotta', 'pathiri', 'pesarattu', 'phulka', 'piadina', 'piaya',
                  'pissaladière', 'pita', 'podpłomyk', 'pogača', 'poli', 'posúch', 'pupusa', 'puri', 'părlenka', 'rieska', 'roti', 'rotti',
                  'sanchuisanda', 'sangak', 'semita', 'sheermal', 'shelpek', 'taftan', 'tigella', 'torta', 'tortilla', 'tunnbröd', 'yufka'],
    'flour': ['besan'],
    'flower': ['dandelion', 'hibiscu', 'hop', 'orchid', 'pansy', 'salsify', 'violet'],
    'fruit': ['boysenberry', 'breadfruit', 'citru', 'honeydew', 'jujube', 'kiwi', 'papaya', 'umeboshi', 'wolfberry', 'yuzu'],
    'gelatin': ['aspic'],
    'honey': ['abbamele'],
    'icecream': ['pop', 'popsicle', 'sherbet', 'sorbet', 'mochi'],
    'lettuce': ['iceberg'],
    'liqueur': ['bénédictine', 'cordial', 'kirschenliqueur', 'kirschwasser', 'schnapp'], 
    'liquor': ['absinthe', 'alcohol', 'grappa', 'mezcal', 'moonshine'],   
    'meat': ['asada', 'bacon', 'bear', 'beef', 'belly', 'bison', 'blade', 'blood', 'boar', 'bone', 'bonein',
             'brain', 'breast',
             'buffalo', 'burger', 'carne', 'carnita', 'char', 'chateaubriand', 'chicken', 'chop', 'chopmeat', 
             'chuck', 'coldcut', 'confit', 'cutlet', 'drummette', 'drumstick', 'duck', 'duckling',
             'eye', 'eyeofround', 'flank', 'foot', 'fowl', 'fryer',
             'game', 'giblet', 'gizzard', 'goat', 'goose', 'ham', 'hanger', 'hen', 'hock', 'iron', 
             'jerky', 'jowl', 'knuckle', 'lamb', 'lean', 'leg', 'liver', 
             'loin', 'marrow', 'meatball', 'mignon', 'mincemeat', 'moose', 'mutton', 'neck', 'nugget', 'oxtail', 
             'pheasant', 'pig', 'pork', 'porterhouse', 'poultry', 'pâté', 
             'quail', 'rabbit', 'rack', 'rib', 'riblet', 'roast', 'rooster', 'round', 'rump',
             'scallopini', 'shank', 'shoulder', 'sirloin', 'skirt', 'spam', 'squirrel', 'strip', 'suet',
             'tallow', 'tbone', 'tender', 'tenderloin', 'thigh',
             'tongue', 'topside', 'tripe', 'tritip', 'turkey', 'venison', 'wing', 'wingette'],
    'mushroom': ['cremini', 'maitake', 'matsutake', 'morel', 'porcini', 'portabello',
                 'shiitake', 'shimeji', 'truffle'],
    'mustard': ['dijon'],
    'noodle': ['capellini', 'fettuccine', 'hair', 'linguine', 'perciatelli', 'raman',
               'spaghetti', 'spaghettini', 'soba', 'vermicelli', 'udon'],
    'nut': ['acorn', 'almond', 'candlenut', 'cashew', 'chestnut', 'hazelnut',
            'macadamia', 'mongongo', 'peanut', 'pecan', 'pistachio', 'walnut'],
    'olive': ['kalamata', 'manzanilla'],
    'onion': ['vidalia'],
    'pasta': ['bowtie', 'cavatappi', 'cavatelli', 'corkscrew', 'ditalini', 'elbow', 
              'farfallini', 'fideo', 'fusilli', 'gemelli', 'macaroni', 
              'manicotti', 'orzo', 'pappardelle', 'penne', 'rigate', 'rotelle', 'rotini',
              'tagliatelle', 'tortellini', 'tubettini', 'wheel', 'ziti'],
    'paste': ['doubanjiang', 'duxelle', 'gochujang', 'membrillo',
              'tahini','ulek', 'wasabi', 'yuzukosho'], 
    'pastry': ['croissant', 'crumpet', 'doughnut', 'muffin', 'scone'],
    'pepper': ['aleppo', 'anaheim', 'ancho', 'arbol', 'bell', 'capsicum', 'cascabel', 'cayenne', 'chile', 
               'chilcostle', 'chipotle', 'fresno', 'guajillo', 
               'habanero', 'jalapeno', 'mulato', 'piquillo',
               'padron', 'pasilla', 'peperoncini', 'pimento', 'poblano',  'serrano', 'shishito'],    
    'potato': ['fingerling', 'gold', 'obrien', 'russet', 'yukon'],
    'rice': ['arborio', 'basmati', 'carnaroli', 'paella', 'poha', 'risotto'],
    'root': ['cassava', 'ginger', 'yucca'],
    'salsa': ['verde'],
    'sauce': ['adobo', 'aioli', 'alfredo', 'bechamel', 'chimichurri', 'demiglace', 'hoisin', 
              'glacé', 'hollandaise', 'marinara', 'mole',
              'passata', 'pati', 'pesto', 'remoulade', 'roux', 'sriracha', 'sweetandsour',
              'tamari', 'tartar', 'teriyaki', 'tzatziki', 'worcestershire'],
    'sausage': ['andouille', 'bologna', 'brat', 'bratwurst', 'capicola', 'chorizo', 'frank', 'frankfurter', 'hotdog',
                'kielbasa', 'knockwurst', 'link', 'liverwurst', 'merguez', 'pastrami', 'patty', 'salami', 'wiener'],
    'seasoning': ['ajwain', 'allspice', 'amchur', 'anise', 'annatto', 'asafoetida', 'bark', 'basil', 'berry',
                  'caraway', 'cardamom', 'chervil', 'chia', 'chicory',
                  'cilantro', 'cinnamon', 'clove', 'coriander', 'cumin', 'dill', 'extract',
                  'flavor', 'flavoring', 'flax', 'furikake', 'grainsofparadise',
                  'herb', 'jamaican', 'jerk', 'leaf',
                  'lemongras', 'licorice', 'menthe', 'mint', 'mitsuba', 'msg',
                  'nigella', 'nutmeg', 'oiloforange', 'oregano', 'paprika', 'parsley', 'pepita', 'peppermint',
                  'pimenton', 'pollen', 'poppy', 'powder', 'root', 'rosemary', 'rub', 'saffron', 'sage', 'seed', 'sesame',
                  'sorrel', 'spice', 'tarragon', 'tea', 'thread', 'thyme', 'togarashi',
                  'zaatar', 'zest', 'épice'],
    'seaweed': ['agar ', 'algae', 'arame', 'badderlock', 'bladderwrack', 'carola', 'cava', 'channelled wrack ',
                'chlorella', 'cochayuyo ', 'corticata', 'cottonii', 'dulse', 'edulis', 'eucheuma', 'fucales',
                'gelidiella', 'gim', 'gutweed', 'hijiki', 'hiromi', 'hiziki', 'hypnea', 'kelp', 'kombu', 'konbu',
                'laverbread ', 'moss', 'mozuku', 'nori', 'oarweed', 'ogonori', 'papillatus', 'sargassum', 'spinosum',
                'thongweed', 'wakame', 'wrack'],
    'shoot': ['bamboo'],
    'soda': ['colon'], # colon = get_lemma(cola)
    'squash': ['calabaza', 'mirliton', 'qua'],
    'sugar': ['turbinado'],
    'sweetener': ['erythritol', 'fructose', 'glucose', 'maltose', 'stevia', 'treacle'],
    'tea': ['assam', 'ginseng', 'lapsang', 'matcha', 'souchong'],
    'tofu': ['aburaage', 'seitan', 'yuba'],
    'vegetable': ['cob', 'fern', 'peapod'], 
    'wine': ['beaujolai', 'blanc', 'burgundy', 'cabernet', 'chardonnay', 'chianti', 'grigio', 'malbec', 'merlot',
             'moscato', 'muscadet', 'muscat', 'noir', 'prosecco', 'riesling', 'sangiovese', 'sangria',
             'sauvignon', 'shaoxing', 'shiraz', 'vermouth', 'zinfandel'],
    'yeast': ['poolish', 'rennet', 'starter']
}


# In[ ]:


stopwords = { # from spacy, minus a few manually
    'a', 'about', 'above', 'across', 'after', 'afterwards', 'again', 'against', 'all', 'almost', 'alone', 'along',
    'already', 'also', 'although', 'always', 'am', 'among', 'amongst', 'amount', 'an', 'and', 'another', 'any', 
    'anyhow', 'anyone', 'anything', 'anyway', 'anywhere', 'are', 'around', 'as', 'at', 'back', 'be', 'became',
    'because', 'become', 'becomes', 'becoming', 'been', 'before', 'beforehand', 'behind', 'being', 'below', 'beside',
    'besides', 'between', 'beyond', 'both', 'bottom', 'but', 'by', 'ca', 'call', 'can', 'cannot', 'could', 'did', 'do',
    'does', 'doing', 'done', 'down', 'due', 'during', 'each', 'eight', 'either', 'eleven', 'else', 'elsewhere', 'empty',
    'enough', 'even', 'ever', 'every', 'everyone', 'everything', 'everywhere', 'except', 'few', 'fifteen', 'fifty', 'first',
    'five', 'for', 'former', 'formerly', 'forty', 'four', 'from', 'front', 'full', 'further', 'get', 'give', 'go',
    'had', 'has', 'have', 'he', 'hence', 'her', 'here', 'hereafter', 'hereby', 'herein', 'hereupon', 
    'hers', 'herself', 'him', 'himself', 'his', 'how', 'however', 'hundred', 'i', 'if', 'in', 'indeed', 
    'into', 'is', 'it', 'its', 'itself', 'just', 'keep', 'last', 'latter', 'latterly', 'least', 'made',
    'make', 'many', 'may', 'me', 'meanwhile', 'might', 'mine', 'more', 'moreover', 'most', 'mostly', 'move',
    'much', 'must', 'my', 'myself', 'name', 'namely', 'neither', 'never', 'nevertheless', 'next', 'nine', 'nobody',
    'none', 'noone', 'nor', 'not', 'nothing', 'now', 'nowhere', 'of', 'off', 'often', 'on', 'once', 'one', 'only',
    'onto', 'or', 'other', 'others', 'otherwise', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'part', 'per',
    'perhaps', 'please', 'put', 'quite', 'rather', 're', 'really', 'regarding', 'same', 'say', 'see', 'seem',
    'seemed', 'seeming', 'seems', 'serious', 'several', 'she', 'should', 'show', 'side', 'since', 'six', 'sixty',
    'so', 'some', 'somehow', 'someone', 'something', 'sometime', 'sometimes', 'somewhere', 'still', 'such', 'take',
    'ten', 'than', 'that', 'the', 'their', 'them', 'themselves', 'then', 'thence', 'there', 'thereafter', 'thereby',
    'therefore', 'therein', 'thereupon', 'these', 'they', 'third', 'this', 'those', 'though', 'three', 'through',
    'throughout', 'thru', 'thus', 'to', 'together', 'too', 'top', 'toward', 'towards', 'twelve', 'twenty', 'two',
    'under', 'unless', 'until', 'up', 'upon', 'us', 'used', 'using', 'various', 'very', 'via', 'was', 'we', 'well',
    'were', 'what', 'whatever', 'when', 'whence', 'whenever', 'where', 'whereafter', 'whereas', 'whereby', 'wherein',
    'whereupon', 'wherever', 'whether', 'which', 'while', 'whither', 'who', 'whoever', 'whole', 'whom', 'whose',
    'why', 'will', 'with', 'within', 'without', 'would', 'yet', 'you', 'your', 'yours', 'yourself', 'yourselves'
}


# In[ ]:


# invert dict of {k1: v1, k2: v1, k3: v2} to {v1: [k1, k2], v2: k3}
def invert_dict_singles(orig):
    new = {}
    for k, v in orig.items():
        new[v] = new.get(v, [])
        new[v].append(k)
    return new

# invert dict of {k1: [v1, v2], k2: [v3]} to {v1: k1, v2: k1, v3: k2}
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


# phrase regex cleaning
char_pattern = re.compile(r'[®™’%!/\-\'\.\(\)]')
brand_char_pattern = re.compile(r'\d+')
parenthetical_pattern = re.compile(r'\(.*\)')
of_pattern = re.compile(r'(\w) of (?:the )?')
low_pattern = re.compile(r'\b(?:less|light|low|no|non|reduced) ')
free_pattern = re.compile(r' free\b')
high_pattern = re.compile(r'\b(?:full|high) ')
heads_to_sub = invert_dict_lists(head_subs)
supertype_appends = invert_dict_lists(supertypes)
brands_to_sub = invert_dict_lists(brands_to_sub_lists)
# WARNING: remove brands in reverse alphabetical order
brand_names = sorted(brands_to_pull | set(brands_to_sub.keys()), reverse=True)
compiled_brands = re.compile(r'(\b' + r'\b)|(\b'.join(brand_names) + r'\b)')
compiled_spelling = []
for k, v in sorted(special_spelling.items()):
    k = re.compile(r'(\b)' + k + r'(\b)')
    v = r'\1' + v + r'\2'
    compiled_spelling.append((k, v))
compiled_exceptions = []
for k, v in sorted(exceptions.items()):
    k = re.compile(r'(\b)' + k + r'(\b)')
    v = r'\1' + v + r'\2'
    compiled_exceptions.append((k, v))


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


# In[ ]:


lemmatize = Lemmatizer(LEMMA_INDEX, LEMMA_EXC, LEMMA_RULES)

@memoize
def get_lemma(word):
    return lemmatize(word, u'NOUN')[-1]


# In[ ]:


def flatten(ings):
    flat = []
    for ing in ings:
        flat.extend(ing.mods + ing.brands + ing.langs)
    return flat


# In[ ]:


# WARNING: don't overwrite the existing manually tweaked dictionary!!!
def make_freq_dict(word_counts):
    lines = []
    for word, freq in sorted(word_counts.items(), key=itemgetter(1), reverse=True):
        if freq > 4 and len(word) > 3:
            lines.append('{0} {1}\n'.format(word, freq))
    with open('data/new_frequency_dictionary.txt', 'w+', encoding='utf-8') as file:
        file.write(lines)

