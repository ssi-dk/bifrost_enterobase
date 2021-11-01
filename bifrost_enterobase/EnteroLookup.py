#!/usr/bin/env python3

import os
import argparse
import subprocess
#import re
import sys
#from urllib2 import HTTPError
#import urllib2
#import base64
#import json
import time
from yaml import safe_load
from pprint import pprint

def get_args():
	parser = argparse.ArgumentParser(
		description='')
	parser.add_argument("ST", help="ST to lookup in enterobase")
	parser.add_argument("--id", help= "Add this if you want strain ID in output", default="NA" )
	parser.add_argument("--stfile", help= "Yaml file with serotype counts pr ST")
	return parser.parse_args()

def get_token(address):
	response = safe_load(subprocess.check_output(["curl",address]))
	if "api_token" in response:
		token = response["api_token"]
	else:
		token="eyJhbGciOiJIUzI1NiIsImV4cCI6MTU0MDkyMzQ4MywiaWF0IjoxNTI1MTU1NDgzfQ.eyJ1c2VybmFtZSI6Ik1hb3MiLCJjaXR5IjoiQ29wZW5oYWdlbiIsImNvbmZpcm1lZCI6MSwiYWxsb3dlZF9zY2hlbWVzIjoiY2dNTFNUX3YyIiwiZmlyc3RuYW1lIjoiTWFyayIsImFwaV9hY2Nlc3Nfc2VudGVyaWNhIjoiVHJ1ZSIsImNvdW50cnkiOiJEZW5tYXJrIiwiaWQiOjEzMzAsImFkbWluaXN0cmF0b3IiOm51bGwsImVtYWlsIjoibWFvc0Bzc2kuZGsiLCJkZXBhcnRtZW50IjoiRm9vZGJvcm5lIHBhdGhvZ2VuIHN1cnZlaWxsYW5jZSIsInZpZXdfc3BlY2llcyI6IlRydWUiLCJsYXN0bmFtZSI6Ik9lc3Rlcmx1bmQiLCJhY3RpdmUiOm51bGwsInVwbG9hZF9yZWFkcyI6IlRydWUiLCJpbnN0aXR1dGlvbiI6IlN0YXRlbnMgU2VydW0gSW5zdGl0dXQifQ.qSAkPS_oyjL1vyqXzQBmXwc3zvrGS-r8KGP-OHIeynw"
	return token

def get_serotype(token, ST):
	address = "https://enterobase.warwick.ac.uk/api/v2.0/senterica/MLST_Achtman/sts?st_id={}&sts?show_alleles=true&limit=5".format(ST)
	cmd = ['curl', '-X', 'GET', '--header', 'Accept: application/json', '--user', token + ":", address]
	response = subprocess.check_output(cmd).decode()
	wait = 1
	while not "STs" in response and wait < 1000:
		print("Failed\tEnterobase_reply:\n{}".format(response),file=sys.stderr)
		time.sleep(wait)
		wait *= 2
		response = subprocess.check_output(cmd).decode()
	response = safe_load(response)
	serotypes = response["STs"][0]['info']['predict']['serotype']
	result = []
	for i in range(2):
		try:
			result.extend(map(str, serotypes[i]))
		except IndexError:
			result.extend(("Not found", "0"))
	return result

def get_serotype_from_enterobase(ST):
	ENTEROBASE_USERNAME = os.environ.get('ENTEROBASE_USERNAME')
	ENTEROBASE_PASSWORD = os.environ.get('ENTEROBASE_PASSWORD')
	ENTEROBASE_SERVER = os.environ.get('ENTEROBASE_SERVER')

	address = '%s/api/v2.0/login?username=%s&password=%s' %(ENTEROBASE_SERVER, ENTEROBASE_USERNAME, ENTEROBASE_PASSWORD)
	token = get_token(address)
	result = get_serotype(token, ST)
	return result

def load_json_file(stfile):
	serotypes = safe_load(open(stfile))
	return serotypes

def get_serotype_from_file(ST, stfile):
	#try:
		cache = load_json_file(stfile)
		serotypes = sorted(cache[str(ST)].items(), key=lambda element: element[1], reverse=True)
		if serotypes[0][1] / serotypes[1][1] < 2 or serotypes[0][1] < 3:
			return None
		result = []
		for i in range(2):
			try:
				result.extend(map(str, serotypes[i]))
			except IndexError:
				result.extend(("Not found", "0"))
		return result
	#except Exception:
		return None
	

if __name__ == "__main__":
	args = get_args()
	result = None
	if args.stfile:
		result = get_serotype_from_file(args.ST, args.stfile)
	if result is None:
		result = get_serotype_from_enterobase(args.ST)
	print(f"{args.id}\t{args.ST}"+"\t"+"\t".join(result))

