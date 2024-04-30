const _btg_sys_util = {};

//
//
//  Base64 / binary data / UTF-8 strings utilities
//
//  https://developer.mozilla.org/en-US/docs/Web/JavaScript/Base64_encoding_and_decoding
//
//

// 
// Array of bytes to Base64 string decoding
// 
_btg_sys_util.b64ToUint6 = function(nChr){
	return nChr > 64 && nChr < 91 ?
	  nChr - 65
	: nChr > 96 && nChr < 123 ?
	  nChr - 71
	: nChr > 47 && nChr < 58 ?
	  nChr + 4
	: nChr === 43 ?
	  62
	: nChr === 47 ?
	  63
	:
	  0;
}

_btg_sys_util.base64DecToArr = function(sBase64, nBlocksSize) {
	const
		sB64Enc = sBase64.replace(/[^A-Za-z0-9\+\/]/g, ""), nInLen = sB64Enc.length,
		nOutLen = nBlocksSize ? Math.ceil((nInLen * 3 + 1 >> 2) / nBlocksSize) * nBlocksSize : nInLen * 3 + 1 >> 2, taBytes = new Uint8Array(nOutLen);

	for (let nMod3, nMod4, nUint24 = 0, nOutIdx = 0, nInIdx = 0; nInIdx < nInLen; nInIdx++) {
		nMod4 = nInIdx & 3;
		nUint24 |= _btg_sys_util.b64ToUint6(sB64Enc.charCodeAt(nInIdx)) << 6 * (3 - nMod4);
		if (nMod4 === 3 || nInLen - nInIdx === 1) {
			for (nMod3 = 0; nMod3 < 3 && nOutIdx < nOutLen; nMod3++, nOutIdx++) {
				taBytes[nOutIdx] = nUint24 >>> (16 >>> nMod3 & 24) & 255;
			}
			nUint24 = 0;
		}
	}

	return taBytes;
}


// 
// Base64 string to array encoding
// 
_btg_sys_util.uint6ToB64 = function(nUint6) {
	return nUint6 < 26 ?
	  nUint6 + 65
	: nUint6 < 52 ?
	  nUint6 + 71
	: nUint6 < 62 ?
	  nUint6 - 4
	: nUint6 === 62 ?
	  43
	: nUint6 === 63 ?
	  47
	:
	  65;
}

_btg_sys_util.base64EncArr = function(aBytes) {
	let nMod3 = 2, sB64Enc = "";

	for (let nLen = aBytes.length, nUint24 = 0, nIdx = 0; nIdx < nLen; nIdx++) {
		nMod3 = nIdx % 3;
		// REVERT TO THIS IF NOW BROKEN
		// if (nIdx > 0 && (nIdx * 4 / 3) % 76 === 0) { sB64Enc += "\r\n"; }
		   if (nIdx > 0 && (nIdx * 4 / 3) % 76 === 0) { sB64Enc += ""; }
		nUint24 |= aBytes[nIdx] << (16 >>> nMod3 & 24);
		if (nMod3 === 2 || aBytes.length - nIdx === 1) {
			sB64Enc += String.fromCodePoint(
				_btg_sys_util.uint6ToB64(nUint24 >>> 18 & 63),
				_btg_sys_util.uint6ToB64(nUint24 >>> 12 & 63),
				_btg_sys_util.uint6ToB64(nUint24 >>> 6 & 63),
				_btg_sys_util.uint6ToB64(nUint24 & 63)
			);
			nUint24 = 0;
		}
	}

	return sB64Enc.substr(0, sB64Enc.length - 2 + nMod3) + (nMod3 === 2 ? '' : nMod3 === 1 ? '=' : '==');
}


// 
// UTF-8 array to JS string and vice versa
// 

// todo: also implement these improvements in toybox.
_btg_sys_util.UTF8ArrToStr = function(aBytes) {
	// todo: is array approach actually better?
	const sView = [];

	for (let nPart, nLen = aBytes.length, nIdx = 0; nIdx < nLen; nIdx++) {
		nPart = aBytes[nIdx];
		sView.push(String.fromCodePoint(
			nPart > 251 && nPart < 254 && nIdx + 5 < nLen ? /* six bytes */
			/* (nPart - 252 << 30) may be not so safe in ECMAScript! So...: */
			 (nPart - 252) * 1073741824 + (aBytes[++nIdx] - 128 << 24) + (aBytes[++nIdx] - 128 << 18) + (aBytes[++nIdx] - 128 << 12) + (aBytes[++nIdx] - 128 << 6) + aBytes[++nIdx] - 128
			: nPart > 247 && nPart < 252 && nIdx + 4 < nLen ? /* five bytes */
			 (nPart - 248 << 24) + (aBytes[++nIdx] - 128 << 18) + (aBytes[++nIdx] - 128 << 12) + (aBytes[++nIdx] - 128 << 6) + aBytes[++nIdx] - 128
			: nPart > 239 && nPart < 248 && nIdx + 3 < nLen ? /* four bytes */
			 (nPart - 240 << 18) + (aBytes[++nIdx] - 128 << 12) + (aBytes[++nIdx] - 128 << 6) + aBytes[++nIdx] - 128
			: nPart > 223 && nPart < 240 && nIdx + 2 < nLen ? /* three bytes */
			 (nPart - 224 << 12) + (aBytes[++nIdx] - 128 << 6) + aBytes[++nIdx] - 128
			: nPart > 191 && nPart < 224 && nIdx + 1 < nLen ? /* two bytes */
			 (nPart - 192 << 6) + aBytes[++nIdx] - 128
			: /* nPart < 127 ? */ /* one byte */
			  nPart
		));
	}

	return sView.join('');
}

_btg_sys_util.strToUTF8Arr = function(sDOMStr) {
	let aBytes, nChr, nStrLen = sDOMStr.length, nArrLen = 0;

	// mapping...

	for (let nMapIdx = 0; nMapIdx < nStrLen; nMapIdx++) {
		nChr = sDOMStr.codePointAt(nMapIdx);
		if (nChr > 65536) {
			nMapIdx++;
		}
		nArrLen +=
			nChr     < 0x80 ?
			1 : nChr < 0x800 ?
			2 : nChr < 0x10000 ?
			3 : nChr < 0x200000 ?
			4 : nChr < 0x4000000 ?
			5 : 6;
	}

	aBytes = new Uint8Array(nArrLen);

	// transcription...

	for (let nIdx = 0, nChrIdx = 0; nIdx < nArrLen; nChrIdx++) {
		nChr = sDOMStr.codePointAt(nChrIdx);
		if (nChr < 128) {
			/* one byte */
			aBytes[nIdx++] = nChr;
		} else if (nChr < 0x800) {
			/* two bytes */
			aBytes[nIdx++] = 192 + (nChr >>> 6);
			aBytes[nIdx++] = 128 + (nChr & 63);
		} else if (nChr < 0x10000) {
			/* three bytes */
			aBytes[nIdx++] = 224 + (nChr >>> 12);
			aBytes[nIdx++] = 128 + (nChr >>> 6 & 63);
			aBytes[nIdx++] = 128 + (nChr & 63);
		} else if (nChr < 0x200000) {
			/* four bytes */
			aBytes[nIdx++] = 240 + (nChr >>> 18);
			aBytes[nIdx++] = 128 + (nChr >>> 12 & 63);
			aBytes[nIdx++] = 128 + (nChr >>> 6 & 63);
			aBytes[nIdx++] = 128 + (nChr & 63);
			nChrIdx++;
		} else if (nChr < 0x4000000) {
			/* five bytes */
			aBytes[nIdx++] = 248 + (nChr >>> 24);
			aBytes[nIdx++] = 128 + (nChr >>> 18 & 63);
			aBytes[nIdx++] = 128 + (nChr >>> 12 & 63);
			aBytes[nIdx++] = 128 + (nChr >>> 6 & 63);
			aBytes[nIdx++] = 128 + (nChr & 63);
			nChrIdx++;
		} else /* if (nChr <= 0x7fffffff) */ {
			/* six bytes */
			aBytes[nIdx++] = 252 + (nChr >>> 30);
			aBytes[nIdx++] = 128 + (nChr >>> 24 & 63);
			aBytes[nIdx++] = 128 + (nChr >>> 18 & 63);
			aBytes[nIdx++] = 128 + (nChr >>> 12 & 63);
			aBytes[nIdx++] = 128 + (nChr >>> 6 & 63);
			aBytes[nIdx++] = 128 + (nChr & 63);
			nChrIdx++;
		}
	}

	return aBytes;
}


// Shortcuts
_btg_sys_util.btoa = function(st){
	if (!st){return ''}
	return _btg_sys_util.base64EncArr(_btg_sys_util.strToUTF8Arr(st))
}

_btg_sys_util.atob = function(st){
	if (!st){return ''}
	return _btg_sys_util.UTF8ArrToStr(_btg_sys_util.base64DecToArr(st))
}


// Quick string encoding (deprecated soon)
_btg_sys_util.u8btoa = function(st) {
    return _btg_sys_util.btoa(unescape(encodeURIComponent(st)));
}
// Decode
_btg_sys_util.u8atob = function(st) {
    return decodeURIComponent(escape(_btg_sys_util.atob(st)));
}

Object.freeze(_btg_sys_util);

// window.bootlegger_sys_funcs = new btg_sys();