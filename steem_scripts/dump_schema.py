#!/usr/bin/env python3

import json

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

    db_api = node.get_api("database_api")
    json_schema = await db_api.get_schema()
    schema = json.loads(json_schema)
    print(json.dumps(schema, indent=1, sort_keys=True))

def sys_main():
    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.run_sync(lambda : main(sys.argv, io_loop=io_loop))

if __name__ == "__main__":
    sys_main()

