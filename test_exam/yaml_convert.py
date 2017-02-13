import argparse
import yaml

def main():
    parser = argparse.ArgumentParser(description='Clean up messy '
                                     'latex-generated yaml.')
    parser.add_argument('filename', type=str,
                        help='file to cleanup')
    filename = parser.parse_args().filename
    with open(filename) as f:
        exam_data = yaml.load(f)

    widgets = exam_data['widgets']

    def sp_to_points(value):
        return round(value/2**16/72, 5)

    # Eval is here because we cannot do automatic addition in latex.
    widgets = {name: {key: (sp_to_points(eval(value))
                            if key != 'page' else value)
                      for key, value in entries.items()}
               for name, entries in widgets.items()}
    exam_data['widgets'] = widgets
    with open(filename, 'w') as f:
        yaml.dump(exam_data, f)

if __name__ == '__main__':
    main()
