// Deterministic OpenAI-compatible chat-completions mock for gate tests.
// Turn 1 (no tool message yet): emits one tool call taken from MOCK_TOOL / MOCK_ARGS.
// Turn 2+: emits a final text that echoes the last tool result, so the test can grep it.
import http from "node:http";
import fs from "node:fs";
const port = Number(process.env.MOCK_PORT ?? 18080);
const log = process.env.MOCK_LOG ?? "/dev/null";
const tool = process.env.MOCK_TOOL ?? "bash";
const args = process.env.MOCK_ARGS ?? JSON.stringify({ command: "echo hi" });
function sse(res, chunks) {
  res.writeHead(200, { "content-type": "text/event-stream", "cache-control": "no-cache" });
  for (const c of chunks) res.write(`data: ${JSON.stringify(c)}\n\n`);
  res.end("data: [DONE]\n\n");
}
const base = { id: "mock-1", object: "chat.completion.chunk", created: 0, model: "mock" };
http.createServer((req, res) => {
  let body = "";
  req.on("data", (d) => (body += d));
  req.on("end", () => {
    fs.appendFileSync(log, body + "\n");
    if (req.url?.endsWith("/models")) {
      res.writeHead(200, { "content-type": "application/json" });
      return res.end('{"data":[{"id":"mock"}]}');
    }
    const msgs = JSON.parse(body || "{}").messages ?? [];
    const toolMsgs = msgs.filter((m) => m.role === "tool");
    if (toolMsgs.length === 0) {
      return sse(res, [
        {
          ...base,
          choices: [
            {
              index: 0,
              delta: {
                role: "assistant",
                tool_calls: [{ index: 0, id: "call_1", type: "function", function: { name: tool, arguments: args } }],
              },
              finish_reason: null,
            },
          ],
        },
        { ...base, choices: [{ index: 0, delta: {}, finish_reason: "tool_calls" }] },
      ]);
    }
    const last = toolMsgs[toolMsgs.length - 1];
    const text = typeof last.content === "string" ? last.content : JSON.stringify(last.content);
    sse(res, [
      { ...base, choices: [{ index: 0, delta: { role: "assistant", content: "TOOL_RESULT<<" + text.slice(0, 400) + ">>" }, finish_reason: null }] },
      { ...base, choices: [{ index: 0, delta: {}, finish_reason: "stop" }] },
    ]);
  });
}).listen(port, "127.0.0.1", () => console.log(`mock listening ${port}`));
