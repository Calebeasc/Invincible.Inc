import argparse
import asyncio
from pathlib import Path

from aiohttp import ClientError, ClientSession, ClientTimeout, WSCloseCode, WSMsgType, web

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Serve a built SPA and proxy API traffic to a backend.")
    parser.add_argument("--root", required=True, help="Directory containing index.html and built assets")
    parser.add_argument("--port", type=int, required=True, help="Port to listen on")
    parser.add_argument("--backend", required=True, help="Backend origin, for example http://127.0.0.1:8742")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--proxy-prefix", action="append", default=[], help="Path prefix to proxy to the backend")
    return parser


def normalize_prefixes(prefixes: list[str]) -> tuple[str, ...]:
    normalized = []
    for prefix in prefixes:
        if not prefix.startswith("/"):
            prefix = f"/{prefix}"
        normalized.append(prefix.rstrip("/") or "/")
    return tuple(dict.fromkeys(normalized))


def should_proxy(path: str, prefixes: tuple[str, ...]) -> bool:
    for prefix in prefixes:
        if path == prefix or path.startswith(f"{prefix}/"):
            return True
    return False


def filter_headers(headers) -> dict[str, str]:
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
    }


def upstream_error_response(request: web.Request, detail: str, status: int = 503) -> web.StreamResponse:
    headers = {
        "Cache-Control": "no-store",
        "X-Proxy-Error": "upstream-unavailable",
    }
    if request.method == "HEAD":
        return web.Response(status=status, headers=headers)
    return web.json_response({"detail": detail, "upstream": request.app["backend"]}, status=status, headers=headers)


async def proxy_http(request: web.Request) -> web.StreamResponse:
    backend = request.app["backend"]
    target_url = f"{backend}{request.rel_url}"
    body = await request.read()
    headers = filter_headers(request.headers)

    try:
        async with request.app["session"].request(
            request.method,
            target_url,
            data=body if body else None,
            headers=headers,
            allow_redirects=False,
        ) as response:
            proxied_headers = filter_headers(response.headers)
            payload = await response.read()
            return web.Response(
                status=response.status,
                headers=proxied_headers,
                body=payload if request.method != "HEAD" else b"",
            )
    except (ClientError, asyncio.TimeoutError) as exc:
        return upstream_error_response(
            request,
            f"backend unavailable while proxying {request.method} {request.rel_url.path}: {type(exc).__name__}",
        )


async def proxy_websocket(request: web.Request) -> web.StreamResponse:
    backend = request.app["backend"]
    ws_server = web.WebSocketResponse()
    await ws_server.prepare(request)

    target_url = f"{backend.replace('http://', 'ws://').replace('https://', 'wss://')}{request.rel_url}"
    try:
        async with request.app["session"].ws_connect(target_url, headers=filter_headers(request.headers)) as ws_client:
            async def client_to_backend() -> None:
                async for message in ws_server:
                    if message.type == WSMsgType.TEXT:
                        await ws_client.send_str(message.data)
                    elif message.type == WSMsgType.BINARY:
                        await ws_client.send_bytes(message.data)
                    elif message.type == WSMsgType.CLOSE:
                        await ws_client.close()

            async def backend_to_client() -> None:
                async for message in ws_client:
                    if message.type == WSMsgType.TEXT:
                        await ws_server.send_str(message.data)
                    elif message.type == WSMsgType.BINARY:
                        await ws_server.send_bytes(message.data)
                    elif message.type == WSMsgType.CLOSE:
                        await ws_server.close()

            await asyncio.gather(client_to_backend(), backend_to_client())
    except (ClientError, asyncio.TimeoutError):
        await ws_server.close(code=WSCloseCode.TRY_AGAIN_LATER, message=b"backend unavailable")

    return ws_server


def resolve_static_path(root: Path, request_path: str) -> Path | None:
    relative = request_path.lstrip("/") or "index.html"
    candidate = (root / relative).resolve()
    if root not in candidate.parents and candidate != root:
        return None
    if candidate.is_dir():
        candidate = candidate / "index.html"
    if candidate.is_file():
        return candidate
    return None


async def spa_handler(request: web.Request) -> web.StreamResponse:
    path = request.rel_url.path
    prefixes = request.app["proxy_prefixes"]

    if should_proxy(path, prefixes):
        if request.headers.get("Upgrade", "").lower() == "websocket":
            return await proxy_websocket(request)
        return await proxy_http(request)

    root: Path = request.app["root"]
    static_path = resolve_static_path(root, path)
    if static_path:
        return web.FileResponse(static_path)

    return web.FileResponse(root / "index.html")


async def on_startup(app: web.Application) -> None:
    timeout = ClientTimeout(total=30, connect=5, sock_connect=5, sock_read=30)
    app["session"] = ClientSession(timeout=timeout)


async def on_cleanup(app: web.Application) -> None:
    await app["session"].close()


def main() -> None:
    args = build_parser().parse_args()
    root = Path(args.root).resolve()
    index_file = root / "index.html"
    if not index_file.is_file():
        raise SystemExit(f"SPA root missing index.html: {index_file}")

    app = web.Application()
    app["backend"] = args.backend.rstrip("/")
    app["root"] = root
    app["proxy_prefixes"] = normalize_prefixes(args.proxy_prefix)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    app.router.add_route("*", "/{tail:.*}", spa_handler)

    print(f"Serving {root} on http://{args.host}:{args.port} -> {app['backend']}")
    web.run_app(app, host=args.host, port=args.port, handle_signals=False)


if __name__ == "__main__":
    main()
