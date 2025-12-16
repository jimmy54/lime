import { getValue } from "../../utils/obj.ts";
import { spilt_pinyin } from "./split_pinyin.ts";

export function generate_shuang_pinyin(pinyin_k_l: Array<string>) {
	const sm_map = { zh: "v", ch: "i", sh: "u" };
	const ym_map = {
		iu: "q",
		ia: "w",
		ua: "w",
		e: "e",
		uan: "r",
		ue: "t",
		ve: "t",
		ing: "y",
		uai: "y",
		u: "u",
		i: "i",
		o: "o",
		uo: "o",
		un: "p",
		a: "a",
		iong: "s",
		ong: "s",
		iang: "d",
		uang: "d",
		en: "f",
		eng: "g",
		ang: "h",
		an: "j",
		ao: "k",
		ai: "l",
		ei: "z",
		ie: "x",
		iao: "c",
		ui: "v",
		v: "v",
		ou: "b",
		in: "n",
		ian: "m",
	};
	const raw = {
		a: "aa",
		ai: "ai",
		an: "an",
		ang: "ah",
		ao: "ao",
		e: "ee",
		ei: "ei",
		en: "en",
		eng: "eg",
		er: "er",
		o: "oo",
		ou: "ou",
	};
	const dbp2fullp: Record<string, string> = {};

	for (const i of pinyin_k_l) {
		const r = getValue(raw, i);
		if (r) {
			dbp2fullp[r] = i;
			continue;
		}
		const [s, y] = spilt_pinyin(i);
		const ds = getValue(sm_map, s) ?? s;
		const dy = getValue(ym_map, y) ?? y;
		if ((ds + dy).length !== 2) continue;
		dbp2fullp[ds + dy] = i;
	}
	return dbp2fullp;
}
