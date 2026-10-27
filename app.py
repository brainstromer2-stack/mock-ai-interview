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

# --- THEME STYLING CONFIGURATION ---
if "theme" not in st.session_state:
    st.session_state.theme = "🌙 Dark Mode"

theme_choice = st.sidebar.selectbox("🎨 Interface Theme", ["🌙 Dark Mode", "☀️ Light Mode", "💼 Corporate Executive"], index=0)
st.session_state.theme = theme_choice

# Define Theme Colors
if theme_choice == "🌙 Dark Mode":
    bg_color, panel_bg, text_color, border_color, accent_color = "#0e1117", "#161b22", "#f8fafc", "#30363d", "#2563eb"
elif theme_choice == "☀️ Light Mode":
    bg_color, panel_bg, text_color, border_color, accent_color = "#f8fafc", "#ffffff", "#0f172a", "#cbd5e1", "#2563eb"
else:  # Corporate Executive
    bg_color, panel_bg, text_color, border_color, accent_color = "#0f172a", "#1e293b", "#f1f5f9", "#334155", "#3b82f6"

st.markdown(f"""
<style>
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    .main-header {{ font-size: 2.4rem; font-weight: 700; color: {accent_color}; margin-bottom: 0px; }}
    .sub-caption {{ font-size: 1.05rem; opacity: 0.8; margin-bottom: 20px; }}
    .panel {{ background-color: {panel_bg}; border: 1px solid {border_color}; border-radius: 12px; padding: 16px; margin-bottom: 12px; }}
    .guidance-box {{ background-color: {panel_bg}; border-left: 4px solid {accent_color}; padding: 12px 16px; border-radius: 6px; margin-bottom: 15px; font-size: 0.95rem; }}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🎤 AI Mock Interviewer Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-caption">Real-time local computer vision posture cues, speech recognition transcription, and dynamic non-repetitive feedback analytics.</p>', unsafe_allow_html=True)

# --- WEBCAM & SPEECH COMPONENT ---
COMPONENT_HTML = r"""
<div style="font-family:system-ui,sans-serif">
<style>
.panel-inner{border:1px solid #cbd5e1;border-radius:12px;padding:16px;margin-bottom:12px;background:rgba(255,255,255,0.02);box-shadow: 0 2px 4px rgba(0,0,0,0.05)}
.row{display:flex;gap:16px;flex-wrap:wrap}.col{flex:1;min-width:280px}
video{width:100%;max-height:260px;background:#0f172a;border-radius:8px;object-fit:cover}
button{border:0;border-radius:8px;padding:10px 16px;margin:6px 6px 6px 0;cursor:pointer;background:#334155;color:#f8fafc;font-weight:600;transition: background 0.2s}
button:hover{background:#475569}
.primary{background:#2563eb;color:white}
.primary:hover{background:#1d4ed8}
.danger{background:#dc2626;color:white}
.danger:hover{background:#b91c1c}
.status{font-size:13px;padding:6px 0;font-weight:500}
textarea{width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:12px;font:inherit;background:rgba(0,0,0,0.1);color:inherit}
</style>
<div class="row">
 <div class="col panel-inner">
  <h3>📷 Live Posture Monitor</h3>
  <video id="video" autoplay playsinline muted></video>
  <div id="camStatus" class="status">Camera not started.</div>
  <b>Posture cue:</b> <span id="posture" style="color:#38bdf8">Waiting for camera…</span><br>
  <b>Shoulder visibility:</b> <span id="visibility">—</span><br><br>
  <button class="primary" id="startCam">Start camera</button>
  <button class="danger" id="stopCam">Stop camera</button>
 </div>
 <div class="col panel-inner">
  <h3>🎙️ Speech Transcript</h3>
  <div id="micStatus" class="status">Microphone idle.</div>
  <button class="primary" id="startMic">Start speaking</button>
  <button id="stopMic">Stop speaking</button>
  <label style="display:block;margin-top:8px"><b>Transcribed answer (editable):</b></label>
  <textarea id="answer" rows="7" placeholder="Click 'Start speaking' or type your response here…"></textarea>
 </div>
</div>
<script>
(() => {
 const video=document.getElementById('video'), camStatus=document.getElementById('camStatus');
 const postureEl=document.getElementById('posture'), visibilityEl=document.getElementById('visibility');
 const micStatus=document.getElementById('micStatus'), answer=document.getElementById('answer');
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
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){micStatus.textContent='Speech recognition unsupported. Please type your answer.';return;}
  recognition=new SR();recognition.continuous=true;recognition.interimResults=true;recognition.lang='en-US';
  finalText=answer.value?answer.value+' ':'';
  recognition.onstart=()=>micStatus.textContent='Listening… speak clearly.';
  recognition.onerror=e=>micStatus.textContent='Microphone error: '+e.error;
  recognition.onend=()=>{micStatus.textContent='Listening stopped.';send();};
  recognition.onresult=e=>{let interim='';for(let i=e.resultIndex;i<e.results.length;i++){let t=e.results[i][0].transcript;if(e.results[i].isFinal)finalText+=t+' ';else interim+=t;}answer.value=(finalText+interim).trim();send();};
  recognition.start();
 };
 document.getElementById('stopMic').onclick=()=>{if(recognition)recognition.stop();};
 answer.addEventListener('input',send);
})();
</script>
</div>
"""

QUESTIONS = {
    "Software Developer": [
        "Tell me about yourself and your technical background.",
        "Describe a challenging bug you solved and how you approached it.",
        "How do you make sure your code is reliable and maintainable?"
    ],
    "Student / Fresher": [
        "Tell me about yourself.",
        "Describe a project or achievement you are proud of.",
        "What is one skill you are working to improve, and how?"
    ],
    "Sales / Customer Service": [
        "Tell me about yourself and your experience working with people.",
        "Describe how you would handle an unhappy customer.",
        "How do you stay motivated when you hear 'no'?"
    ],
    "General": [
        "Tell me about yourself.",
        "What is one strength you would bring to this role?",
        "Describe a challenge you faced and how you handled it."
    ]
}

with st.sidebar:
    st.header("⚙️ Interview Setup")
    role = st.selectbox("Select Role", list(QUESTIONS))
    level = st.selectbox("Experience Level", ["Student / Entry-level", "Intermediate", "Experienced"])
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

if "qidx" not in st.session_state: st.session_state.qidx = 0
if "answers" not in st.session_state: st.session_state.answers = []

qs = QUESTIONS[role]
st.session_state.qidx %= len(qs)

st.markdown(f"### Question {st.session_state.qidx + 1} of {len(qs)}")
st.info(f"**Prompt:** {qs[st.session_state.qidx]}")

# --- INTERACTIVE GUIDANCE BOX (STAR METHOD HINTS) ---
with st.expander("💡 Guidance & Tips for Answering This Question (STAR Framework)", expanded=False):
    st.markdown("""
    * **Situation / Task**: Briefly set the context or explain the core problem you faced.
    * **Action**: Highlight the specific steps *you* personally took, tools used, or decisions made.
    * **Result**: Conclude with the measurable outcome, feedback received, or lesson learned.
    * **Tip**: Keep your response structured between 60 to 120 words for optimal impact.
    """)

browser_data = components.html(COMPONENT_HTML, height=560, scrolling=True)
if not isinstance(browser_data, dict): 
    browser_data = {}

answer = st.text_area("Your response (transcribed or typed manually)", value=browser_data.get("answer", ""), height=130, key="answer_box")
posture = browser_data.get("posture", "No live posture data received yet.")

def advanced_heuristic_feedback(text, posture_note, question=""):
    """Advanced dynamic heuristic analyzer with randomized variation to prevent repetition."""
    answer = (text or "").strip()
    lower = answer.lower()
    words_list = re.findall(r"\b[\w'-]+\b", answer)
    words = len(words_list)
    improvements, strengths = [], []
    q_lower = (question or "").lower()

    # Dynamic Length Analysis
    if words < 12:
        strengths.append("Quick, direct opening.")
        improvements.append(f"Your answer contains only {words} words. Expand on your answer by detailing your personal role and the project outcome.")
    elif words < 35:
        strengths.append("Concise and to the point.")
        improvements.append("Add one concrete technical example or specific metric to substantiate your claim.")
    elif words <= 130:
        strengths.append("Excellent pacing and depth of detail.")
    else:
        strengths.append("Comprehensive explanation provided.")
        improvements.append("Consider trimming minor tangents to keep the interviewer fully focused on core milestones.")

    # STAR Keyword Detection
    has_situation = any(term in lower for term in ["when", "project", "role", "time", "company", "team", "background"])
    has_action = any(term in lower for term in ["built", "designed", "implemented", "resolved", "led", "developed", "created", "analyzed", "handled"])
    has_result = any(term in lower for term in ["result", "outcome", "improved", "reduced", "increased", "learned", "successfully", "delivered"])

    if has_situation: strengths.append("Successfully established context or background situation.")
    else: improvements.append("Begin by clearly establishing the context or challenge you encountered.")

    if has_action: strengths.append("Demonstrated clear personal ownership through
