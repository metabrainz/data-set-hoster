#!/usr/bin/env python3

import sys
import collections
import uuid

import pybktree
import psycopg2
from psycopg2.extras import register_uuid, DictCursor

from Levenshtein import distance
import config

USE_LIMITED_DATA = True

ArtistCreditNode = collections.namedtuple('ArtistCreditNode', 'artist_credit_name artist_credit_id')
RecordingNode = collections.namedtuple('RecordingNode', 'recording_name recording_id artist_credit_id')

def create_artist_credit_tree():

    def node_distance(x, y):
        return distance(x.artist_credit_name, y.artist_credit_name)

    tree = pybktree.BKTree(node_distance, [])

    with psycopg2.connect(config.DB_CONNECT_MB) as conn:
        with conn.cursor(cursor_factory=DictCursor) as curs:
            print("execute query")
            query = """SELECT DISTINCT artist_credit_id, artist_credit_name
                         FROM mapping.recording_artist_credit_pairs"""
            if USE_LIMITED_DATA:
                query += " LIMIT 100000"
            curs.execute(query)
            count = 0
            print("build artist index")
            while True:
                row = curs.fetchone()
                if not row:
                    break

                tree.add(ArtistCreditNode(row['artist_credit_name'], row['artist_credit_id']))
                count += 1
                if count % 500000 == 0:
                    print("  %s" % count)

    return tree


def create_recording_tree():

    def node_distance(x, y):
        return distance(x.recording_name, y.recording_name)

    tree = pybktree.BKTree(node_distance, [])

    with psycopg2.connect(config.DB_CONNECT_MB) as conn:
        with conn.cursor(cursor_factory=DictCursor) as curs:
            print("execute query")
            query = """SELECT recording_name, recording_id, artist_credit_id
                         FROM mapping.recording_artist_credit_pairs"""
            if USE_LIMITED_DATA:
                query += " LIMIT 500000"
            curs.execute(query)
            count = 0
            print("build recording index")
            while True:
                row = curs.fetchone()
                if not row:
                    break

                tree.add(RecordingNode(row['recording_name'], row['recording_id'], row['artist_credit_id']))
                count += 1
                if count % 500000 == 0:
                    print("  %s" % count)

    return tree


def interactive_artist_queries(artist_tree):

    while True:
        f = input("search> ")
        if not f:
            break

        node = ArtistCreditNode(f.strip().lower(), 0)
        for score, node in artist_tree.find(node, 3)[:25]:
            print("%d %-30s" % (score, node.artist_credit_name[:29]))
        print()


def interactive_recording_queries(recording_tree):

    while True:
        f = input("search> ")
        if not f:
            break

        node = RecordingNode(f.strip().lower(), 0, 0)
        for score, node in recording_tree.find(node, 5)[:25]:
            print("%d %-30s %d" % (score, node.recording_name[:29], node.artist_credit_id))
        print()


def match(artist_tree, recording_tree, recording_msids):

    with psycopg2.connect(config.DB_CONNECT_MSB) as conn:
        with conn.cursor(cursor_factory=DictCursor) as curs:
            register_uuid(curs)
            query = """SELECT lower(unaccent(rj.data->>'artist'::TEXT)) AS artist_name, artist as artist_msid,
                              lower(unaccent(rj.data->>'title'::TEXT)) AS recording_name, r.gid AS recording_msid
                         FROM recording r
                         JOIN recording_json rj ON r.data = rj.id
              LEFT OUTER JOIN release rl ON r.release = rl.gid
                        WHERE r.gid IN %s"""
            curs.execute(query, (tuple(recording_msids),))
            while True:
                row = curs.fetchone()
                if not row:
                    break

                a_node = ArtistCreditNode(row['artist_name'].strip().lower(), 0)
                artists = artist_tree.find(a_node, 3)
                artist_credit_ids = sorted([ a.artist_credit_id for score, a in artists ])
                artist_credit_index = {}
                for score, artist in artists:
                    print(artist)
                    artist_credit_index[artist.artist_credit_id] = artist.artist_credit_name

                r_node = RecordingNode(row['recording_name'].strip().lower(), 0, 0)
                recordings = recording_tree.find(r_node, 5)
                for score, recording in recordings:
                    if recording.artist_credit_id in artist_credit_ids:
                        print("%-60s %-30s" % (row['recording_name'][:59], row['artist_name'][:29]))
                        print("%-60s %-30s" % (recording.recording_name[:59], artist_credit_index[recording.artist_credit_id][:29]))
                        print()


if __name__ == "__main__":
    artist_tree = create_artist_credit_tree()
    recording_tree = create_recording_tree()
    recording_msids = []
    with open(sys.argv[1], "r") as unmatched:
        while True:
            line = unmatched.readline()
            if not line:
                break

            recording_msids.append(uuid.UUID(line.strip()))

    match(artist_tree, recording_tree, recording_msids)
