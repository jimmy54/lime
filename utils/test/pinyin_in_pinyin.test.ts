import { assertEquals } from "jsr:@std/assert@1.0.16/equals";
import { pinyin_in_pinyin } from "../pinyin_in_pinyin.ts";
import { PinyinAndKey } from "../../key_map/pinyin/keys_to_pinyin.ts";

Deno.test("拼音匹配", () => {
	const p1: PinyinAndKey[] = [
		{ py: "ni", key: "", preeditShow: "" },
		{ py: "hao", key: "", preeditShow: "" },
		{ py: "wo", key: "", preeditShow: "" },
	];
	assertEquals(pinyin_in_pinyin([p1], [["wo", "ni"]]), [p1[2]]);
	assertEquals(pinyin_in_pinyin([p1], [["wo", "ni"], ["shi"]]), false); // <
	assertEquals(pinyin_in_pinyin([p1, p1], [["wo", "ni"], ["shi"]]), false); // 不相等
	assertEquals(
		pinyin_in_pinyin(
			[p1, p1],
			[
				["wo", "ni"],
				["ni", "wo"],
			],
		),
		[p1[2], p1[0]],
	); // === 取首个匹配的
	assertEquals(pinyin_in_pinyin([p1, p1], [["wo", "ni"]]), [p1[2]]); // 要匹配的在输入里面
});
