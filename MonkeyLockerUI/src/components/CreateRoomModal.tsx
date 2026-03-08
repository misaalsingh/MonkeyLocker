import { useState } from "react";
import { createRoom } from "../api/rooms";
import type { Room } from "../api/rooms";

interface Props {
  onClose: () => void;
  onCreated: (room: Room) => void;
}

export default function CreateRoomModal({ onClose, onCreated }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isPrivate, setIsPrivate] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const room = await createRoom({
        name: name.trim(),
        description: description.trim() || undefined,
        is_private: isPrivate,
      });
      onCreated(room);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create room");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <div style={styles.header}>
          <h2 style={styles.title}>Create a Room</h2>
          <button onClick={onClose} style={styles.closeBtn}>✕</button>
        </div>

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.field}>
            <label style={styles.label}>Name *</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Spring Break Madrid 2026"
              style={styles.input}
              required
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What's this room for?"
              style={styles.textarea}
              rows={3}
            />
          </div>

          <label style={styles.toggleRow}>
            <div style={styles.toggleInfo}>
              <span style={styles.toggleLabel}>Private room</span>
              <span style={styles.toggleHint}>Only invited members can join</span>
            </div>
            <div
              onClick={() => setIsPrivate((p) => !p)}
              style={{
                ...styles.toggle,
                background: isPrivate ? "#1a1a1a" : "#dadce0",
              }}
            >
              <div
                style={{
                  ...styles.toggleThumb,
                  transform: isPrivate ? "translateX(20px)" : "translateX(2px)",
                }}
              />
            </div>
          </label>

          {error && <p style={styles.error}>{error}</p>}

          <div style={styles.row}>
            <button type="button" onClick={onClose} style={styles.secondaryBtn}>
              Cancel
            </button>
            <button type="submit" style={styles.primaryBtn} disabled={loading || !name.trim()}>
              {loading ? "Creating…" : "Create Room"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.5)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
  },
  modal: {
    background: "#fff",
    borderRadius: "10px",
    padding: "28px",
    width: "100%",
    maxWidth: "440px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "20px",
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
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  field: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  label: {
    fontSize: "13px",
    fontWeight: 500,
    color: "#3c4043",
  },
  input: {
    padding: "10px 12px",
    border: "1px solid #dadce0",
    borderRadius: "6px",
    fontSize: "14px",
    outline: "none",
  },
  textarea: {
    padding: "10px 12px",
    border: "1px solid #dadce0",
    borderRadius: "6px",
    fontSize: "14px",
    resize: "vertical",
    outline: "none",
    fontFamily: "inherit",
  },
  toggleRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    cursor: "pointer",
    padding: "4px 0",
  },
  toggleInfo: {
    display: "flex",
    flexDirection: "column",
    gap: "2px",
  },
  toggleLabel: {
    fontSize: "14px",
    fontWeight: 500,
    color: "#1a1a1a",
  },
  toggleHint: {
    fontSize: "12px",
    color: "#666",
  },
  toggle: {
    position: "relative",
    width: "44px",
    height: "24px",
    borderRadius: "12px",
    transition: "background 0.2s",
    cursor: "pointer",
    flexShrink: 0,
  },
  toggleThumb: {
    position: "absolute",
    top: "2px",
    width: "20px",
    height: "20px",
    borderRadius: "50%",
    background: "#fff",
    transition: "transform 0.2s",
    boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
  },
  row: {
    display: "flex",
    gap: "12px",
    marginTop: "4px",
  },
  primaryBtn: {
    flex: 1,
    padding: "10px",
    background: "#1a1a1a",
    color: "#fff",
    border: "none",
    borderRadius: "6px",
    fontSize: "14px",
    fontWeight: 500,
    cursor: "pointer",
  },
  secondaryBtn: {
    flex: 1,
    padding: "10px",
    background: "transparent",
    color: "#1a1a1a",
    border: "1px solid #dadce0",
    borderRadius: "6px",
    fontSize: "14px",
    cursor: "pointer",
  },
  error: {
    margin: 0,
    color: "#d93025",
    fontSize: "13px",
  },
};
