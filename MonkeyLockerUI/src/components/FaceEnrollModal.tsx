import { useRef, useState } from "react";
import Webcam from "react-webcam";
import { enrollFace } from "../api/users";

interface Props {
  onClose: () => void;
  onSuccess: () => void;
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

export default function FaceEnrollModal({ onClose, onSuccess }: Props) {
  const webcamRef = useRef<Webcam>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleEnroll() {
    const screenshot = webcamRef.current?.getScreenshot();
    if (!screenshot) {
      setError("Could not read camera. Please allow camera access and try again.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const file = dataURLtoFile(screenshot, "face.jpg");
      await enrollFace(file);
      onSuccess();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Enrollment failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <div style={styles.header}>
          <h2 style={styles.title}>Enroll Your Face</h2>
          <button onClick={onClose} style={styles.closeBtn}>✕</button>
        </div>

        <p style={styles.hint}>
          Look directly at the camera, then click Enroll Face.
        </p>

        <div style={styles.webcamWrapper}>
          <Webcam
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            style={styles.webcam}
            videoConstraints={{ facingMode: "user", width: 640, height: 480 }}
            mirrored
          />
          <div style={styles.faceGuide} />
        </div>

        <button
          onClick={handleEnroll}
          style={{ ...styles.primaryBtn, opacity: loading ? 0.7 : 1 }}
          disabled={loading}
        >
          {loading ? "Enrolling…" : "Enroll Face"}
        </button>

        {error && <p style={styles.error}>{error}</p>}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.6)",
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
    gap: "16px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  title: {
    margin: 0,
    fontSize: "18px",
    fontWeight: 600,
  },
  closeBtn: {
    background: "none",
    border: "none",
    fontSize: "18px",
    cursor: "pointer",
    color: "#666",
    padding: "4px",
  },
  hint: {
    margin: 0,
    fontSize: "14px",
    color: "#666",
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
  faceGuide: {
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    width: "160px",
    height: "200px",
    border: "2px dashed rgba(255,255,255,0.5)",
    borderRadius: "50%",
    pointerEvents: "none",
  },
  primaryBtn: {
    padding: "12px",
    background: "#1a1a1a",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    fontSize: "15px",
    fontWeight: 500,
    cursor: "pointer",
  },
  error: {
    margin: 0,
    color: "#d93025",
    fontSize: "13px",
  },
};
