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
    parser.add_argument("-x", "--exit", dest="exit", action="store_true", help="Exit when fully caught up to server")

    args = parser.parse_args(argv[1:])

    node = steem_api.ApiNode(io_loop=io_loop, websocket_url=args.server)
    node.start()
    await node.wait_for_connection()

    try:
        await print_blocks(node, exit_on_finish=args.exit)
    except BrokenPipeError:
        pass

async def print_blocks(node, exit_on_finish=False):
    db_api = node.get_api("database_api")
    raw_block_api = node.get_api("raw_block_api")

    last_printed = 0
    while True:
        dgpo = await db_api.get_dynamic_global_properties()
        lib = dgpo["last_irreversible_block_num"]
        printed_this_time = 0
        while lib > last_printed:
            block_num = last_printed + 1
            block = await raw_block_api.get_raw_block(block_num=block_num)
            sys.stdout.write(block["raw_block"])
            sys.stdout.write("\n")
            last_printed = block_num
            printed_this_time += 1
        if printed_this_time > 0:
            sys.stdout.flush()
        else:
            if exit_on_finish:
                blockchain_now = datetime.datetime.strptime(dgpo["head_block_time"], "%Y-%m-%dT%H:%M:%S")
                realtime_threshold = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
                is_realtime = (blockchain_now >= realtime_threshold)
                if is_realtime:
                    break
            await tornado.gen.sleep(3)

def sys_main():
    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.run_sync(lambda : main(sys.argv, io_loop=io_loop))

if __name__ == "__main__":
    sys_main()
