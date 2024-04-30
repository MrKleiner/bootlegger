let compiled_fonts = [];
const _blob_url = window.URL || window.webkitURL;
for (const font of fnt_pool)
{
	const font_data = [
		'@font-face{',
		'\t', `font-family: '${font.family}';`, '\n',
		'\t', `font-weight: '${font.weight}';`, '\n',
		'\t', `font-style: '${font.ftype}';`,   '\n',
		'\t', `src: url('`,
			_blob_url.createObjectURL(
				new Blob([_btg_sys_util.base64DecToArr(font.bt)])
			),
		`');`, '\n',
		'}',
	];

	compiled_fonts.push(font_data.join(''));
}
const style_dom = document.createElement('style');
style_dom.id = 'bootlegger_fonts';
style_dom.textContent = compiled_fonts.join('\n\n');
document.body.append(style_dom);
// reset vars to free up memory
compiled_fonts = null;
fnt_pool = null;