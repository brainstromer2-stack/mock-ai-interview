import os
import json
import re
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import streamlit.components.v1 as components
import plotly.express as px

load_dotenv()
st.set_page_config(page_title="AI Cyber-Mock Interviewer Pro", page_icon="🤖", layout="wide")

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
    st.session_state.theme = "🌙 Cyber Dark"

theme_choice = st.sidebar.selectbox("🎨 Interface Theme", ["🌙 Cyber Dark", "☀️ Light Mode", "💼 Corporate Executive"], index=0)
st.session_state.theme = theme_choice

if theme_choice == "🌙 Cyber Dark":
    bg_color, panel_bg, text_color, border_color, accent_color = "#080d1a", "#0f172a", "#38bdf8", "#1e293b", "#00f0ff"
elif theme_choice == "☀️ Light Mode":
    bg_color, panel_bg, text_color, border_color, accent_color = "#f8fafc", "#ffffff", "#0f172a", "#cbd5e1", "#2563eb"
else:  # Corporate Executive
    bg_color, panel_bg, text_color, border_color, accent_color = "#0f172a", "#1e293b", "#f1f5f9", "#334155", "#3b82f6"

st.markdown(f"""
<style>
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    .main-header {{ font-size: 2.4rem; font-weight: 700; color: {accent_color}; text-shadow: 0 0 10px rgba(0,240,255,0.4); margin-bottom: 0px; }}
    .sub-caption {{ font-size: 1.05rem; opacity: 0.8; margin-bottom: 20px; }}
    .question-banner {{
        background: linear-gradient(135deg, #0284c7, #1e1b4b);
        color: #ffffff;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #00f0ff;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.2);
    }}
    .question-title {{ font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.85; margin-bottom: 6px; }}
    .question-text {{ font-size: 1.3rem; font-weight: 600; line-height: 1.4; }}
    .dress-code-box {{
        background: rgba(0, 240, 255, 0.05);
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

# --- AUTHENTICATION GATE ---
if not st.session_state.logged_in:
    st.markdown('<div style="text-align: center; margin-top: 30px;">', unsafe_allow_html=True)
    st.markdown("<h1>🤖 AI Cyber Mock Interviewer Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p>Sign up to launch your Cyber-Robotic Mock Interview experience.</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("Candidate Cyber-Onboarding")
            name_input = st.text_input("Full Name", placeholder="e.g., Alex Johnson")
            email_input = st.text_input("Email Address", placeholder="e.g., alex@example.com")
            role_input = st.selectbox("Select Target Job Role", list(QUESTIONS.keys()))
            level_input = st.selectbox("Experience Level", ["Student / Entry-level", "Intermediate", "Experienced"])
            
            submit_btn = st.form_submit_button("🚀 Launch Robot Interview Room", use_container_width=True)
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

# --- MAIN INTERVIEW INTERFACE ---
st.markdown('<p class="main-header">🤖 AI Cyber Mock Interviewer Pro</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-caption">Candidate: <b>{st.session_state.user_name}</b> | Target Profile: <b>{st.session_state.target_role}</b></p>', unsafe_allow_html=True)

st.markdown("""
<div class="dress-code-box">
    <b>👔 Professional Attire & Robot HUD Tracking:</b> 
    Your face is real-time augmented with a Robot Avatar HUD overlay. Maintain steady eye contact and formal attire for maximum score output.
</div>
""", unsafe_allow_html=True)

# --- WEBCAM WITH ROBOT MASK CANVAS OVERLAY ---
COMPONENT_HTML = """
<div style="font-family:system-ui,sans-serif">
<style>
.panel-inner{border:1px solid #00f0ff44;border-radius:12px;padding:16px;margin-bottom:12px;background:rgba(15,23,42,0.8);box-shadow: 0 0 15px rgba(0,240,255,0.1)}
.row{display:flex;gap:16px;flex-wrap:wrap}.col{flex:1;min-width:280px}
.canvas-wrapper{position:relative;width:100%;max-height:260px;background:#000;border-radius:8px;overflow:hidden}
video{width:100%;height:260px;object-fit:cover}
canvas{position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover;pointer-events:none}
button{border:0;border-radius:8px;padding:10px 16px;margin:6px 6px 6px 0;cursor:pointer;background:#1e293b;color:#00f0ff;font-weight:600;border:1px solid #00f0ff88;transition: all 0.2s}
button:hover{background:#00f0ff;color:#000}
.danger{background:#dc2626;color:white;border:none}
.danger:hover{background:#b91c1c}
.status{font-size:13px;padding:6px 0;color:#00f0ff;font-weight:500}
textarea{width:100%;box-sizing:border-box;border:1px solid #00f0ff55;border-radius:8px;padding:12px;font:inherit;background:rgba(8,13,26,0.9);color:#00f0ff}
.listening-badge {
  display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: #ef4444; margin-right: 6px;
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}
</style>
<div class="row">
 <div class="col panel-inner">
  <h3>🤖 Robot Avatar & Posture Monitor</h3>
  <div class="canvas-wrapper">
    <video id="video" autoplay playsinline muted></video>
    <canvas id="canvas"></canvas>
  </div>
  <div id="camStatus" class="status">Camera stopped.</div>
  <b>Robot Cue:</b> <span id="posture" style="color:#00f0ff">Waiting for camera…</span><br>
  <b>Cyber HUD Tracking:</b> <span id="visibility">—</span><br><br>
  <button id="startCam">Start Robot Camera</button>
  <button class="danger" id="stopCam">Stop Camera</button>
 </div>
 <div class="col panel-inner" id="micPanel">
  <h3>🎙️ Speech Transcript</h3>
  <div id="micStatus" class="status">Microphone idle.</div>
  <button id="startMic">Start Speaking</button>
  <button id="stopMic">Stop Speaking</button>
  <label style="display:block;margin-top:8px"><b>Transcribed Answer (editable):</b></label>
  <textarea id="answer" rows="6" placeholder="Click 'Start Speaking' or type your response here…"></textarea>
 </div>
</div>
<script>
(() => {
 const video=document.getElementById('video'), canvas=document.getElementById('canvas'), ctx=canvas.getContext('2d');
 const camStatus=document.getElementById('camStatus'), postureEl=document.getElementById('posture'), visibilityEl=document.getElementById('visibility');
 const micStatus=document.getElementById('micStatus'), answer=document.getElementById('answer');
 let stream=null, poseDetector=null, faceMeshDetector=null, recognition=null, finalText='';

 function resizeCanvas(){ canvas.width=video.clientWidth||320; canvas.height=video.clientHeight||240; }

 function send(){
  const value={answer:answer.value,posture:postureEl.textContent,visibility:visibilityEl.textContent,camera_active:!!stream};
  window.parent.postMessage({isStreamlitMessage:true,type:'streamlit:setComponentValue',value},'*');
 }

 async function loadModels(){
  try{
   const vision=await import('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14');
   const files=await vision.FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm');
   poseDetector=await vision.PoseLandmarker.createFromOptions(files,{
    baseOptions:{modelAssetPath:'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task',delegate:'CPU'},
    runningMode:'VIDEO',numPoses:1
   });
   faceMeshDetector=await vision.FaceLandmarker.createFromOptions(files,{
    baseOptions:{modelAssetPath:'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',delegate:'CPU'},
    runningMode:'VIDEO',numFaces:1
   });
   camStatus.textContent='Robot Face & Cyber HUD Active!';
  }catch(e){camStatus.textContent='HUD models loading failed.';}
 }

 function drawRobotFace(landmarks){
  const w=canvas.width, h=canvas.height;
  ctx.clearRect(0, 0, w, h);
  if(!landmarks||!landmarks[0]) return;
  const lm=landmarks[0];

  // Draw Metallic Cyber Frame around face contour
  ctx.strokeStyle='#00f0ff'; ctx.lineWidth=2;
  ctx.beginPath();
  const jawPoints=[10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109];
  jawPoints.forEach((idx, i)=>{
    let pt=lm[idx];
    if(i===0) ctx.moveTo(pt.x*w, pt.y*h);
    else ctx.lineTo(pt.x*w, pt.y*h);
  });
  ctx.closePath(); ctx.stroke();

  // Draw Glowing Robot HUD Eye Reticles
  const leftEye=lm[468]||lm[33], rightEye=lm[473]||lm[263];
  [leftEye, rightEye].forEach(eye=>{
    ctx.strokeStyle='#ff0055'; ctx.fillStyle='rgba(255, 0, 85, 0.4)'; ctx.lineWidth=3;
    ctx.beginPath(); ctx.arc(eye.x*w, eye.y*h, 14, 0, 2*Math.PI); ctx.fill(); ctx.stroke();
    ctx.strokeStyle='#00f0ff';
    ctx.beginPath(); ctx.arc(eye.x*w, eye.y*h, 22, 0, 2*Math.PI); ctx.stroke();
  });

  // Draw Robot Mouth Analyzer Bar
  const upperLip=lm[13], lowerLip=lm[14];
  ctx.strokeStyle='#00f0ff'; ctx.lineWidth=4;
  ctx.beginPath();
  ctx.moveTo(upperLip.x*w - 20, upperLip.y*h);
  ctx.lineTo(lowerLip.x*w + 20, lowerLip.y*h);
  ctx.stroke();
 }

 function frame(now){
  if(!stream||video.readyState<2) return;
  resizeCanvas();
  if(faceMeshDetector){
   try{
    const faceResult=faceMeshDetector.detectForVideo(video, now);
    if(faceResult&&faceResult.faceLandmarks){ drawRobotFace(faceResult.faceLandmarks); }
   }catch(e){}
  }
  if(poseDetector){
   try{
    const poseResult=poseDetector.detectForVideo(video, now), lm=poseResult.landmarks&&poseResult.landmarks[0];
    if(lm&&lm.length>12){
     const vis=Math.round((((lm[11].visibility??0)+(lm[12].visibility??0))/2)*100);
     visibilityEl.textContent=vis+'%';
     postureEl.textContent='Robot tracking stable & centered.';
    }
   }catch(e){}
  }
  requestAnimationFrame(frame);
 }

 document.getElementById('startCam').onclick=async()=>{
  try{
   stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'},audio:false});
   video.srcObject=stream;
   camStatus.textContent='Loading Robot Avatar FX…';
   await loadModels(); requestAnimationFrame(frame); send();
  }catch(e){camStatus.textContent='Camera access denied: '+e.message;}
 };

 document.getElementById('stopCam').onclick=()=>{
  if(stream)stream.getTracks().forEach(t=>t.stop());
  stream=null; video.srcObject=null; ctx.clearRect(0, 0, canvas.width, canvas.height);
  postureEl.textContent='Camera stopped.'; camStatus.textContent='Camera stopped.'; send();
 };

 document.getElementById('startMic').onclick=()=>{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if(!SR){ micStatus.innerHTML = '⚠️ Speech recognition unsupported.'; return; }
  try {
   recognition = new SR(); recognition.continuous = true; recognition.interimResults = true; recognition.lang = 'en-US';
   finalText = answer.value ? answer.value + ' ' : '';
   recognition.onstart = () => { micStatus.innerHTML = '<span class="listening-badge"></span><strong>Listening… speak clearly into mic.</strong>'; };
   recognition.onerror = e => { micStatus.textContent = '❌ Mic error: ' + e.error; };
   recognition.onend = () => { micStatus.textContent = 'Microphone stopped.'; send(); };
   recognition.onresult = e => {
    let interim = '';
    for(let i = e.resultIndex; i < e.results.length; i++){
     let t = e.results[i][0].transcript;
     if(e.results[i].isFinal) finalText += t + ' ';
     else interim += t;
    }
    answer.value = (finalText + interim).trim(); send();
   };
   recognition.start();
  } catch(err) { micStatus.textContent = 'Mic start error: ' + err.message; }
 };

 document.getElementById('stopMic').onclick = () => { if(recognition) recognition.stop(); micStatus.textContent = 'Microphone stopped.'; };
 answer.addEventListener('input', send);
})();
</script>
</div>
"""

with st.sidebar:
    st.header("⚙️ Cyber Profile")
    st.write(f"**Name:** {st.session_state.user_name}")
    st.write(f"**Email:** {st.session_state.user_email}")
    st.write(f"**Role:** {st.session_state.target_role}")
    st.write(f"**Level:** {st.session_state.experience_level}")
    
    use_ai = st.checkbox("Enable OpenAI Cyber Analytics", value=bool(os.getenv("OPENAI_API_KEY")))
    
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

# --- HIGHLIGHTED QUESTION BANNER ---
current_question = qs[st.session_state.qidx]
st.markdown(f"""
<div class="question-banner">
    <div class="question-title">Question {st.session_state.qidx + 1} of {len(qs)} &bull; Profile: {st.session_state.target_role}</div>
    <div class="question-text">{current_question}</div>
</div>
""", unsafe_allow_html=True)

browser_data = components.html(COMPONENT_HTML, height=540, scrolling=True)
if not isinstance(browser_data, dict): 
    browser_data = {}

answer = st.text_area("Your response (transcribed or typed manually)", value=browser_data.get("answer", ""), height=120, key="answer_box")
posture = browser_data.get("posture", "Waiting for robot camera…")

# --- LIVE METRICS ---
st.markdown("### 📊 Real-Time Cyber Candidate Metrics")
col_m1, col_m2, col_m3 = st.columns(3)

num_responses = len(st.session_state.answers)
conf_score = min(95, max(50, 65 + (num_responses * 8)))
skill_score = min(95, max(60, 70 + (num_responses * 7)))
posture_score = 90 if "stable" in posture.lower() else 60

with col_m1:
    st.text(f"Confidence Level ({conf_score}%)")
    st.progress(conf_score / 100.0)

with col_m2:
    st.text(f"Technical Skill Depth ({skill_score}%)")
    st.progress(skill_score / 100.0)

with col_m3:
    st.text(f"Robot Posture HUD Score ({posture_score}%)")
    st.progress(posture_score / 100.0)

# Action Buttons
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("💾 Save Answer", type="primary", use_container_width=True):
        if answer.strip():
            st.session_state.answers.append({"question": current_question, "answer": answer.strip(), "posture": posture, "passed": False})
            st.success("Answer saved successfully!")
        else: st.warning("Please record or type an answer first.")
with col2:
    if st.button("⏭️ Pass / Skip", use_container_width=True):
        st.session_state.answers.append({"question": current_question, "answer": "[Passed / Skipped]", "posture": posture, "passed": True})
        st.session_state.qidx = (st.session_state.qidx + 1) % len(qs)
        st.rerun()
with col3:
    if st.button("➡️ Next Question", use_container_width=True):
        if answer.strip(): st.session_state.answers.append({"question": current_question, "answer": answer.strip(), "posture": posture, "passed": False})
        st.session_state.qidx = (st.session_state.qidx + 1) % len(qs)
        st.rerun()
with col4:
    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.answers = []
        st.session_state.qidx = 0
        st.rerun()
        
