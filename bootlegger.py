from pathlib import Path as PathMain
import json, sys, io, shutil, base64


THISDIR = PathMain(__file__).parent

MODULE_REF =  b'$this'
SYS_REF =     b'$all'
STORAGE_REF = b'$storage'
BTG_SYS_CONSTANTS = b'bootlegger_storage'

STR_FONT_PREFAB = (THISDIR / 'chunks' / 'font.css').read_bytes()

class Path(type(PathMain())):
	@property
	def basename(self):
		return self.name.split('.')[0]


def multi_replace(tgt_bytes, replacements):
	if type(replacements) == dict:
		tgt_iter = replacements.items()
	else:
		tgt_iter = replacements

	cv_dict = {
		bytes: {
			bytes: lambda e: e,
			str: lambda e: e.encode(),
		},
		str: {
			bytes: lambda e: e.decode(),
			str: lambda e: e,
		}
	}

	src_data_type = type(tgt_bytes)

	for query, replace_with in tgt_iter:
		# todo: smarter way of achieving this
		tgt_bytes = tgt_bytes.replace(
			cv_dict[src_data_type][type(query)](query),
			cv_dict[src_data_type][type(replace_with)](replace_with),
		)
	return tgt_bytes



class BTGWritePaths:
	def __init__(self, btg):
		self.btg = btg
		self._modules_out_dir = None
		self._fonts_index = None
		self._singlefile = None

	@property
	def modules_out_dir(self):
		if self._modules_out_dir != None:
			return self._modules_out_dir

		modules_dir = self.btg.resolve_path(self.btg.cfg['jsmodules'])
		print('Modules dir in out', modules_dir)
		tgt_write_dir = self.btg.cfg['writename']
		print('tgt write dir in out', modules_dir)

		# If not explicitely specified - write next to sources
		if not tgt_write_dir:
			tgt_write_dir = (
				modules_dir.parent /
				f"""{modules_dir.name}{self.btg.cfg['writesuffix']}"""
			)
			print('Writing next to sources:', tgt_write_dir)
		else:
			# If project is specified - try writing relative to it
			# Else - try relative to sources
			write_base = self.btg.cfg.project_dir or modules_dir.parent
			tgt_write_dir = (write_base / tgt_write_dir).resolve()
			print('Writing next to project:', tgt_write_dir, write_base, tgt_write_dir)

		if not tgt_write_dir.parent.exists() or tgt_write_dir == modules_dir:
			self._modules_out_dir = False
		else:
			self._modules_out_dir = tgt_write_dir

		print('Resolved tgt write dir', self._modules_out_dir)
		return self._modules_out_dir

	def resolve_path(self, query):
		if not query:
			return None

		query = Path(str(query))

		# 1 - Check if the path is absolute
		#     and exists already
		if query.is_absolute():
			if query.parent.is_dir():
				return query

		# 2 - check relative to the project
		if self.btg.cfg.project_dir:
			project_relative = (self.btg.cfg.project_dir / query).resolve()
			if project_relative.parent.is_dir():
				return project_relative

		# 3 - check relative to the modules dir
		if self.modules_out_dir:
			modules_relative = (self.modules_out_dir / query).resolve()
			if modules_relative.parent.is_dir():
				return project_relative

		# Finally return None, if the path could no be resolved
		return None

	@property
	def fonts_index(self):
		if self._fonts_index != None:
			return self._fonts_index

		# Try using the path provided in the config
		tgt_path = self.resolve_path(self.btg.cfg['fonts']['output_tgt'])
		if not tgt_path:
			self._fonts_index = False
		else:
			self._fonts_index = tgt_path

		return self._fonts_index

	@property
	def singlefile(self):
		if self._singlefile != None:
			return self._singlefile

		# Try using the path provided in the config
		tgt_path = self.resolve_path(self.btg.cfg['onefile']['output_tgt'])
		if not tgt_path:
			self._singlefile = False
		else:
			self._singlefile = tgt_path

		return self._singlefile



class BTGConfig:
	DEFAULTS_BASE = {
		'jsmodules':           ('modules',      str, False ),
		'project':             (None,           str,       ),
		'writename':           (None,           str, False ),
		'writesuffix':         ('_c',           str, False ),
		'simplify':            (0,              int,       ),
		'sys_name':            ('__bootlegger', str, False ),
		'collapse_modules':    (False,          bool,      ),
		'fonts':               ({},             dict,      ),
		'onefile':             ({},             dict,      ),
		# 'art':                 (True, bool),
		'sync':                ({},             dict,      ),
		'root_module_name':    ('window.',      str, False ),
		'css_context':         (True,           bool,      ),
		'css_context_symbol':  ('~~',           str, False ),
		'use_global_ctx_prop': (False,          bool,False ),
	}
	DEFAULTS_SYNC = {
		'do_sync':   (True, bool, ),
		'dest':      (None, str,  ),
		'loc':       (None, str,  ),
		'auth':      (None, str,  ),
		'sync_mods': (True, bool, ),
		'folders':   ([],   list, )
	}
	DEFAULTS_ONEFILE = {
		'do_onefile':            (False, bool),
		'onefile_only':          (False, bool),
		'output_tgt':            ('compound.js', str),
		'file_header':           (None, str),
		'scenario':              ([], list),
		'sign_libs':             (True, bool),
		'libs':                  (None, str),
		'libs_order':            ([], list),
		'add_libs':              ([], list),
		'module_order':          ([], list),
		'bin_fonts':             (None, str),
		'variables':             (None, str),
		'separate_module_files': (False, bool),
	}
	DEFAULTS_FONTS = {
		'do_fonts':    (False,            bool,      ),
		'src_dir':     ('fonts',          str, False ),
		'output_tgt':  ('font_index.css', str, False ),
		'url_prefix':  ('',               str,       ),
	}
	DEFAULTS_CLS_REFERENCE = {
		# !%~ pause ?= _pause, resume ?= _resume
		'definition_symbol': ('!%~', bool, ),
		'async_prefix':      ('?',   str,  ),
	}
	CFG_GRP_DICT = {
		'sync':    DEFAULTS_SYNC,
		'onefile': DEFAULTS_ONEFILE,
		'fonts':   DEFAULTS_FONTS,
		'cls':     DEFAULTS_CLS_REFERENCE,
	}

	# input_data can be either a dict
	# or a path pointing to a json file
	def __init__(self, input_data):
		self.cfg_file_path = None
		self.cfg_file_dir = None
		print('Input cfg data:', input_data)
		if type(input_data) != dict:
			# todo: this was moved up, becuase input_data
			# gets overridden with a json dict
			self.cfg_file_path = Path(input_data)
			self.cfg_file_dir = Path(input_data).parent

			# Some editors recognize // as comments in json files.
			# This adds a VERY primitive support for that.
			# Don't lie, comments in json files are handy.
			lines = Path(input_data).read_bytes().split(b'\n')
			input_data = json.loads(
				b'\n'.join([l for l in lines if not l.strip().startswith(b'//')])
			)

		# Base data
		self.cfg_data = self.merge(
			input_data,
			self.DEFAULTS_BASE
		)

		print('CFG data:', self.cfg_data)

		# Config groups
		# todo: merge right into cfg_data
		for grp_name, grp_data in self.CFG_GRP_DICT.items():
			input_cfg = input_data.get(grp_name)
			if input_cfg:
				self.cfg_data[grp_name] = self.merge(
					input_cfg,
					grp_data
				)
			else:
				print('CFG Group', grp_name, 'Not present')
				self.cfg_data[grp_name] = self.merge(
					{},
					grp_data
				)

		self.cfg_data['jsmodules'] = Path(self.cfg_data['jsmodules'])

		# todo: wtf is this ?
		self.project_dir = None
		if self.cfg_data['project']:
			self.project_dir = Path(self.cfg_data['project'])
			if not self.project_dir.is_dir():
				self.project_dir = None

	@staticmethod
	def merge(input_data, defaults):
		merge_result = {}
		for cfg_key in defaults:
			def_value, tgt_type, *can_be_falsy = defaults[cfg_key]
			input_entry_data = input_data.get(cfg_key)

			if not isinstance(input_entry_data, tgt_type):
				merge_result[cfg_key] = def_value
			else:
				if can_be_falsy and not can_be_falsy[0] and not input_entry_data:
					merge_result[cfg_key] = def_value
				else:
					merge_result[cfg_key] = input_entry_data

		return merge_result

	def __getitem__(self, keyname):
		return self.cfg_data.get(keyname)


class BTGEasySync:
	def __init__(self, btg):
		self.btg = btg
		self.cfg = btg.cfg['sync']


class ScenarioEntry:
	def __init__(self, entry_dict):
		self.entry_dict = entry_dict

		self._target = None
		self._wrap = False
		self._process = False

		self.bad_target = ('.', '../', '', '/', '\\', './',)
		self.sys_targets = ('?main',)

	@property
	def target(self):
		if self._target != None:
			return self._target

		data = self.entry_dict.get('target', '').strip()

		if data.lower() in self.sys_targets:
			self._target = data.lower()
			return self._target

		if not data or (data in self.bad_target):
			self._target = False
			return None

		self._target = data
		return self._target

	@property
	def wrap(self):
		return self.entry_dict.get('wrap', False)

	@property
	def process(self):
		return self.entry_dict.get('process', False)
	


class OneFile:
	def __init__(self, btg):
		self.btg = btg
		self.cfg = btg.cfg['onefile']
		self.buf = io.BytesIO()

	# Only used for abstract files for now.
	# Replaces:
	#  - $this -> Modules dir reference
	#  - $all -> Modules dir reference
	#  - $storage -> Variables storage
	def place_js_constants(self, tgt_bytes):
		if not type(tgt_bytes) in (str, bytes):
			print(
				'Fatal: Could not place JS constants into an',
				"""arbitrary buffer, because it's of type""",
				type(tgt_bytes), 'but can only be of type bytes|str',
			)
			return ''

		return multi_replace(tgt_bytes, [
			(
				MODULE_REF,
				self.btg.base_js_path
			),
			(
				SYS_REF,
				self.btg.base_js_path
			),
			(
				STORAGE_REF,
				f"""{self.btg.cfg['root_module_name']}{BTG_SYS_CONSTANTS}"""
			)
		])

	# Write modules composite data to the buffer
	def write_main(self):
		if self.cfg['separate_module_files']:
			for mdname, mdata in self.btg.modules.items():
				for _, jsbuf in mdata['js']:
					with WrapJSCode(self.buf) as wrap:
						wrap.write(jsbuf)
		else:
			for mdname, mdata in self.btg.modules.items():
				with WrapJSCode(self.buf) as wrap:
					for _, jsbuf in mdata['js']:
						wrap.write(jsbuf)

	# Write the resulting buffer to a file
	def write_file(self):
		if not self.btg.write_paths.singlefile:
			print(
				'Could not resolve singlefile write path:',
				self.btg.write_paths.singlefile
			)
			return
		self.btg.write_paths.singlefile.write_bytes(self.buf.getvalue())

	def write_css(self):
		self.buf.write(b'\n')
		with WrapJSCode(self.buf) as wrap:
			wrap.write('let cssb64 = ['.encode())
			for mdname, mdata in self.btg.modules.items():
				for _, jsbuf in mdata['css']:
					Bootlegger.buf_line_write(self.buf, [
						'`', base64.b64encode(jsbuf.getvalue()), '`,'
					])
			wrap.write('];'.encode())
			wrap.write(b'\n')

			wrap.write(
				(THISDIR / 'chunks' / 'bin_css.js').read_bytes()
			)

	def run(self):
		# Write global header file
		fheader = self.btg.resolve_path(self.cfg['file_header'], 'file')
		if fheader:
			self.buf.write(fheader.read_bytes())
			self.buf.write(b'\n'*5)
		else:
			print('File header not present, not writing')

		# todo: write libs here
		# todo: write sys funcs here
		# todo: test: quick sys funcs write
		self.buf.write(
			(THISDIR / 'chunks' / 'btg_util.js').read_bytes()
		)
		# todo: write fonts here
		# todo: write css here
		# todo: test: force write binary css
		self.write_css()
		# todo: write variables here

		# Write scenario
		# todo: separate into a function?
		main_done = False
		for sc_entry in map(ScenarioEntry, self.cfg['scenario']):
			self.buf.write(b'\n')

			if (sc_entry.target == '?main') and not main_done:
				self.write_main()
				main_done = True
				continue

			# If it's not a sys entry - treat like an abstract file
			file_path = self.btg.resolve_path(sc_entry.target, 'file')
			if not file_path:
				print(
					'WARNING: Could not resolve target path',
					sc_entry.target,
					'from a scenario entry',
					self.btg.cfg.cfg_file_dir
				)
				continue

			# Get the contents of the file
			data_bytes = file_path.read_bytes()

			# Execute actions on it, if any
			if sc_entry.process:
				data_bytes = self.place_js_constants(data_bytes)
			if sc_entry.wrap:
				with WrapJSCode(self.buf) as wrap:
					wrap.write(data_bytes)
			else:
				self.buf.write(data_bytes)

		if not main_done:
			self.write_main()

		# Write the resulting file to disk
		self.write_file()



class BTGFont:
	def __init__(self, fonts_dir, url_prefix='', no_decor=False):
		self.no_decor = no_decor
		self.fonts_dir = Path(fonts_dir)
		self.font_name = self.fonts_dir.name
		self.str_buf = None
		self.bin_buf = None
		self.font_data_index = None
		self.url_prefix = url_prefix or ''

	# A dict with all the file paths indexed
	# according to weight/style
	@property
	def data_index(self):
		if self.font_data_index:
			return self.font_data_index

		font_data = {}

		for font_file in self.fonts_dir.glob('*'):
			if not font_file.is_file():
				continue

			# todo: better way of doing this?
			fweight, fstyle, fext = font_file.name.split('.')
			fweight = int(fweight)
			fstyle = fstyle.strip()
			fext = fext.strip()

			if not font_data.get(fweight):
				font_data[fweight] = {}

			font_data[fweight][fstyle] = font_file

		self.font_data_index = font_data

	# CSS with URLs
	@property
	def str_data(self):
		if self.str_buf:
			return self.str_buf

		font_data = self.data_index
		self.str_buf = io.BytesIO()

		Bootlegger.buf_line_write(self.str_buf, [
			'/*==============================================*/',
			'\n',
			f'/*{self.fonts_dir.name}*/',
			'\n',
			'/*==============================================*/',
			'\n',
		])

		for fweight, weight_styles in self.font_data_index.items():
			for fstyle, font_file in weight_styles.items():
				css_url = f'{self.url_prefix}/{self.fonts_dir.name}/{font_file.name}'

				self.str_buf.write(
					multi_replace(STR_FONT_PREFAB, [
						('$family',   self.font_name ),
						('$weight',   str(fweight)   ),
						('$style',    fstyle         ),
						('$filepath', css_url        ),
					])
				)

				self.str_buf.write(b'\n')

		return self.str_buf

	# A stringified json dict with font file content as base64
	@property
	def bin_data(self):
		if self.bin_buf:
			return self.bin_buf

		font_data = self.data_index
		# self.str_buf = io.BytesIO()
		fonts_dict = []

		for fweight, weight_styles in self.font_data_index.items():
			for fstyle, font_file in weight_styles.items():
				fonts_dict.append({
					'family': self.font_name,
					'weight': fweight,
					'fstyle': fstyle,
					'bt': base64.b64encode(font_file.read_bytes()).decode(),
				})

		self.bin_buf = json.dumps(fonts_dict)


class WrapJSCode:
	def __init__(self, tgt_buf):
		self.buf = tgt_buf

	def __enter__(self):
		self.buf.write(b'(function() {')
		self.buf.write(b'\n')
		return self
		
	def __exit__(self, type, value, traceback):
		self.buf.write(b'\n')
		self.buf.write(b'})();')
		self.buf.write(b'\n')

	def write(self, data):
		if type(data) == bytes:
			self.buf.write(data)
		else:
			data.seek(0)
			# todo: is .read() actually any different from .getvalue() ?
			# (should be better than getvalue)
			self.buf.write(data.read())


class ModuleUnit:
	def __init__(self, btg, module_abspath):
		self.btg = btg
		self.md_path = Path(module_abspath)
		self.md_name = self.md_path.basename

		self.buffers = {
			'js':    [],
			'css':   [],
			'other': [],
		}

		self._compound_js = None
		self._compound_css = None

	@property
	def compound_js(self):
		if self._compound_js != None:
			return self._compound_js

	def __getitem__(self, tgt_item):
		if not tgt_item in self.buffers:
			print(
				'Fatal: requested', tgt_item,
				'from ModuleUnit buffers, but it does not exist'
			) 



# todo: Create custom buffer class
# with wrap functions and line writes
class Bootlegger:
	def __init__(self, cfg_data):
		self.cfg = BTGConfig(cfg_data)
		# todo: There's a miniscule amount of Geneva convention violations:
		# BTGWritePaths may or may not depend on when exactly it was
		# initialized
		self.write_paths = BTGWritePaths(self)
		self.modules = {}
		self.fonts = []

		self.js_simplify = [
			lambda l: not l.strip().startswith(b'//'),
			lambda l: not l.strip().startswith(b'//') and l.strip(),
		]

		self.one_file = OneFile(self)

	@staticmethod
	def buf_line_write(tgt_buf, lines):
		for l in lines:
			tgt_buf.write(
				l.encode() if isinstance(l, str) else l
			)

	@staticmethod
	def wrap_autoexec_func(tgt_str, indent=0, tgt_buf=None):
		buf = tgt_buf or io.BytesIO()
		buf.write(b'\t'*indent)
		buf.write(b'(function() {')
		buf.write(b'\n')
		# todo: simply replace line breaks, like '\n\t' ?
		for ln in tgt_str.split(b'\n'):
			buf.write(b'\t'*indent)
			buf.write(b'\t')
			buf.write(ln.encode())
		buf.write(b'\n')
		buf.write(b'\t'*indent)
		buf.write(b'})();')

		return buf

	def resolve_path(self, query, path_type='dir'):
		if not query:
			return

		proj_root = Path(str(self.cfg['project'])) if self.cfg['project'] else None
		query = Path(str(query))

		resolved = None

		# 1 - Check if it's absolute and exists already
		if query.exists():
			resolved = query

		# 2 - Try checking relative to the project
		#     if project was specified
		if proj_root and not resolved:
			proj_rel = (proj_root / query).resolve()
			if proj_rel.exists():
				resolved = proj_rel

		# 3 - Try checking relative to config file,
		#     if possible.
		if not resolved and self.cfg.cfg_file_dir:
			print('Final try: resolving shit', self.cfg.cfg_file_dir, query)
			cfg_dir_rel = (self.cfg.cfg_file_dir / query).resolve()
			if cfg_dir_rel.exists():
				resolved = cfg_dir_rel

		# 4 - Finally, check if the resolved path is of
		#     requested type
		if resolved:
			if (path_type == 'dir' and not resolved.is_dir()) \
			or (path_type == 'file' and not resolved.is_file()) :
				print(
					'Resolved path',
					resolved,
					'is not of required type',
					path_type
				)
				return None

		# 5: todo: security: make sure the resolved query
		# doesn't point to an obscure location

		return resolved

	@property
	def base_js_path(self):
		return f"""{self.cfg['root_module_name']}{self.cfg['sys_name']}"""

	# tgt_module is absolute path
	def process_module(self, tgt_module_dir):
		tgt_module_dir = Path(tgt_module_dir)
		tgt_module_name = tgt_module_dir.basename
		self.modules[tgt_module_name] = {
			'js':    [],
			'css':   [],
			'other': [],
		}
		tgt_module = self.modules[tgt_module_name]

		for file in tgt_module_dir.glob('*'):
			if not file.is_file():
				continue

			file_bytes = file.read_bytes()
			file_buf = io.BytesIO()

			if file.suffix != '.css':
				file_bytes = multi_replace(file_bytes, [
					(
						MODULE_REF,
						f"""{self.base_js_path}.{tgt_module_name}"""
					),
					(
						SYS_REF,
						self.base_js_path
					),
					(
						STORAGE_REF,
						f"""{self.cfg['root_module_name']}{BTG_SYS_CONSTANTS}"""
					)
				])

			if file.suffix == '.js':
				simplify = self.cfg['simplify']
				if simplify > 0:
					flines = file_bytes.split(b'\n')
					file_bytes = b'\n'.join(
						filter(self.js_simplify[simplify-1], flines)
					)

				self.buf_line_write(file_buf, [
					'\n',
					'if(!', self.base_js_path, '){', self.base_js_path, '={}};',
					'\n',

					'if(!', self.base_js_path, '.', tgt_module_name, '){',
						self.base_js_path, '.', tgt_module_name, '={}};',
					'\n',

					file_bytes
				])
				tgt_module['js'].append(
					(file.name, file_buf)
				)
				continue

			if file.suffix == '.css':
				ctx_symbol = self.cfg['css_context_symbol']
				ctx_declare = f'!{ctx_symbol}'.encode()
				css_lines = file_bytes.split(b'\n')
				ctx = None

				for li, ln in enumerate(css_lines):
					# todo: safer detection ?
					if ctx_declare in ln:
						ctx = multi_replace(ln, [
							('/*', ''),
							('*/', ''),
							(ctx_declare, '')
						]).strip()
						continue
					# important todo: .encode in advance
					if ctx_symbol.encode() in ln and ctx:
						css_lines[li] = multi_replace(ln, [
							(ctx_symbol, ctx)
						])

				# todo: is join faster than writing the lines
				# individually ?
				file_buf.write(
					b'\n'.join(css_lines)
				)
				tgt_module['css'].append(
					(file.name, file_buf)
				)
				continue

			file_buf.write(file_bytes)
			tgt_module['other'].append(
				(file.name, file_buf)
			)

	def process_fonts(self):
		fonts_dir = self.resolve_path(self.cfg['fonts']['src_dir'])
		if not fonts_dir:
			print('Bad font dir')
			return

		url_prefix = self.cfg['fonts']['url_prefix'] or f'/{fonts_dir.name}'

		for fnt in fonts_dir.glob('*'):
			if not fnt.is_dir():
				continue

			self.fonts.append(
				BTGFont(fnt, url_prefix)
			)

	def make_modules(self):
		modules_dir = self.resolve_path(self.cfg['jsmodules'])
		if not modules_dir:
			print('Modules source dir does not exist')
		for module_dir in modules_dir.glob('*'):
			if not module_dir.is_dir():
				continue

			self.process_module(module_dir)

	# Sequentially run everything according to config
	def run(self):
		# 1 - Main things first:
		#     process javascript
		self.make_modules()

		# 2 - Process fonts, if any:
		if self.cfg['fonts']['do_fonts'] and not self.cfg['onefile']['onefile_only']:
			self.process_fonts()

		module_write_tgt = self.write_paths.modules_out_dir
		if not module_write_tgt:
			print(
				'Fatal Error: Could not find a suitable place to output',
				'compiled modules.',
				'Is the output destination same as source?',
				'Does parent of the output destination exist?',
				'Sources:', self.resolve_path(self.cfg['jsmodules']),
				'Output:', module_write_tgt,
			)
			return

		# Write modules
		if not self.cfg['onefile']['onefile_only']:
			# Wipe the write destination dir
			shutil.rmtree(module_write_tgt, ignore_errors=True)

			for mdname, mdata in self.modules.items():
				for ftype in ('js', 'css', 'other'):
					for fname, fbuf in mdata[ftype]:
						write_tgt = module_write_tgt / mdname / fname
						write_tgt.parent.mkdir(parents=True, exist_ok=True)
						write_tgt.write_bytes(fbuf.getvalue())

		# Write fonts
		if self.cfg['fonts']['do_fonts'] and not self.cfg['onefile']['onefile_only']:
			print('Writing fonts')
			self.write_paths.fonts_index.unlink(missing_ok=True)
			with open(self.write_paths.fonts_index, 'wb') as fnt_idx:
				for fnt in self.fonts:
					fnt_idx.write(fnt.str_data.getvalue())
					fnt_idx.write(b'\n')

		# Write onefile
		if self.cfg['onefile']['do_onefile']:
			self.one_file.run()

		print('Done building')






class _Bootlegger:
	def __init__(self, cfgpath='nil'):
		self.js_mods = {}
		self.css_mods = {}

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
			print('vro wtf', cfg_json)
		except Exception as e:
			print('There were some problems reading the bootlegger config file...')
			print('See details:')
			raise e

		defauls = {
			'jsmodules':          (None, str),
			'sys_name':           (None, str),
			'modules_order':      ([], list),
			'project':            (None, str),
			'writename':          (None, str),
			'writesuffix':        (None, str),
			'onlyfile':           (False, bool),
			'onefile':            ({}, dict),
			'art':                (True, bool),
			'collapse':           (0, int),
			'sync':               (False, dict),
			'fonts':              (None, str),
			'root_module_name':   ('window.', str),
			'override_sys_name':  ('bootlegger', str),
			'css_context':        (True, bool),
			'css_context_symbol': ('~~', str),
		}

		defauls_sync = {
			'dest':      (None, str),
			'loc':       (None, str),
			'auth':      (None, str),
			'sync_mods': (True, bool),
			'folders':   ([], list)
		}

		defaults_onlyfile = {
			'output_to':   (None, str),
			'file_header': (None, str),
			'code_header': (None, str),
			'file_footer': (None, str),
			'sign_libs':   (True, bool),
			'libs':        (None, str),
			'libs_order':  ([], list),
			'add_libs':    ([], list),
			'bin_fonts':   (None, str),
			'variables':   (None, str)
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


		self.btg_sys_name = self.cfg['override_sys_name']

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
		# print('kys', self.cfg)
		if None in (self.cfg['jsmodules'], self.cfg['sys_name']):
			raise ValueError('jsmodules or sys_name is undefined')


	def path_resolver(self, query=None, tp='dir'):
		if query in (None, '', False, b''):
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

	def css_path(self, csstext):
		ctx_symbol = self.cfg['css_context_symbol']
		css = csstext.split('\n')
		ctx = None

		for li, ln in enumerate(css):
			if f'!{ctx_symbol}' in ln:
				ctx = ln.replace('/*', '').replace('*/', '').replace(f'!{ctx_symbol}', '').strip()
				continue
			if ctx_symbol in ln and ctx:
				css[li] = ln.replace(ctx_symbol, ctx)

		return '\n'.join(css)




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
			if cfg.get('writesuffix') != None and str(cfg.get('writesuffix')).lower() != 'auto':
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
					if self.cfg['css_context']:
						evaluated = self.css_path(mfile.read_text(encoding='UTF-8'))
					else:
						evaluated = (
							mfile.read_text(encoding='UTF-8')
							.replace(self.this_mod_def, current_mod_name)
						)
				else:
					evaluated = (
						mfile.read_text(encoding='UTF-8')
						.replace(self.this_mod_def,  f"""{self.cfg['root_module_name']}{self.btg_sys_name}.{current_mod_name}""")
						.replace(self.whole_sys_def, f"""{self.cfg['root_module_name']}{self.btg_sys_name}""")
						.replace(self.storage_def,   f"""{self.cfg['root_module_name']}{self.btg_sys_name_storage}""")
					)

				# Write the evaulated result to the compiled modules pool, if not onlyfile
				if not self.cfg['onlyfile']:
					if mfile.suffix.lower() == '.js':
						# evaluated = '\n' + f'if (!{self.cfg.root_module_name}{self.btg_sys_name}.{current_mod_name}){{{self.cfg.root_module_name}{self.btg_sys_name}.{current_mod_name}={{}}}};' + '\n' + evaluated
						evaluated = (
							'\n'
							+
							'if(!'
							+
							self.cfg['root_module_name']
							+
							self.btg_sys_name + '.'
							+
							current_mod_name
							+ '){' +
							self.cfg['root_module_name'] + self.btg_sys_name + '.' + current_mod_name
							+
							'={}};' + '\n'
							+
							evaluated
						)
						# evaluated = '\n' + f'if (!{self.cfg.root_module_name}{self.btg_sys_name}){{{self.cfg.root_module_name}{self.btg_sys_name} = {{}}}};' + '\n' + evaluated
						
						evaluated = (
							'\n'
							+
							'if(!'
							+
							self.cfg['root_module_name']
							+
							self.btg_sys_name
							+ '){' +
							self.cfg['root_module_name']
							+
							self.btg_sys_name
							+
							'={}};' + '\n'
							+
							evaluated
						)
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
					# evaluated = '\n' + f'if (!{self.cfg.root_module_name}{self.btg_sys_name}){{{self.cfg.root_module_name}{self.btg_sys_name} = {{}}}};' + '\n' + evaluated
					# evaluated = '\n' + f'if (!{self.cfg.root_module_name}{self.btg_sys_name}.{current_mod_name}){{{self.cfg.root_module_name}{self.btg_sys_name}.{current_mod_name}={{}}}};' + '\n' + evaluated
					evaluated = (
						'\n'
						+
						'if(!'
						+
						self.cfg['root_module_name']
						+
						self.btg_sys_name + '.'
						+
						current_mod_name
						+ '){' +
						self.cfg['root_module_name'] + self.btg_sys_name + '.' + current_mod_name
						+
						'={}};' + '\n'
						+
						evaluated
					)
					# evaluated = '\n' + f'if (!{self.cfg.root_module_name}{self.btg_sys_name}){{{self.cfg.root_module_name}{self.btg_sys_name} = {{}}}};' + '\n' + evaluated
					
					evaluated = (
						'\n'
						+
						'if(!'
						+
						self.cfg['root_module_name']
						+
						self.btg_sys_name
						+ '){' +
						self.cfg['root_module_name']
						+
						self.btg_sys_name
						+
						'={}};' + '\n'
						+
						evaluated
					)



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
						.replace(self.this_mod_def,  f"""{self.cfg['root_module_name']}{self.btg_sys_name}{self.btg_sys_name}.{module_binds.split(' ')[0]}""")
						.replace(self.whole_sys_def, f"""{self.cfg['root_module_name']}{self.btg_sys_name}{self.btg_sys_name}""")
						.replace(self.storage_def,   f"""{self.cfg['root_module_name']}{self.btg_sys_name}{self.btg_sys_name_storage}""")
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
		comp_file += f"""{self.cfg['root_module_name']}{self.btg_sys_name} = {{}};"""
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




if __name__ == '__main__':
	# print('Sys args', Path(sys.argv[1]))
	btg = Bootlegger(
		Path(sys.argv[1])
	)
	btg.run()

