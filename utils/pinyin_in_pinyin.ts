import type {
	PinyinAndKey,
	PinyinL,
} from "../key_map/pinyin/keys_to_pinyin.ts";

export function pinyin_in_pinyin(
	pinyin_input: PinyinL,
	token_pinyin_dy: Array<Array<string>>,
) {
	const token_pinyin: PinyinAndKey[] = [];
	let pyeq = true;
	if (pinyin_input.length >= token_pinyin_dy.length) {
		for (const [i, ps] of token_pinyin_dy.entries()) {
			const input_posi = pinyin_input[i];
			const zi_posi = ps;
			let find_zi_eq = false;
			for (const p of zi_posi) {
				const x = input_posi.find((x) => x.py === p || x.py === "*");
				if (x) {
					token_pinyin.push(x);
					find_zi_eq = true;
					break;
				}
			}
			if (!find_zi_eq) {
				pyeq = false;
				break;
			}
		}
		return pyeq ? token_pinyin : false;
	}
	return false;
}
