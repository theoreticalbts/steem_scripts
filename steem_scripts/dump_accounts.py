#!/usr/bin/env python3

import argparse
import base64
import bz2
import datetime
import gzip
import json
import shutil
import sys
import tempfile
import time

from steem_watch import steem_api

import tornado
import tornado.gen

async def main(argv, io_loop=None):
    parser = argparse.ArgumentParser(description="Create bootstrap files for Steem")
    parser.add_argument("-s", "--server", dest="server", metavar="WEBSOCKET_URL", help="Specify API server")

    args = parser.parse_args(argv[1:])

    node = steem_api.ApiNode(io_loop=io_loop, websocket_url=args.server)
    node.start()
    await node.wait_for_connection()

    try:
        await print_accounts(node)
    except BrokenPipeError:
        pass

async def print_accounts(node):
    db_api = node.get_api("database_api")
    last_account_name = ""
    names = set()
    while True:
        new_names = await node.lookup_accounts(last_account_name, 1000)
        n = len(names)
        names.update(new_names)
        if len(names) == n:
            break
        last_account_name = new_names[-1]
    names = sorted(names)
    for k, v in itertools.groupby(enumerate(u), lambda e : e[0]//5):
        query_names = [name for i, name in v]
        accounts = await node.lookup_account_names(query_names)
        for a in accounts:
            json.dump(a, sys.stdout, separators=(",", ":"), sort_keys=True)
            sys.stdout.write("\n")
    sys.stdout.flush()
    return
