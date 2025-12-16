import { type Context, Hono } from "hono";
import { bearerAuth } from "hono/bearer-auth";
import { HTTPException } from "hono/http-exception";
import { logger } from "hono/logger";
import { verifyKey } from "./key.ts";
import { keys_to_pinyin } from "./key_map/pinyin/keys_to_pinyin.ts";
import { commit, single_ci } from "./main.ts";

const app = new Hono();

app.use("*", logger());
app.use(
	"/*",
	bearerAuth({
		verifyToken: (t) => {
			return verifyKey(t);
		},
	}),
);

// 辅助函数：处理查询参数
const getParam = (
	c: Context,
	key: string,
	defaultValue: string = "",
): string => {
	const value = c.req.query(key);
	return value ? decodeURIComponent(value) : defaultValue;
};

const getBoolParam = (
	c: Context,
	key: string,
	defaultValue: boolean = false,
): boolean => {
	const value = c.req.query(key);
	if (value === undefined) return defaultValue;
	return value === "true";
};

// API: 获取候选词 - POST 方法
app.post("/candidates", async (c) => {
	const body = await c.req.json<{ keys?: string }>();
	const keys = body.keys || "";

	console.log(keys);

	const pinyinInput = keys_to_pinyin(keys);
	const result = single_ci(pinyinInput);

	return c.json(result);
});

// API: 获取候选词 - GET 方法
app.get("/candidates", (c) => {
	const keys = getParam(c, "keys");

	console.log(keys);

	const pinyinInput = keys_to_pinyin(keys);
	const result = single_ci(pinyinInput);

	return c.json(result);
});

// API: 提交文字 - POST 方法
app.post("/commit", async (c) => {
	try {
		const body = await c.req.json();
		const text = body.text || "";
		const isNew = body.new ?? true;
		const shouldUpdate = body.update ?? false;

		if (!text) {
			throw new HTTPException(400, { message: "未提供文本内容" });
		}

		const userContext = await commit(text, shouldUpdate, isNew);
		console.log(userContext.join("").slice(-20));

		return c.json({
			message: "文本提交成功",
		});
	} catch (error) {
		if (error instanceof HTTPException) throw error;
		console.error("提交文本失败:", error);
		throw new HTTPException(400, { message: "请求数据格式错误" });
	}
});

// API: 提交文字 - GET 方法
app.get("/commit", async (c) => {
	try {
		const text = getParam(c, "text");
		const isNew = getBoolParam(c, "new", true);
		const shouldUpdate = getBoolParam(c, "update", false);

		if (!text) {
			throw new HTTPException(400, { message: "未提供文本内容" });
		}

		const userContext = await commit(text, shouldUpdate, isNew);
		console.log(userContext.join("").slice(-20));

		return c.json({
			message: "文本提交成功",
		});
	} catch (error) {
		if (error instanceof HTTPException) throw error;
		console.error("提交文本失败:", error);
		throw new HTTPException(400, { message: "请求参数错误" });
	}
});

export default app;
