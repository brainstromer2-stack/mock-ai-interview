import os
import json
import re
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import streamlit.components.v1 as components
import plotly.express as px

load_dotenv()
st.set_page_config(page_title="Executive AI Cyber Interviewer", page_icon="🤖", layout="wide")

# --- INITIALIZE SESSION STATE FOR AUTHENTICATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "target_role" not in st.session_state:
    st.session_state.target_role = "Software Developer"
if "experience_level" not in st.session_state:
    st.session_state.experience_level = "Intermediate"
if "theme" not in st.session_state:
    st.session_state.theme = "👔 Executive Midnight"

# --- EXECUTIVE THEME STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f3f4f6; font-family: 'Inter', system-ui, sans-serif; }
    .main-header { font-size: 2.5rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.025em; margin-bottom: 0px; }
    .sub-caption { font-size: 1.05rem; color: #94a3b8; margin-bottom: 24px; font-weight: 400; }
    
    /* Cyber Robot Interviewer Console */
    .robot-console {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        border: 1px solid #38bdf8;
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px -5px rgba(56, 189, 248, 0.15);
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .robot-avatar-box {
        background: #020617;
        border: 2px solid #38bdf8;
        border-radius: 50%;
        width: 70px;
        height: 70px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 32px;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
        flex-shrink: 0;
        animation: cyber-glow 3s infinite alternate;
    }
    @keyframes cyber-glow {
        0% { box-shadow: 0 0 10px rgba(56, 189, 248, 0.3); }
        100% { box-shadow: 0 0 20px rgba(56, 189, 248, 0.7); }
    }
    .robot-content { flex-grow: 1; }
    .robot-title { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: #38bdf8; font-weight: 700; margin-bottom: 6px; }
    .robot-speech { font-size: 1.25rem; font-weight: 600; line-height: 1.4; color: #ffffff; }

    /* Dress Code Card */
    .dress-code-box {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid #334155;
        border-left: 4px solid #38bdf8;
        padding: 14px 18px;
        border-radius: 10px;
        margin-bottom: 20px;
        font-size: 0.95rem;
        color: #cbd5e1;
    }

    section[data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #1e293b; }
</style>
""", unsafe_allow_html=True)

# --- QUESTION BANK ---
QUESTIONS = {
    "Software Developer": [
        "Walk me through a complex architectural decision or system design you implemented recently.",
        "Describe a critical production bug you debugged under pressure and how you resolved it.",
        "How do you ensure high code quality, maintainability, and test coverage across your team?"
    ],
    "Data Scientist / AI Engineer": [
        "Explain how you handle data drift and model degradation in production machine learning pipelines.",
        "Describe a time when your model's performance didn't meet business expectations. How did you iterate?",
        "How do you balance model interpretability vs. predictive accuracy when presenting insights to stakeholders?"
    ],
    "Product Manager": [
        "How do you prioritize your product backlog when faced with conflicting stakeholder requests?",
        "Tell me about a time when a product launch failed or underperformed. What did you learn?",
        "How do you define and measure product success using quantitative and qualitative metrics?"
    ],
    "Sales / Customer Service": [
        "Walk me through how you handle an objection from a high-stakes client or customer.",
        "Describe a situation where you successfully turned an upset customer into a loyal advocate.",
        "How do you maintain high personal motivation and resilience during a tough quota period?"
    ]
}

# --- AUTHENTICATION GATE ---
if not st.session_state.logged_in:
    st.markdown('<div style="text-align: center; max-width: 500px; margin: 60px auto 30px auto;">', unsafe_allow_html=True)
    st.markdown("<h1>🤖 AI Cyber Interviewer</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8;'>Enter your candidate credentials to initialize the cyber-interrogator suite.</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("Candidate Credentials")
            name_input = st.text_input("Full Name", placeholder="e.g., Victoria Sterling")
            email_input = st.text_input("Email Address", placeholder="e.g., v.sterling@enterprise.com")
            role_input = st.selectbox("Target Role Track", list(QUESTIONS.keys()))
            level_input = st.selectbox("Seniority Level", ["Student / Entry-level", "Intermediate", "Experienced"])
            
            submit_btn = st.form_submit_button("🚀 Initialize Cyber Session", use_container_width=True)
            if submit_btn:
                if name_input.strip() and email_input.strip():
                    st.session_state.logged_in = True
                    st.session_state.user_name = name_input.strip()
                    st.session_state.user_email = email_input.strip()
                    st.session_state.target_role = role_input
                    st.session_state.experience_level = level_input
                    st.rerun()
                else:
                    st.warning("Please provide your name and email to proceed.")
    st.stop()

# --- MAIN APP INTERFACE ---
st.markdown('<p class="main-header">🤖 Executive Cyber Interview Suite</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-caption">Candidate: <b>{st.session_state.user_name}</b> &bull; Track: <b>{st.session_state.target_role}</b> ({st.session_state.experience_level})</p>', unsafe_allow_html=True)

st.markdown("""
<div class="dress-code-box">
    <b>👔 Professional Presentation Note:</b> Formal business attire (collared shirt, blazer, or executive wear) and well-lit environments maximize your visual poise rating and executive selection probability score.
</div>
""", unsafe_allow_html=True)

# --- WEBCAM & SPEECH COMPONENT ---
COMPONENT_HTML = """
<div style="font-family:system-ui,sans-serif">
<style>
.panel-inner{border:1px solid #334155;border-radius:14px;padding:18px;margin-bottom:12px;background:#0f172a;box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1)}
.row{display:flex;gap:18px;flex-wrap:wrap}.col{flex:1;min-width:280px}
video{width:100%;max-height:190px;background:#020617;border-radius:10px;object-fit:cover;border:1px solid #1e293b}
button{border:0;border-radius:8px;padding:9px 15px;margin:4px 4px 4px 0;cursor:pointer;background:#334155;color:#f8fafc;font-weight:600;font-size:13px;transition: all 0.2s}
button:hover{background:#475569}
.primary{background:#2563eb;color:white}
.primary:hover{background:#1d4ed8}
.danger{background:#dc2626;color:white}
.danger:hover{background:#b91c1c}
.status{font-size:12px;padding:4px 0;color:#94a3b8;font-weight:500}
.live-badge{background:#0284c7;color:#fff;padding:3px 10px;border-radius:6px;font-size:11px;font-weight:700;display:inline-block;margin-bottom:8px;letter-spacing:0.025em}
textarea{width:100%;box-sizing:border-box;border:1px solid #334155;border-radius:10px;padding:12px;font:inherit;background:#020617;color:#f8fafc;font-size:14px}
textarea:focus{outline:none;border-color:#38bdf8}
.listening-badge {
  display: inline-block; width: 9px; height: 9px; border-radius: 50%; background-color: #ef4444; margin-right: 6px;
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}
.mic-active-box { border: 2px solid #ef4444 !important; background: rgba(239, 68, 68, 0.03) !important; }
.indicator-bar-container { margin-top: 8px; font-size: 11px; color: #cbd5e1; font-weight: 500; }
.bar-track { background: #1e293b; border-radius: 6px; height: 7px; width: 100%; margin-top: 3px; overflow: hidden; }
.bar-fill { background: #38bdf8; height: 100%; border-radius: 6px; transition: width 0.3s ease; }
</style>
<div class="row">
 <div class="col panel-inner">
  <div class="live-badge">LIVE CAMERA & POISE HUD</div>
  <video id="video" autoplay playsinline muted></video>
  <div id="camStatus" class="status">Camera standby.</div>
  
  <div style="font-size:12px; margin-top:6px; background:#020617; padding:8px 10px; border-radius:8px; border:1px solid #1e293b; color:#cbd5e1;">
   <b>Posture:</b> <span id="posture" style="color:#38bdf8">Awaiting video feed…</span><br>
   <b>Visibility:</b> <span id="visibility">—</span>
  </div>

  <div class="indicator-bar-container">
    <div>Confidence Index (<span id="confLbl">65</span>%)</div>
    <div class="bar-track"><div class="bar-fill" id="confBar" style="width: 65%;"></div></div>
  </div>
  <div class="indicator-bar-container">
    <div>Technical Alignment (<span id="skillLbl">70</span>%)</div>
    <div class="bar-track"><div class="bar-fill" id="skillBar" style="width: 70%; background: #4ade80;"></div></div>
  </div>
  <div class="indicator-bar-container">
    <div>Posture Stability (<span id="postureBarLbl">85</span>%)</div>
    <div class="bar-track"><div class="bar-fill" id="postureBar" style="width: 85%; background: #facc15;"></div></div>
  </div>

  <div style="margin-top:12px">
   <button class="primary" id="startCam">Start Camera</button>
   <button class="danger" id="stopCam">Stop</button>
  </div>
 </div>
 <div class="col panel-inner" id="micPanel">
  <div class="live-badge" style="background:#059669">SPEECH TRANSCRIPTION</div>
  <div id="micStatus" class="status">Microphone standby.</div>
  <label style="display:block;margin-top:4px;font-size:13px;color:#cbd5e1"><b>Response Transcript:</b></label>
  <textarea id="answer" rows="10" placeholder="Click 'Start Speaking' or type your response here…"></textarea>
  <div style="margin-top:12px">
   <button class="primary" id="startMic">Start Speaking</button>
   <button id="stopMic">Stop</button>
  </div>
 </div>
</div>
<script>
(() => {
 const video=document.getElementById('video'), camStatus=document.getElementById('camStatus');
 const postureEl=document.getElementById('posture'), visibilityEl=document.getElementById('visibility');
 const micStatus=document.getElementById('micStatus'), answer=document.getElementById('answer');
 const micPanel=document.getElementById('micPanel');
 const postureBar=document.getElementById('postureBar'), postureBarLbl=document.getElementById('postureBarLbl');
 const confBar=document.getElementById('confBar'), confLbl=document.getElementById('confLbl');
 const skillBar=document.getElementById('skillBar'), skillLbl=document.getElementById('skillLbl');
 let stream=null, detector=null, recognition=null, finalText='';

 function send(){
  const value={answer:answer.value,posture:postureEl.textContent,visibility:visibilityEl.textContent,camera_active:!!stream};
  window.parent.postMessage({isStreamlitMessage:true,type:'streamlit:setComponentValue',value},'*');
 }

 async function loadPose(){
  try{
   const vision=await import('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14');
   const files=await vision.FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm');
   detector=await vision.PoseLandmarker.createFromOptions(files,{
    baseOptions:{modelAssetPath:'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task',delegate:'CPU'},
    runningMode:'VIDEO',numPoses:1
   });
   camStatus.textContent='Active — Pose analytics online.';
  }catch(e){camStatus.textContent='Failed to initialize pose model.';}
 }

 function frame(now){
  if(!stream||video.readyState<2)return;
  if(detector){
   try{
    const result=detector.detectForVideo(video,now), lm=result.landmarks&&result.landmarks[0];
    if(lm&&lm.length>12){
     const nose=lm[0], ls=lm[11], rs=lm[12];
     const vis=Math.round((((ls.visibility??0)+(rs.visibility??0))/2)*100);
     visibilityEl.textContent=vis+'%';
     const shoulderTilt=Math.abs(ls.y-rs.y), headOffset=Math.abs(nose.x-(ls.x+rs.x)/2);
     let pScore = 85;
     if(vis<45){postureEl.textContent='Step back for optimal framing.'; pScore=50;}
     else if(shoulderTilt>.09){postureEl.textContent='Shoulder alignment uneven.'; pScore=65;}
     else if(headOffset>.13){postureEl.textContent='Head off-center; face forward.'; pScore=70;}
     else{postureEl.textContent='Optimal posture & centering.'; pScore=95;}
     
     postureBar.style.width = pScore + '%';
     postureBarLbl.textContent = pScore;

     const words = answer.value ? answer.value.trim().split(/\s+/).length : 0;
     let cScore = Math.min(95, Math.max(50, 60 + Math.floor(words / 3)));
     let sScore = Math.min(95, Math.max(60, 65 + Math.floor(words / 4)));
     
     confBar.style.width = cScore + '%';
     confLbl.textContent = cScore;
     skillBar.style.width = sScore + '%';
     skillLbl.textContent = sScore;

    }else{postureEl.textContent='Candidate not detected clearly.';visibilityEl.textContent='Low';}
   }catch(e){}
  }
  requestAnimationFrame(frame);
 }

 document.getElementById('startCam').onclick=async()=>{
  try{stream=window.stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'},audio:false});video.srcObject=stream;
   camStatus.textContent='Initializing pose telemetry…';await loadPose();requestAnimationFrame(frame);send();}
  catch(e){camStatus.textContent='Camera permission denied.';}
 };

 document.getElementById('stopCam').onclick=()=>{if(stream)stream.getTracks().forEach(t=>t.stop());stream=null;video.srcObject=null;postureEl.textContent='Camera offline.';visibilityEl.textContent='—';camStatus.textContent='Camera stopped.';send();};

 document.getElementById('startMic').onclick=()=>{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!SR){ micStatus.innerHTML = '⚠️ Speech recognition unsupported. Type below.'; return; }
  try {
   recognition = new SR(); recognition.continuous = true; recognition.interimResults = true; recognition.lang = 'en-US';
   finalText = answer.value ? answer.value + ' ' : '';
   recognition.onstart = () => {
    micStatus.innerHTML = '<span class="listening-badge"></span><strong>Recording… articulate clearly.</strong>';
    micPanel.classList.add('mic-active-box');
   };
   recognition.onerror = e => { micStatus.textContent = '❌ Error: ' + e.error; micPanel.classList.remove('mic-active-box'); };
   recognition.onend = () => { micStatus.textContent = 'Microphone recording halted.'; micPanel.classList.remove('mic-active-box'); send(); };
   recognition.onresult = e => {
    let interim = '';
    for(let i = e.resultIndex; i < e.results.length; i++){
     let t = e.results[i][0].transcript;
     if(e.results[i].isFinal) finalText += t + ' '; else interim += t;
    }
    answer.value = (finalText + interim).trim(); send();
   };
   recognition.start();
  } catch(err) { micStatus.textContent = 'Mic initialization failed: ' + err.message; }
 };

 document.getElementById('stopMic').onclick = () => {
  if(recognition) recognition.stop();
  micPanel.classList.remove('mic-active-box');
  micStatus.textContent = 'Microphone standby.';
 };

 answer.addEventListener('input', send);
})();
</script>
</div>
"""

with st.sidebar:
    st.header("👔 Executive Profile")
    st.markdown(f"""
    * **Name:** {st.session_state.user_name}
    * **Email:** {st.session_state.user_email}
    * **Track:** {st.session_state.target_role}
    * **Level:** {st.session_state.experience_level}
    """)
    
    use_ai = st.checkbox("Enable GPT-4o Analytics", value=bool(os.getenv("OPENAI_API_KEY")))
    
    st.divider()
    st.markdown("### 📊 Session Progress")
    if "answers" in st.session_state and st.session_state.answers:
        answered = len([a for a in st.session_state.answers if not a.get("passed", False)])
        passed = len([a for a in st.session_state.answers if a.get("passed", False)])
        st.metric("Attempted", answered)
        st.metric("Passed", passed)
    else:
        st.metric("Attempted", 0)
        st.metric("Passed", 0)
        
    st.divider()
    if st.button("🚪 End Session & Switch", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.answers = []
        st.session_state.qidx = 0
        st.rerun()

if "qidx" not in st.session_state: st.session_state.qidx = 0
if "answers" not in st.session_state: st.session_state.answers = []

qs = QUESTIONS[st.session_state.target_role]
st.session_state.qidx %= len(qs)

# --- CYBER ROBOT INTERVIEWER PROMPT CONSOLE ---
current_question = qs[st.session_state.qidx]
st.markdown(f"""
<div class="robot-console">
    <div class="robot-avatar-box">🤖</div>
    <div class="robot-content">
        <div class="robot-title">AI Interrogator &bull; Assessment Item {st.session_state.qidx + 1} of {len(qs)} [{st.session_state.target_role}]</div>
        <div class="robot-speech">"{current_question}"</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- STAR METHOD GUIDANCE ---
with st.expander("💡 Executive Response Framework (STAR Method)", expanded=False):
    st.markdown("""
    * **Situation / Task**: Outline the operational context, business challenge, or technical constraints.
    * **Action**: Detail your specific strategic ownership, architecture decisions, or execution steps.
    * **Result**: Highlight quantifiable business impact, performance metrics, or key lessons learned.
    * **Tip**: Maintain structured pacing between 75 to 130 words.
    """)

browser_data = components.html(COMPONENT_HTML, height=540, scrolling=True)
if not isinstance(browser_data, dict): 
    browser_data = {}

answer = st.text_area("Your response (transcribed or edited manually)", value=browser_data.get("answer", ""), height=110, key="answer_box")
posture = browser_data.get("posture", "Awaiting video feed…")

def advanced_heuristic_feedback(text, posture_note, question=""):
    answer = (text or "").strip()
    lower = answer.lower()
    words_list = re.findall(r"\b[\w'-]+\b", answer)
    words = len(words_list)
    improvements, strengths = [], []

    if words < 12:
        strengths.append("Direct initial premise.")
        improvements.append(f"Response is concise ({words} words). Elaborate further on your personal contribution and business outcome.")
    elif words < 35:
        strengths.append("Clear delivery.")
        improvements.append("Include specific technical metrics or project milestones to strengthen your assertion.")
    elif words <= 140:
        strengths.append("Excellent professional depth and pacing.")
    else:
        strengths.append("Comprehensive coverage.")
        improvements.append("Streamline minor tangents to keep stakeholder focus on core achievements.")

    has_situation = any(term in lower for term in ["when", "project", "role", "time", "company", "team", "background", "designed", "built"])
    has_action = any(term in lower for term in ["led", "developed", "created", "analyzed", "handled", "implemented", "resolved", "prioritized"])
    has_result = any(term in lower for term in ["result", "outcome", "improved", "reduced", "increased", "learned", "successfully", "delivered", "metric"])

    if has_situation: strengths.append("Successfully established context.")
    else: improvements.append("Open by articulating the underlying context or challenge.")

    if has_action: strengths.append("Demonstrated direct ownership with active terminology.")
    else: improvements.append("Explicitly state the exact steps *you* spearheaded.")

    if has_result: strengths.append("Concluded effectively with a tangible outcome.")
    else: improvements.append("Summarize with a quantifiable business result or takeaway.")

    score = 50 + min(words, 70) // 3 + (12 if has_situation else 0) + (13 if has_action else 0) + (12 if has_result else 0)
    if words < 12: score -= 12
    score = max(35, min(97, score))

    return {
        "score": score, 
        "strengths": strengths, 
        "improvements": improvements,
        "sample_tip": "Structure: Situation -> Strategic Action -> Quantifiable Result."
    }

def get_ai_feedback(text, question):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""Review this interview answer constructively as an executive hiring director for a {st.session_state.target_role} role ({st.session_state.experience_level}).
Candidate Name: {st.session_state.user_name}
Question: {question}
Answer: {text}
Webcam Posture Cues: {posture}
Return valid JSON with:
- score (integer 0-100)
- strengths (array of unique strings specific to this answer)
- improvements (array of unique actionable suggestions)
- sample_tip (string)
Evaluate content, clarity, strategic structure, and professional relevance."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Return only valid JSON."}, {"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.5
    )
    return json.loads(response.choices[0].message.content)

# Action Buttons
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("💾 Save Response", type="primary", use_container_width=True):
        if answer.strip():
            st.session_state.answers.append({"question": current_question, "answer": answer.strip(), "posture": posture, "passed": False})
            st.success("Response securely saved.")
        else: 
            st.warning("Please record or input a response first.")
with col2:
    if st.button("⏭️ Skip Item", use_container_width=True):
        st.session_state.answers.append({"question": current_question, "answer": "[Passed / Skipped]", "posture": posture, "passed": True})
        st.info("Item marked as passed.")
        st.session_state.qidx = (st.session_state.qidx + 1) % len(qs)
        st.rerun()
with col3:
    if st.button("➡️ Next Item", use_container_width=True):
        if answer.strip(): 
            st.session_state.answers.append({"question": current_question, "answer": answer.strip(), "posture": posture, "passed": False})
        st.session_state.qidx = (st.session_state.qidx + 1) % len(qs)
        st.rerun()
with col4:
    if st.button("🔄 Reset Suite", use_container_width=True):
        st.session_state.answers = []
        st.session_state.qidx = 0
        st.rerun()

st.divider()

# --- ANALYTICS & SELECTION ODDS ---
st.header("📊 Executive Performance & Selection Analytics")

if st.session_state.answers:
    scores, labels = [], []
    valid_scores_list = []
    
    for idx, item in enumerate(st.session_state.answers, 1):
        if not item.get("passed", False):
            fb_prev = advanced_heuristic_feedback(item["answer"], item.get("posture", ""))
            score_val = fb_prev["score"]
            scores.append(score_val)
            valid_scores_list.append(score_val)
            labels.append(f"Q{idx}")
        else:
            scores.append(0)
            labels.append(f"Q{idx} (Passed)")

    if valid_scores_list:
        avg_score = sum(valid_scores_list) / len(valid_scores_list)
        selection_probability = int((avg_score * 0.70) + (85 * 0.15) + (85 * 0.15))
    else:
        selection_probability = 40

    st.markdown("### 🎯 Estimated Candidature Selection Probability")
    sp_col1, sp_col2 = st.columns([1, 2])
    with sp_col1:
        st.metric("Offer Probability", f"{selection_probability}%", delta="Top Tier Fit" if selection_probability > 75 else "Developing Fit")
    with sp_col2:
        if selection_probability >= 80:
            st.success("🟢 **Executive Recommendation**: High candidacy alignment across technical competence, structural articulation, and poise.")
        elif selection_probability >= 65:
            st.warning("🟡 **Conditional Recommendation**: Solid foundation. Refine quantitative metrics and maintain consistent vertical posture.")
        else:
            st.error("🔴 **Development Required**: Expand response depth, apply structured STAR method, and ensure formal presentation standards.")

    st.divider()

    if scores:
        fig = px.bar(
            x=labels, y=scores, 
            labels={"x": "Assessment Item", "y": "Performance Score (/100)"},
            title=f"Score Progression: {st.session_state.user_name}",
            color=scores, color_continuous_scale="Blues"
        )
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#f3f4f6"))
        st.plotly_chart(fig, use_container_width=True)

    for i, item in enumerate(st.session_state.answers, 1):
        with st.expander(f"Question {i}: {item['question']} {'[PASSED]' if item.get('passed') else ''}"):
            st.markdown(f"**Candidate Response:** {item['answer']}")
            st.markdown(f"**Posture Telemetry:** {item.get('posture', 'Unavailable')}")
            
            if not item.get("passed", False):
                if st.button(f"Generate Detailed Evaluation (Q{i})", key=f"feedback_{i}", type="secondary"):
                    try:
                        with st.spinner("Analyzing competency matrix…"):
                            fb = get_ai_feedback(item["answer"], item["question"]) if use_ai and os.getenv("OPENAI_API_KEY") else advanced_heuristic_feedback(item["answer"], item.get("posture", ""), item["question"])
                        
                        m1, m2 = st.columns(2)
                        with m1:
                            st.metric("Evaluation Score", f"{fb.get('score', 0)} / 100")
                        with m2:
                            st.info(f"**Coaching Directive:** {fb.get('sample_tip', '')}")

                        st.subheader("✅ Core Strengths")
                        for s in fb.get("strengths", []):
                            st.markdown(f"- {s}")

                        st.subheader("🔧 Areas for Optimization")
                        for imp in fb.get("improvements", []):
                            st.markdown(f"- {imp}")

                    except Exception as e:
                        st.error(f"Evaluation failed: {e}")
            else:
                st.info("Item skipped — no evaluation generated.")

    st.divider()
    report = f"# Executive Interview Performance & Selection Dossier\n\n"
    report += f"**Candidate:** {st.session_state.user_name} ({st.session_state.user_email})\n"
    report += f"**Track:** {st.session_state.target_role} ({st.session_state.experience_level})\n"
    report += f"**Estimated Selection Probability:** {selection_probability}%\n\n"
    report += "## Assessment Transcript\n"

    for i, item in enumerate(st.session_state.answers, 1):
        status = "PASSED" if item.get("passed") else "ATTEMPTED"
        report += f"### Item {i} ({status})\n**Prompt:** {item['question']}\n\n**Response:**\n{item['answer']}\n\n**Posture Status:** {item.get('posture', 'N/A')}\n\n---\n"
    
    st.download_button("📥 Download Executive Dossier (Markdown)", report, file_name=f"executive_dossier_{st.session_state.user_name.replace(' ', '_')}.md", mime="text/markdown")
else:
    st.caption("No assessment items recorded yet. Answer or pass items above to generate analytics and selection odds.")
