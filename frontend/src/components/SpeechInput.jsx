import { useState, useRef, useEffect } from "react"

export default function SpeechInput({ onTranscript, onFinalTranscript }) {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [liveText, setLiveText] = useState("")
  const [error, setError] = useState("")
  const [supported, setSupported] = useState(true)

  const recognitionRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const streamRef = useRef(null)

  useEffect(() => {
    // Check browser support
    if (!("webkitSpeechRecognition" in window) &&
        !("SpeechRecognition" in window)) {
      setSupported(false)
    }
    return () => stopAll()
  }, [])

  const startRecording = async () => {
    setError("")
    setLiveText("")
    audioChunksRef.current = []

    try {
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        }
      })
      streamRef.current = stream

      // LAYER 1: Web Speech API for live display
      if (supported) {
        const SpeechRecognition =
          window.SpeechRecognition ||
          window.webkitSpeechRecognition

        const recognition = new SpeechRecognition()
        recognition.continuous = true
        recognition.interimResults = true
        recognition.lang = "en-IN" // Indian English

        recognition.onresult = (event) => {
          let interim = ""
          let final = ""
          for (let i = event.resultIndex;
               i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript
            if (event.results[i].isFinal) {
              final += transcript + " "
            } else {
              interim += transcript
            }
          }
          const display = final + interim
          setLiveText(display)
          if (onTranscript) onTranscript(display)
        }

        recognition.onerror = (e) => {
          console.warn("Web Speech error:", e.error)
          // Don't stop — Whisper will still work
        }

        recognition.start()
        recognitionRef.current = recognition
      }

      // LAYER 2: MediaRecorder for Whisper audio
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm"
          : "audio/ogg"
      })

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.start(1000) // collect every 1 second
      mediaRecorderRef.current = mediaRecorder
      setIsRecording(true)

    } catch (err) {
      setError(
        err.name === "NotAllowedError"
          ? "Microphone access denied. Please allow microphone in browser settings."
          : "Could not access microphone: " + err.message
      )
    }
  }

  const stopRecording = async () => {
    setIsRecording(false)
    setIsProcessing(true)

    // Stop Web Speech API
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      recognitionRef.current = null
    }

    // Stop MediaRecorder and get audio
    return new Promise((resolve) => {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.onstop = async () => {
          try {
            // Convert audio chunks to base64
            const audioBlob = new Blob(
              audioChunksRef.current,
              { type: "audio/webm" }
            )

            const reader = new FileReader()
            reader.onloadend = async () => {
              const base64 = reader.result.split(",")[1]

              // Send to Groq Whisper via our backend
              const response = await fetch("/api/transcribe", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                  audio: base64,
                  format: "webm"
                })
              })

              const result = await response.json()

              if (result.success && result.text) {
                setLiveText(result.text)
                if (onFinalTranscript) {
                  onFinalTranscript(result.text)
                }
              } else {
                setError(
                  "Transcription failed. Please type your complaint."
                )
              }

              setIsProcessing(false)
              resolve()
            }
            reader.readAsDataURL(audioBlob)

          } catch (err) {
            setError("Could not process audio: " + err.message)
            setIsProcessing(false)
            resolve()
          } finally {
            // Stop microphone
            if (streamRef.current) {
              streamRef.current.getTracks()
                .forEach(t => t.stop())
            }
          }
        }
        mediaRecorderRef.current.stop()
      } else {
        setIsProcessing(false)
        resolve()
      }
    })
  }

  const stopAll = () => {
    if (recognitionRef.current) recognitionRef.current.stop()
    if (mediaRecorderRef.current &&
        mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop()
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
    }
  }

  const handleToggle = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  const handleClear = () => {
    setLiveText("")
    setError("")
    if (onFinalTranscript) onFinalTranscript("")
  }

  // Render
  return (
    <div style={{
      border: "1.5px solid var(--border)",
      borderRadius: "10px",
      padding: "16px",
      background: isRecording
        ? "rgba(168,54,43,0.04)"
        : "var(--surface)"
    }}>

      {/* Header */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "12px"
      }}>
        <span style={{
          fontFamily: "var(--sans)",
          fontSize: "13px",
          fontWeight: 600,
          color: "var(--text-primary)"
        }}>
          🎤 Voice Input
        </span>
        {liveText && (
          <button onClick={handleClear} style={{
            fontSize: "11px",
            color: "var(--text-muted)",
            background: "none",
            border: "none",
            cursor: "pointer"
          }}>
            Clear
          </button>
        )}
      </div>

      {/* Record Button */}
      <button
        onClick={handleToggle}
        disabled={isProcessing}
        style={{
          width: "100%",
          padding: "12px",
          borderRadius: "8px",
          border: "none",
          cursor: isProcessing ? "not-allowed" : "pointer",
          background: isRecording
            ? "var(--seal, #A8362B)"
            : "var(--saffron, #FF6B00)",
          color: "white",
          fontFamily: "var(--sans)",
          fontSize: "14px",
          fontWeight: 600,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "8px",
          transition: "all 0.2s"
        }}
      >
        {isProcessing ? (
          <> ⏳ Processing with Whisper...</>
        ) : isRecording ? (
          <> ⏹ Stop Recording</>
        ) : (
          <> 🎤 Start Speaking</>
        )}
      </button>

      {/* Recording indicator */}
      {isRecording && (
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          marginTop: "10px",
          fontSize: "12px",
          color: "var(--seal, #A8362B)"
        }}>
          <span style={{
            width: "8px", height: "8px",
            borderRadius: "50%",
            background: "var(--seal, #A8362B)",
            animation: "pulse 1s infinite"
          }}/>
          Recording... speak your complaint clearly
        </div>
      )}

      {/* Live transcript display */}
      {liveText && (
        <div style={{
          marginTop: "12px",
          padding: "12px",
          background: "var(--ash, #F4F6F9)",
          borderRadius: "6px",
          fontSize: "13px",
          lineHeight: "1.6",
          color: "var(--text-secondary)",
          fontFamily: "var(--sans)",
          minHeight: "60px"
        }}>
          {liveText}
        </div>
      )}

      {/* Error */}
      {error && (
        <div style={{
          marginTop: "10px",
          padding: "10px",
          background: "#FBF3F2",
          border: "1px solid #D9B7BB",
          borderRadius: "6px",
          fontSize: "12px",
          color: "var(--seal, #A8362B)"
        }}>
          {error}
        </div>
      )}

      {/* Instructions */}
      {!isRecording && !liveText && !error && (
        <p style={{
          marginTop: "10px",
          fontSize: "11.5px",
          color: "var(--text-muted)",
          lineHeight: "1.5"
        }}>
          Click the button and speak your complaint.
          Whisper AI will transcribe it accurately.
          Review and edit before submitting.
        </p>
      )}
    </div>
  )
}
