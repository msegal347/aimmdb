import os
import sys
from os import path

from setuptools import setup, find_packages


here = path.abspath(path.dirname(__file__))

share_aimmdb = os.path.join(here, "share", "aimmdb")


def get_data_files():
    """Get data files in share/aimmdb"""

    data_files = []
    for (d, _dirs, filenames) in os.walk(share_aimmdb):
        rel_d = os.path.relpath(d, here)
        data_files.append((rel_d, [os.path.join(rel_d, f) for f in filenames]))
    return data_files


setup(
    name="aimmdb",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "tiled[all]",
        "pymongo",
        "pyarrow",
        "psycopg2-binary",
        "httpx",
        "strawberry-graphql[fastapi]",
        "h5py",
        "msgpack",
        "mongomock",
    ],
    python_requires="~=3.9",
    entry_points={
        "tiled.structure_client": [
            "MongoAdapter = aimmdb.client:MongoCatalog",
            "AIMMCatalog = aimmdb.client:AIMMCatalog",
            "XAS_TEY = aimmdb.client:XASClient",
            "XAS_TFY = aimmdb.client:XASClient",
            "XAS_trans = aimmdb.client:XASClient",
        ],
    },
    data_files=get_data_files(),
    package_data={"aimmdb": ["data/*"]},
)
