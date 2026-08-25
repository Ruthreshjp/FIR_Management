import { useState, useRef, useEffect } from "react"

const FIELD_LABELS = {
  "complainant.name": "Complainant Name",
  "complainant.email": "Email",
  "complainant.phone": "Phone Number",
  "complainant.age": "Age",
  "complainant.address": "Address",
  "complainant.city": "City",
  "complainant.gender": "Gender",
  "complainant.id_type": "ID Proof Type",
  "complainant.id_number": "ID Proof Number",
  "incident.date": "Incident Date",
  "incident.time": "Incident Time",
  "incident.location": "Incident Location",
  "incident.landmark": "Landmark",
  "incident.station": "Police Station",
  "incident.district": "District",
  "accused.name": "Accused Name",
  "accused.description": "Accused Description",
  "accused.vehicle": "Vehicle Details",
  "accused.weapon": "Weapon Used",
}

export default function SpeechFormFiller({ onFieldsExtracted, onSwitchToManual }) {
  const [mode, setMode] = useState("idle")
  // modes: idle | recording | processing | review-transcript | extracting | review | manual

  const [transcript, setTranscript] = useState("")
  const [rawTranscript, setRawTranscript] = useState("")
  const [extractedFields, setExtractedFields] = useState(null)
  const [missingFields, setMissingFields] = useState([])
  const [error, setError] = useState("")
  const [recordingTime, setRecordingTime] = useState(0)

  const [liveTranscript, setLiveTranscript] = useState("")
  
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const streamRef = useRef(null)
  const timerRef = useRef(null)
  const recognitionRef = useRef(null)
  const finalTranscriptRef = useRef("")

  // Timer for recording duration
  useEffect(() => {
    if (mode === "recording") {
      timerRef.current = setInterval(() => {
        setRecordingTime(t => t + 1)
      }, 1000)
    } else {
      clearInterval(timerRef.current)
      setRecordingTime(0)
    }
    return () => clearInterval(timerRef.current)
  }, [mode])

  const formatTime = (s) =>
    `${Math.floor(s/60).toString().padStart(2,"0")}:${(s%60).toString().padStart(2,"0")}`

  const startRecording = async () => {
    setError("")
    setLiveTranscript("")
    finalTranscriptRef.current = ""
    audioChunksRef.current = []

    // 1. Setup Web Speech API for Live Preview
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    if (SpeechRecognition) {
      recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-IN';
      
      recognition.onresult = (e) => {
        let interim = '';
        let final = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
          if (e.results[i].isFinal) final += e.results[i][0].transcript;
          else interim += e.results[i][0].transcript;
        }
        if (final) finalTranscriptRef.current += final + ' ';
        setLiveTranscript(finalTranscriptRef.current + interim);
      };
      recognition.onerror = (e) => console.warn("Live transcript error:", e.error);
      recognitionRef.current = recognition;
    }

    // 2. Setup MediaRecorder for Groq Whisper
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true
        }
      })
      streamRef.current = stream

      const mr = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm" : "audio/ogg"
      })
      mr.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data)
      }
      mr.start(1000)
      mediaRecorderRef.current = mr
      
      if (recognition) {
        try { recognition.start(); } catch(e) {}
      }
      
      setMode("recording")

    } catch (err) {
      setError(
        err.name === "NotAllowedError"
          ? "Microphone permission denied. Please allow in browser."
          : "Microphone error: " + err.message
      )
    }
  }

  const stopAndProcess = () => {
    setMode("processing")

    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch(e) {}
    }

    // Stop microphone stream immediately
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
    }

    // Give MediaRecorder 500ms to flush final chunk
    setTimeout(() => {
      if (!mediaRecorderRef.current ||
          mediaRecorderRef.current.state === "inactive") {
        processAudioChunks()
        return
      }

      mediaRecorderRef.current.onstop = () => {
        processAudioChunks()
      }

      try {
        mediaRecorderRef.current.stop()
      } catch(e) {
        console.error("MediaRecorder stop error:", e)
        processAudioChunks() // try anyway
      }
    }, 500)
  }

  const processAudioChunks = async () => {
    try {
      console.log("[Speech] Audio chunks collected:", audioChunksRef.current.length)

      if (audioChunksRef.current.length === 0) {
        setError("No audio recorded. Make sure your microphone is working.")
        setMode("idle")
        return
      }

      const mimeType = mediaRecorderRef.current?.mimeType || "audio/webm"
      const blob = new Blob(audioChunksRef.current, { type: mimeType })

      if (blob.size < 1000) {
        setError("Recording too short or empty. Please speak for at least 3 seconds.")
        setMode("idle")
        return
      }

      const formData = new FormData()
      const format = mimeType.includes("ogg") ? "ogg" : "webm"
      formData.append("audio", blob, `recording.${format}`)
      formData.append("format", format)

      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 180000) // 3 minutes timeout

      try {
        const res = await fetch("http://localhost:5000/api/transcribe", {
          method: "POST",
          body: formData,
          signal: controller.signal
        })

        clearTimeout(timeout)

        if (!res.ok) {
          throw new Error(`Server error ${res.status}`)
        }

        const data = await res.json()
        if (data.success && data.text) {
          setRawTranscript(data.text)
          setMode("review-transcript")
        } else {
          setError(data.error || "Transcription failed.")
          setMode("idle")
        }
      } catch (fetchErr) {
        clearTimeout(timeout)
        setError("Network error or timeout. Please check backend connection. (" + fetchErr.message + ")")
        setMode("idle")
      }
    } catch (err) {
      setError("Unexpected error: " + err.message)
      setMode("manual")
    }
  }

  const extractDetails = async () => {
    setMode("extracting")
    setError("")
    
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 60000)
      
      const res = await fetch("http://localhost:5000/api/speech/extract-fields", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript: rawTranscript }),
        signal: controller.signal
      })
      
      clearTimeout(timeout)
      
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      
      const data = await res.json()
      
      if (data.success && data.fields) {
        setTranscript(data.transcript || rawTranscript)
        setExtractedFields(data.fields)
        if (onFieldsExtracted) onFieldsExtracted(data.fields)
        setMode("review")
      } else {
        setError(data.error || "Field extraction failed.")
        setMode("review-transcript")
      }
    } catch (err) {
      setError("Failed to extract fields: " + err.message)
      setMode("review-transcript")
    }
  }

  const speakAgain = () => {
    setMode("idle")
    setError("")
    setLiveTranscript("")
  }

  // ── RENDER ──

  // IDLE: Show speak button
  if (mode === "idle") return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.title}>🎤 Voice Complaint Entry</span>
        <button
          onClick={() => onSwitchToManual ? onSwitchToManual() : setMode("manual")}
          style={styles.linkBtn}
        >
          Fill form manually instead
        </button>
      </div>
      {error && (
        <div style={{ padding: '12px', background: '#FFF5F5', color: 'var(--danger)', borderRadius: '8px', marginBottom: '16px', fontWeight: '500', fontSize: '14px', border: '1px solid var(--danger)' }}>
          ❌ {error}
        </div>
      )}
      <p style={styles.hint}>
        Speak your complete complaint including your name,
        phone number, address, incident details, and what happened.
        The form will be filled automatically.
      </p>
      <div style={styles.exampleBox}>
        <span style={styles.exampleLabel}>Example:</span>
        <p style={styles.exampleText}>
          "My name is Sanjay, my phone number is 8220079401,
          I live at Sabari Nagar, Pallipalyam, Erode.
          Yesterday night at 10 PM near the market road,
          gangsters were selling cocaine to students..."
        </p>
      </div>
      <button onClick={startRecording} type="button" style={styles.recordBtn}>
        🎤 &nbsp; Start Speaking
      </button>
    </div>
  )

  // RECORDING: Live display
  if (mode === "recording") return (
    <div style={{...styles.container, borderColor: "#A8362B"}}>
      <div style={styles.recordingHeader}>
        <div style={styles.recDot}/>
        <span style={styles.recLabel}>
          Recording {formatTime(recordingTime)}
        </span>
        <button type="button" onClick={stopAndProcess} style={styles.stopBtn}>
          ⏹ &nbsp; Stop & Process
        </button>
      </div>
      <p style={styles.hint}>
        Audio is being recorded. Speak your complete complaint clearly.
      </p>
      {liveTranscript && (
        <div style={styles.liveTranscriptBox}>
          <span style={styles.liveTranscriptLabel}>Live Transcript Preview:</span>
          <p style={styles.liveTranscriptText}>{liveTranscript}</p>
        </div>
      )}
    </div>
  )

  // PROCESSING
  if (mode === "processing") return (
    <div style={styles.container}>
      <div style={styles.processingBox}>
        <div style={styles.spinner} />
        <div style={{ marginLeft: "15px" }}>
          <p style={styles.processingTitle}>Processing...</p>
          <p style={styles.processingText}>
            Transcribing audio with Whisper...
          </p>
        </div>
      </div>
    </div>
  )

  // REVIEW TRANSCRIPT
  if (mode === "review-transcript") return (
    <div style={styles.container}>
      <div style={styles.reviewHeader}>
        <span style={styles.title}>📝 Review Transcript</span>
        <button type="button" onClick={speakAgain} style={styles.linkBtn}>
          🎤 Discard & Record Again
        </button>
      </div>
      
      {error && (
        <div style={{ padding: '12px', background: '#FFF5F5', color: 'var(--danger)', borderRadius: '8px', marginBottom: '16px', fontWeight: '500', fontSize: '14px', border: '1px solid var(--danger)' }}>
          ❌ {error}
        </div>
      )}
      
      <p style={styles.hint}>
        Please review the transcribed text. You can edit any mistakes or add missing details manually before we extract the form fields.
      </p>
      
      <textarea
        value={rawTranscript}
        onChange={(e) => setRawTranscript(e.target.value)}
        style={{
          width: "100%",
          minHeight: "150px",
          padding: "16px",
          borderRadius: "8px",
          border: "1.5px solid var(--border)",
          fontFamily: "var(--sans)",
          fontSize: "14px",
          lineHeight: "1.6",
          marginBottom: "16px",
          backgroundColor: "#F8FAFC",
          color: "var(--text-primary)"
        }}
      />
      
      <button 
        onClick={extractDetails} 
        style={{...styles.recordBtn, background: "var(--india-blue, #003580)"}}
      >
        ✨ Extract Details & Fill Form
      </button>
    </div>
  )

  // EXTRACTING
  if (mode === "extracting") return (
    <div style={styles.container}>
      <div style={styles.processingBox}>
        <div style={styles.spinner} />
        <div style={{ marginLeft: "15px" }}>
          <p style={styles.processingTitle}>Analyzing Transcript...</p>
          <p style={styles.processingText}>
            Using LLM to extract complaint details and auto-fill the form...
          </p>
        </div>
      </div>
    </div>
  )

  // REVIEW: Show extracted fields with missing highlights
  if (mode === "review" && extractedFields) return (
    <div style={styles.container}>
      <div style={styles.reviewHeader}>
        <span style={styles.title}>
          ✅ Fields extracted from speech
        </span>
        <div style={styles.reviewActions}>
          <button type="button" onClick={speakAgain} style={styles.linkBtn}>
            🎤 Speak again
          </button>
          <button
            type="button"
            onClick={() => onSwitchToManual ? onSwitchToManual() : setMode("manual")}
            className="btn btn-primary"
            style={{ padding: '8px 16px', fontSize: '13px', borderRadius: '6px' }}
          >
            ➡️ Review & Submit Form
          </button>
        </div>
      </div>

      {/* Transcript */}
      <details style={styles.transcriptBox}>
        <summary style={styles.transcriptSummary}>
          View Raw Transcript
        </summary>
        <p style={styles.transcriptText}>{transcript}</p>
      </details>

      {/* Drafted Complaint Narrative */}
      {extractedFields?.complaint_narrative && (
        <div style={styles.draftBox}>
          <h4 style={styles.draftTitle}>Drafted Complaint</h4>
          <p style={styles.draftText}>{extractedFields.complaint_narrative}</p>
        </div>
      )}

      {/* Extracted fields grid */}
      <div style={styles.fieldGrid}>
        {Object.entries(FIELD_LABELS).map(([key, label]) => {
          const [section, field] = key.split(".")
          const value = extractedFields[section]?.[field]
          const isMissing = !value ||
            missingFields.includes(key) ||
            missingFields.includes(field)

          return (
            <div
              key={key}
              style={{
                ...styles.fieldCard,
                borderColor: isMissing ? "#E67E22" : "#3D6B4F",
                background: isMissing ? "#FFF9F5" : "#F0FFF4"
              }}
            >
              <span style={styles.fieldLabel}>{label}</span>
              {isMissing ? (
                <span style={styles.missingTag}>
                  ⚠️ Not mentioned
                </span>
              ) : (
                <span style={styles.fieldValue}>
                  {String(value)}
                </span>
              )}
            </div>
          )
        })}
      </div>

      {/* Missing fields warning */}
      {missingFields.length > 0 && (
        <div style={styles.warningBox}>
          <p style={styles.warningTitle}>
            ⚠️ {missingFields.length} fields not detected
          </p>
          <p style={styles.warningText}>
            Speak again to add missing details,
            or scroll down to fill them manually in the form.
          </p>
          <button type="button" onClick={speakAgain} style={styles.speakAgainBtn}>
            🎤 Speak again to fill missing fields
          </button>
        </div>
      )}

      {/* Witnesses */}
      {extractedFields.witnesses?.length > 0 && (
        <div style={styles.witnessBox}>
          <span style={styles.fieldLabel}>
            Witnesses detected:
          </span>
          {extractedFields.witnesses.map((w, i) => (
            <div key={i} style={styles.witnessPill}>
              {w.name} {w.phone ? `· ${w.phone}` : ""}
            </div>
          ))}
        </div>
      )}
    </div>
  )

  // MANUAL fallback
  if (mode === "manual") return (
    <div style={styles.manualBar}>
      <span style={styles.hint}>
        {error ? (
          <span style={{ color: 'var(--danger)', fontWeight: 600 }}>❌ {error}</span>
        ) : (
          "Filling form manually"
        )}
      </span>
      <button type="button" onClick={speakAgain} style={styles.linkBtn}>
        🎤 Try voice instead
      </button>
    </div>
  )

  return null
}

// Inline styles matching your design system
const styles = {
  container: {
    border: "1.5px solid var(--border, #DDE3ED)",
    borderRadius: "10px",
    padding: "20px",
    marginBottom: "20px",
    background: "var(--surface, #fff)",
    transition: "border-color 0.2s"
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "12px"
  },
  reviewHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "14px",
    flexWrap: "wrap",
    gap: "8px"
  },
  reviewActions: { display: "flex", gap: "12px" },
  title: {
    fontFamily: "var(--serif, serif)",
    fontSize: "16px",
    fontWeight: 600,
    color: "var(--text-primary, #0D1B2A)"
  },
  hint: {
    fontSize: "12.5px",
    color: "var(--text-muted, #8A96A8)",
    lineHeight: 1.5,
    marginBottom: "14px"
  },
  exampleBox: {
    background: "var(--ash, #F4F6F9)",
    borderRadius: "8px",
    padding: "12px",
    marginBottom: "16px"
  },
  exampleLabel: {
    fontSize: "11px",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    color: "var(--text-muted, #8A96A8)"
  },
  exampleText: {
    fontSize: "12.5px",
    color: "var(--text-secondary, #4A5568)",
    lineHeight: 1.6,
    marginTop: "6px",
    fontStyle: "italic"
  },
  recordBtn: {
    width: "100%",
    padding: "14px",
    borderRadius: "8px",
    border: "none",
    cursor: "pointer",
    background: "var(--saffron, #FF6B00)",
    color: "white",
    fontSize: "15px",
    fontWeight: 700,
    letterSpacing: "0.3px"
  },
  stopBtn: {
    padding: "8px 18px",
    borderRadius: "6px",
    border: "none",
    cursor: "pointer",
    background: "var(--seal, #A8362B)",
    color: "white",
    fontSize: "13px",
    fontWeight: 600
  },
  linkBtn: {
    background: "none",
    border: "none",
    cursor: "pointer",
    color: "var(--saffron, #FF6B00)",
    fontSize: "12.5px",
    fontWeight: 600,
    textDecoration: "underline"
  },
  recordingHeader: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    marginBottom: "14px"
  },
  recDot: {
    width: "10px", height: "10px",
    borderRadius: "50%",
    background: "#A8362B",
    animation: "pulse 1s infinite"
  },
  recLabel: {
    flex: 1,
    fontFamily: "var(--mono, monospace)",
    fontSize: "13px",
    color: "#A8362B",
    fontWeight: 600
  },
  liveBox: {
    minHeight: "80px",
    padding: "14px",
    background: "var(--ash, #F4F6F9)",
    borderRadius: "8px",
    fontSize: "14px",
    lineHeight: 1.7,
    color: "var(--text-primary, #0D1B2A)",
    marginBottom: "10px"
  },
  processingBox: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
    padding: "20px"
  },
  spinner: {
    width: "36px", height: "36px",
    border: "3px solid var(--border, #DDE3ED)",
    borderTop: "3px solid var(--saffron, #FF6B00)",
    borderRadius: "50%",
    animation: "spin 1s linear infinite",
    flexShrink: 0
  },
  processingTitle: {
    fontSize: "14px",
    fontWeight: 600,
    color: "var(--text-primary, #0D1B2A)",
    margin: 0
  },
  processingSubtitle: {
    fontSize: "12px",
    color: "var(--text-muted, #8A96A8)",
    margin: "4px 0 0"
  },
  fieldGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
    gap: "10px",
    marginBottom: "16px"
  },
  fieldCard: {
    padding: "10px 14px",
    borderRadius: "8px",
    border: "1.5px solid",
    display: "flex",
    flexDirection: "column",
    gap: "4px"
  },
  fieldLabel: {
    fontSize: "10.5px",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    color: "var(--text-muted, #8A96A8)"
  },
  fieldValue: {
    fontSize: "13.5px",
    fontWeight: 600,
    color: "var(--text-primary, #0D1B2A)"
  },
  missingTag: {
    fontSize: "12px",
    color: "#E67E22",
    fontWeight: 500
  },
  warningBox: {
    background: "#FFF9F5",
    border: "1.5px solid #E67E22",
    borderRadius: "8px",
    padding: "14px",
    marginBottom: "14px"
  },
  warningTitle: {
    fontSize: "13px",
    fontWeight: 700,
    color: "#E67E22",
    margin: "0 0 4px"
  },
  warningText: {
    fontSize: "12px",
    color: "var(--text-secondary, #4A5568)",
    margin: "0 0 10px"
  },
  speakAgainBtn: {
    padding: "8px 16px",
    borderRadius: "6px",
    border: "none",
    cursor: "pointer",
    background: "#FF6B00",
    color: "white",
    fontSize: "12.5px",
    fontWeight: 600
  },
  witnessBox: {
    display: "flex",
    flexWrap: "wrap",
    gap: "8px",
    alignItems: "center",
    marginTop: "8px"
  },
  witnessPill: {
    padding: "4px 12px",
    borderRadius: "20px",
    background: "var(--india-blue-light, #E8EEF8)",
    color: "var(--india-blue, #003580)",
    fontSize: "12.5px",
    fontWeight: 500
  },
  transcriptBox: {
    marginBottom: "14px",
    background: "var(--ash, #F4F6F9)",
    borderRadius: "8px",
    padding: "10px 14px"
  },
  transcriptSummary: {
    fontSize: "12px",
    fontWeight: 600,
    color: "var(--text-muted, #8A96A8)",
    cursor: "pointer"
  },
  transcriptText: {
    fontSize: "12.5px",
    lineHeight: 1.7,
    color: "var(--text-secondary, #4A5568)",
    marginTop: "8px"
  },
  manualBar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "10px 16px",
    background: "var(--ash, #F4F6F9)",
    borderRadius: "8px",
    marginBottom: "16px"
  },
  liveTranscriptBox: {
    marginTop: "16px",
    padding: "12px",
    background: "#F7FAFC",
    borderRadius: "8px",
    border: "1px dashed #CBD5E0",
  },
  liveTranscriptLabel: {
    fontSize: "12px",
    fontWeight: "bold",
    color: "#718096",
    display: "block",
    marginBottom: "4px"
  },
  liveTranscriptText: {
    fontSize: "14px",
    color: "#2D3748",
    margin: 0,
    fontStyle: "italic"
  },
  draftBox: {
    marginTop: "16px",
    padding: "16px",
    background: "#F0F4F8",
    borderRadius: "8px",
    borderLeft: "4px solid var(--india-blue, #003580)",
    marginBottom: "20px"
  },
  draftTitle: {
    margin: "0 0 8px 0",
    fontSize: "14px",
    fontWeight: "bold",
    color: "var(--india-blue, #003580)"
  },
  draftText: {
    fontSize: "14px",
    color: "#2D3748",
    lineHeight: "1.5",
    margin: 0,
    whiteSpace: "pre-wrap"
  }
}
