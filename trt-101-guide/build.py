# Builds index.html (the editable page) from guide.html (the print master).
# Run this after every edit to guide.html so the two never drift apart.
import re
BASE = '/Users/julianhierro/trt-guy-101-guide/'
h    = open(BASE+'guide.html', encoding='utf-8').read()
head = open('/tmp/ed_head.html', encoding='utf-8').read().replace('td-injection-asset','td-101-guide')
tail = open('/tmp/ed_tail.html', encoding='utf-8').read().replace('td-injection-asset','td-101-guide').replace('?v=21','?v=25')

screen_css = '''
/* ---- screen-only chrome (never printed) ---- */
@media screen{
  body{background:#e7eaef;padding:26px 0 60px}
  .sheet{width:210mm;margin:0 auto;background:#fff;padding:18mm 16mm;box-shadow:0 10px 40px rgba(11,13,16,.16)}
  .cover{height:253mm}
  .pdfbar{position:fixed;right:22px;bottom:96px;z-index:2147483000}
  .pdfbar a{
    display:inline-flex;align-items:center;gap:9px;cursor:pointer;border:0;
    font:700 14px/1 Inter,sans-serif;color:#fff;background:var(--acc);text-decoration:none;
    padding:15px 22px;border-radius:12px;box-shadow:0 10px 26px rgba(26,92,255,.34);
    transition:transform .16s ease,background .16s ease;
  }
  .pdfbar a:hover{background:var(--acc-d);transform:translateY(-2px)}
}
@media print{ .pdfbar{display:none !important} }
'''
h = re.sub(r'/\* ---- on-screen preview only ---- \*/\n@media screen\{.*?\n\}\n', screen_css.lstrip()+'\n', h, flags=re.S)

h = h.replace('</style>\n</head>', '</style>\n'+head+'\n</head>')

# The editor cancels clicks on every <a>/<button> from a capture-phase handler on
# `document`, so an inline onclick never fires while editing. Binding on `window`
# in the capture phase runs first, and stopping propagation there keeps the
# editor's blocker from ever seeing it.
pdfbar = '''</div><!-- /sheet -->

<script>
(function(){
  // the Control Center reads views/visitors from these beacons; without it the
  // guide's card sat permanently at zero
  var TRACK_URL='https://jv-dashboard-chi.vercel.app/api/pageview', PAGE_KEY='trtdad-101-guide';
  function vid(){try{var k='td-vid',v=localStorage.getItem(k);if(!v){v=Math.random().toString(36).slice(2)+Date.now().toString(36);localStorage.setItem(k,v);}return v;}catch(e){return 'anon';}}
  function utm(){var ks=['utm_source','utm_medium','utm_campaign','utm_content','utm_term'],sp=new URLSearchParams(location.search),s={},o='';
    try{s=JSON.parse(sessionStorage.getItem('td-utm')||'{}');}catch(e){}
    ks.forEach(function(k){var v=sp.get(k);if(v)s[k]=v;});
    try{sessionStorage.setItem('td-utm',JSON.stringify(s));}catch(e){}
    ks.forEach(function(k){if(s[k])o+='&'+k+'='+encodeURIComponent(s[k]);});return o;}
  if(/[?&]edit=1/.test(location.search))return;
  var u=TRACK_URL+'?p='+encodeURIComponent(PAGE_KEY)+'&e=view&v='+encodeURIComponent(vid())+utm();
  try{if(navigator.sendBeacon&&navigator.sendBeacon(u))return;}catch(e){}
  try{new Image().src=u;}catch(e){}
})();
</script>


<div class="pdfbar" data-noedit>
  <a id="jvPdf" href="TRT-Guy-TRT-101-Guide.pdf" download="The-TRT-101-Guide.pdf">Download The PDF <span>&darr;</span></a>
</div>

<script>
(function () {
  // The editor cancels clicks on every <a>/<button> from a capture-phase handler on
  // `document`. Running first on `window` and stopping propagation there keeps the
  // blocker from seeing this one — and because we never preventDefault, the browser
  // performs its normal download.
  window.addEventListener('click', function (e) {
    if (!e.target.closest || !e.target.closest('#jvPdf')) return;
    e.stopPropagation();
    if (e.stopImmediatePropagation) e.stopImmediatePropagation();
  }, true);
  window.addEventListener('mousedown', function (e) {
    if (e.target.closest && e.target.closest('.pdfbar')) e.stopPropagation();
  }, true);
})();
</script>

'''
h = h.replace('</div><!-- /sheet -->', pdfbar + tail + '\n', 1)
open(BASE+'index.html','w',encoding='utf-8').write(h)
print('index.html rebuilt', len(h))
