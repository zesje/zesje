""" Module that contains helpers for yaml operations """

import re
from collections import OrderedDict

import pandas
import yaml


def parse(yml):
    """ Get the important parameters from a yaml """

    version = yml['protocol_version']
    exam_name = yml['name']
    widget_data = yml['widgets']


    if version == 0:
        widgets = pandas.DataFrame(widget_data).T
        widgets.index.name = 'name'
        if widgets.values.dtype == object:
            # probably the yaml has not been processed
            raise RuntimeError('Widget data must be numerical')
        qr = widgets[widgets.index.str.contains('qrcode')]
        widgets = widgets[~widgets.index.str.contains('qrcode')]
    elif version == 1:

        def normalize_widgets(wid):
            # widgets are a *list* with fields 'name' and 'data.
            # In version 0 this was a dictionary (i.e. unordered), now it is a
            # list so we can construct an OrderedDict and preserves the ordering.
            # This is important if we want to re-upload and diff the yaml
            # and there are changes to widget names/data.
            wid = OrderedDict((str(w['name']), w['data']) for w in wid)
            df = pandas.DataFrame(wid).T
            df.index.name = 'name'
            return df

        qr = normalize_widgets(filter(lambda d: 'qrcode' in str(d['name']), widget_data))
        widgets = normalize_widgets(filter(lambda d: 'qrcode' not in str(d['name']), widget_data))
    else:
        raise RuntimeError('Version {} not supported'.format(version))

    return version, exam_name, qr, widgets


def normalize_coords(value):
    """Convert latex-generated coordinates into inches.

    Assumes that latex produces output of form "1234567+ 7654321".
    """
    if not isinstance(value, str):
        return value

    a, sign, b = re.match(r'(\d+) *([-+]) *(\d+)', value).groups()
    value = int(a) + int(b) * (-1 if sign=='-' else 1)
    return round(value/2**16/72, 5)


def load(yml):
    """ Read yaml from string and cleans it """


    """Clean up the widgets in the raw yaml from the exam latex compilation.

    We must both perform an arithmetic operation, and convert the units to
    points.
    """
    yml = yaml.safe_load(yml)

    version = yml['protocol_version']
    if version == 0:
    # Eval is here because we cannot do automatic addition in latex.
        clean_widgets = {name: {key: (normalize_coords(value)
                                    if key != 'page' else value)
                                for key, value in entries.items()}
                        for name, entries in yml['widgets'].items()}
    elif version == 1:
        clean_widgets = [
            {'name': entries['name'],
            'data': {key: (normalize_coords(value)
                            if key not in  ('page', 'name') else value)
                    for key, value in entries['data'].items()}
            }
            for entries in yml['widgets']
        ]
    else:
        raise RuntimeError('YAML version {} is not supported'.format(version))

    return dict(
        name=yml['name'],
        protocol_version=yml['protocol_version'],
        widgets=clean_widgets,
    )


def read(filename):
    """ Read yaml from disk """
    with open(filename) as f:
        return yaml.safe_load(f)

def save(yml, path):
    """ save yaml to disk """
    print("Saving " + path)
    try:
        with open(path, 'w') as f:
            f.write(yaml.safe_dump(yml, default_flow_style=False))
    except Exception:
        print("Failed to save " + path)
