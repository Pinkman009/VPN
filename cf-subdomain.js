const fs = require('fs');
const path = require('path');

const p = path.join(process.env.APPDATA, 'xdg.config', '.wrangler', 'config', 'default.toml');
if (!fs.existsSync(p)) {
    console.log('config missing');
    process.exit(1);
}
const t = fs.readFileSync(p, 'utf8');
const m = t.match(/oauth_token\s*=\s*"([^"]+)"/);
if (!m) {
    console.log('no token');
    process.exit(1);
}
const token = m[1];
const ACCOUNT = process.argv[2];

async function main() {
    // Check existing workers.dev subdomain
    let res = await fetch(`https://api.cloudflare.com/client/v4/accounts/${ACCOUNT}/workers/subdomain`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    let body = await res.json().catch(() => ({}));
    console.log('GET subdomain status:', res.status, 'success:', body.success);
    if (res.ok && body.success && body.result && body.result.value) {
        console.log('subdomain:', body.result.value);
        return;
    }
    // Try to create it
    const name = 'mi-' + Math.random().toString(36).slice(2, 10);
    for (const verb of ['PUT', 'POST']) {
        res = await fetch(`https://api.cloudflare.com/client/v4/accounts/${ACCOUNT}/workers/subdomain`, {
            method: verb,
            headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ subdomain: name, name }),
        });
        body = await res.json().catch(() => ({}));
        console.log(verb, 'subdomain create status:', res.status, 'success:', body.success);
        if (res.ok && body.success) break;
        if (body.errors) console.log(JSON.stringify(body.errors).slice(0, 300));
    }
    // Re-check
    res = await fetch(`https://api.cloudflare.com/client/v4/accounts/${ACCOUNT}/workers/subdomain`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    body = await res.json().catch(() => ({}));
    if (body.result && body.result.value) console.log('subdomain now:', body.result.value);
}

main().catch(e => { console.log('ERR', e.message); process.exit(1); });