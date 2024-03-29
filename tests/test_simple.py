import os
import shutil
from argparse import Namespace
from pathlib import Path

import pymongo
import pytest
from bifrost_enterobase import launcher
from bifrostlib import common, database_interface, datahandling
from bifrostlib.datahandling import (Component, ComponentReference, Run,
                                     RunReference, Sample, SampleReference)


@pytest.fixture
def test_connection():
    assert datahandling.has_a_database_connection()
    assert (
        "TEST" in os.environ["BIFROST_DB_KEY"].upper()
    )  # A very basic piece of protection ensuring the word test is in the DB


def test_cwd():
    bifrost_install_dir = os.environ["BIFROST_INSTALL_DIR"]
    print(f"bifrost cwd: {bifrost_install_dir}")
    assert bifrost_install_dir != ""


class TestBifrostEnterobase:
    component_name = "enterobase__v1.1.8"
    bifrost_install_dir = Path(os.environ['BIFROST_INSTALL_DIR'])
    bifrost_config_and_data_path = bifrost_install_dir/"bifrost/test_data"
    current_dir = os.getcwd()
    test_dir = bifrost_config_and_data_path/"output/test__enterobase/"
    # This class stores the paths needed for this tests

    r1 = str(bifrost_config_and_data_path/"samples/SRR2094561_1.fastq.gz")
    r2 = str(bifrost_config_and_data_path/"samples/SRR2094561_2.fastq.gz")

    json_entries = [
        {
            "_id": {"$oid": "000000000000000000000001"},
            "display_name": "SRR2094561",
            "name": "SRR2094561",
            "components": [],
            "categories": {
                "paired_reads": {"summary": {"data": [r1, r2]}},
                "mlst": {"summary": {"sequence_type": {"senterica": "34"}}},
                "species_detection": {"summary": {"species": "Salmonella enterica"}},
            },
        }
    ]
    bson_entries = [database_interface.json_to_bson(i) for i in json_entries]

    @classmethod
    def setup_class(cls):
        with pymongo.MongoClient(os.environ["BIFROST_DB_KEY"]) as client:
            db = client.get_database()
            cls.clear_all_collections(db)
            col = db["samples"]
            col.insert_many(cls.bson_entries)
            launcher.initialize()
            os.chdir(cls.bifrost_install_dir)

    @classmethod
    def teardown_class(cls):
        client = pymongo.MongoClient(os.environ["BIFROST_DB_KEY"])
        db = client.get_database()
        #cls.clear_all_collections(db)

    @staticmethod
    def clear_all_collections(db):
        db.drop_collection("components")
        db.drop_collection("hosts")
        db.drop_collection("run_components")
        db.drop_collection("runs")
        db.drop_collection("sample_components")
        db.drop_collection("samples")

    def test_info(self):
        launcher.parse_and_run(["--info"])

    def test_help(self):
        with pytest.raises(SystemExit):
            launcher.parse_and_run(["--help"])

    def test_pipeline(self):
        print(self.test_dir)
        if os.path.isdir(self.test_dir):
            shutil.rmtree(self.test_dir)

        os.mkdir(self.test_dir)
        test_args = [
            "--sample_name", "SRR2094561",
            "--outdir", str(self.test_dir)
        ]
        launcher.main(args=test_args)
        assert (self.test_dir/self.component_name/"datadump_complete").exists()
        #shutil.rmtree(self.test_dir)
        #assert not os.path.isdir(f"{self.test_dir}/{self.component_name}")

    def test_db_output(self):
        with pymongo.MongoClient(os.environ["BIFROST_DB_KEY"]) as client:
            print(f"databases: {client.list_database_names()}")
            db = client.get_database()
            print(f"collections: {db.list_collection_names()}")
            sample = db["samples"]
            sample_data = sample.find_one({})
            print(f"sample_data: {sample_data}")
            assert len(sample_data) > 1
            assert (
                sample_data["categories"]["serotype"]["summary"]["serotype"]
                == "Typhimurium monophasic"
            )
