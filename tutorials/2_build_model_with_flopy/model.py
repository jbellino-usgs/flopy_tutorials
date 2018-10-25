from collections import OrderedDict

# define model dimensions
nlay = 1
nrow = 275
ncol = 182
delx, dely = 2500., 2500.
ul = (999987.84, 10817376.82)
ll = (999987.84, 10129876.82)
(xul, yul) = ul
(xll, yll) = ll
units = 'feet'
rotation = 0.

# define grid projection information
proj4_items_dict = OrderedDict([('proj', 'utm'),
                                ('zone', '17 +north'),
                                ('ellps', 'GRS80'),
                                ('towgs84', '0,0,0,0,0,0,0'),
                                ('units', 'ft'),
                                ('no_defs', '')])
proj4_items = list(['+{}={}'.format(k, v) for k, v in proj4_items_dict.items() if v != ''])
proj4_items.extend(list(['+{}'.format(k) for k, v in proj4_items_dict.items() if v == '']))
proj4_str = ' '.join(proj4_items)
