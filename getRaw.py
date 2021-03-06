import cProfile
import pstats
from time import time
from os import path, remove

import argparse
from imposm.parser import OSMParser
import json
import codecs

THRESHOLD = 50

def prep_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'source',
        help='Source file to parse (.pbf, .osm.bz2, or .osm)')
    parser.add_argument(
        '--profile',
        action='store_true')
    return parser

def nodeTags(nodes):
    for id, tags, coords in nodes:
        takeTags(tags)

def wayTags(ways):
    for id, tags, refs in ways:
        takeTags(tags)

def tag_filter(tags):
    if 'name' in tags:
        for key in tags.keys():
            if key not in ['amenity', 'shop', 'name']:
                del tags[key]

def takeTags(tags):
    # too many lookups?
    if 'name' in tags:
        for key in tags.keys():
            if key != 'name':
                fullName = key + '/' + tags[key] + '|' + tags['name']
                if fullName not in counts:
                    counts[fullName] = 1
                counts[fullName] += 1
                length = len(counts)
                if length > 1000000:
                    # will we ever have more than a million items > 5?
                    # the correct way would be to do some type of distribution and drop the bottom x%
                    cleanup(length)

def cleanup(length):
    copy = counts.copy()
    for key in copy:
        if counts[key] < 5:
            del counts[key]

def done():
    out = {}
    for key in counts:
        if counts[key] > THRESHOLD:
            out[key] = counts[key]
    write(out)

def write(out):
    if path.isfile(args['output']):
        remove(args['output'])

    outfile = codecs.open(args['output'], 'w', 'utf-8')
    json.dump(
        out,
        outfile,
        sort_keys=True,
        indent=4,
        separators=(',', ': '),
        ensure_ascii=False
    )

args = vars(prep_args().parse_args())
args['output'] = 'topNames.json'

if args['profile']:
    print args

if __name__ == '__main__':
    if args['profile']:
        prW = cProfile.Profile()
        prW.enable()

    start = time()
    print 'start ' + str(start)
    counts = {}

    p = OSMParser(
        ways_tag_filter=tag_filter,
        nodes_tag_filter=tag_filter,
        ways_callback=wayTags,
        nodes_callback=nodeTags)

    p.parse(args['source'])
    done()
    end = time()
    print 'end: ' + str(end)
    print 'duration: ' + str(round(end - start)) + ' seconds'

if args['profile']:
    prW.disable()
    ps = pstats.Stats(prW)
    ps.sort_stats('time')
    a = ps.print_stats(20)
