export default {
  async fetch(request) {
    const upgrade = request.headers.get('Upgrade');
    if (upgrade !== 'websocket') {
      return new Response('ok', { status: 200 });
    }
    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);
    server.accept();
    server.addEventListener('message', (e) => {
      server.send(e.data);
    });
    return new Response(null, { status: 101, webSocket: client });
  },
};