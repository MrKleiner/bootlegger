


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
			'art': (True, bool)
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


		#
		# eval paths
		#

		# eval jsmodules, if any
		self.cfg['jsmodules'] = self.path_resolver(self.cfg['jsmodules'])

		# eval project path, if any
		self.cfg['project'] = self.path_resolver(self.cfg['project'])

		# eval libs path, if any
		# just do it right away, why wait, ffs
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
		wrapped += '\n'
		wrapped += '})();'
		return wrapped


	def compile_folders(self):
		import shutil
		from pathlib import Path
		#
		# evaluate naming scheme
		#

		modules_pool = self.cfg['jsmodules']

		# this is not needed if onlyfile is true...
		# determine where to put compiled modules
		if not self.cfg['onlyfile']:
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


		# get a list of folders inside the modules folder
		# aka get the list of modules
		flds = [f for f in modules_pool.glob('*') if f.is_dir()]


		# for every module
		for mod in flds:
			current_mod_name = mod.basename
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
				evaluated = (
					mfile.read_text(encoding='UTF-8')
					.replace(self.this_mod_def, f'window.{self.btg_sys_name}.{current_mod_name}')
					.replace(self.whole_sys_def, f'window.{self.btg_sys_name}')
					.replace(self.storage_def, f'window.{self.btg_sys_name_storage}')
				)

				# The module has to be declared before we can add stuff to it...
				# It's possible to create a file defining all these modules, but it'd be required to manually link it
				# it's not a peoblem when it's a single file, becuase all we have to do is simply declare this somewhere in the top.
				# But when it's a proper multi-file system - it either has to be a separate file declaring all this stuff
				# or simply try to add this in the very beginning of every module file IF NEEDED
				if mfile.suffix.lower() == '.js':
					evaluated = f'if (!window.bootlegger.{current_mod_name}){{window.bootlegger.{current_mod_name}={{}}}}' + '\n' + evaluated


				# now append it to the pool
				# (for singlefile thingy)
				if mfile.suffix.lower() == '.js':
					self.js_mods[mod.basename].append(evaluated)
				if mfile.suffix.lower() == '.css':
					self.css_mods[mod.basename].append(evaluated)



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
			return

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

		# then appened remaining ones
		for remaining_module in self.js_mods:
			modules_buffer_js.append(self.js_mods[remaining_module])
			modules_buffer_css.append(self.css_mods[remaining_module])

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
		import json
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
		unit_array = f"""new Uint8Array([{','.join([str(b) for b in vpath.read_bytes()])}])"""

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

		self.wrap_autofunc((
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

		# comp_file += ('\n'*10).join(self.processed_js)
		for code in self.processed_js:
			comp_file += ('\n'*5).join(code)




		return comp_file






	def exec_onefile(self):
		self.compile_folders()
		self.reorder_modules()
		self.process_libs()

		onefile_path = self.path_resolver(self.cfg['onefile']['output_to']) or self.cfg['jsmodules'].parent

		(onefile_path / f"""{self.cfg['sys_name']}.pwned.js""").write_bytes(self.compile_singlefile().encode())



def mdma():
	ded = bootlegger()
	ded.compile_folders()
	ded.reorder_modules()
	ded.process_libs()
	ded.exec_onefile()
	# Path('test_sex.js').write_bytes(ded.)


mdma()