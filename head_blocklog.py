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

def parse_time_interval(interval):
    time_units = {"s" : 1, "m" : 60, "h" : 60*60, "d" : 24*60*60}

    if interval[-1] in time_units:
        result = int(interval[:-1]) * time_units[interval[-1]]
    else:
        result = int(interval)
    return result

async def main(argv, io_loop=None):
    parser = argparse.ArgumentParser(description="Print size/sha256sum of block log")
    parser.add_argument("-s", "--server", dest="server", metavar="WEBSOCKET_URL", help="Specify API server")
    parser.add_argument("-i", "--interval", dest="interval", metavar="SECONDS", default="1d", help="How long between saves (suffixes supported: s,m,h,d)")
    parser.add_argument("-p", "--poll", dest="poll", metavar="SECONDS", default="0", help="Persist, polling for new blocks (0/omitted quits without polling)")

    args = parser.parse_args(argv[1:])
    print_interval = parse_time_interval(args.interval)
    print_interval_td = datetime.timedelta(seconds=print_interval)
    poll_interval = parse_time_interval(args.interval)
    epoch = datetime.datetime(1970, 1, 1)

    node = steem_api.ApiNode(io_loop=io_loop, websocket_url=args.server)
    node.start()
    await node.wait_for_connection()

    db_api = node.get_api("database_api")
    raw_block_api = node.get_api("raw_block_api")

    next_block_num = 1
    last_inum = 0
    hasher = hashlib.sha256()
    total_size = 0

    last_lib = -1

    while True:
        dgpo = await db_api.get_dynamic_global_properties()
        lib = dgpo["last_irreversible_block_num"]
        if lib == last_lib:
            if poll_interval == 0:
                break
            else:
                await tornado.gen.sleep(poll_interval)
                continue
        last_lib = lib
        while (lib > 1) and (next_block_num < lib):
            block = await raw_block_api.get_raw_block( block_num=next_block_num )
            bdata = base64.b64decode(block["raw_block"])
            timestamp = datetime.datetime.strptime( block["timestamp"], "%Y-%m-%dT%H:%M:%S" )
            # inum : Interval number
            binum = (timestamp - epoch) // print_interval_td
            if binum != last_inum:
                istart = ( epoch + binum * print_interval_td ).strftime("%Y-%m-%dT%H:%M:%S")
                print( istart, next_block_num-1, total_size, hasher.hexdigest() )
                sys.stdout.flush()
                last_inum = binum
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
