// 虚构教学代码：真实系统仍需服务端鉴权、持久化和幂等保障。
export function applyOrderEvent(current, event) {
  if (event.version <= current.version) return current;
  return { ...current, status: event.status, version: event.version };
}
