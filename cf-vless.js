// Minimal VLESS-over-WebSocket worker for Cloudflare Workers.
// TCP only (browsers/system-proxy use CONNECT). UDP is not supported by cloudflare:sockets.

import { connect } from 'cloudflare:sockets';

const USER_UUID = 'f0ba27ab-279d-4dd5-ad87-821d2351c2ba';
const UUID_BYTES = uuidToBytes(USER_UUID);

function uuidToBytes(uuid) {
    const hex = uuid.replace(/-/g, '');
    const arr = new Uint8Array(16);
    for (let i = 0; i < 16; i++) arr[i] = parseInt(hex.substr(i * 2, 2), 16);
    return arr;
}

function concat(a, b) {
    const out = new Uint8Array(a.length + b.length);
    out.set(a, 0);
    out.set(b, a.length);
    return out;
}

function bytesEqual(a, b) {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
    return true;
}

function parseVlessHeader(buf) {
    if (buf.length < 1 + 16 + 1 + 1 + 2 + 1) return null;
    let i = 0;
    const uuid = buf.slice(1, 17);
    i = 17;
    const addonsLen = buf[i];
    i += 1 + addonsLen;
    if (buf.length < i + 1 + 2 + 1) return null;
    const cmd = buf[i]; i++;
    const port = (buf[i] << 8) | buf[i + 1]; i += 2;
    const atyp = buf[i]; i++;
    let hostname = '';
    if (atyp === 1) {
        if (buf.length < i + 4) return null;
        hostname = `${buf[i]}.${buf[i + 1]}.${buf[i + 2]}.${buf[i + 3]}`;
        i += 4;
    } else if (atyp === 2) {
        if (buf.length < i + 1) return null;
        const len = buf[i]; i++;
        if (buf.length < i + len) return null;
        hostname = new TextDecoder().decode(buf.slice(i, i + len));
        i += len;
    } else if (atyp === 3) {
        if (buf.length < i + 16) return null;
        const parts = [];
        for (let j = 0; j < 16; j += 2) parts.push(((buf[i + j] << 8) | buf[i + j + 1]).toString(16));
        hostname = parts.join(':');
        i += 16;
    } else {
        return null;
    }
    return { uuid, cmd, hostname, port, payload: buf.slice(i) };
}

function tcpConnect(hostname, port) {
    const host = hostname.includes(':') && !hostname.startsWith('[') ? `[${hostname}]` : hostname;
    return connect(`${host}:${port}`, {});
}

export default {
    async fetch(request) {
        const upgrade = (request.headers.get('Upgrade') || '').toLowerCase();
        if (upgrade !== 'websocket') {
            return new Response('not found', { status: 404, headers: { 'Content-Type': 'text/plain' } });
        }
        const pair = new WebSocketPair();
        const [client, server] = Object.values(pair);
        server.accept();
        handleSession(server);
        return new Response(null, { status: 101, webSocket: client });
    },
};

async function handleSession(ws) {
    let headerParsed = false;
    let headerBuf = new Uint8Array(0);
    let remoteWriter = null;
    let remoteReader = null;
    const respHeader = new Uint8Array([0, 0]);

    async function pumpRemote() {
        try {
            while (true) {
                const { done, value } = await remoteReader.read();
                if (done) {
                    try { ws.close(1000); } catch (e) { }
                    return;
                }
                if (value && value.length) {
                    ws.send(value);
                }
            }
        } catch (e) {
            try { ws.close(1000); } catch (e2) { }
        }
    }

    ws.addEventListener('message', async (event) => {
        try {
            let data;
            if (event.data instanceof ArrayBuffer) {
                data = new Uint8Array(event.data);
            } else if (event.data instanceof Uint8Array) {
                data = event.data;
            } else if (event.data && event.data.arrayBuffer) {
                data = new Uint8Array(await event.data.arrayBuffer());
            } else {
                data = new TextEncoder().encode(String(event.data));
            }
            if (!headerParsed) {
                headerBuf = concat(headerBuf, data);
                const parsed = parseVlessHeader(headerBuf);
                if (!parsed) return;
                headerParsed = true;
                if (!bytesEqual(parsed.uuid, UUID_BYTES)) {
                    try { ws.close(3405, 'invalid user'); } catch (e) { }
                    return;
                }
                if (parsed.cmd !== 1) {
                    // TCP only: reject UDP/XUDP cleanly
                    try { ws.close(); } catch (e) { }
                    return;
                }
                const socket = tcpConnect(parsed.hostname, parsed.port);
                remoteWriter = socket.writable.getWriter();
                remoteReader = socket.readable.getReader();
                ws.send(respHeader);
                if (parsed.payload.length) {
                    await remoteWriter.write(parsed.payload);
                }
                pumpRemote();
            } else if (remoteWriter) {
                await remoteWriter.write(data);
            }
        } catch (e) {
            try { ws.close(); } catch (e2) { }
        }
    });

    ws.addEventListener('close', () => {
        try { remoteWriter && remoteWriter.close(); } catch (e) { }
    });

    ws.addEventListener('error', () => {
        try { remoteWriter && remoteWriter.close(); } catch (e) { }
    });
}