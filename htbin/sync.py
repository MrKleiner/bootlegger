import os, sys, json, hashlib, base64, cgi, shutil, zipfile
from pathlib import Path


# parse url params into a dict, if any
get_cgi_params = cgi.parse()
url_params = {}
for it in get_cgi_params:
	url_params[it] = ''.join(get_cgi_params[it])

# don't even bother if auth is invalid
def authed():
	# get byte data of the incoming request
	byte_data = sys.stdin.buffer.read()

	# with open(str('killme.txt'), 'w') as nein:
	# 	nein.write(str(Path(base64.b64decode(url_params['dest'].encode()).decode())))

	# eval paths
	pl_path = Path(base64.b64decode(url_params['dest'].encode()).decode()) / 'btg_incoming_playload.zip'
	main_dir = pl_path.parent

	# save zip file
	pl_path.write_bytes(byte_data)

	# process the zip file
	with zipfile.ZipFile(str(pl_path), 'r') as zip_ref:
		# get a list of files/folders to delete before extraction
		# relativepath = zipfile.Path(zip_ref).iterdir()

		# delete queued entries
		# for rm in zipfile.Path(zip_ref).iterdir():
		# 	continue
		# 	if (main_dir / rm.name).is_file():
		# 		(main_dir / rm.name).unlink(missing_ok=True)
		# 	if (main_dir / rm.name).is_dir():
		# 		try:
		# 			shutil.rmtree(str(main_dir / rm.name))
		# 		except:
		# 			pass

		# extract everything
		zip_ref.extractall(str(main_dir))

	# remove the payload
	pl_path.unlink(missing_ok=True)


# validate auth
def check_auth():
	a_db_raw = Path(base64.b64decode(url_params['dbloc'].encode()).decode()).read_text()
	a_db = json.loads('\n'.join([nc for nc in a_db_raw.split('\n') if not nc.strip().startswith('//')]))
	# if auth was successful - proceed
	if a_db['sync_pswd'] == base64.b64decode(url_params['auth'].encode()).decode():
		authed()

check_auth()




