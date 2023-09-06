#!python
from jinja2 import Template
import os
import json
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--name', default='dataset', help='Name of the final image.')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--all', action='store_true', help='Builds all the projects.')
group.add_argument('--list', nargs='+', help='Only builds specified projects.')
parser.add_argument('--no-build', action='store_true', required=False, help='Disables docker build.')
args = parser.parse_args()

with open('./config.json', 'r') as f:
    config = json.load(f)

with open('./flags.txt', 'w') as f:
    f.write('\n'.join(config['classes']))

project_dir = config['project_dir']
projects = []

if args.all:
    for p in os.listdir(project_dir):
        with open(f'{project_dir}/{p}', 'r') as f:
            projects.append(json.load(f))
else:
    for p in args.list:
        with open(f'{project_dir}/{p}.json', 'r') as f:
            projects.append(json.load(f))

with open('Dockerfile.j2', 'r') as f:
    template = Template(f.read())

with open('Dockerfile', 'w') as f:
    f.write(template.render(projects=projects))

if not args.no_build:
    os.system(f'sudo docker build . -t {args.name}')
else:
    print('Docker build skipped.')