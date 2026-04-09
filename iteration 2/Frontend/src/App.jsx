import{useState}from"react";
import"./App.css";
import{useEffect,useRef}from"react";

const API_BASE="http://136.113.194.22:8000";

function App(){
  const[username,setUsername]=useState("");
  const[password,setPassword]=useState("");
  const[currentUser,setCurrentUser]=useState("");
  const[loginError,setLoginError]=useState("");
  const[loginPopup,setLoginPopup]=useState("");
  const[jobDescription,setJobDescription]=useState("");
  const[messages,setMessages]=useState([
    {role:"assistant",content:"Paste the job description you want to prepare for, then ask your job application questions."},
  ]);
  const[input,setInput]=useState("");
  const[sending,setSending]=useState(false);
  const[status,setStatus]=useState("");
  const handleLogin=async()=>{
    const cleanUsername=username.trim();
    const cleanPassword=password.trim();

    if(!cleanUsername||!cleanPassword){
      setLoginError("Enter username and password");
      return;
    }

    try{
      setLoginError("");
      const res=await fetch(`${API_BASE}/login`,{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
          username:cleanUsername,
          password:cleanPassword,
        }),
      });

      const data=await res.json();

      if(!res.ok){
        throw new Error(data.detail||"Login failed");
      }

      setCurrentUser(data.username);
      setPassword("");
      setLoginPopup("Login successful");
      setTimeout(()=>setLoginPopup(""),2000);
    }catch(err){
      setLoginError(err.message||"Login failed");
    }
  };
  const handleSend=async()=>{
    const text=input.trim();
    if(!text||sending||!currentUser)return;
    setInput("");
    setMessages((prev)=>[...prev,{role:"user",content:text}]);

    if(!jobDescription){
      setJobDescription(text);
      setMessages((prev)=>[
        ...prev,
        {role:"assistant",content:"Got it. Now ask your job application questions."},
      ]);
      return;
    }

    setSending(true)

    try{
      const res=await fetch(`${API_BASE}/chat`,{
        method:"POST",
        headers:{
          "Content-Type":"application/json",
          "X-User":currentUser,
        },
        body: JSON.stringify({ message: text, job_description: jobDescription }),
      });
      if(!res.ok){
        const t=await res.text();
        throw new Error(t||"Chat failed");
      }
      const data=await res.json();
      setTimeout(()=>setStatus(""),2000);
    
      const clean = (data.reply || "")
        .replace(/according to the sources.*?,/i,"")
        .replace(/\[[^\]]+\]/g,"")
        .trim();
    
      setMessages(p=>[...p,{role:"assistant",content:clean}]);
    
    }catch (e) {
      const msg = e?.message || "Request failed";
      setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${msg}` }]);
    } finally {
      setSending(false);
    }      
  };
  const handleLogout=()=>{
    setCurrentUser("");
    setUsername("");
    setPassword("");
    setJobDescription("");
    setLoginError("");
    setLoginPopup("");
    setInput("");
    setStatus("");
    setMessages([
      {role:"assistant",content:"Paste the job description you want to prepare for, then ask your job application questions."},
    ]);
  };
  const endRef=useRef(null);
  useEffect(()=>{endRef.current?.scrollIntoView({behavior:"smooth"});},[messages]);

  const uploadFile=async(file)=>{
    if(!currentUser)return;
    try{
      setStatus("Uploading...");
      const formData=new FormData();
      formData.append("file",file);
      const res=await fetch(`${API_BASE}/upload`,{
        method:"POST",
        headers:{
          "X-User":currentUser,
        },
        body:formData,
      });

      if(!res.ok){
        const text=await res.text();
        throw new Error(text||"Upload failed");
      }
      const data=await res.json();
      setStatus(`File uploaded:${data.filename}`);
      setTimeout(()=>setStatus(""),2000);
    }catch(err){
      setStatus("Upload failed or embedding failed after upload");
      setTimeout(()=>setStatus(""),3000);
    }
  };
  const TypingDots = () => (
    <span className="typing-dots" aria-label="Generating">
      <span>.</span><span>.</span><span>.</span>
    </span>
  );

  if(!currentUser){
    return(
      <div className="page">
        <div className="login-card">
          <div className="chat-header">JobPrep Login</div>

          <div className="login-form">
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e)=>setUsername(e.target.value)}
            />

            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e)=>setPassword(e.target.value)}
              onKeyDown={(e)=>{
                if(e.key==="Enter")handleLogin();
              }}
            />

            <button onClick={handleLogin}>Login</button>

            {loginError&&<div className="login-error">{loginError}</div>}
          </div>

          {loginPopup&&<div className="popup-box">{loginPopup}</div>}
        </div>
      </div>
    );
  }

  return(
    <div className="page">
      <div>
        <div className="chatbox">
          <div className="chat-header chat-header-row">
            <span>Job Application Helper</span>
            <button className="logout-btn" onClick={handleLogout}>Logout</button>
          </div>

          <div className="chat-messages">
  {messages.map((m, i) => (
    <div
      key={i}
      className={`msg ${m.role === "user" ? "user" : "assistant"}`}
    >
      {m.content}
    </div>
  ))}

  {sending && (
    <div className="msg assistant">
      <span className="typing-dots" aria-label="Generating">
        <span>.</span><span>.</span><span>.</span>
      </span>
    </div>
  )}

  <div ref={endRef} />
</div>



          <div className="chat-input">
            <div
              className="upload-btn"
              onClick={()=>document.getElementById("fileInput").click()}
              title="Choose file"
            >
              +
            </div>

            <input
              id="fileInput"
              type="file"
              accept=".txt,.pdf"
              style={{display:"none"}}
              onChange={(e)=>{
                const file=e.target.files?.[0];
                if(file){
                  uploadFile(file);
                  e.target.value="";
                }
              }}
            />

            <input
              type="text"
              placeholder="Type a message..."
              value={input}
              onChange={(e)=>setInput(e.target.value)}
              onKeyDown={(e)=>{
                if(e.key==="Enter")handleSend();
              }}
            />

            <button onClick={handleSend} disabled={sending}>
              Send
            </button>
          </div>
        </div>

        {status&&<div className="below-status">{status}</div>}
        {loginPopup&&<div className="popup-box">{loginPopup}</div>}
      </div>
    </div>
  );
}

export default App;
