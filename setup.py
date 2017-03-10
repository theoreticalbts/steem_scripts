from setuptools import setup

setup(
    name="steem_scripts",
    version="0.0.1.dev1",
    packages=["steem_scripts"],
    license="MIT",
    long_description=open("README.md").read(),
    entry_points={
        "console_scripts" :
        [
            "b64_dump_blocks = steem_scripts.b64_dump_blocks:sys_main",
            "head_blocklog = steem_scripts.head_blocklog:sys_main",
        ]
    },
    install_requires=[
        "tornado",
        "steem_watch",
        ],
)
