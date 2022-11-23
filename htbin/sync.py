#!/usr/bin/python3
import os, sys, json, hashlib, base64, cgi, shutil, zipfile, cgitb
from pathlib import Path
cgitb.enable()
form = cgi.FieldStorage()
# parse url params into a dict, if any
# get_cgi_params = cgi.parse()
url_params = {
	'dest': ''.join(form.getlist('dest')),
	'auth': ''.join(form.getlist('auth')),
	'dbloc': ''.join(form.getlist('dbloc'))
}
# for it in get_cgi_params:
# 	url_params[it] = ''.join(get_cgi_params[it])

# value = form.getlist("username")
# usernames = ",".join(value)

return_info = {}

# don't even bother if auth is invalid
def authed():
	
	# get byte data of the incoming request
	byte_data = sys.stdin.buffer.read()

	return_info['data_length'] = len(byte_data)

	# with open(str('killme.txt'), 'w') as nein:
	# 	nein.write(str(Path(base64.b64decode(url_params['dest'].encode()).decode())))

	# eval paths
	pl_path = Path(base64.b64decode(url_params['dest'].encode()).decode()) / 'btg_incoming_playload.zip'
	main_dir = pl_path.parent

	return_info['pl_path'] = pl_path
	return_info['main_dir'] = main_dir

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

		return_info['maybe_extracted'] = True

	# remove the payload
	pl_path.unlink(missing_ok=True)

	return_info['del_payload'] = True



# validate auth
def check_auth():
	a_db_raw = Path(base64.b64decode(url_params['dbloc'].encode()).decode()).read_text()
	a_db = json.loads('\n'.join([nc for nc in a_db_raw.split('\n') if not nc.strip().startswith('//')]))
	# if auth was successful - proceed
	if a_db['sync_pswd'] == base64.b64decode(url_params['auth'].encode()).decode():
		authed()
		return_info['all_done'] = True
		# buffer...
		sys.stdout.buffer.write(json.dumps(return_info).encode())
		# it's unknown wtf does this function do, but it's just there...
		sys.stdout.flush()

check_auth()




