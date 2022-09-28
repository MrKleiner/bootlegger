


class bootlegger:
	def __init__(self, cfgpath='nil'):
		from pathlib import Path
		import json

		try:
			read_cfg = Path(sys.argv[1]).read_text().split('\n')
			clear_cfg = [ln for ln in read_cfg if not (ln.strip().startswith('//'))]
			cfg_json = json.loads('\n'.join(nc_cfg))
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
			'bin_fonts': (None, str),
			'variables': (None, str)
		}

		defaults_onlyfile = {
			'output_to': (None, str),
			'file_header': (None, str),
			'code_header': (None, str),
			'file_footer': (None, str),
			'sign_libs': (True, bool),
			'libs': (None, str),
			'libs_order': ([], list),
			'add_libs': ([], list)
		}

		self.cfg = {}

		# merge provided params with dfault
		# compare: defaults --> provided
		# basically, populate the local cfg with either provided or default
		for cfg_entry in defauls:
			# write default if parameter does not exist in the provided dict or is of the wrong type, else - use provided
			self.cfg[cfg_entry] = defauls[cfg_entry] if (not isinstance(cfg_json.get(cfg_entry), defauls[cfg_entry][1]) or not cfg_json.get(cfg_entry)) else cfg_json.get(cfg_entry)

		# merge onefile params with default
		if cfg_json.get('onefile'):
			for cfg_onef in defaults_onlyfile:
				self.cfg['onefile'][cfg_onef] = defaults_onlyfile[cfg_onef] if (not isinstance(cfg_json['onefile'].get(cfg_onef), defaults_onlyfile[cfg_onef][1]) or not cfg_json['onefile'].get(cfg_onef)) else cfg_json['onefile'].get(cfg_onef)
		else:
			self.cfg['onefile'] = False




		"""
		self.cfg = {
			'jsmodules': 		None if (cfg_json.get('jsmodules') == 			True or not cfg_json.get('jsmodules')) 	else 		cfg_json.get('jsmodules'),
			'sys_name': 		None if (cfg_json.get('sys_name') == 			True or not cfg_json.get('sys_name')) else 			cfg_json.get('sys_name'),
			'modules_explicit': None if (cfg_json.get('modules_explicit') == 	True or not cfg_json.get('modules_explicit')) else 	cfg_json.get('modules_explicit'),
			'project': 			None if (cfg_json.get('project') == 			True or not cfg_json.get('project')) else 			cfg_json.get('project'),
			'writename': 		None if (cfg_json.get('writename') == 			True or not cfg_json.get('writename')) else 		cfg_json.get('writename'),
			'writesuffix': 		None if (cfg_json.get('writesuffix') == 		True or not cfg_json.get('writesuffix')) else 		cfg_json.get('writesuffix'),
			'onlyfile': 		None if (cfg_json.get('onlyfile') == 			True or not cfg_json.get('onlyfile')) else 			cfg_json.get('onlyfile'),
			'onefile': 			{}	 if (cfg_json.get('onefile') == 			True or not cfg_json.get('onefile')) else 			cfg_json.get('onefile')
		}

		if not cfg_json.get('onefile') or not isinstance(cfg_json.get('onefile'), dict):
			self.cfg['onefile'] = {}
			cfg_json['onefile'] = {}

		self.cfg['onefile'] = {
			'output_to': None if (cfg_json['onefile'].get('output_to') == True or not cfg_json['onefile'].get('output_to')) else cfg_json['onefile'].get('output_to'),
			'header_pre': None if (cfg_json['onefile'].get('header_pre') == True or not cfg_json['onefile'].get('header_pre')) else cfg_json['onefile'].get('header_pre'),
			'header': None if (cfg_json['onefile'].get('header') == True or not cfg_json['onefile'].get('header')) else cfg_json['onefile'].get('header'),
			'footer': None if (cfg_json['onefile'].get('footer') == True or not cfg_json['onefile'].get('footer')) else cfg_json['onefile'].get('footer'),
			'sign_libs': None if (cfg_json['onefile'].get('sign_libs') == True or not cfg_json['onefile'].get('sign_libs')) else cfg_json['onefile'].get('sign_libs'),
			'libs': None if (cfg_json['onefile'].get('libs') == True or not cfg_json['onefile'].get('libs')) else cfg_json['onefile'].get('libs'),
		}
		"""





