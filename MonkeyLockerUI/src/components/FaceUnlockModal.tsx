import { useRef, useState, useEffect } from "react";
import Webcam from "react-webcam";
import { verifyFace } from "../api/users";

interface Props {
  roomName: string;
  onClose: () => void;
  onUnlocked: () => void;
}

function dataURLtoFile(dataUrl: string, filename: string): File {
  const arr = dataUrl.split(",");
  const mime = arr[0].match(/:(.*?);/)![1];
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) u8arr[n] = bstr.charCodeAt(n);
  return new File([u8arr], filename, { type: mime });
}

const MAX_ATTEMPTS = 6;
const SCAN_INTERVAL_MS = 1500;

type Phase = "scanning" | "checking" | "failed";

export default function FaceUnlockModal({ roomName, onClose, onUnlocked }: Props) {
  const webcamRef = useRef<Webcam>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isProcessing = useRef(false);

  const [phase, setPhase] = useState<Phase>("scanning");
  const [attempts, setAttempts] = useState(0);

  function stopScanning() {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }

  function startScanning() {
    isProcessing.current = false;
    setAttempts(0);
    setPhase("scanning");
    intervalRef.current = setInterval(scan, SCAN_INTERVAL_MS);
  }

  async function scan() {
    if (isProcessing.current) return;
    const screenshot = webcamRef.current?.getScreenshot();
    if (!screenshot) return;

    isProcessing.current = true;
    setPhase("checking");

    try {
      const file = dataURLtoFile(screenshot, "face.jpg");
      const result = await verifyFace(file);

      if (result.verified) {
        stopScanning();
        onUnlocked();
        return;
      }

      setAttempts((prev) => {
        const next = prev + 1;
        if (next >= MAX_ATTEMPTS) {
          stopScanning();
          setPhase("failed");
        } else {
          setPhase("scanning");
        }
        return next;
      });
    } catch {
      setPhase("scanning");
    } finally {
      isProcessing.current = false;
    }
  }

  useEffect(() => {
    startScanning();
    return stopScanning;
  }, []);

  const statusLabel: Record<Phase, string> = {
    scanning: "Looking for your face…",
    checking: "Checking…",
    failed: "Couldn't verify your face",
  };

  const statusColor: Record<Phase, string> = {
    scanning: "#666",
    checking: "#1a73e8",
    failed: "#d93025",
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <div style={styles.header}>
          <div>
            <h2 style={styles.title}>Face Unlock</h2>
            <p style={styles.subtitle}>{roomName}</p>
          </div>
          <button onClick={() => { stopScanning(); onClose(); }} style={styles.closeBtn}>
            ✕
          </button>
        </div>

        <div style={styles.webcamWrapper}>
          <Webcam
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            style={styles.webcam}
            videoConstraints={{ facingMode: "user", width: 640, height: 480 }}
            mirrored
          />
          {/* Scanning ring overlay */}
          <div
            style={{
              ...styles.scanRing,
              borderColor:
                phase === "checking"
                  ? "#1a73e8"
                  : phase === "failed"
                  ? "#d93025"
                  : "rgba(255,255,255,0.6)",
              animation: phase === "scanning" ? "pulse 1.5s ease-in-out infinite" : "none",
            }}
          />
        </div>

        <div style={{ ...styles.status, color: statusColor[phase] }}>
          {phase === "scanning" && <span style={styles.dot} />}
          {statusLabel[phase]}
          {phase === "checking" && " ···"}
        </div>

        {phase === "failed" && (
          <button onClick={startScanning} style={styles.retryBtn}>
            Try Again
          </button>
        )}

        {attempts > 0 && phase !== "failed" && (
          <p style={styles.attemptsHint}>
            {MAX_ATTEMPTS - attempts} attempt{MAX_ATTEMPTS - attempts !== 1 ? "s" : ""} remaining
          </p>
        )}
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.6; transform: translate(-50%, -50%) scale(1); }
          50% { opacity: 1; transform: translate(-50%, -50%) scale(1.04); }
        }
      `}</style>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.65)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
  },
  modal: {
    background: "#fff",
    borderRadius: "12px",
    padding: "28px",
    width: "100%",
    maxWidth: "420px",
    display: "flex",
    flexDirection: "column",
    gap: "14px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  title: {
    margin: "0 0 2px",
    fontSize: "18px",
    fontWeight: 600,
  },
  subtitle: {
    margin: 0,
    fontSize: "13px",
    color: "#666",
  },
  closeBtn: {
    background: "none",
    border: "none",
    fontSize: "18px",
    cursor: "pointer",
    color: "#666",
    padding: "4px",
  },
  webcamWrapper: {
    position: "relative",
    width: "100%",
    borderRadius: "10px",
    overflow: "hidden",
    background: "#000",
  },
  webcam: {
    width: "100%",
    display: "block",
    borderRadius: "10px",
  },
  scanRing: {
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    width: "170px",
    height: "210px",
    border: "2.5px solid",
    borderRadius: "50%",
    pointerEvents: "none",
    transition: "border-color 0.3s",
  },
  status: {
    fontSize: "14px",
    fontWeight: 500,
    display: "flex",
    alignItems: "center",
    gap: "8px",
    minHeight: "20px",
  },
  dot: {
    display: "inline-block",
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    background: "currentColor",
    flexShrink: 0,
  },
  attemptsHint: {
    margin: 0,
    fontSize: "12px",
    color: "#9aa0a6",
  },
  retryBtn: {
    padding: "10px",
    background: "#1a1a1a",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    fontSize: "14px",
    fontWeight: 500,
    cursor: "pointer",
  },
};
