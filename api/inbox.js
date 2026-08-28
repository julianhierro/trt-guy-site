// The GoHighLevel inbox, proxied.
//
// Everything the Control Center shows about conversations comes through here,
// for one reason: the GHL token must never reach a browser. It reads and
// replies on Julian's behalf, so anyone holding it owns the account.
//
// This endpoint is therefore gated twice — the token lives only in the Vercel
// env, and every request must carry the passcode in CC_KEY. Without the second
// gate the inbox would be a public web page showing leads' phone numbers.
//
// Required env on Vercel:
//   GHL_API_KEY     private integration token for location WmcafLXT7njeQOu3fqlP
//                   with scopes: conversations.readonly,
//                   conversations/message.readonly, conversations/message.write,
//                   contacts.readonly
//   CC_KEY          the passcode the dashboard asks for once
// Optional:
//   GHL_LOCATION_ID, GHL_EMAIL_FROM

const GHL_API = 'https://services.leadconnectorhq.com';
const TOKEN = process.env.GHL_API_KEY;
const CC_KEY = process.env.CC_KEY;
const LOCATION_ID = process.env.GHL_LOCATION_ID || 'WmcafLXT7njeQOu3fqlP';
const EMAIL_FROM = process.env.GHL_EMAIL_FROM || 'TRT Guy <admin@jackedvegans.com>';

function ghl(method, path, body) {
  return fetch(`${GHL_API}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      Version: '2021-04-15',           // conversations live on this version
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
}

async function readJson(r) {
  const text = await r.text();
  try { return { ok: r.ok, status: r.status, json: JSON.parse(text) }; }
  catch (e) { return { ok: r.ok, status: r.status, json: null, text: text.slice(0, 400) }; }
}

// GHL names a channel a dozen different ways depending on the endpoint.
// Collapse all of them to the four Julian actually uses, plus 'other'.
function channelOf(raw) {
  const s = String(raw || '').toUpperCase();
  if (s.includes('EMAIL')) return 'email';
  if (s.includes('INSTAGRAM') || s === 'IG') return 'ig';
  if (s.includes('FACEBOOK') || s.includes('GMB') || s === 'FB') return 'fb';
  if (s.includes('WHATSAPP')) return 'wa';
  if (s.includes('SMS') || s.includes('PHONE') || s.includes('CALL') || s.includes('VOICEMAIL')) return 'sms';
  if (s.includes('LIVE_CHAT') || s.includes('WEBCHAT')) return 'chat';
  return 'other';
}
// what to hand back to /conversations/messages when replying on that channel
const SEND_TYPE = { email:'Email', sms:'SMS', ig:'IG', fb:'FB', wa:'WhatsApp', chat:'Live_Chat' };

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => (
    { '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

/* ── list: the newest conversations, one line each ───────────────────────── */
async function list(req) {
  const limit = Math.min(parseInt(req.query.limit, 10) || 20, 50);
  const params = new URLSearchParams({ locationId: LOCATION_ID, limit: String(limit), sortBy: 'last_message_date', sort: 'desc' });
  if (req.query.q) params.set('query', String(req.query.q).slice(0, 120));
  if (req.query.unread === '1') params.set('status', 'unread');

  const r = await readJson(await ghl('GET', `/conversations/search?${params}`));
  if (!r.ok) return { status: r.status, body: { error: 'GHL refused the conversation list', ghl: r.json || r.text } };

  const rows = (r.json && (r.json.conversations || r.json.items)) || [];
  return { status: 200, body: {
    total: (r.json && r.json.total) || rows.length,
    conversations: rows.map(c => ({
      id: c.id,
      contactId: c.contactId,
      name: (c.fullName || c.contactName || c.email || c.phone || 'Unknown').trim(),
      email: c.email || '',
      phone: c.phone || '',
      channel: channelOf(c.lastMessageType || c.type),
      unread: c.unreadCount || 0,
      preview: (c.lastMessageBody || '').replace(/\s+/g, ' ').trim().slice(0, 160),
      direction: c.lastMessageDirection || '',
      at: c.lastMessageDate || c.dateUpdated || c.dateAdded || null,
    })),
  } };
}

/* ── thread: the messages inside one conversation ────────────────────────── */
async function thread(req) {
  const id = String(req.query.id || '');
  if (!id) return { status: 400, body: { error: 'id is required' } };

  const r = await readJson(await ghl('GET', `/conversations/${encodeURIComponent(id)}/messages?limit=40`));
  if (!r.ok) return { status: r.status, body: { error: 'GHL refused the thread', ghl: r.json || r.text } };

  const box = (r.json && r.json.messages) || {};
  const rows = box.messages || box || [];
  return { status: 200, body: {
    messages: (Array.isArray(rows) ? rows : []).map(m => ({
      id: m.id,
      channel: channelOf(m.messageType || m.type),
      // an email body arrives as HTML; the dashboard renders text, so strip it here
      body: String(m.body || m.text || '').replace(/<br\s*\/?>/gi, '\n').replace(/<[^>]+>/g, '').trim(),
      inbound: String(m.direction || '').toLowerCase() === 'inbound',
      at: m.dateAdded || null,
      status: m.status || '',
      attachments: Array.isArray(m.attachments) ? m.attachments.length : 0,
    })).reverse(),                       // GHL returns newest first; read order is oldest first
  } };
}

/* ── send: reply on whatever channel the thread is already on ────────────── */
async function send(req) {
  const b = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
  const contactId = String(b.contactId || '');
  const text = String(b.text || '').trim();
  const channel = channelOf(b.channel);
  const type = SEND_TYPE[channel];

  if (!contactId) return { status: 400, body: { error: 'contactId is required' } };
  if (!text) return { status: 400, body: { error: 'Nothing to send' } };
  if (!type) return { status: 400, body: { error: `Can't reply on ${b.channel} from here` } };

  const payload = { type, contactId, conversationId: b.conversationId || undefined };
  if (type === 'Email') {
    payload.subject = (b.subject || 'Re: your message').slice(0, 160);
    payload.html = '<div style="font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6">'
      + esc(text).replace(/\n/g, '<br>') + '</div>';
    payload.emailFrom = EMAIL_FROM;
    if (b.replyMessageId) payload.replyMessageId = b.replyMessageId;
  } else {
    payload.message = text;
  }

  const r = await readJson(await ghl('POST', '/conversations/messages', payload));
  if (!r.ok) {
    // The usual causes are worth naming: Instagram and Facebook only accept a
    // reply inside 24 hours of the lead's last message, and SMS needs a number
    // on the location.
    return { status: r.status, body: { error: 'GHL would not send it', channel, ghl: r.json || r.text } };
  }
  return { status: 200, body: { sent: true, channel, id: (r.json && (r.json.messageId || r.json.msg)) || null } };
}

/* ── diag: what can this token actually do? ──────────────────────────────── */
async function diag() {
  const probe = async (label, path) => {
    try {
      const r = await ghl('GET', path);
      const t = await r.text();
      return { label, status: r.status, ok: r.ok, note: r.ok ? '' : t.slice(0, 200) };
    } catch (e) { return { label, status: 0, ok: false, note: e.message }; }
  };
  return { status: 200, body: {
    tokenSet: !!TOKEN, keySet: !!CC_KEY, locationId: LOCATION_ID,
    checks: [
      await probe('conversations.readonly', `/conversations/search?locationId=${LOCATION_ID}&limit=1`),
      await probe('contacts.readonly', `/contacts/?locationId=${LOCATION_ID}&limit=1`),
    ],
  } };
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-CC-Key');
  res.setHeader('Cache-Control', 'no-store');
  if (req.method === 'OPTIONS') return res.status(204).end();

  if (!TOKEN) return res.status(500).json({ error: 'GHL_API_KEY is not set on this deployment' });

  const action = String((req.query && req.query.action) || 'list');

  // diag is the one action that runs without the passcode — it reports whether
  // the deployment is wired up and never returns a single word of anyone's data
  if (action === 'diag') {
    const out = await diag();
    return res.status(out.status).json(out.body);
  }

  if (!CC_KEY) return res.status(500).json({ error: 'CC_KEY is not set on this deployment' });
  const given = req.headers['x-cc-key'] || (req.query && req.query.key) || '';
  if (given !== CC_KEY) return res.status(401).json({ error: 'Wrong passcode' });

  try {
    const out = action === 'thread' ? await thread(req)
              : action === 'send'   ? await send(req)
              : await list(req);
    return res.status(out.status).json(out.body);
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
};
