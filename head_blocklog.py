#!/usr/bin/env python3

import argparse
import base64
import bz2
import datetime
import gzip
import hashlib
import json
import shutil
import struct
import sys
import tempfile

from steem_watch import steem_api

import tornado
import tornado.gen

async def main(argv, io_loop=None):
    parser = argparse.ArgumentParser(description="Print size/sha256sum of block log")
    parser.add_argument("-s", "--server", dest="server", metavar="WEBSOCKET_URL", help="Specify API server")

    args = parser.parse_args(argv[1:])

    node = steem_api.ApiNode(io_loop=io_loop, websocket_url=args.server)
    node.start()
    await node.wait_for_connection()

    db_api = node.get_api("database_api")
    raw_block_api = node.get_api("raw_block_api")

    next_block_num = 1
    last_date = ""
    hasher = hashlib.sha256()
    total_size = 0

    last_lib = -1

    while True:
        dgpo = await db_api.get_dynamic_global_properties()
        lib = dgpo["last_irreversible_block_num"]
        if lib == last_lib:
            break
        last_lib = lib
        while (lib > 1) and (next_block_num < lib):
            block = await raw_block_api.get_raw_block( block_num=next_block_num )
            bdata = base64.b64decode(block["raw_block"])
            bdate = block["timestamp"][:10]
            if bdate != last_date:
                print( bdate, total_size, hasher.hexdigest() )
                sys.stdout.flush()
                last_date = bdate
            offset = total_size
            total_size += len(bdata) + 8
            hasher.update(bdata)
            hasher.update(struct.pack("<Q", offset))
            next_block_num += 1
    return

def sys_main():
    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.run_sync(lambda : main(sys.argv, io_loop=io_loop))

if __name__ == "__main__":
    sys_main()
