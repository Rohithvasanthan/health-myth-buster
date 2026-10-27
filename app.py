import json, re
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

BASE = Path(__file__).resolve().parent
CANDIDATES = [BASE / 'data' / 'myths.json', BASE / 'data.json']

st.set_page_config(page_title='Health Myth Buster', page_icon='🩺', layout='wide', initial_sidebar_state='auto')

# Important: do not style/hide Streamlit's header, sidebar, or sidebar buttons.
st.markdown('''<style>
:root { color-scheme: light; }
.stApp { background: #f5f8fc; color: #172b4d; }
.block-container { max-width: 1180px; padding: 1.2rem 1rem 3rem; }
.hero { background: linear-gradient(120deg,#123c69,#087f8c); color:#fff; padding: clamp(1.2rem,4vw,2.4rem); border-radius:22px; margin-bottom:1.2rem; }
.hero h1 { color:#fff !important; font-size:clamp(1.7rem,4vw,2.5rem); margin:0 0 .5rem; }
.hero p { color:#e5f8ff !important; line-height:1.6; margin:0; }
.metric { background:#fff; border:1px solid #e0e8f1; border-radius:15px; padding:1rem; min-height:95px; }
.metric .label { color:#61738a; font-size:.85rem; }
.metric .value { color:#123c69; font-size:1.65rem; font-weight:800; }
.card { background:#fff; border:1px solid #dce6f0; border-radius:16px; padding:1rem 1.1rem; margin:.6rem 0; }
.stButton > button, .stFormSubmitButton > button { border-radius:11px; min-height:2.8rem; font-weight:700; }
[data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input { background:#fff !important; color:#172b4d !important; border-radius:11px; }
[data-testid="stTextArea"] textarea::placeholder, [data-testid="stTextInput"] input::placeholder { color:#75849a !important; opacity:1; }
[data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3, [data-testid="stMain"] p { color:#172b4d; }
.small { color:#63758b; font-size:.9rem; }
@media (max-width: 640px) { .block-container { padding: .7rem .65rem 2rem; } .hero { border-radius:15px; } }
</style>''', unsafe_allow_html=True)

@st.cache_data
def load_db():
    for path in CANDIDATES:
        if path.exists():
            raw = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(raw, list): return raw, path
            if isinstance(raw, dict) and isinstance(raw.get('claims'), list): return raw['claims'], path
    return [], None

def norm(s):
    s = str(s or '').casefold().replace('’', "'")
    return re.sub(r'[^a-z0-9\s]', ' ', s).strip()

def match_claim(query, db):
    q = norm(query)
    if not q: return None, 'empty'
    # Exact phrase / known-claim match first.
    for item in db:
        candidates = [item.get('claim', '')] + item.get('phrases', [])
        for phrase in candidates:
            p = norm(phrase)
            if p and (q == p or p in q):
                return item, 'Specific phrase matched'
    # Conservative keyword match: every matched entry must meet its own threshold.
    q_words = set(q.split())
    scored = []
    for item in db:
        kws = [norm(k) for k in item.get('keywords', []) if norm(k)]
        hits = [k for k in kws if k in q_words]
        threshold = int(item.get('minimum_keyword_matches', 3))
        if len(hits) >= max(3, threshold):
            scored.append((len(hits), len(hits) / max(1, len(set(kws))), item, hits))
    if not scored: return None, 'No sufficiently strong match'
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    # Ambiguous scores are safer as UNVERIFIED.
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return None, 'Ambiguous keyword match'
    score, ratio, item, hits = scored[0]
    if ratio < 0.25: return None, 'Weak keyword match'
    return item, 'Keyword match: ' + ', '.join(hits)

def sources_for(item):
    out=[]
    for s in item.get('sources', []):
        if isinstance(s, str): out.append({'title':'Health source','url':s})
        else: out.append({'title':s.get('title', s.get('name','Health source')), 'url':s.get('url','')})
    return out

def verdict_of(item):
    v = str(item.get('verdict','UNVERIFIED')).upper()
    return v if v in {'TRUE','FALSE','UNVERIFIED'} else 'UNVERIFIED'

def show_result(item, match_note=''):
    v=verdict_of(item)
    colors={'TRUE':('#047857','#ecfdf5','#a7f3d0'),'FALSE':('#b91c1c','#fef2f2','#fecaca'),'UNVERIFIED':('#a16207','#fffbeb','#fde68a')}
    fg,bg,bd=colors[v]
    claim=item.get('claim','Claim')
    reason=item.get('reason',item.get('explanation','No explanation available.'))
    st.markdown(f'''<div class="card" style="background:{bg};border-color:{bd}"><div style="font-size:.78rem;font-weight:800;letter-spacing:.1em;color:{fg}">FACT-CHECK VERDICT</div><div style="font-size:2rem;font-weight:850;color:{fg}">{v}</div><div style="color:#243b53;font-weight:650">{claim}</div></div>''',unsafe_allow_html=True)
    st.markdown('**Why this result?**')
    st.write(reason)
    if match_note: st.caption(match_note)
    src=sources_for(item)
    st.markdown('**Evidence sources**')
    if src:
        for i,s in enumerate(src,1):
            if s['url'].startswith('https://') or s['url'].startswith('http://'):
                st.markdown(f"{i}. [{s['title']}]({s['url']})")
            else: st.write(f"{i}. {s['title']}")
    else: st.warning('No source links are attached to this record yet.')
    st.info('Educational information only — not medical advice. Always ask a doctor.')

try:
    db, db_path = load_db()
except (OSError, json.JSONDecodeError) as e:
    db, db_path = [], None
    st.error(f'Database could not be loaded: {e}')

true_n=sum(verdict_of(x)=='TRUE' for x in db)
false_n=sum(verdict_of(x)=='FALSE' for x in db)
unverified_n=sum(verdict_of(x)=='UNVERIFIED' for x in db)

st.markdown('''<div class="hero"><div style="font-size:.78rem;font-weight:800;letter-spacing:.15em;color:#a7f3d0">THINK · CHECK · SHARE RESPONSIBLY</div><h1>🩺 Health Myth Buster</h1><p>Check common health messages against a source-linked educational database.</p></div>''',unsafe_allow_html=True)

# Three always-visible navigation choices: no dependence on the sidebar toggle.
page = st.radio('Choose a screen', ['1 · Check a claim','2 · Browse database','3 · Unknown claim & safety'], horizontal=True, label_visibility='visible')
st.caption(f'Database: {len(db)} entries · Source file: {db_path.name if db_path else "not found"}')

if page.startswith('1'):
    a,b,c=st.columns(3)
    for col,label,value in [(a,'Database claims',len(db)),(b,'TRUE entries',true_n),(c,'FALSE entries',false_n)]:
        with col: st.markdown(f'<div class="metric"><div class="label">{label}</div><div class="value">{value}</div></div>',unsafe_allow_html=True)
    st.write('')
    st.subheader('Enter or paste a health claim')
    with st.form('claim_check_form'):
        claim=st.text_area('Health claim',placeholder='Example: Antibiotics cure viral infections.',height=120,max_chars=1000)
        submitted=st.form_submit_button('🔎 Check this claim',type='primary',use_container_width=True)
    if submitted:
        if not claim.strip(): st.warning('Please enter a claim first.')
        else:
            item,note=match_claim(claim,db)
            st.session_state['last_claim']=claim.strip()
            if item is None:
                st.session_state['last_result']={'claim':claim.strip(),'verdict':'UNVERIFIED','reason':'No sufficiently specific matching entry was found in this local database. This tool cannot determine whether the claim is true or false without a human fact-check.','keywords':[],'sources':[]}
                st.session_state['last_note']=note
                st.session_state['last_screen']='unknown'
            else:
                st.session_state['last_result']=item
                st.session_state['last_note']=note
                st.session_state['last_screen']='result'
    if st.session_state.get('last_result') and st.session_state.get('last_screen')=='result':
        st.markdown('---'); st.subheader('2 · Fact-check result'); show_result(st.session_state['last_result'],st.session_state.get('last_note',''))
    elif st.session_state.get('last_result') and st.session_state.get('last_screen')=='unknown':
        st.markdown('---'); st.subheader('3 · Unknown claim'); show_result(st.session_state['last_result'],st.session_state.get('last_note',''))
        st.warning('This claim is not confirmed as true or false. Check it with reliable sources before sharing.')

elif page.startswith('2'):
    st.subheader('Browse the claim database')
    q=st.text_input('Search by claim or keyword',placeholder='Try: fever, vaccine, antibiotics, nutrition')
    vf=st.selectbox('Filter verdict',['All','TRUE','FALSE','UNVERIFIED'])
    nq=norm(q)
    filtered=[]
    for item in db:
        searchable=norm(' '.join([item.get('claim',''),item.get('reason',item.get('explanation','')),' '.join(item.get('keywords',[]))]))
        if (not nq or nq in searchable) and (vf=='All' or verdict_of(item)==vf): filtered.append(item)
    st.caption(f'{len(filtered)} matching entries')
    for item in filtered:
        with st.expander(f"{verdict_of(item)} · {item.get('claim','Untitled claim')}"):
            st.write(item.get('reason',item.get('explanation','')))
            st.write('**Keywords:** '+', '.join(item.get('keywords',[])))
            st.write('**Review status:** '+item.get('review_status','needs_human_review'))
            for s in sources_for(item):
                if s['url'].startswith(('https://','http://')): st.markdown(f"- [{s['title']}]({s['url']})")
                else: st.write('- '+s['title'])

else:
    st.subheader('Unknown claim handling')
    st.markdown('''When a claim does not match a specific database record, the app returns **UNVERIFIED** instead of guessing. This is the third screen required for the project demonstration.''')
    unknown_text=st.text_area('Try an unknown claim',placeholder='Example: A spoon of moonlight cures every illness.',key='unknown_demo')
    if st.button('Show unknown-claim screen',type='primary',use_container_width=True):
        st.session_state['unknown_demo_result']=unknown_text.strip()
    if st.session_state.get('unknown_demo_result'):
        st.markdown('<div class="card" style="background:#fffbeb;border-color:#fde68a"><div style="color:#a16207;font-weight:800">VERDICT · UNVERIFIED</div><h3>No matching database entry</h3><p style="color:#334155">This claim has not been checked by this prototype. No true/false conclusion is made.</p></div>',unsafe_allow_html=True)
        st.info('Do not treat this result as medical advice. Always ask a doctor.')
    st.divider()
    st.markdown('**Safety and limitations**')
    st.write('• The app searches a local JSON database; it does not perform live internet research or use an AI model to verify claims.')
    st.write('• Keyword matching can make mistakes. An exact/keyword match is not proof of truth.')
    st.write('• Verify each verdict against at least two relevant, reliable sources and ask a teacher or qualified health professional to review the final list.')
    st.write('• Do not use this tool to diagnose illness, choose medicines, or delay medical care.')

st.divider()
st.caption('HCL Jigsaw educational prototype · Local database matching · Always ask a doctor.')
