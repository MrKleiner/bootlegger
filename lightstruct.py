






class lightstruct:
	"""
	A class to easily get file headers, like in C.
	Except this is all lies compared to C
	"""

	# def __new__(cls, ref, **args):
	# 	return super().__new__(cls, ref, args) 

	def __init__(self, ref, **args):
		import sys
		from pathlib import Path
		self.Path = Path

		self.sys = sys
		self.struct = args
		self.is_template = False
		for arg in args:
			if len(args[arg]) < 2:
				self.struct[arg] = (args[arg][0], 1)
			else:
				self.struct[arg] = args[arg]

		# print(args)
		if ref != None:
			self.fl_path = ref
			self.fl_ref = open(str(ref), 'r+b')
		else:
			self.is_template = True

	def __getitem__(self, gt):
		return self.read_rule_from_offs_file(gt)

	def __setitem__(self, rname, nv):
		return self.upd_chunk(rname, nv)

	def dump_header(self):
		allhead = {}
		for hd in self.struct:
			allhead[hd] = self[hd]

		return allhead

	def read_rule_from_offs_file(self, rname):
		import struct

		offs = self.eval_offs(rname)

		self.fl_ref.seek(offs, 0)

		rule = self.struct[rname]

		if len(rule) < 2:
			amt = 1
		else:
			amt = rule[1]

		result = []

		for one in range(amt):
			if rule[0] == str:
				result.append(self.fl_ref.read(1).decode())

			if rule[0] == int:
				result.append(int.from_bytes(self.fl_ref.read(4), self.sys.byteorder))

			if rule[0] == 'short':
				result.append(int.from_bytes(self.fl_ref.read(2), self.sys.byteorder))

			if rule[0] == 'long':
				result.append(int.from_bytes(self.fl_ref.read(8), self.sys.byteorder))

			if rule[0] == float:
				result.append(struct.unpack('f', self.fl_ref.read(4))[0])

		return tuple(result)

	# eval the amount of bytes taken by a single rule
	def eval_amount(self, rule):
		total_offs = 0
		if rule[0] == str:
			total_offs += rule[1]

		if rule[0] == float or rule[0] == int:
			total_offs += rule[1] * 4

		if rule[0] == 'short':
			total_offs += rule[1] * 2

		if rule[0] == 'long':
			total_offs += rule[1] * 8

		return total_offs

	def eval_offs(self, rulename):
		total_offs = 0
		for rl in self.struct:
			if rulename == rl:
				break
			rule = self.struct[rl]
			total_offs += self.eval_amount(rule)

		return total_offs

	def upd_chunk(self, rname, newval):
		import struct as enc

		rule = self.struct[rname]

		if len(newval) != rule[1]:
			return False

		tgt_offs = self.eval_offs(rname)

		self.fl_ref.seek(tgt_offs, 0)

		if rule[0] == str:
			for st in newval:
				val = st
				if not isinstance(st, bytes):
					val = st.encode()
				self.fl_ref.write(val)

		if rule[0] == float:
			for fl in newval:
				self.fl_ref.write(enc.pack('f', fl))

		if rule[0] == int:
			for intg in newval:
				self.fl_ref.write(intg.to_bytes(4, self.sys.byteorder))

		if rule[0] == 'short':
			for intg in newval:
				self.fl_ref.write(intg.to_bytes(2, self.sys.byteorder))

		if rule[0] == 'long':
			for intg in newval:
				self.fl_ref.write(intg.to_bytes(8, self.sys.byteorder))



	# basically overwrite the header struct with default values
	def flush(self):
		for rule in self.struct:
			self.fl_ref.write(bytes(self.eval_amount(self.struct[rule])))

	# reserve bytes in a file OR apply this pattern to an existing file
	def apply_to_file(self, flpath):
		if not self.is_template == True:
			return None

		# return super().__new__(lightstruct, flpath, self.struct)
		pth = self.Path(flpath)
		doflush = False
		if not pth.is_file():
			pth.write_bytes(b'')
			doflush = True

		created = lightstruct(pth, **self.struct)

		if doflush == True:
			created.flush()

		return created



		



if __name__ == '__main__':
	from pathlib import Path
	import json, os
	from random import random

	os.system('cls')

	generic = lightstruct(
		r'E:\!webdesign\cbtool\proto\map\sample_cubemap_sex.vtf',
		signature =      (str, 4),
		version =        (int, 2),
		headerSize =     (int, 1),
		width =          ('short', 1),
		height =         ('short', 1),
		flags =          (int, 1),
		frames =         ('short', 1),
		firstFrame =     ('short', 1),
		padding0 =       (str, 4),
		reflectivity =   (float, 3),
		padding1 =       (str, 4),
		bumpmapScale =   (float, 1)
	)
	print('')
	print('')
	print('')

	print('generic triple float', generic['reflectivity'][1])
	generic['reflectivity'] = (0.325, random(), 0.347)
	print('generic NEW triple float',generic['reflectivity'][1])

	generic_dump_head = generic.dump_header()

	for generic_h in generic_dump_head:
		print(generic_h, generic_dump_head[generic_h])

	print('')
	print('')
	print('')

	generic_new_path = Path(r'E:\!webdesign\cbtool\proto\map\generic_new.lol')
	generic_new_path.write_bytes(b'')

	generic_new = lightstruct(
		generic_new_path,
		signature =      (str, 4),
		version =        (int, 2),
		headerSize =     (int, 1),
		width =          ('short', 1),
		height =         ('short', 1),
		flags =          (int, 1),
		frames =         ('short', 1),
		firstFrame =     ('short', 1),
		padding0 =       (str, 4),
		reflectivity =   (float, 3),
		padding1 =       (str, 4),
		bumpmapScale =   (float, 1)
	)

	generic_new.flush()

	generic_new_headers = generic_new.dump_header()

	for generic_new_h in generic_new_headers:
		print(generic_new_h, generic_new_headers[generic_new_h])


	# template
	templ = lightstruct(
		None,
		signature =      (str, 4),
		version =        (int, 2),
		headerSize =     (int, 1),
		width =          ('short', 1),
		height =         ('short', 1),
		flags =          (int, 1),
		frames =         ('short', 1),
		firstFrame =     ('short', 1),
		padding0 =       (str, 4),
		reflectivity =   (float, 3),
		padding1 =       (str, 4),
		bumpmapScale =   (float, 1)
	)

	Path('E:/!webdesign/cbtool/proto/map/generic_new1.lol').unlink(missing_ok=True)
	Path('E:/!webdesign/cbtool/proto/map/generic_new2.lol').unlink(missing_ok=True)

	templ1 = Path('E:/!webdesign/cbtool/proto/map/generic_new1.lol')
	templ1_ref = templ.apply_to_file(templ1)
	print('')
	print(templ1_ref['width'])
	templ1_ref['width'] = (64,)
	print(templ1_ref['width'])

	templ2 = Path('E:/!webdesign/cbtool/proto/map/generic_new2.lol')
	templ2_ref = templ.apply_to_file(templ2)
	print('')
	print(templ2_ref['width'])
	templ2_ref['width'] = (128,)
	print(templ2_ref['width'])

	print(templ1_ref['width'])
