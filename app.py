import os
import json
import re
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import streamlit.components.v1 as components

load_dotenv()
st.set_page_config(page_title="AI Mock Interviewer", page_icon="🎤", layout="wide")
st.title("🎤 AI Mock Interviewer")
st.caption("Live browser webcam posture cues + microphone speech-to-text + interview feedback.")

# This browser component processes webcam frames locally with MediaPipe Tasks Vision.
# It uses browser Web Speech API for transcription, so no PyAudio is required.
COMPONENT_HTML = r"""
<div style="font-family:system-ui,sans-serif">
<style>
.panel{border:1px solid #bbb8;border-radius:12px;padding:12px;margin-bottom:12px}
.row{display:flex;gap:12px;flex-wrap:wrap}.col{flex:1;min-width:260px}
video{width:100%;max-height:320px;background:#111;border-radius:10px;object-fit:cover}
button{border:0;border-radius:8px;padding:10px 14px;margin:4px 4px 4px 0;cursor:pointer;background:#e5e7eb;color:#111;font-weight:600}
.primary{background:#2563eb;color:white}.status{font-size:14px;padding:8px 0}
textarea{width:100%;box-sizing:border-box;border:1px solid #aaa;border-radius:8px;padding:10px;font:inherit}
</style>
<div class="row">
 <div class="col panel">
  <h3>📷 Live posture check</h3><video id="video" autoplay playsinline muted></video>
  <div id="camStatus" class="status">Camera not started.</div>
  <b>Posture cue:</b> <span id="posture">Waiting for camera…</span><br>
  <b>Shoulder visibility:</b> <span id="visibility">—</span><br>
  <button class="primary" id="startCam">Start camera</button><button id="stopCam">Stop camera</button>
  <p style="font-size:12px;opacity:.75">Approximate visual cues only. Keep your face and shoulders in frame.</p>
 </div>
 <div class="col panel">
  <h3>🎙️ Microphone answer</h3><div id="micStatus" class="status">Not listening.</div>
  <button class="primary" id="startMic">Start speaking</button><button id="stopMic">Stop speaking</button>
  <label><b>Transcribed answer (editable):</b></label>
  <textarea id="answer" rows="8" placeholder="Click Start speaking and answer the question…"></textarea>
  <p style="font-size:12px;opacity:.75">Speech-to-text uses browser support (Chrome/Edge recommended). You can edit the text or type if unsupported.</p>
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
   camStatus.textContent='Camera active — live pose cues running.';
  }catch(e){camStatus.textContent='Camera is on, but pose model did not load. Check network access or browser console.';}
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
     if(vis<45)postureEl.textContent='Move back so your face and shoulders are visible.';
     else if(shoulderTilt>.09)postureEl.textContent='Shoulders appear uneven; adjust your position.';
     else if(headOffset>.13)postureEl.textContent='Head appears off-center; try facing the camera.';
     else postureEl.textContent='Face and shoulders appear reasonably centered.';
    }else{postureEl.textContent='Person not detected clearly; adjust lighting or camera.';visibilityEl.textContent='Low';}
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
  if(!SR){micStatus.textContent='Speech recognition unsupported here. Try Chrome/Edge or type your answer.';return;}
  recognition=new SR();recognition.continuous=true;recognition.interimResults=true;recognition.lang='en-US';
  finalText=answer.value?answer.value+' ':'';
  recognition.onstart=()=>micStatus.textContent='Listening… speak your answer.';
  recognition.onerror=e=>micStatus.textContent='Microphone error: '+e.error+'. Check browser permission.';
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
 st.header("Interview setup")
 role=st.selectbox("Interview role",list(QUESTIONS))
 level=st.selectbox("Experience level",["Student / Entry-level","Intermediate","Experienced"])
 use_ai=st.checkbox("Use OpenAI detailed feedback",value=bool(os.getenv("OPENAI_API_KEY")))
 st.caption("Without an API key, basic feedback is used.")
if "qidx" not in st.session_state: st.session_state.qidx=0
if "answers" not in st.session_state: st.session_state.answers=[]
qs=QUESTIONS[role]
st.session_state.qidx %= len(qs)
st.subheader(f"Question {st.session_state.qidx+1} of {len(qs)}")
st.markdown(f"### {qs[st.session_state.qidx]}")
st.info("Click Start camera and Start speaking in the panel. Allow browser permissions. Chrome or Edge is recommended.")
browser_data=components.html(COMPONENT_HTML,height=590,scrolling=True)
if not isinstance(browser_data,dict): browser_data={}
answer=st.text_area("Your answer (transcribed or typed)",value=browser_data.get("answer",""),height=130,key="answer_box")
posture=browser_data.get("posture","No live posture data received yet.")

def basic_feedback(text, posture_note, question=""):
    """Generate answer-specific feedback without requiring an API key."""
    answer = (text or "").strip()
    lower = answer.lower()
    words_list = re.findall(r"\b[\w'-]+\b", answer)
    words = len(words_list)
    sentences = [s.strip() for s in re.split(r"[.!?]+", answer) if s.strip()]
    improvements, strengths = [], []
    q_lower = (question or "").lower()

        strengths.append("You addressed the question with a concise response.")
        improvements.append("Add one concrete detail or example so the interviewer can judge your experience.")
    elif words <= 110:
        strengths.append("Your answer has enough detail to build on.")
    else:
        strengths.append("You provided substantial detail.")
        improvements.append("Trim repeated points and keep the answer focused on the most relevant details.")

    evidence_terms = ["for example", "for instance", "when i", "in my project", "at my", "we built", "i built", "i worked", "i handled", "i created", "i solved", "i led", "i improved", "i achieved", "i delivered", "i helped"]
    has_example = any(term in lower for term in evidence_terms)
    has_numbers = bool(re.search(r"\b\d+(?:%| percent| users| days| weeks| months| years)?\b", lower))
    if has_example:
        strengths.append("You included a personal action or example.")
    else:
        improvements.append("Make the answer more specific by describing something you personally did.")

    has_reasoning = any(term in lower for term in ["because", "so that", "the reason", "in order to", "decided to", "approach"])
    has_action = any(term in lower for term in ["i ", "we ", "first", "then", "next", "implemented", "tested", "analysed", "analyzed", "debugged", "communicated", "planned"])
    has_result = any(term in lower for term in ["result", "as a result", "finally", "which meant", "led to", "improved", "reduced", "increased", "learned", "learnt", "achieved", "completed", "resolved"]) or has_numbers
    if has_action:
        strengths.append("You describe an action or approach, not just an opinion.")
    else:
        improvements.append("Explain the steps you personally took, in the order you took them.")
    if has_reasoning:
        strengths.append("You explain some of the thinking behind your decision.")
    else:
        improvements.append("Add why you chose that approach or decision.")
    if has_result:
        strengths.append("You mention an outcome, learning, or measurable detail.")
    else:
        improvements.append("Finish with the result: what changed, what you achieved, or what you learned.")

    if any(term in q_lower for term in ["tell me about yourself", "technical background", "strength"]):
        if any(term in lower for term in ["skill", "experience", "project", "strength", "background", "interested"]):
            strengths.append("You connect your response to your background or relevant skills.")
        else:
            improvements.append("Connect your introduction to your relevant skills, experience, or career goal.")
    elif any(term in q_lower for term in ["bug", "challenge", "handled", "achievement", "project"]):
        if any(term in lower for term in ["problem", "challenge", "issue", "bug", "goal", "task"]):
            strengths.append("You identify a problem, challenge, or goal.")
        else:
            improvements.append("Clearly state the problem or goal before explaining your solution.")
        if not any(term in lower for term in ["fix", "solution", "solve", "resolved", "approach", "implemented"]):
            improvements.append("Explain the specific solution you chose and why it worked.")
    elif any(term in q_lower for term in ["customer", "unhappy", "people", "no"]):
        if any(term in lower for term in ["listen", "understand", "empathy", "question", "solution", "follow up", "follow-up"]):
            strengths.append("You mention a customer-focused response.")
        else:
            improvements.append("Show how you would listen, understand the person's concern, and agree on a practical next step.")
    elif any(term in q_lower for term in ["improve", "skill", "working to"]):
        if any(term in lower for term in ["practice", "learn", "course", "feedback", "improve", "plan"]):
            strengths.append("You mention a way to develop your skills.")
        else:
            improvements.append("Name a specific skill and explain the steps you are taking to improve it.")
    elif any(term in q_lower for term in ["reliable", "maintainable", "code"]):
        if any(term in lower for term in ["test", "review", "document", "readable", "maintain", "version control"]):
            strengths.append("You mention a practice that supports code quality.")
        else:
            improvements.append("Mention concrete practices such as tests, code reviews, clear naming, documentation, or version control.")

    if len(sentences) <= 1 and words >= 25:
        improvements.append("Break the answer into a few clear sentences so your main points are easier to follow.")
    if any(x in lower for x in ["um ", " uh ", "like like", "you know you know"]):
        improvements.append("Watch for repeated filler phrases; a short pause can help you sound more organised.")
    if any(x in (posture_note or "").lower() for x in ["off-center", "uneven", "move back"]):
        improvements.append("The camera cue suggests adjusting your position so your face and shoulders are centered and visible.")

    improvements = list(dict.fromkeys(improvements))[:5]
    strengths = list(dict.fromkeys(strengths))[:4]
    if not strengths:
        strengths = ["You made an attempt; use the suggestions to make the answer more complete."]
    if not improvements:
        improvements = ["Your answer covers several useful points. Add a concise example or measurable outcome to make it even stronger."]

    score = 40 + min(words, 90) // 3 + (8 if has_example else 0) + (6 if has_action else 0) + (6 if has_result else 0) + (4 if has_reasoning else 0)
    if words < 12:
        score -= 8
    score = max(30, min(95, score))
    return {"score": score, "strengths": strengths, "improvements": improvements,
            "sample_tip": "Try this structure: briefly set the context, explain your own actions and reasoning, then finish with the result or lesson learned."}


def get_ai_feedback(text, question):
 client=OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
 prompt=f"""Review this interview answer constructively. Role: {role}. Experience: {level}.
Question: {question}\nAnswer: {text}\nApproximate webcam cue: {posture}
Return JSON with score (0-100 integer), strengths (array), improvements (array), sample_tip (string).
Assess answer content and structure, not accent, appearance, disability, or personal traits. Do not overclaim what the webcam cue proves."""
 response=client.chat.completions.create(model="gpt-4o-mini",messages=[{"role":"system","content":"Return only valid JSON."},{"role":"user","content":prompt}],response_format={"type":"json_object"},temperature=.3)
 return json.loads(response.choices[0].message.content)

a,b,c=st.columns(3)
with a:
 if st.button("💾 Save answer",type="primary",use_container_width=True):
  if answer.strip():
   st.session_state.answers.append({"question":qs[st.session_state.qidx],"answer":answer.strip(),"posture":posture})
   st.success("Answer saved.")
  else: st.warning("Speak or type an answer first.")
with b:
 if st.button("➡️ Next question",use_container_width=True):
  if answer.strip(): st.session_state.answers.append({"question":qs[st.session_state.qidx],"answer":answer.strip(),"posture":posture})
  st.session_state.qidx=(st.session_state.qidx+1)%len(qs)
  st.rerun()
with c:
 if st.button("🔄 Reset interview",use_container_width=True):
  st.session_state.answers=[];st.session_state.qidx=0;st.rerun()
st.divider()
st.header("📊 Review saved answers")
if st.session_state.answers:
 for i,item in enumerate(st.session_state.answers,1):
  with st.expander(f"Question {i}: {item['question']}"):
   st.write("**Answer:**",item["answer"])
   st.write("**Posture cue:**",item.get("posture","Unavailable"))
   if st.button(f"Get feedback for answer {i}",key=f"feedback_{i}"):
    try:
     fb=get_ai_feedback(item["answer"],item["question"]) if use_ai and os.getenv("OPENAI_API_KEY") else basic_feedback(item["answer"],item.get("posture",""),item["question"])
     st.metric("Score",f"{fb.get('score',0)}/100")
     st.write("**Strengths**")
     for x in fb.get("strengths",[]): st.write("- "+str(x))
     st.write("**Improvements**")
     for x in fb.get("improvements",[]): st.write("- "+str(x))
     st.write("**Tip:**",fb.get("sample_tip","Use clear examples."))
    except Exception as e: st.error(f"Feedback failed: {e}")
 report="# AI Mock Interview Report\n\n"
 for i,item in enumerate(st.session_state.answers,1):
  report+=f"## Question {i}\n{item['question']}\n\n**Answer:**\n{item['answer']}\n\n**Posture cue:** {item.get('posture','Unavailable')}\n\n"
 st.download_button("Download interview report",report,file_name="interview_report.md",mime="text/markdown")
else: st.caption("Save at least one answer to review it here.")
