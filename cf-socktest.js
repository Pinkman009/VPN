import { connect } from 'cloudflare:sockets';

export default {
  async fetch(request) {
    return new Response('import-ok ' + typeof connect, { status: 200 });
  },
};