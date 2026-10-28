import os
import json
import re
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import streamlit.components.v1 as components
import plotly.express as px

load_dotenv()
st.set_page_config(page_title="AI Mock Interviewer Pro", page_icon="🎤", layout="wide")

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
    st.session_state.theme = "🌙 Dark Mode"

# --- THEME STYLING CONFIGURATION ---
theme_choice = st.sidebar.selectbox("🎨 Interface Theme", ["🌙 Dark Mode", "☀️ Light Mode", "💼 Corporate Executive"], index=0)
st.session_state.theme = theme_choice

if theme_choice == "🌙 Dark Mode":
    bg_color, panel_bg, text_color, border_color, accent_color, card_bg = "#0e1117", "#161b22", "#f8fafc", "#30363d", "#2563eb", "#1f2937"
elif theme_choice == "☀️ Light Mode":
    bg_color, panel_bg, text_color, border_color, accent_color, card_bg = "#f8fafc", "#ffffff", "#0f172a", "#cbd5e1", "#2563eb", "#f1f5f9"
else:  # Corporate Executive
    bg_color, panel_bg, text_color, border_color, accent_color, card_bg = "#0f172a", "#1e293b", "#f1f5f9", "#334155", "#3b82f6", "#1e293b"

st.markdown(f"""
<style>
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    .main-header {{ font-size: 2.4rem; font-weight: 700; color: {accent_color}; margin-bottom: 0px; }}
    .sub-caption {{ font-size: 1.05rem; opacity: 0.8; margin-bottom: 20px; }}
    .question-banner {{
        background: linear-gradient(135deg, {accent_color}, #1e40af);
        color: #ffffff;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    .question-title {{ font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.85; margin-bottom: 6px; }}
    .question-text {{ font-size: 1.3rem; font-weight: 600; line-height: 1.4; }}
    .dress-code-box {{
        background: rgba(37, 99, 235, 0.1);
        border: 1px dashed {accent_color};
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 16px;
    }}
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

# --- AUTHENTICATION GATE (LOGIN / SIGNUP) ---
if not st.session_state.logged_in:
    st.markdown('<div style="text-align: center; margin-top: 30px;">', unsafe_allow_html=True)
    st.markdown("<h1>🎤 Welcome to AI Mock Interviewer Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p>Sign up or log in to customize your interview profile and track your progress.</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("Candidate Onboarding / Login")
            name_input = st.text_input("Full Name", placeholder="e.g., Alex Johnson")
            email_input = st.text_input("Email Address", placeholder="e.g., alex@example.com")
            role_input = st.selectbox("Select Target Job Role", list(QUESTIONS.keys()))
            level_input = st.selectbox("Experience Level", ["Student / Entry-level", "Intermediate", "Experienced"])
            
            submit_btn = st.form_submit_button("🚀 Start Interview Session", use_container_width=True)
            if submit_btn:
                if name_input.strip() and email_input.strip():
                    st.session_state.logged_in = True
                    st.session_state.user_name = name_input.strip()
                    st.session_state.user_email = email_input.strip()
                    st.session_state.target_role = role_input
                    st.session_state.experience_level = level_input
                    st.rerun()
                else:
                    st.warning("Please enter your name and email to proceed.")
    st.stop()

# --- MAIN APP INTERFACE ---
st.markdown('<p class="main-header">🎤 AI Mock Interviewer Pro</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-caption">Candidate: <b>{st.session_state.user_name}</b> | Role: <b>{st.session_state.target_role}</b> ({st.session_state.experience_level})</p>', unsafe_allow_html=True)

# --- DRESS CODE NOTICE ---
st.markdown("""
<div class="dress-code-box">
    <b>👔 Professional Attire & Dress Code Tip:</b> 
    Wearing formal or business-casual attire (collared shirt, blazer, or neat formal wear) significantly improves initial visual impressions, confidence scoring, and overall candidate selection odds.
</div>
""", unsafe_allow_html=True)

# --- WEBCAM & SPEECH COMPONENT ---
COMPONENT_HTML = """
<div style="font-family:system-ui,sans-serif">
<style>
.panel-inner{border:1px solid #cbd5e1;border-radius:12px;padding:16px;margin-bottom:12px;background:rgba(255,255,255,0.02);box-shadow: 0 2px 4px rgba(0,0,0,0.05)}
.row{display:flex;gap:16px;flex-wrap:wrap}.col{flex:1;min-width:280px}
video{width:100%;max-height:240px;background:#0f172a;border-radius:8px;object-fit:cover}
button{border:0;border-radius:8px;padding:10px 16px;margin:6px 6px 6px 0;cursor:pointer;background:#334155;color:#f8fafc;font-weight:600;transition: background 0.2s}
button:hover{background:#475569}
.primary{background:#2563eb;color:white}
.primary:hover{background:#1d4ed8}
.danger{background:#dc2626;color:white}
.danger:hover{background:#b91c1c}
.status{font-size:13px;padding:6px 0;font-weight:500}
textarea{width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:12px;font:inherit;background:rgba(0,0,0,0.1);color:inherit}
.listening-badge {
  display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: #ef4444; margin-right: 6px;
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}
.mic-active-box { border: 2px solid #ef4444 !important; background: rgba(239, 68, 68, 0.05) !important; }
</style>
<div class="row">
 <div class="col panel-inner">
  <h3>📷 Live Posture & Attire Monitor</h3>
  <video id="video" autoplay playsinline muted></video>
  <div id="camStatus" class="status">Camera not started.</div>
  <b>Posture cue:</b> <span id="posture" style="color:#38bdf8">Waiting for camera…</span><br>
  <b>Shoulder visibility:</b> <span id="visibility">—</span><br><br>
  <button class="primary" id="startCam">Start camera</button>
  <button class="danger" id="stopCam">Stop camera</button>
 </div>
 <div class="col panel-inner" id="micPanel">
  <h3>🎙️ Speech Transcript</h3>
  <div id="micStatus" class="status">Microphone idle.</div>
  <button class="primary" id="startMic">Start speaking</button>
  <button id="stopMic">Stop speaking</button>
  <label style="display:block;margin-top:8px"><b>Transcribed answer (editable):</b></label>
  <textarea id="answer" rows="6" placeholder="Click 'Start speaking' or type your response here…"></textarea>
 </div>
</div>
<script>
(() => {
 const video=document.getElementById('video'), camStatus=document.getElementById('camStatus');
 const postureEl=document.getElementById('posture'), visibilityEl=document.getElementById('visibility');
 const micStatus=document.getElementById('micStatus'), answer=document.getElementById('answer');
 const micPanel=document.getElementById('micPanel');
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
   camStatus.textContent='Camera active — live pose analysis running.';
  }catch(e){camStatus.textContent='Pose model failed to load.';}
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
     if(vis<45)postureEl.textContent='Move back so face and shoulders are visible.';
     else if(shoulderTilt>.09)postureEl.textContent='Shoulders appear uneven; adjust posture.';
     else if(headOffset>.13)postureEl.textContent='Head appears off-center; face forward.';
     else postureEl.textContent='Posture is well-centered and balanced.';
    }else{postureEl.textContent='Person not detected clearly.';visibilityEl.textContent='Low';}
   }catch(e){}
  }
  requestAnimationFrame(frame);
 }

 document.getElementById('startCam').onclick=async()=>{
  try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'},audio:false});video.srcObject=stream;
   camStatus.textContent='Camera started. Loading pose model…';await loadPose();requestAnimationFrame(frame);send();}
  catch(e){camStatus.textContent='Camera permission denied.';}
 };

 document.getElementById('stopCam').onclick=()=>{if(stream)stream.getTracks().forEach(t=>t.stop());stream=null;video.srcObject=null;postureEl.textContent='Camera stopped.';visibilityEl.textContent='—';camStatus.textContent='Camera stopped.';send();};

 document.getElementById('startMic').onclick=()=>{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!SR){
   micStatus.innerHTML = '⚠️ Speech recognition unsupported. Please use Chrome/Edge or type your answer.';
   return;
  }
  try {
   recognition = new SR();
   recognition.continuous = true;
   recognition.interimResults = true;
   recognition.lang = 'en-US';
   finalText = answer.value ? answer.value + ' ' : '';

   recognition.onstart = () => {
    micStatus.innerHTML = '<span class="listening-badge"></span><strong>Listening… speak clearly into your microphone.</strong>';
    micPanel.classList.add('mic-active-box');
   };
   recognition.onerror = e => {
    micStatus.textContent = '❌ Microphone error: ' + e.error;
    micPanel.classList.remove('mic-active-box');
   };
   recognition.onend = () => {
    micStatus.textContent = 'Microphone stopped listening.';
    micPanel.classList.remove('mic-active-box');
    send();
   };
   recognition.onresult = e => {
    let interim = '';
    for(let i = e.resultIndex; i < e.results.length; i++){
     let t = e.results[i][0].transcript;
     if(e.results[i].isFinal) finalText += t + ' ';
     else interim += t;
    }
    answer.value = (finalText + interim).trim();
    send();
   };
   recognition.start();
  } catch(err) {
   micStatus.textContent = 'Failed to start microphone: ' + err.message;
  }
 };

 document.getElementById('stopMic').onclick = () => {
  if(recognition) recognition.stop();
  micPanel.classList.remove('mic-active-box');
  micStatus.textContent = 'Microphone stopped.';
 };

 answer.addEventListener('input', send);
})();
</script>
</div>
"""

with st.sidebar:
    st.header("⚙️ User Profile")
    st.write(f"**Name:** {st.session_state.user_name}")
    st.write(f"**Email:** {st.session_state.user_email}")
    st.write(f"**Role:** {st.session_state.target_role}")
    st.write(f"**Level:** {st.session_state.experience_level}")
    
    use_ai = st.checkbox("Enable OpenAI Analytics", value=bool(os.getenv("OPENAI_API_KEY")))
    
    st.divider()
    st.markdown("### 📈 Session Progress")
    if "answers" in st.session_state and st.session_state.answers:
        answered = len([a for a in st.session_state.answers if not a.get("passed", False)])
        passed = len([a for a in st.session_state.answers if a.get("passed", False)])
        st.metric("Attempted", answered)
        st.metric("Passed", passed)
    else:
        st.metric("Attempted", 0)
        st.metric("Passed", 0)
        
    st.divider()
    if st.button("🚪 Logout / Switch Profile", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.answers = []
        st.session_state.qidx = 0
        st.rerun()

if "qidx" not in st.session_state: st.session_state.qidx = 0
if "answers" not in st.session_state: st.session_state.answers = []

qs = QUESTIONS[st.session_state.target_role]
st.session_state.qidx %= len(qs)

# --- HIGHLIGHTED QUESTION PROMPT BANNER ---
current_question = qs[st.session_state.qidx]
st.markdown(f"""
<div class="question-banner">
    <div class="question-title">Question {st.session_state.qidx + 1} of {len(qs)} &bull; Profile: {st.session_state.target_role}</div>
    <div class="question-text">{current_question}</div>
</div>
""", unsafe_allow_html=True)

# --- STAR METHOD GUIDANCE ---
with st.expander("💡 Guidance & Tips for Answering This Question (STAR Framework)", expanded=False):
    st.markdown("""
    * **Situation / Task**: Set the technical or professional context and state the core objective.
    * **Action**: Explain the exact technical or strategic steps *you* personally executed.
    * **Result**: Conclude with tangible outcomes, performance gains, metrics, or lessons learned.
    * **Tip**: Keep your response concise, structured, and focused on your individual impact.
    """)

browser_data = components.html(COMPONENT_HTML, height=540, scrolling=True)
if not isinstance(browser_data, dict): 
    browser_data = {}

answer = st.text_area("Your response (transcribed or typed manually)", value=browser_data.get("answer", ""), height=120, key="answer_box")
posture = browser_data.get("posture", "Waiting for camera…")

# --- LIVE CANDIDATURE METRICS (CONFIDENCE, SKILLS, POSTURE BARS) ---
st.markdown("### 📊 Real-Time Candidate Analysis Indicators")
col_m1, col_m2, col_m3 = st.columns(3)

num_responses = len(st.session_state.answers)
conf_score = min(95, max(50, 65 + (num_responses * 8)))
skill_score = min(95, max(60, 70 + (num_responses * 7)))

posture_score = 85
if "uneven" in posture.lower() or "off-center" in posture.lower() or "move back" in posture.lower():
    posture_score = 55
elif "balanced" in posture.lower() or "centered" in posture.lower():
    posture_score = 92

with col_m1:
    st.text(f"Confidence Level ({conf_score}%)")
    st.progress(conf_score / 100.0)

with col_m2:
    st.text(f"Technical Skill Match ({skill_score}%)")
    st.progress(skill_score / 100.0)

with col_m3:
    st.text(f"Posture & Stability ({posture_score}%)")
    st.progress(posture_score / 100.0)

mc1, mc2 = st.columns(2)
mc1.metric("Live Posture Analysis Status", posture)
mc2.metric("Response Pacing Rating", "Optimal" if len(answer.split()) > 20 else "Awaiting detailed answer")

def advanced_heuristic_feedback(text, posture_note, question=""):
    answer = (text or "").strip()
    lower = answer.lower()
    words_list = re.findall(r"\b[\w'-]+\b", answer)
    words = len(words_list)
    improvements, strengths = [], []

    if words < 12:
        strengths.append("Quick opening.")
        improvements.append(f"Your answer contains only {words} words. Elaborate with specifics on your role and outcome.")
    elif words < 35:
        strengths.append("Concise delivery.")
        improvements.append("Add a concrete example or metric to substantiate your professional claim.")
    elif words <= 140:
        strengths.append("Solid depth and pacing.")
    else:
        strengths.append("Thorough explanation.")
        improvements.append("Trim minor tangents to keep the focus tight on core milestones.")

    has_situation = any(term in lower for term in ["when", "project", "role", "time", "company", "team", "background", "designed", "built"])
    has_action = any(term in lower for term in ["led", "developed", "created", "analyzed", "handled", "implemented", "resolved", "prioritized"])
    has_result = any(term in lower for term in ["result", "outcome", "improved", "reduced", "increased", "learned", "successfully", "delivered", "metric"])

    if has_situation: strengths.append("Successfully established context.")
    else: improvements.append("Start by clearly stating the context or challenge you encountered.")

    if has_action: strengths.append("Demonstrated personal ownership with active verbs.")
    else: improvements.append("Explicitly state the exact steps *you* performed.")

    if has_result: strengths.append("Concluded with an effective outcome or takeaway.")
    else: improvements.append("Wrap up by highlighting the measurable result or lesson learned.")

    score = 50 + min(words, 70) // 3 + (12 if has_situation else 0) + (13 if has_action else 0) + (12 if has_result else 0)
    if words < 12: score -= 12
    score = max(35, min(97, score))

    return {
        "score": score, 
        "strengths": strengths, 
        "improvements": improvements,
        "sample_tip": "Remember: Situation -> Action -> Measurable Result."
    }

def get_ai_feedback(text, question):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""Review this interview answer constructively as an expert hiring manager for a {st.session_state.target_role} role ({st.session_state.experience_level}).
Candidate Name: {st.session_state.user_name}
Question: {question}
Answer: {text}
Webcam Posture Cues: {posture}
Return valid JSON with:
- score (integer 0-100)
- strengths (array of unique strings specific to this answer)
- improvements (array of unique actionable suggestions)
- sample_tip (string)
Evaluate content, clarity, structure, and professional relevance."""
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
    if st.button("💾 Save Answer", type="primary", use_container_width=True):
        if answer.strip():
            st.session_state.answers.append({"question": current_question, "answer": answer.strip(), "posture": posture, "passed": False})
            st.success("Answer saved successfully!")
        else: 
            st.warning("Please record or type an answer first.")
with col2:
    if st.button("⏭️ Pass / Skip", use_container_width=True):
        st.session_state.answers.append({"question": current_question, "answer": "[Passed / Skipped]", "posture": posture, "passed": True})
        st.info("Question skipped and logged.")
        st.session_state.qidx = (st.session_state.qidx + 1) % len(qs)
        st.rerun()
with col3:
    if st.button("➡️ Next Question", use_container_width=True):
        if answer.strip(): 
            st.session_state.answers.append({"question": current_question, "answer": answer.strip(), "posture": posture, "passed": False})
        st.session_state.qidx = (st.session_state.qidx + 1) % len(qs)
        st.rerun()
with col4:
    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.answers = []
        st.session_state.qidx = 0
        st.rerun()

st.divider()

# --- ANALYTICS & SAVED ANSWERS WITH SELECTION PROBABILITY ---
st.header("📊 Performance Analytics & Selection Odds")

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

    # Calculate Overall Selection Odds
    if valid_scores_list:
        avg_score = sum(valid_scores_list) / len(valid_scores_list)
        # Weighting: 70% answer quality, 15% posture, 15% professional attire/presentation
        selection_probability = int((avg_score * 0.70) + (posture_score * 0.15) + (85 * 0.15))
    else:
        selection_probability = 40

    st.markdown("### 🎯 Estimated Candidate Selection Odds")
    sp_col1, sp_col2 = st.columns([1, 2])
    with sp_col1:
        st.metric("Probability of Offer/Selection", f"{selection_probability}%", delta="High Fit" if selection_probability > 75 else "Moderate Fit")
    with sp_col2:
        if selection_probability >= 80:
            st.success("🟢 **Strong Hire Recommendation**: High alignment in technical depth, STAR structure, posture stability, and professional attire.")
        elif selection_probability >= 65:
            st.warning("🟡 **Moderate Hire Recommendation**: Solid foundation. Enhance specific project metrics and maintain consistent upright posture.")
        else:
            st.error("🔴 **Needs Improvement**: Expand answer detail, practice STAR framework, and ensure formal professional presentation.")

    st.divider()

    if scores:
        fig = px.bar(
            x=labels, y=scores, 
            labels={"x": "Interview Question", "y": "Performance Score (/100)"},
            title=f"Session Score Progression for {st.session_state.user_name}",
            color=scores, color_continuous_scale="Viridis"
        )
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color=text_color))
        st.plotly_chart(fig, use_container_width=True)

    for i, item in enumerate(st.session_state.answers, 1):
        with st.expander(f"Question {i}: {item['question']} {'[PASSED]' if item.get('passed') else ''}"):
            st.markdown(f"**Recorded Answer:** {item['answer']}")
            st.markdown(f"**Posture Note Recorded:** {item.get('posture', 'Unavailable')}")
            
            if not item.get("passed", False):
                if st.button(f"Generate Detailed Feedback (Q{i})", key=f"feedback_{i}", type="secondary"):
                    try:
                        with st.spinner("Analyzing communication depth & profile relevance..."):
                            fb = get_ai_feedback(item["answer"], item["question"]) if use_ai and os.getenv("OPENAI_API_KEY") else advanced_heuristic_feedback(item["answer"], item.get("posture", ""), item["question"])
                        
                        m1, m2 = st.columns(2)
                        with m1:
                            st.metric("Score", f"{fb.get('score', 0)} / 100")
                        with m2:
                            st.info(f"**Coaching Tip:** {fb.get('sample_tip', '')}")

                        st.subheader("✅ Key Strengths")
                        for s in fb.get("strengths", []):
                            st.markdown(f"- {s}")

                        st.subheader("🔧 Areas for Improvement")
                        for imp in fb.get("improvements", []):
                            st.markdown(f"- {imp}")

                    except Exception as e:
                        st.error(f"Feedback generation failed: {e}")
            else:
                st.info("Passed question — no evaluation required.")

    st.divider()
    report = f"# AI Mock Interview Executive Summary & Selection Odds\n\n"
    report += f"**Candidate Name:** {st.session_state.user_name}\n"
    report += f"**Email:** {st.session_state.user_email}\n"
    report += f"**Target Role:** {st.session_state.target_role} ({st.session_state.experience_level})\n"
    report += f"**Estimated Selection Probability:** {selection_probability}%\n\n"
    report += "## Session Breakdown\n"

    for i, item in enumerate(st.session_state.answers, 1):
        status = "PASSED" if item.get("passed") else "ATTEMPTED"
        report += f"### Question {i} ({status})\n**Prompt:** {item['question']}\n\n**Response:**\n{item['answer']}\n\n**Posture Cue:** {item.get('posture', 'N/A')}\n\n---\n"
    
    st.download_button("📥 Download Comprehensive Markdown Report", report, file_name=f"interview_report_{st.session_state.user_name.replace(' ', '_')}.md", mime="text/markdown")
else:
    st.caption("No answers recorded yet. Answer or pass questions above to view analytics and selection odds.")
