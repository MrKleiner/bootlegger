


class bootlegger:
	def __init__(self, cfgpath='nil'):
		from pathlib import Path
		import json, sys

		self.js_mods = {}
		self.css_mods = {}

		self.btg_sys_name = 'bootlegger'
		self.btg_sys_name_storage = 'bootlegger_storage'

		self.this_mod_def = '$this'
		self.whole_sys_def = '$all'
		self.storage_def = '$storage'

		self.processed_libs = ''

		self.processed_js = []
		self.processed_css = []

		self.reordered_modules = []

		self.evbinds = ''

		self.chunks = Path(__file__).parent / 'chunks'


		try:
			read_cfg = Path(sys.argv[1]).read_text().split('\n')
			clear_cfg = [ln for ln in read_cfg if not (ln.strip().startswith('//'))]
			cfg_json = json.loads('\n'.join(clear_cfg))
		except Exception as e:
			print('There were some problems reading the config file...')
			print('See details:')
			raise e

		defauls = {
			'jsmodules': (None, str),
			'sys_name': (None, str),
			'modules_order': ([], list),
			'project': (None, str),
			'writename': (None, str),
			'writesuffix': (None, str),
			'onlyfile': (False, bool),
			'onefile': ({}, dict),
			'art': (True, bool),
			'collapse': (0, int),
			'sync': (False, dict),
			'fonts': (None, str)
		}

		defauls_sync = {
			'dest': (None, str),
			'loc': (None, str),
			'auth': (None, str),
			'sync_mods': (True, bool),
			'folders': ([], list)
		}

		defaults_onlyfile = {
			'output_to': (None, str),
			'file_header': (None, str),
			'code_header': (None, str),
			'file_footer': (None, str),
			'sign_libs': (True, bool),
			'libs': (None, str),
			'libs_order': ([], list),
			'add_libs': ([], list),
			'bin_fonts': (None, str),
			'variables': (None, str)
		}

		self.cfg = {}

		# merge provided params with dfault
		# compare: defaults --> provided
		# basically, populate the local cfg with either provided or default
		for cfg_entry in defauls:
			# write default if parameter does not exist in the provided dict or is of the wrong type, else - use provided
			self.cfg[cfg_entry] = defauls[cfg_entry][0] if (not isinstance(cfg_json.get(cfg_entry), defauls[cfg_entry][1])) else cfg_json.get(cfg_entry)

		# merge onefile params with default
		if cfg_json.get('onefile'):
			for cfg_onef in defaults_onlyfile:
				self.cfg['onefile'][cfg_onef] = defaults_onlyfile[cfg_onef][0] if (not isinstance(cfg_json['onefile'].get(cfg_onef), defaults_onlyfile[cfg_onef][1])) else cfg_json['onefile'].get(cfg_onef)
		else:
			self.cfg['onefile'] = False


		# merge sync params with default
		for cfg_sync in defauls_sync:
			self.cfg['sync'][cfg_sync] = defauls_sync[cfg_sync][0] if (not isinstance(cfg_json['sync'].get(cfg_sync), defauls_sync[cfg_sync][1])) else cfg_json['sync'].get(cfg_sync)




		#
		# eval paths
		#

		# eval jsmodules, if any
		self.cfg['jsmodules'] = self.path_resolver(self.cfg['jsmodules'])

		# eval project path, if any
		self.cfg['project'] = self.path_resolver(self.cfg['project'])

		# eval libs path, if any
		# just do it right away, why wait, ffs
		if self.cfg['onefile']:
			self.cfg['onefile']['libs'] = self.path_resolver(self.cfg['onefile']['libs'])

		# now check minimal requirements
		# if it's still None - raise error
		if None in [self.cfg['jsmodules'], self.cfg['sys_name']]:
			raise ValueError('jsmodules or sys_name is undefined')


	def path_resolver(self, query=None, tp='dir'):
		from pathlib import Path
		if query == None or query == '':
			return

		qry = Path(str(query))
		proj = Path(str(self.cfg['project']))

		if tp == 'dir':
			# if specified path exists as an absolute path
			# then use it right away
			if qry.is_dir():
				resolved = qry
			elif (proj / qry).is_dir():
				# if it's not absolute - try as relative to the project
				resolved = proj / qry
			else:
				resolved = None
		else:
			# else - test for file
			# important todo: this is not the intended functionality
			# the tp param explicitly specifies whether to test for file or dir

			# if specified path exists as an absolute path
			# then use it right away
			if qry.is_file():
				resolved = qry
			elif (proj / qry).is_file():
				# if it's not absolute - try as relative to the project
				resolved = proj / qry
			else:
				resolved = None

		return resolved

	def commented_art(self, txt='sex', fnt='alligrator'):
		from art import text2art
		text = text2art(txt, font=fnt) if (self.cfg['art'] == True) else txt
		return '\n'.join([('// ' + ln) for ln in text.split('\n')])

	def wrap_autofunc(self, txt='', tabs=1):
		wrapped = ''
		wrapped += '(function() {'
		wrapped += '\n'
		# add tabs
		wrapped += '\n'.join([('\t'*tabs + ln) for ln in txt.split('\n')])
		# wrapped += txt
		wrapped += '\n'
		wrapped += '})();'
		return wrapped

	def basename(self, pthlib=None):
		if not pthlib:
			return ''
		return pthlib.name.split('.')[0] 


	def compile_folders(self):
		import shutil
		from pathlib import Path


		#
		# evaluate and store naming scheme
		#

		modules_pool = self.cfg['jsmodules']

		cfg = self.cfg

		# this is not needed if onlyfile is true...
		# determine where to put compiled modules
		# this will also create the root folder to put compiled modules to
		if not self.cfg['onlyfile']:
			# by default it's the parent folder of the modules folder
			compiled_folder_name = modules_pool.name

			# if writename is valid and not auto, then use what was manually specified
			# otherwise - use the name of the source folder
			if cfg.get('writename') and str(cfg.get('writename')).lower() != 'auto':
				compiled_folder_name = cfg['writename']

			# by default the folder suffix is _c
			compiled_folder_suffix = '_c'
			# If suffix is present, not auto and writename is not specified OR is auto
			# then use what was specified
			# Otherwise - add "_c"
			if cfg.get('writesuffix') and str(cfg.get('writesuffix')).lower() != 'auto' and (not cfg.get('writename') or cfg.get('writename') == 'auto'):
				compiled_folder_suffix = cfg['writesuffix']

			# save evaluated folder suffix
			self.fl_suffix = compiled_folder_suffix

			# final result (compiled folders write name)
			compiled_folder_name += compiled_folder_suffix
			comp_folder_path = modules_pool.parent / compiled_folder_name

			# be very careful: abort if SOMEHOW the compiled folder path matches the src folder path...
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

			self.output_modules_folder = comp_folder_path

		# get a list of folders inside the modules folder
		# aka get the list of modules
		flds = [f for f in modules_pool.glob('*') if f.is_dir()]


		# for every module
		for mod in flds:
			current_mod_name = self.basename(mod)
			print('Processing module', current_mod_name)

			# define this module in the global js modules dict
			self.js_mods[current_mod_name] = []
			# and css
			self.css_mods[current_mod_name] = []

			# Create this module's folder in the compiled destination
			# IF not onlyfile
			if not self.cfg['onlyfile']:
				(comp_folder_path / current_mod_name).mkdir(exist_ok=True)

			# for every file in this module (folder)
			for mfile in [mf for mf in mod.glob('*') if mf.is_file()]:
				print('Reading module file', mfile.name)

				# actually replace the stuff
				if mfile.suffix.lower() == '.css':
					evaluated = (
						mfile.read_text(encoding='UTF-8')
						.replace(self.this_mod_def, current_mod_name)
					)
				else:
					evaluated = (
						mfile.read_text(encoding='UTF-8')
						.replace(self.this_mod_def, f'window.{self.btg_sys_name}.{current_mod_name}')
						.replace(self.whole_sys_def, f'window.{self.btg_sys_name}')
						.replace(self.storage_def, f'window.{self.btg_sys_name_storage}')
					)

				# Write the evaulated result to the compiled modules pool, if not onlyfile
				if not self.cfg['onlyfile']:
					if mfile.suffix.lower() == '.js':
						evaluated = '\n' + f'if (!window.bootlegger.{current_mod_name}){{window.bootlegger.{current_mod_name}={{}}}};' + '\n' + evaluated
						evaluated = '\n' + f'if (!window.bootlegger){{window.bootlegger = {{}}}};' + '\n' + evaluated
					(comp_folder_path / current_mod_name / mfile.name).write_bytes(evaluated.encode())

				# now append it to the pool
				# (for singlefile thingy)
				if mfile.suffix.lower() == '.js':
					# collapsed = evaluated
					process = evaluated.split('\n')
					# sex = evaluated

					if self.cfg['collapse'] == 1:
						evaluated = '\n'.join([ln for ln in process if not ln.strip().startswith('//')])

					if self.cfg['collapse'] == 2:
						evaluated = '\n'.join([ln for ln in process if not (ln.strip() == '')])

					if self.cfg['collapse'] == 3:
						import re
						print('collapsing', self.basename(mod))
						evaluated = '\n'.join([ln for ln in process if not (ln.strip() == '' or ln.strip().startswith('//'))])
						# evaluated = re.sub(r'([^\(\.]\/\*[^\(]*)\*\/', '', evaluated, re.M)
						evaluated = re.sub(r'\/\*.*?\*\/', '', evaluated, flags=re.DOTALL)


					# The module has to be declared before we can add stuff to it...
					# It's possible to create a file defining all these modules, but it'd be required to manually link it
					# it's not a peoblem when it's a single file, becuase all we have to do is simply declare this somewhere in the top.
					# But when it's a proper multi-file system - it either has to be a separate file declaring all this stuff
					# or simply try to add this in the very beginning of every module file IF NEEDED
					evaluated = '\n' + f'if (!window.bootlegger){{window.bootlegger = {{}}}};' + '\n' + evaluated
					evaluated = '\n' + f'if (!window.bootlegger.{current_mod_name}){{window.bootlegger.{current_mod_name}={{}}}};' + '\n' + evaluated

					# write down the evaluated result
					self.js_mods[self.basename(mod)].append(evaluated)
				if mfile.suffix.lower() == '.css':
					self.css_mods[self.basename(mod)].append(evaluated)


	def syncer(self):
		# todo: MAYBE add md5 hash validation

		# minimal requirements
		if not self.cfg['sync']['dest'] or not self.cfg['sync']['loc'] or not self.cfg['sync']['auth']:
			print('Malformed sync config')
			return

		import requests, base64
		from zipfile import ZipFile
		from pathlib import Path

		# the system doesnt bother (for now)
		# it collects everything and then overrides everything
		# for now the system does not provide any extra support for large files
		# it's assumed that the entire sync payload is around 10mb in size
		# everything is zipped into a zip archive and sent to a remote destination

		# todo: random internet article suggests to collect all the files beforehand...
		# but it doesn't really matter...

		# todo: this looks too bootleg even for bootlegger

		# collect all files to be zipped
		zp_paths = [(self.path_resolver(p, 'dir') or self.path_resolver(p, 'file')) for p in self.cfg['sync']['payload']]
		# remove invalid entries
		zp_paths = [valid for valid in zp_paths if valid != None]

		print(zp_paths)

		# files in the archive have to be relative to the working dir
		# todo: it'd actually be safer to get the parent dir of the jsmodules right away
		rel_path = self.cfg['project'] or self.cfg['jsmodules'].parent

		# first of all - rglob modules
		for md in self.output_modules_folder.rglob('*'):
			zp_paths.append(md)

		# now rglob additional folders
		for rg_idx, rg in enumerate(zp_paths):
			if rg.is_dir():
				# remove the folder entry itself
				del zp_paths[rg_idx]

				# append rglobbed results
				for gl in rg.rglob('*'):
					zp_paths.append(gl)

		# generate and write zip file
		# the write destination is always the containing folder of the jsmodules
		pl_path = self.cfg['jsmodules'].parent / 'sync_payload.zip'
		with ZipFile(str(pl_path), 'w') as zip:
			for file in zp_paths:
				zip.write(file)

		# send zip file to the remote destination
		# headers
		rq_headers = {
			'CONTENT_TYPE': '*/*'
		}

		prms = {
			'dest': base64.b64encode(self.cfg['sync']['loc'].encode()).decode(),
			'auth': base64.b64encode(self.cfg['sync']['auth'].encode()).decode(),
			'dbloc': base64.b64encode(self.cfg['sync']['authdb'].encode()).decode()
		}

		send_payload = requests.post(
			url=f"""{self.cfg['sync']['dest']}/htbin/sync.py""",
			headers=rq_headers,
			params=prms,
			data=pl_path.read_bytes()
		)

		print(send_payload.text)

		# delete the zip payload
		pl_path.unlink(missing_ok=True)

	def compile_binds(self):
		from pathlib import Path
		import json

		# collect binds from every module
		module_events = {}
		# for every js module in the jsmodules folder...
		for md in self.reordered_modules:
			# go through every json with binds
			for md_binds_file in (self.cfg['jsmodules'] / md).glob('*.binds.json'):
				# evaluate binds json
				binds_json = json.loads(md_binds_file.read_bytes())
				# go through every event
				for evt in binds_json:
					# create the current event binds pool in the global pool if doesn't exist
					if module_events.get(evt) == None:
						module_events[evt] = {}

					# ???
					display_name = f"""{md_binds_file.parent.name} {self.basename(md_binds_file)}"""

					# create the events pool
					module_events[evt][display_name] = [bnd for bnd in binds_json[evt]]

		# collapse everything into actual code
		compiled_events = ''

		# for every event type
		for etype in module_events:
			# open the event type
			compiled_events += f"""document.addEventListener('{etype}', tr_event => {{"""

			# for every module
			for module_binds in module_events[etype]:
				# mark the module
				compiled_events += '\n'*3
				compiled_events += '\t// =========================================='
				compiled_events += '\n'
				compiled_events += '\t// \t' + module_binds
				compiled_events += '\n'
				compiled_events += '\t// =========================================='
				compiled_events += '\n'*1

				# add actual binds
				for c_action in module_events[etype][module_binds]:
					# evaluate the function parameters
					functionparams = ', '.join(list(filter(None, [
						# event goes first
						'tr_event' if c_action['pass_event'] == True else '',
						# then element
						f"""event.target.closest('{c_action.get('selector')}')""" if c_action.get('pass_element') == True else '',
						# then params
						c_action.get('pass_params') if c_action.get('pass_params') != None and c_action.get('pass_params').strip() != '' else ''
					])))

					compiled_events += '\n'
					compiled_events += '\t'

					# also evaluate functions
					evaluated_function = (
						c_action['function']
						.replace(self.this_mod_def, f"""window.{self.btg_sys_name}.{module_binds.split(' ')[0]}""")
						.replace(self.whole_sys_def, f'window.{self.btg_sys_name}')
						.replace(self.storage_def, f'window.{self.btg_sys_name_storage}')
					)

					compiled_events += f"""if (event.target.closest('{c_action['selector']}'))"""
					compiled_events += f"""{{{evaluated_function}({functionparams})}}"""

					# compiled_events += ('else{ ' + c_action.get('else') + '(' + functionparams + ') }') if c_action.get('else') != None else ''
					compiled_events += f"""else{{{c_action.get('else')}({functionparams})}}""" if c_action.get('else') != None else ''

				compiled_events += '\n'*2

			compiled_events += '\n'
			compiled_events += """});"""
			compiled_events += '\n'*3

		self.evbinds = compiled_events

		# save the compiled result
		(self.cfg['jsmodules'].parent / f"""{self.cfg['sys_name']}.evbinds.js""").write_bytes(compiled_events.encode())


	def sign_fonts(self):
		from pathlib import Path

		fonts_path = self.path_resolver(self.cfg['fonts'])
		if not fonts_path:
			return None

		css_prefab = (self.chunks / 'font.css').read_text()

		fonts_dump = ''

		# go through every subfolder of the fonts path
		# every folder is a font with font files inside
		# folder's name is also the font's name
		for fnt in fonts_path.glob('*'):
			# skip files inside the root fonts folder
			# also skip this font if it was specified that it's in manual mode
			if not fnt.is_dir() or (fnt / 'font.manual').is_file():
				continue

			# write font name, for convenience
			fonts_dump += '/*==============================================*/'
			fonts_dump += '\n'
			fonts_dump += f'/*{fnt.name}*/'
			fonts_dump += '\n'
			fonts_dump += '/*==============================================*/'
			fonts_dump += '\n'

			# go through every single file inside every subfolder of the fonts folder
			# and add every file as a font according to a strict schema
			for fnt_file in fnt.glob('*'):
				# skip if not file
				if not fnt_file.is_file():
					continue

				# split font name
				# every part of the font's name is a parameter
				fnt_info = fnt_file.name.split('.')

				# add this font variation to the pool
				fonts_dump += (
					css_prefab
					.replace('$family', fnt.name)
					.replace('$weight', fnt_info[0])
					.replace('$style', fnt_info[1])
					.replace('$filepath', f"""/{str(fnt_file.relative_to(fonts_path.parent).as_posix())}""")
				)
				fonts_dump += '\n'

			fonts_dump += '\n'*8


		# Write font index
		(self.cfg['jsmodules'].parent / f"""{self.cfg['sys_name']}.fnt_index.css""").write_bytes(fonts_dump.encode())



	#
	# Onefile
	#

	def compile_fonts(self):
		import json
		from pathlib import Path
		import base64
		# strict folder struct:
		# every folder is a font name
		# every file name inside that folder is:
		# font_type(aka regular/italic).font_weight(aka 300)
		fonts_path = self.path_resolver(self.cfg['onefile']['bin_fonts'])
		if not fonts_path:
			return []

		fonts_dict = []
		for fnt in fonts_path.glob('*'):
			if not fnt.is_dir():
				continue

			for fnt_file in fnt.glob('*'):
				if not fnt_file.is_file():
					continue

				cfont = {}
				cfont['family'] = fnt.name
				cfont['weight'] = fnt_file.name.split('.')[0]
				cfont['ftype'] = fnt_file.name.split('.')[1]
				# cfont['bt'] = [b for b in fnt_file.read_bytes()]
				cfont['bt'] = base64.b64encode(fnt_file.read_bytes()).decode()

				fonts_dict.append(cfont)

		return json.dumps(fonts_dict)

	def reorder_modules(self):
		# store ordered modules here
		modules_buffer_js = []
		modules_buffer_css = []

		# first append ordered modules
		# (every module is an array of processed texts)
		for module in self.cfg['modules_order']:
			modules_buffer_js.append(self.js_mods[module])
			modules_buffer_css.append(self.css_mods[module])
			del self.js_mods[module]
			del self.css_mods[module]
			self.reordered_modules.append(module)

		# then appened remaining ones
		for remaining_module in self.js_mods:
			modules_buffer_js.append(self.js_mods[remaining_module])
			modules_buffer_css.append(self.css_mods[remaining_module])
			self.reordered_modules.append(remaining_module)

		self.processed_js = modules_buffer_js
		self.processed_css = modules_buffer_css

	def process_libs(self):
		from pathlib import Path
		import requests
		# from art import text2art

		libspath = self.cfg['onefile']['libs']
		# only do it if libs are present
		if not libspath:
			print('No Libs To Process')
			return

		# proceed

		# dict:
		# lib root folder: lib text
		unordered_libs = {}

		# array:
		# every entry is libname + libtext
		ordered_libs = []

		# create chaotic unordered dict of all libs
		# every library is named after its most parent folder
		for chaos_lib in libspath.glob('*'):
			# chaotic means that we simply get the first js file we find
			unordered_libs[chaos_lib.name] = [l for l in chaos_lib.rglob('*.js')][0].read_text(encoding='utf-8')


		#
		# First append ordered libs
		#

		# Append ordered libs, delete them from unordered libs
		# and then appened remeinig libs
		for order_lib in self.cfg['onefile']['libs_order']:
			lib_file = (libspath / Path(order_lib))
			print('Processing library', lib_file, order_lib)
			# dont do shit if this file does not exist
			if not lib_file.is_file():
				print('This library does not exist on disk')
				continue
			print('Library exists, proceed')

			# lib name based on its containing folder
			libname = Path(order_lib).parents[-2].name
			print('Lib name', libname)

			# if it exists - append it to the ordered array
			# sign it and add text
			ordered_libs.append(
				# sign
				self.commented_art(libname, 'alligator')
				+
				# a few line breaks
				'\n'*3
				+
				# the library itself
				lib_file.read_text(encoding='utf-8')
			)

			# delete this lib from the
			del unordered_libs[libname]

		#
		# Then append remaining libraries
		#
		for remaining_lib in unordered_libs:
			print('Processing library', remaining_lib)
			ordered_libs.append(
				# sign
				self.commented_art(remaining_lib, 'alligator')
				+
				# a few line breaks
				'\n'*3
				+
				# the library itself
				unordered_libs[remaining_lib]
			)


		#
		# Finally, append urls
		#
		for remote in self.cfg['onefile']['add_libs']:
			if remote['type'] == 'url':

				# headers
				rq_headers = {
					# 'acce'
				}

				get_lib = requests.get(url=remote['src'], headers=rq_headers, params=None)

				ordered_libs.append(
					# sign
					self.commented_art(remote['name'], 'alligator')
					+
					# a few line breaks
					'\n'*3
					+
					# the library itself
					get_lib.text
				)


		# save processed libs
		self.processed_libs = ordered_libs

	def process_variable(self, vpath=''):
		from pathlib import Path
		import json, base64
		varpath = Path(vpath)
		if not varpath.is_file():
			return ''

		compiled_var = ''		

		var_cfg_raw = varpath.name.split('.')
		# (delete decorative extension)
		del var_cfg_raw[-1]

		var_type = var_cfg_raw[-1].lower()
		# (delete var type)
		del var_cfg_raw[-1]

		var_loc = '.'.join(var_cfg_raw).lower().strip('.')

		# just do this right away
		# for now everything uses this anyway...
		# unit_array = f"""new Uint8Array([{','.join([str(b) for b in vpath.read_bytes()])}])"""
		unit_array = f"""window.bootlegger_sys_funcs.base64DecToArr('{base64.b64encode(vpath.read_bytes()).decode()}')"""

		# ensure that the variable location exists
		dest = ''
		deep_path = []
		del var_cfg_raw[-1]
		for dst in var_cfg_raw:
			# important todo: the replace() is an extremely retarded hack to get rid of double dots
			# double dots happen when there's still no deep path
			dest += f"""if(!btg.{'.'.join(deep_path)}.{dst}){{btg.{'.'.join(deep_path)}.{dst} = {{}}}};""".replace('..', '.')
			deep_path.append(dst)
		#
		# evaluate variable by type
		#
		if var_type == 'text':
			compiled_var = f"""btg.{var_loc} = window.bootlegger_sys_funcs.UTF8ArrToStr({unit_array});"""

		if var_type == 'bytes_raw':
			compiled_var = f"""btg.{var_loc} = {unit_array};"""

		if var_type == 'bytes':
			compiled_var = f"""btg.{var_loc} = {{'bytes': {unit_array}, 'url': (window.URL || window.webkitURL).createObjectURL(new Blob([({unit_array})]))}}"""

		if var_type == 'json':
			compiled_var = f"""btg.{var_loc} = JSON.parse(window.bootlegger_sys_funcs.UTF8ArrToStr({unit_array}));"""

		return dest + compiled_var

	def compile_css(self):
		import base64
		from pathlib import Path
		css_buffer = ''
		compiled = ''

		# collapse all in one string
		# (every entry is an array of texts from files)
		for css in self.processed_css:
			css_buffer += '\n'.join(css)

		compiled += f'var cssb64 = `{base64.b64encode(css_buffer.encode()).decode()}`;'
		compiled += '\n'
		compiled += (self.chunks / 'css.js').read_text().strip()

		return self.wrap_autofunc(compiled)




	def compile_singlefile(self):
		from pathlib import Path
		# from art import text2art
		comp_file = ''

		# onefile consists of:
		# - Software name
		# - Total header, stored in a file the path to which is specified in the cfg 
		# and is either relative to the project dir or is absolute
		# - Libraries
		# - Fonts
		# - Css
		# - Variables
		# - Main Code
		# - Footer


		#
		# Header. Software name
		#
		comp_file += self.commented_art(self.cfg['sys_name'], 'tarty9')

		# breaks
		comp_file += '\n'*20


		#
		# User file header, if any
		#
		fheader = self.path_resolver(self.cfg['onefile']['file_header'], 'file')
		if fheader:
			comp_file += fheader.read_text(encoding='utf-8')

		# breaks
		comp_file += '\n'*20


		#
		# Libraries
		#

		# mark libraries block
		comp_file += self.commented_art('LIBS', 'tarty8')
		comp_file += '\n'*10

		# every entry is a processed text of a library
		for lib in self.processed_libs:
			comp_file += lib
			comp_file += '\n'*10


		#
		# sys funcs, needed for various shit
		#
		comp_file += '\n'*10
		comp_file += (self.chunks / 'btg_util.js').read_text(encoding='utf-8')
		comp_file += '\n'*10


		#
		# Fonts
		#
		comp_file += '\n'*10
		comp_file += self.commented_art('FONTS', 'tarty8')
		comp_file += '\n'*5

		comp_file += self.wrap_autofunc((
			f'var fnt_pool = {self.compile_fonts()}'
			+
			'\n'
			+
			(self.chunks / 'btg_fonts.js').read_text().strip()
		))



		#
		# CSS
		#
		comp_file += '\n'*10
		comp_file += self.commented_art('CSS', 'tarty8')
		comp_file += '\n'*5

		comp_file += self.compile_css()



		#
		# Variables, if any
		#

		# mark variables block
		comp_file += '\n'*10
		comp_file += self.commented_art('VARS', 'tarty8')
		comp_file += '\n'*5

		comp_file += 'const btg = {};'
		comp_file += '\n'*2
		comp_file += 'window.bootlegger = {};'
		comp_file += '\n'*5

		vars_path = self.path_resolver(self.cfg['onefile']['variables'])
		if vars_path:
			for var in vars_path.rglob('*'):
				comp_file += self.process_variable(var)
				comp_file += '\n'*3

		#
		# Code
		#

		# mark codes block
		comp_file += '\n'*15
		comp_file += self.commented_art('CODE', 'tarty8')
		comp_file += '\n'*10

		#
		# Add binds, if any
		#
		comp_file += (self.cfg['jsmodules'].parent / f"""{self.cfg['sys_name']}.evbinds.js""").read_text()
		comp_file += '\n'*5

		# comp_file += ('\n'*10).join(self.processed_js)
		for code in self.processed_js:
			# cd = ('\n'*3).join(code)
			# if self.cfg['collapse'] == 1:
			# 	cd = ('\n'*3).join(code)
			comp_file += ('\n'*5).join(code)




		return comp_file



	def exec_all(self):
		# folders always have to be compiled before doing anything else
		self.compile_folders()
		# then, modules have to be reordered
		self.reorder_modules()
		# compile binds
		self.compile_binds()
		# lastly, compile fonts
		self.sign_fonts()
		# if onefile is true, then also process libs and compile onefile
		if self.cfg['onefile']:
			onefile_path = self.path_resolver(self.cfg['onefile']['output_to']) or self.cfg['jsmodules'].parent
			self.process_libs()
			(onefile_path / f"""{self.cfg['sys_name']}.pwned.js""").write_bytes(self.compile_singlefile().encode())

		# now exec sync
		self.syncer()


	def exec_onefile(self):
		self.compile_folders()
		self.reorder_modules()
		self.process_libs()

		onefile_path = self.path_resolver(self.cfg['onefile']['output_to']) or self.cfg['jsmodules'].parent

		(onefile_path / f"""{self.cfg['sys_name']}.pwned.js""").write_bytes(self.compile_singlefile().encode())





ded = bootlegger()
ded.exec_all()
