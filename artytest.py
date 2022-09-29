from art import *
from pathlib import Path


with open('sex.txt', 'a', encoding='utf-8') as writepep:
	for fnt in FONT_NAMES:
		writepep.write('\n')
		writepep.write('FONT NAME: ' + fnt)
		writepep.write('\n')
		writepep.write(text2art('SEX', font=fnt))
		writepep.write('\n')





