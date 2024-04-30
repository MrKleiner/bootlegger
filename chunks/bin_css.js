// let pepcss = document.createElement('style');
// pepcss.id = 'bootlegger_css';
// pepcss.textContent = _btg_sys_util.UTF8ArrToStr(
// 	_btg_sys_util.base64DecToArr(cssb64)
// );
// document.body.append(pepcss);
// cssb64 = null;


let pepcss = document.createElement('style');
pepcss.id = 'bootlegger_css';

for (let i = 0; i < cssb64.length; i++) {
	cssb64[i] = _btg_sys_util.UTF8ArrToStr(
		_btg_sys_util.base64DecToArr(cssb64[i])
	);
}
pepcss.textContent = cssb64.join('\n');
document.body.append(pepcss);
cssb64 = null;