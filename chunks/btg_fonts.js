
var compiled_fonts = [];
for (var font of fnt_pool)
{
	compiled_fonts.push(`
@font-face
{
	font-family: '${font.family}';
	font-weight: ${font.weight};
	font-style: ${font.ftype};
	src: url('${(window.URL || window.webkitURL).createObjectURL(new Blob([new Uint8Array(font.bt)]))}');
}
		`.trim());
}
var st = document.createElement('style');
st.id = 'bootlegger_fonts';
st.textContent = compiled_fonts.join('\n\n');
document.body.append(st);
// reset vars to free up memory
compiled_fonts = null;
fnt_pool = null;

