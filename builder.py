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






def path_resolver(query=None, tp='dir'):
	if query == None:
		return

	if tp == 'dir':
		# if specified path exists as an absolute path
		# then use it right away
		if Path(str(query)).is_dir():
			resolved = Path(query)
		elif (Path(str(rootdir)) / Path(str(query))).is_dir():
			# if it's not absolute - try as relative to the project
			resolved = rootdir / Path(query)
		else:
			resolved = None
	else:
		# if specified path exists as an absolute path
		# then use it right away
		if Path(str(query)).is_file():
			resolved = Path(query)
		elif (Path(str(rootdir)) / Path(str(query))).is_file():
			# if it's not absolute - try as relative to the project
			resolved = rootdir / Path(query)
		else:
			resolved = None

	return resolved












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

	
	# test for absolute path:
	# if it's an abs path then use it right away
	modules_pool = path_resolver(cfg['jsmodules'], 'dir')
	
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
				mfile.read_text(encoding='UTF-8')
				.replace('$this', 'window.bootlegger.' + md.basename)
				.replace('$all', 'window.bootlegger')
				.replace('$storage', 'window.bootlegger_storage')
			)
			if mfile.suffix.lower() == '.js':
				hotkeys = 'if (!window.bootlegger.' + md.basename + '){window.bootlegger.' + md.basename + '={}}' + '\n' + hotkeys

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





def get_libs():
	libs_path = path_resolver(cfg['onefile'].get('libs'))
	if libs_path == None:
		return b''

	initial_base = {}

	sorted_libs = []

	# simply get the first JS file in sight
	for lib in libs_path.glob('*'):
		initial_base[lib.name] = [l for l in lib.rglob('*.js')][0].read_text(encoding='utf-8')
	# print(initial_base)
	# first, append sorted
	for sort_lib in cfg['onefile']['libs_explicit']:
		try:
			pull = Path(sort_lib)
			print((libs_path / pull))
			sorted_libs.append(('\n'*15) + text2art(sort_lib, font='alligator') + ('\n'*2) + (libs_path / pull).read_bytes())
			del initial_base[sort_lib]
		except:
			pass
	# and then the rest
	for remain in initial_base:
		try:
			pull = Path(remain)
			sorted_libs.append(('\n'*15) + text2art(sort_lib, font='alligator') + ('\n'*2) + (libs_path / remain).read_bytes())
		except:
			pass
	return '\n'.join(sorted_libs).encode()








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

	# either specified path OR parent dir of the modules folder
	onefile_path = (path_resolver(cfg['onefile'].get('output_to'), 'dir') or Path(cfg['jsmodules']).parent) / (cfg['sys_name'] + '.comp.js')


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
	header_src = path_resolver(cfg['onefile'].get('header_pre'), 'file') or b''
	onef.write(header_src if isinstance(header_src, bytes) else header_src.read_bytes())


	# --------------------------------------
	# separator
	# --------------------------------------
	onef.write(b'\n'*10)
	onef.write(text2art('LIBS', font='tarty8').encode())
	onef.write(b'\n'*10)


	# --------------------------------------
	# write libs, if any
	# --------------------------------------
	onef.write(get_libs())

	# --------------------------------------
	# write main code, if any
	# --------------------------------------
	onef.write(modules_as_ordered()['js'].encode())








































