# Connector and MCP handoff

Use this reference when a video includes a tool-call, connector, or MCP-based
workflow. The final scene should explain a verified handoff, not imply that a
screenshot or browser return is proof of a server-side result.

## Safe teaching sequence

1. Open the supported connector settings in the chosen workspace host.
2. Use the documented authenticated endpoint or connection flow.
3. Confirm the tool is connected and the user is authorized.
4. Say one sentence describing the finished artifact and intended outcome.
5. Call the current supported operation.
6. Read the returned URL/identifier from the server response and open it in a
   clean context when the product permits.
7. Explain where metadata, access, or ownership can be edited afterward.

Use a generic on-screen example and replace the nouns per project:

```text
把当前这份已完成的内容发布到目标服务，并返回可分享 URL。
```

Do not show access tokens, cookies, private slugs, user emails, raw headers, or
unredacted request bodies. If the product currently requires login, keep that
boundary visible instead of promising anonymous publication. A successful
browser return or copied URL is not, by itself, a payment, ownership, or
settlement fact; use the verified server result and record its provenance.

## Visual treatment

Use the project's code/connector surface, reveal one line or state at a time,
then resolve one sanitized URL/identifier with a short hold. Keep the presenter
in a small corner or hidden while the endpoint and result are readable. The
result is the shot anchor; surrounding labels should clear rather than compete
with it.
