#!/usr/bin/env python3

import os
import argparse
import subprocess
import sys
import time
from yaml import safe_load


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("ST", help="ST to lookup in enterobase")
    parser.add_argument(
        "--id", help="Add this if you want strain ID in output", default="NA"
    )
    parser.add_argument("--stfile", help="Yaml file with serotype counts pr ST")
    return parser.parse_args()


def get_token(address):
    response = safe_load(subprocess.check_output(["curl", address]))
    token = response["api_token"]
    return token


def get_serotype(token, ST):
    address = "https://enterobase.warwick.ac.uk/api/v2.0/senterica/MLST_Achtman/sts?st_id={}&sts?show_alleles=true&limit=5".format(
        ST
    )
    cmd = [
        "curl",
        "-X",
        "GET",
        "--header",
        "Accept: application/json",
        "--user",
        token + ":",
        address,
    ]
    response = subprocess.check_output(cmd).decode()
    wait = 1
    while not "STs" in response and wait < 1000:
        print("Failed\tEnterobase_reply:\n{}".format(response), file=sys.stderr)
        time.sleep(wait)
        wait *= 2
        response = subprocess.check_output(cmd).decode()
    response = safe_load(response)
    try:
        serotypes = response["STs"][0]["info"]["predict"]["serotype"]
    except (IndexError, KeyError):
        serotypes = []
    result = []
    for i in range(2):
        try:
            result.extend(map(str, serotypes[i]))
        except IndexError:
            result.extend(("Not found", "0"))
    return result


def get_serotype_from_enterobase(ST):
    ENTEROBASE_USERNAME = os.environ.get("ENTEROBASE_USERNAME")
    ENTEROBASE_PASSWORD = os.environ.get("ENTEROBASE_PASSWORD")
    ENTEROBASE_SERVER = os.environ.get("ENTEROBASE_SERVER")

    address = "%s/api/v2.0/login?username=%s&password=%s" % (
        ENTEROBASE_SERVER,
        ENTEROBASE_USERNAME,
        ENTEROBASE_PASSWORD,
    )
    token = get_token(address)
    result = get_serotype(token, ST)
    return result


def load_json_file(stfile):
    serotypes = safe_load(open(stfile, encoding="utf-8"))
    return serotypes


def data_reliable(serotypes):
    most_abundant_count = int(serotypes[1])
    second_most_abundant_count = int(serotypes[3])
    if most_abundant_count > 3 and most_abundant_count > 2 * second_most_abundant_count:
        return True
    else:
        return False


def get_serotype_from_file(ST, stfile):
    cache = load_json_file(stfile)
    serotypes = sorted(
        cache[str(ST)].items(), key=lambda element: element[1], reverse=True
    )
    result = []
    for i in range(2):
        try:
            result.extend(map(str, serotypes[i]))
        except IndexError:
            result.extend(("Not found", "0"))
    if data_reliable(result):
        return result
    else:
        return None


if __name__ == "__main__":
    args = get_args()
    result = None
    if args.stfile:
        result = get_serotype_from_file(args.ST, args.stfile)
    if result is None:
        result = get_serotype_from_enterobase(args.ST)
    print(f"{args.id}\t{args.ST}" + "\t" + "\t".join(result))
