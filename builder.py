from pathlib import Path
import shutil, json, os, sys, base64
from art import *

# first, read the config...
# the config is cool: it's json which allows comments
# the python file should be executed with the config file path passed as one and the only execution parameter
try:
	read_cfg = Path(sys.argv[1]).read_text().split('\n')
	nc_cfg = [ln for ln in read_cfg if not (ln.strip().startswith('//'))]
	cfg = json.loads('\n'.join(nc_cfg))
except Exception as e:
	print('There were some problems reading the config file...')
	print('See details:')
	raise e


# Evaluate root path, if any
rootdir = Path(str(cfg.get('project')))
rootdir = rootdir if rootdir.is_dir() else None

# evaluate whether to write onefile or not
onefile = True if cfg.get('onefile') else False

# evaluate whether it's ONLY onefile or not
onlyfile = True if cfg.get('onlyfile') == True else False

# default modules order
if not isinstance(cfg.get('modules_explicit'), list):
	cfg['modules_explicit'] = []




# js modules dict
# key: module name
# value: array of text files
js_mods = {}

# css modules dict
css_mods = {}

#
# Main feature: compile folders
#
def compile_folders():
	# write result here
	result = ''

	# evaluate paths

	# first check if this minimal requirement is met
	if not cfg.get('jsmodules'):
		print('ERROR: Minimal requirement not met: js modules folder pool')
		return

	# then check if another minimal requirement is met
	if not cfg.get('sys_name'):
		print('ERROR: Minimal requirement not met: sys_name is not defined')
		return

	eval_path = Path(cfg['jsmodules'])
	
	# test for absolute path:
	# if it's an abs path then use it right away
	modules_pool = None
	if eval_path.is_dir():
		modules_pool = eval_path
	elif ((rootdir or Path('nil')) / eval_path).is_dir():
		modules_pool = rootdir / eval_path
	
	# if it's still none - invalid path
	if not modules_pool:
		print('ERROR: Minimal requirement not met: js modules folder pool')
		return

	print(modules_pool)

	#
	# evaluate naming scheme
	#

	# this is not needed if onlyfile is true...
	if not onlyfile:
		# by default it's the parent folder of the modules folder
		compiled_folder_name = modules_pool.name

		# if writename is valid and not auto, then use what was manually specified
		# otherwise - use the name of the source folder
		if cfg.get('writename') and str(cfg.get('writename')).lower() != 'auto':
			compiled_folder_name = cfg['writename']

		compiled_folder_suffix = '_c'
		# If suffix is present, not auto and writename is not specified OR is auto
		# then use what was specified
		# Otherwise - add "_c"
		if cfg.get('writesuffix') and str(cfg.get('writesuffix')).lower() != 'auto' and (not cfg.get('writename') or cfg.get('writename') == 'auto'):
			compiled_folder_suffix = cfg['writesuffix']

		# final result
		compiled_folder_name += compiled_folder_suffix
		comp_folder_path = modules_pool.parent / compiled_folder_name

		# be very careful: return if SOMEHOW the compiled folder path matches the src folder path...
		if str(comp_folder_path) == str(modules_pool):
			print('Fatal Error: Compiled folder name matches source folder name')
			return

		# Once we've ensured that we're not wiping the source folder - do wipe the compiled destination folder
		try:
			shutil.rmtree(str(comp_folder_path))
		except:
			pass

		# now create this folder again
		comp_folder_path.mkdir(exist_ok=True)



	#
	# Compile folders
	#

	# get a list of folders inside the modules folder
	flds = [f for f in modules_pool.glob('*') if f.is_dir()]

	# for every module
	for md in flds:
		# define this module in the global js modules dict
		js_mods[md.basename] = []
		# and css
		css_mods[md.basename] = []

		# create this module's folder in the compiled destination
		# IF not onlyfile
		if not onlyfile:
			(comp_folder_path / md.name).mkdir(exist_ok=True)

		# for every file in this module...
		for mfile in [mf for mf in md.glob('*') if mf.is_file()]:
			# replace shortcuts...
			print('reading', mfile)
			hotkeys = (
				'if (!window.bootlegger.' + md.basename + '){}'
				mfile.read_text(encoding='UTF-8')
				.replace('$this', 'window.bootlegger.' + md.basename)
				.replace('$all', 'window.bootlegger')
			)

			# if not onlyfile then write shit to a compiled place
			if not onlyfile:
				(comp_folder_path / md.name / mfile.name).write_bytes(hotkeys.encode())

			# now append it to the pool
			# (for singlefile thingy)
			if mfile.suffix.lower() == '.js':
				js_mods[md.name].append(hotkeys)
			if mfile.suffix.lower() == '.css':
				css_mods[md.name].append(hotkeys)



def modules_as_ordered():
	final_order_js = []
	final_order_css = []

	# append the specified ones
	for order in cfg['modules_explicit']:
		# js
		if js_mods.get(order) != None:
			final_order_js.append('\n'.join(js_mods[order]))
			del js_mods[order]
		# css
		if css_mods.get(order) != None:
			final_order_css.append('\n'.join(css_mods[order]))
			del css_mods[order]


	# then appened the remaining ones
	for lefts in js_mods:
		# js
		final_order_js.append('\n'.join(js_mods[lefts]))
		# css
		final_order_js.append('\n'.join(css_mods[lefts]))

	return {'js': '\n'.join(final_order_js)}


# ====================================
# 				Compose...
# ====================================


#
# The folders have to always be treated first...
#
compile_folders()

#
# then, compile onefile, if any
#

# onefile consists of:
# - Software name
# - Total header, stored in a file the path to which is specified in the cfg 
# and is either relative to the project dir or is absolute
# - Libraries
# - Fonts
# - Variables
# - Main Code
# - Footer

if onefile:
	#
	# evaluate onefile location
	#

	# if specified path exists as an absolute path
	# then use it right away
	if Path(str(cfg['onefile'].get('output_to'))).is_dir():
		onefile_path = Path(cfg['onefile']['output_to'])
	elif (Path(str(rootdir)) / Path(str(cfg['onefile'].get('output_to')))).is_dir():
		# if it's not absolute - try as relative to the project
		onefile_path = rootdir / cfg['onefile']['output_to']
	else:
		# finally, if nothing above worked - use the parent dir of the modules input
		onefile_path = Path(cfg['jsmodules']).parent / (cfg['sys_name'] + '.comp.js')

	# wipe the onefile file
	with open(str(onefile_path), 'w', encoding='utf-8') as wiper:
		wiper.write('')

	# open the onefile for writing
	onef = open(str(onefile_path), 'ab')


	# --------------------------------------
	# write the software name
	# --------------------------------------
	onef.write(text2art(cfg['sys_name'], font='tarty9').encode())

	onef.write(b'\n'*10)


	# --------------------------------------
	# write header, if any
	# --------------------------------------

	# eval the path...
	# this is getting old...

	# check if we have to add it at all...
	if cfg['onefile'].get('header_pre'):
		# check for absolute
		if Path(str(cfg['onefile']['header_pre'])).is_file():
			header_src = (Path(cfg['onefile']['header_pre'])).read_bytes()
		elif (Path(str(rootdir)) / Path(str(cfg['onefile']['header_pre']))).is_file():
			# now check for relative path
			header_src = (Path(rootdir) / Path(cfg['onefile']['header_pre'])).read_bytes()
		else:
			# otherwise - dont add shit
			header_src = b''

		onef.write(header_src)


	# --------------------------------------
	# separator
	# --------------------------------------
	onef.write(b'\n'*10)
	onef.write(text2art('MAIN', font='tarty8').encode())
	onef.write(b'\n'*10)


	# --------------------------------------
	# write main code, if any
	# --------------------------------------
	onef.write(modules_as_ordered()['js'].encode())








































