// Server-side proxy for every lead on the TRT Guy site.
// Three sources land here — the low-T quiz, the free email course, and the
// coaching waitlist — and each gets its own tags in GoHighLevel.
// The GHL token stays on the server and is never exposed to the browser.
//
// Required env var on Vercel:  GHL_API_KEY   (the same private integration
// token the jacked-fathers-quiz project already uses for this location)
// Optional:                    GHL_LOCATION_ID, GHL_EMAIL_FROM

const GHL_API = 'https://services.leadconnectorhq.com';
const GHL_TOKEN = process.env.GHL_API_KEY;
const LOCATION_ID = process.env.GHL_LOCATION_ID || 'WmcafLXT7njeQOu3fqlP';
const EMAIL_FROM = process.env.GHL_EMAIL_FROM || 'TRT Guy <julian@trt-guy.com>';

function ghl(method, path, body) {
  return fetch(`${GHL_API}${path}`, {
    method,
    headers: {
      'Authorization': `Bearer ${GHL_TOKEN}`,
      'Version': '2021-07-28',
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

function bloodworkEmailHtml(firstName) {
  const name = esc(firstName) || 'there';
  return `
  <div style="font-family:Arial,Helvetica,sans-serif;font-size:16px;line-height:1.6;color:#1a1a1a;max-width:560px;margin:0 auto">
    <p>Hey ${name},</p>
    <p>You scored positive on the ADAM screen. That means the way you've been feeling lines up with low testosterone.</p>
    <p>That's not a diagnosis, and it's not a reason to panic. It's a reason to get one blood test and stop guessing.</p>
    <p>Here's the exact panel to ask your doctor for. Screenshot this or forward it straight to them:</p>
    <ul style="padding-left:20px">
      <li><strong>Total Testosterone</strong></li>
      <li><strong>Free Testosterone</strong> &mdash; the part your body can actually use</li>
      <li><strong>SHBG</strong></li>
      <li><strong>LH and FSH</strong> &mdash; these show where the problem is starting</li>
      <li><strong>Estradiol (E2)</strong></li>
      <li><strong>A standard metabolic panel + CBC</strong> for the full picture</li>
    </ul>
    <p>Reply back with "&#128170;&#127995;" so I know you're a real one.</p>
    <p>Talk soon,<br>Julian<br>TRT Guy</p>
    <p style="font-size:12px;color:#888;margin-top:24px">This is educational, not medical advice. Always confirm results and next steps with a licensed physician.</p>
  </div>`;
}

// Delivery email for the fertility guide lead magnet. Sent through GoHighLevel.
// (Placeholder copy — refine anytime.)
function fertilityEmailHtml(firstName) {
  const GUIDE = 'https://trt-guy.com/fertility-guide/TRT-Guy-Fertility-Guide.pdf';
  return `
  <div style="font-family:Arial,Helvetica,sans-serif;font-size:16px;line-height:1.6;color:#1a1a1a;max-width:560px;margin:0 auto">
    <p>Please, click the link below to access the fertility guide:</p>
    <p style="margin:22px 0">
      <a href="${GUIDE}" style="display:inline-block;background:#1a5cff;color:#fff;text-decoration:none;padding:14px 26px;border-radius:10px;font-weight:700">Access the Fertility Guide &rarr;</a>
    </p>
    <p>Now, let's make sure you get all my emails.</p>
    <p><strong>Two quick things for you to do now:</strong></p>
    <p><strong>Task #1 — Drag me into your Primary inbox.</strong><br>
    Grab this email and move it to your primary folder/inbox.</p>
    <ul style="padding-left:20px;margin:0 0 12px">
      <li>Gmail: drag it from "Promotions" into "Primary." (Phone: open it &rarr; three dots &rarr; "Move to &rarr; Primary.")</li>
      <li>Apple Mail / Outlook: add my address to your contacts, or mark it "Not Junk."</li>
    </ul>
    <p>This tells your inbox, "I want these."</p>
    <p><strong>Task #2 — Hit reply and tell me your #1 fitness goal and biggest challenge.</strong></p>
    <p>One line is enough: "Lose 20 lbs." "Finally see my abs." "Optimize my hormones."</p>
    <p>I personally ready every single reply and it helps me tailor future emails.</p>
    <p>Whatever your goal is — reply and tell me.</p>
    <p>Do those two things now.</p>
    <p>I'll see your reply.</p>
    <p>-Julian</p>
  </div>`;
}

// Tags are built server-side so the browser can't inject arbitrary ones.
function tagsFor(source, result) {
  const base = ['trt-dad'];
  if (source === 'quiz') {
    base.push('adam-quiz', result === 'positive' ? 'low-t-positive' : 'low-t-negative');
    if (result === 'positive') base.push('bloodwork-interested');
  } else if (source === 'course') {
    base.push('30-emails-30-days');
  } else if (source === 'coaching') {
    base.push('coaching-interest');
  } else if (source === 'checkout') {
    // Reached the order form. Whether they PAID is a separate tag, added by the
    // payment side — so "checkout-started AND NOT coaching-client" is your
    // abandoned-checkout segment.
    base.push('coaching-interest', 'checkout-started');
  } else if (source === 'injection-guide') {
    base.push('injection-guide', 'trt-interested');
  } else if (source === 'trt-rules') {
    base.push('trt-non-negotiables', 'trt-interested');
  } else if (source === 'trt-101-guide') {
    base.push('trt-101-guide', 'trt-interested');
  } else if (source === 'fertility-guide') {
    base.push('fertility-guide', 'trt-interested');
  }
  return base;
}

const SOURCE_LABEL = {
  quiz: 'TRT Guy Low-T Quiz',
  course: 'TRT Guy 30 Emails In 30 Days',
  coaching: 'TRT Guy Coaching Waitlist',
  'injection-guide': 'TRT Guy TRT Injection Guide',
  'trt-rules': 'TRT Guy 5 TRT Non-Negotiables',
  'trt-101-guide': 'TRT Guy TRT 101 Guide',
  'fertility-guide': 'TRT Guy Fertility Guide',
};

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  if (!GHL_TOKEN) {
    return res.status(500).json({ error: 'GHL_API_KEY is not set on this deployment' });
  }

  try {
    const data = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});

    const firstName = (data.firstName || data.first_name || data.name || '').toString().trim();
    const email = (data.email || '').toString().trim();
    const source = ['quiz', 'course', 'coaching', 'injection-guide', 'trt-rules', 'trt-101-guide', 'fertility-guide'].includes(data.source) ? data.source : 'course';
    const result = data.result === 'positive' ? 'positive' : 'negative';

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return res.status(400).json({ error: 'A valid email is required' });
    }

    const tags = tagsFor(source, result);

    const upsert = await ghl('POST', '/contacts/upsert', {
      locationId: LOCATION_ID,
      firstName,
      email,
      source: SOURCE_LABEL[source],
      tags,
    });

    const json = await upsert.json();
    const contactId = json && json.contact && json.contact.id;

    if (!contactId) {
      return res.status(502).json({ error: 'GHL did not return a contact', details: json });
    }

    // On a positive quiz screen, send the bloodwork panel right away.
    let emailQueued = false;
    if (source === 'quiz' && result === 'positive') {
      try {
        const send = await ghl('POST', '/conversations/messages', {
          type: 'Email',
          contactId,
          subject: 'Your Low-T result — and exactly what to get tested',
          html: bloodworkEmailHtml(firstName),
          emailFrom: EMAIL_FROM,
        });
        const sendJson = await send.json();
        emailQueued = !!(sendJson && (sendJson.messageId || sendJson.emailMessageId));
      } catch (e) {
        // Never fail the whole request just because the email didn't queue.
      }
    }

    // Fertility guide: deliver the PDF link by email (sent through GoHighLevel).
    if (source === 'fertility-guide') {
      try {
        const send = await ghl('POST', '/conversations/messages', {
          type: 'Email',
          contactId,
          subject: 'The Fertility Guide — do these 2 quick things (60 seconds)',
          html: fertilityEmailHtml(firstName),
          emailFrom: EMAIL_FROM,
        });
        const sendJson = await send.json();
        emailQueued = !!(sendJson && (sendJson.messageId || sendJson.emailMessageId));
      } catch (e) {
        // Never fail the whole request just because the email didn't queue.
      }
    }

    // echo back what GoHighLevel actually stored, so tagging can be verified
    const storedTags = (json && json.contact && json.contact.tags) || null;
    return res.status(200).json({ success: true, contactId, tags, storedTags, emailQueued });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
};
