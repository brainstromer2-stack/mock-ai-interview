import os
import json
import re
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import streamlit.components.v1 as components
import plotly.graph_objects as go
import plotly.express as px

load_dotenv()
st.set_page_config(page_title="AI Mock Interviewer Pro", page_icon="🎤", layout="wide")

# --- CUSTOM CSS STYLING ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0px;
    }
    .sub-caption {
        font-size: 1.1rem;
        color: #4b5563;
        margin-bottom: 20px;
    }
    .card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 16px;
    }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🎤 AI Mock Interviewer Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-caption">Real-time local computer vision posture cues, speech recognition transcription, and actionable interview analytics.</p>', unsafe_allow_html=True)

COMPONENT_HTML = r"""
<div style="font-family:system-ui,sans-serif">
<style>
.panel{border:1px solid #cbd5e1;border-radius:12px;padding:16px;margin-bottom:12px;background:#ffffff;box-shadow: 0 2px 4px rgba(0,0,0,0.02)}
.row{display:flex;gap:16px;flex-wrap:wrap}.col{flex:1;min-width:280px}
video{width:100%;max-height:280px;background:#0f172a;border-radius:8px;object-fit:cover}
button{border:0;border-radius:8px;padding:10px 16px;margin:6px 6px 6px 0;cursor:pointer;background:#e2e8f0;color:#1e293b;font-weight:600;transition: background 0.2s}
button:hover{background:#cbd5e1}
.primary{background:#2563eb;color:white}
.primary:hover{background:#1d4ed8}
.danger{background:#dc2626;color:white}
.danger:hover{background:#b91c1c}
.status{font-size:13px;padding:6px 0;color:#475569;font-weight:500}
textarea{width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:12px;font:inherit;background:#f8fafc}
textarea:focus{outline:2px solid #2563eb}
</style>
<div class="row">
 <div class="col panel">
  <h3>📷 Live Posture Monitor</h3>
  <video id="video" autoplay playsinline muted></video>
  <div id="camStatus" class="status">Camera not started.</div>
  <b>Posture cue:</b> <span id="posture" style="color:#0284c7">Waiting for camera…</span><br>
  <b>Shoulder visibility:</b> <span id="visibility">—</span><br><br>
  <button class="primary" id="startCam">Start camera</button>
  <button class="danger" id="stopCam">Stop camera</button>
  <p style="font-size:11px;color:#64748b;margin-top:8px">Approximate visual cues only. Keep face and shoulders well-lit in frame.</p>
 </div>
 <div class="col panel">
  <h3>🎙️ Speech Transcript</h3>
  <div id="micStatus" class="status">Microphone idle.</div>
  <button class="primary" id="startMic">Start speaking</button>
  <button id="stopMic">Stop speaking</button>
  <label style="display:block;margin-top:8px"><b>Transcribed answer (editable):</b></label>
  <textarea id="answer" rows="7" placeholder="Click 'Start speaking' or type your response here…"></textarea>
  <p style="font-size:11px;color:#64748b;margin-top:8px">Powered by Web Speech API (Chrome/Edge recommended).</p>
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
  }catch(e){camStatus.textContent='Pose model failed to load. Check network connection.';}
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
     if(vis<45)postureEl.textContent='Move back so your face and shoulders are fully visible.';
     else if(shoulderTilt>.09)postureEl.textContent='Shoulders appear uneven; adjust posture.';
     else if(headOffset>.13)postureEl.textContent='Head appears off-center; face forward.';
     else postureEl.textContent='Posture is well-centered and balanced.';
    }else{postureEl.textContent='Person not detected clearly; adjust lighting.';visibilityEl.textContent='Low';}
   }catch(e){}
  }
  requestAnimationFrame(frame);
 }
 document.getElementById('startCam').onclick=async()=>{
  try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'},audio:false});video.srcObject=stream;
   camStatus.textContent='Camera started. Loading pose model…';await loadPose();requestAnimationFrame(frame);send();}
  catch(e){camStatus.textContent='Camera permission denied or unavailable: '+e.message;}
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
    use_ai = st.checkbox("Enable OpenAI Detailed Analytics", value=bool(os.getenv("OPENAI_API_KEY")))
    st.info("💡 Tip: Without an OpenAI API key, advanced heuristic evaluation is automatically applied.")
    
    st.divider()
    st.markdown("### 📈 Session Statistics")
    if "answers" in st.session_state and st.session_state.answers:
        total_answered = len([a for a in st.session_state.answers if not a.get("passed", False)])
        total_passed = len([a for a in st.session_state.answers if a.get("passed", False)])
        st.metric("Questions Attempted", total_answered)
        st.metric("Questions Passed", total_passed)
    else:
        st.metric("Questions Attempted", 0)
        st.metric("Questions Passed", 0)

if "qidx" not in st.session_state: st.session_state.qidx = 0
if "answers" not in st.session_state: st.session_state.answers = []

qs = QUESTIONS[role]
st.session_state.qidx %= len(qs)

st.markdown(f"### Question {st.session_state.qidx + 1} of {len(qs)}")
st.info(f"**Prompt:** {qs[st.session_state.qidx]}")

browser_data = components.html(COMPONENT_HTML, height=580, scrolling=True)
if not isinstance(browser_data, dict): 
    browser_data = {}

answer = st.text_area("Your response (transcribed or typed manually)", value=browser_data.get("answer", ""), height=130, key="answer_box")
posture = browser_data.get("posture", "No live posture data received yet.")

def advanced_heuristic_feedback(text, posture_note, question=""):
    """Comprehensive fallback feedback generator evaluating structure, relevance, and delivery."""
    answer = (text or "").strip()
    lower = answer.lower()
    words_list = re.findall(r"\b[\w'-]+\b", answer)
    words = len(words_list)
    sentences = [s.strip() for s in re.split(r"[.!?]+", answer) if s.strip()]
    improvements, strengths = [], []
    q_lower = (question or "").lower()

    # Structural Assessment
    if words < 12:
        strengths.append("Direct response opening.")
        improvements.append("Answer is too brief. Elaborate using context, specific action taken, and outcome.")
    elif words < 35:
        strengths.append("Concise core delivery.")
        improvements.append("Incorporate a concrete project example or personal contribution metric.")
    elif words <= 120:
        strengths.append("Balanced depth and detail.")
    else:
        strengths.append("Comprehensive coverage.")
        improvements.append("Trim auxiliary tangents to maintain interviewer engagement.")

    # STAR Method Check
    has_example = any(term in lower for term in ["for example", "instance", "project", "when i", "at my", "built", "implemented"])
    has_action = any(term in lower for term in ["ied", "ed ", "managed", "designed", "resolved", "led", "developed", "created"])
    has_result = any(term in lower for term in ["result", "outcome", "improved", "reduced", "increased", "learned", "achieved"])

    if has_example: strengths.append("Included concrete professional context/example.")
    else: improvements.append("Structure using STAR method: clearly state the Situation, Task, Action, and Result.")
    
    if has_action: strengths.append("Clearly highlighted personal ownership and actions.")
    else: improvements.append("Emphasize your specific individual contributions using active verbs ('I designed', 'I fixed').")

    if has_result: strengths.append("Successfully highlighted an outcome or lesson learned.")
    else: improvements.append("Conclude your answer with a quantifiable result or takeaway.")

    # Scoring calculation
    score = 45 + min(words, 80) // 3 + (10 if has_example else 0) + (10 if has_action else 0) + (10 if has_result else 0)
    if words < 12: score -= 10
    score = max(35, min(96, score))

    return {
        "score": score, 
        "strengths": strengths if strengths else ["Attempted the response with basic structure."], 
        "improvements": improvements if improvements else ["Refine timing and maintain focus on key achievements."],
        "sample_tip": "Structure your response with: 1. Context, 2. Your specific action, 3. Measurable result."
    }

def get_ai_feedback(text, question):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""Review this interview answer constructively as an expert hiring manager. Role: {role}. Level: {level}.
Question: {question}
Answer: {text}
Webcam Posture Cues: {posture}
Return valid JSON with:
- score (integer 0-100)
- strengths (array of strings)
- improvements (array of strings)
- sample_tip (string)
Evaluate content, clarity, structure, and professional relevance. Avoid comments on immutable personal traits."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Return only valid JSON."}, {"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3
    )
    return json.loads(response.choices[0].message.content)

# Action Buttons Layout
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("💾 Save Answer", type="primary", use_container_width=True):
        if answer.strip():
            st.session_state.answers.append({"question": qs[st.session_state.qidx], "answer": answer.strip(), "posture": posture, "passed": False})
            st.success("Answer saved successfully!")
        else: 
            st.warning("Please provide an answer before saving.")
with col2:
    if st.button("⏭️ Pass / Skip", use_container_width=True):
        st.session_state.answers.append({"question": qs[st.session_state.qidx], "answer": "[Passed / Skipped by Candidate]", "posture": posture, "passed": True})
        st.info("Question skipped and logged as passed.")
        st.session_state.qidx = (st.session_state.qidx + 1) % len(qs)
        st.rerun()
with col3:
    if st.button("➡️ Next Question", use_container_width=True):
        if answer.strip(): 
            st.session_state.answers.append({"question": qs[st.session_state.qidx], "answer": answer.strip(), "posture": posture, "passed": False})
        st.session_state.qidx = (st.session_state.qidx + 1) % len(qs)
        st.rerun()
with col4:
    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.answers = []
        st.session_state.qidx = 0
        st.rerun()

st.divider()

# --- REVIEW SAVED ANSWERS & ANALYTICS ---
st.header("📊 Performance Analytics & Saved Answers")

if st.session_state.answers:
    # Graphical Data Summary
    valid_scores = []
    labels = []
    for idx, item in enumerate(st.session_state.answers, 1):
        if not item.get("passed", False):
            # Evaluate preview score
            fb_prev = advanced_heuristic_feedback(item["answer"], item.get("posture", ""))
            valid_scores.append(fb_prev["score"])
            labels.append(f"Q{idx}")
        else:
            valid_scores.append(0)
            labels.append(f"Q{idx} (Passed)")

    if valid_scores:
        fig = px.bar(
            x=labels, 
            y=valid_scores, 
            labels={"x": "Interview Question", "y": "Performance Score (/100)"},
            title="Score Progression Across Session",
            color=valid_scores,
            color_continuous_scale="Blues"
        )
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    for i, item in enumerate(st.session_state.answers, 1):
        with st.expander(f"Question {i}: {item['question']} {'[SKIPPED/PASSED]' if item.get('passed') else ''}"):
            st.write(**"Recorded Answer:"**, item["answer"])
            st.write(**"Posture Note Recorded:"**, item.get("posture", "Unavailable"))
            
            if not item.get("passed", False):
                if st.button(f"Generate Deep Feedback (Q{i})", key=f"feedback_{i}", type="secondary"):
                    try:
                        with st.spinner("Analyzing response and delivery metrics..."):
                            fb = get_ai_feedback(item["answer"], item["question"]) if use_ai and os.getenv("OPENAI_API_KEY") else advanced_heuristic_feedback(item["answer"], item.get("posture", ""), item["question"])
                        
                        m1, m2 = st.columns(2)
                        with m1:
                            st.metric("Evaluated Score", f"{fb.get('score', 0)} / 100")
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
                st.info("This question was passed. No feedback generated.")

    st.divider()
    
    # Export Report
    report = "# AI Mock Interview Performance Report\n\n"
    for i, item in enumerate(st.session_state.answers, 1):
        status = "PASSED / SKIPPED" if item.get("passed") else "ATTEMPTED"
        report += f"## Question {i} ({status})\n**Prompt:** {item['question']}\n\n**Response:**\n{item['answer']}\n\n**Posture Status:** {item.get('posture', 'N/A')}\n\n---\n"
    
    st.download_button("📥 Download Comprehensive Markdown Report", report, file_name="interview_performance_report.md", mime="text/markdown")

else:
    st.caption("No answers saved yet. Complete or pass questions above to generate graphical analytics and structured reports.")
