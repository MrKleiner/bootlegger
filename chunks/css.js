


var pepcss = document.createElement('style');
pepcss.id = 'bootlegger_css';
pepcss.textContent = window.bootlegger_sys_funcs.UTF8ArrToStr(
	window.bootlegger_sys_funcs.base64DecToArr(cssb64)
);
document.body.append(pepcss);
cssb64 = null;




