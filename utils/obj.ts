export function getValue<T>(
	obj: Record<string, T>,
	key: string,
): T | undefined {
	return obj[key];
}
