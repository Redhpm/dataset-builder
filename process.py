#!python
import random as rd
import binascii
import argparse
import r2pipe
import json
import csv
import os

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--extract', action='store_true', required=False, help='Enables extraction.')
parser.add_argument('--merge', action='store_true', required=False, help='Enables merge to binary blob.')
args = parser.parse_args()


with open('./config.json', 'r') as f:
    config = json.load(f)

VEC_LEN = config['vec_len'] #With 1 byte reserved for class ID
MIN_LEN = config['min_len']
TRAIN_PERCENT = config['train_proportion']

def normalize_hexpairs(hexpairs):
    '''
    Truncates or pads hexpairs to VEC_LEN.
    '''
    if (l := len(hexpairs)) >= 2 * VEC_LEN:
        return hexpairs[:VEC_LEN] + hexpairs[l - VEC_LEN:]
    else:
        return hexpairs[:l // 2] + '00'*(VEC_LEN - (l // 2)) + hexpairs[l // 2:]

def extract_functions_hexpairs_normalized(file_name, outfile):
    '''
    Extracts hexpairs from function of file.
    Minimum MIN_LEN.
    '''
    r2 = r2pipe.open(file_name, ["-2"])

    r2.cmd('aaf')
    imports = r2.cmdj("iij")
    def try_key(d, k):
        try:
            return d[k]
        except KeyError:
            return -1
        
    imports_plt = [try_key(i, 'plt') for i in imports]
    fs = r2.cmdj('aflj')

    f_data = []
    for f in fs:
        if f['offset'] not in imports_plt:
            hexpairs = r2.cmd(f'p8f @ {f["offset"]}').strip()
            if len(hexpairs) > 2 * MIN_LEN:
                f_data.append([f['name'], normalize_hexpairs(hexpairs)])
    
    with open(outfile, 'w') as fd:
        writer = csv.writer(fd, delimiter=",", quotechar='"',
                            quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(['name', 'hexpairs'])
        writer.writerows(f_data)

def extract_functions_all(directory, outdir):
    '''
    Extracts function for all binaries in dataset directory.
    '''
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    for fn in os.walk(directory):
        if not fn[1]:
            for name in fn[2]:
                extract_functions_hexpairs_normalized(fn[0]+ '/' + name, outdir + '/' + name.split('.bin')[0] + '.csv')
                print(f'Extracted : {name}.')

def merge(directory, outtrain, outtest, classes):
    '''
    Merges all function extracted into 2 binary blobs, for training and testing.
    '''
    with open(outtrain, 'wb') as ftrain:
        with open(outtest, 'wb') as ftest:
            for fn in os.listdir(directory):
                with open(directory + '/' + fn, newline='') as csv_f:
                    reader = csv.reader(csv_f, delimiter=",", quotechar='"',
                                quoting=csv.QUOTE_NONNUMERIC)
                    for row in reader:
                        if row[0] != 'name':
                            if rd.random() < TRAIN_PERCENT:
                                ftrain.write(classes.index(fn.split('.')[0].split('_')[1])).to_bytes(1, 'big')
                                ftrain.write(binascii.unhexlify(row[1].strip()))
                            else:
                                ftest.write(classes.index(fn.split('.')[0].split('_')[1])).to_bytes(1, 'big')
                                ftest.write(binascii.unhexlify(row[1].strip()))

if args.extract:
    extract_functions_all(config['bins_dir'], config['csv_dir'])
if args.merge:
    merge(config['csv_dir'], config['train_blob'], config['test_blob'], config['classes'])