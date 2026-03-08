import { useRef, useState } from "react";
import { uploadImage } from "../api/images";
import type { RoomImage } from "../api/images";

interface Props {
  roomId: number;
  onClose: () => void;
  onUploaded: (images: RoomImage[]) => void;
}

function isImage(f: File) {
  return f.type.startsWith("image/");
}

function dedup(existing: File[], incoming: File[]): File[] {
  const keys = new Set(existing.map((f) => `${f.name}:${f.size}`));
  return [...existing, ...incoming.filter((f) => !keys.has(`${f.name}:${f.size}`))];
}

export default function ImageUploadModal({ roomId, onClose, onUploaded }: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(null);
  const [failedNames, setFailedNames] = useState<string[]>([]);

  const isUploading = progress !== null && progress.done < progress.total;

  function addFiles(list: FileList | File[]) {
    const images = Array.from(list).filter(isImage);
    setFiles((prev) => dedup(prev, images));
  }

  function removeFile(index: number) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    setDragging(true);
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!files.length) return;

    setFailedNames([]);
    setProgress({ done: 0, total: files.length });

    const successes: RoomImage[] = [];
    const failures: string[] = [];

    for (let i = 0; i < files.length; i++) {
      try {
        const img = await uploadImage(roomId, files[i]);
        successes.push(img);
      } catch {
        failures.push(files[i].name);
      }
      setProgress({ done: i + 1, total: files.length });
    }

    if (successes.length) onUploaded(successes);

    if (failures.length) {
      setFailedNames(failures);
      setProgress(null);
    } else {
      onClose();
    }
  }

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <div style={styles.header}>
          <h2 style={styles.title}>Add Photos</h2>
          <button onClick={onClose} style={styles.closeBtn} disabled={isUploading}>
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} style={styles.form}>
          {/* Drop zone */}
          <div
            style={{
              ...styles.dropzone,
              borderColor: dragging ? "#1a1a1a" : "#dadce0",
              background: dragging ? "#f1f3f4" : "#fafafa",
            }}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <p style={styles.dropzoneIcon}>🖼️</p>
            <p style={styles.dropzoneText}>Drag & drop photos here</p>
            <p style={styles.dropzoneHint}>JPG, PNG, WEBP, GIF supported</p>
            <div style={styles.dropzoneBtns}>
              <button
                type="button"
                style={styles.browseBtn}
                onClick={() => fileInputRef.current?.click()}
              >
                Select Files
              </button>
              <button
                type="button"
                style={styles.browseBtn}
                onClick={() => folderInputRef.current?.click()}
              >
                Select Folder
              </button>
            </div>

            {/* hidden inputs */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              style={{ display: "none" }}
              onChange={(e) => e.target.files && addFiles(e.target.files)}
            />
            <input
              ref={folderInputRef}
              type="file"
              accept="image/*"
              // @ts-expect-error non-standard but widely supported
              webkitdirectory=""
              multiple
              style={{ display: "none" }}
              onChange={(e) => e.target.files && addFiles(e.target.files)}
            />
          </div>

          {/* File queue */}
          {files.length > 0 && (
            <div style={styles.queueHeader}>
              <span style={styles.queueCount}>{files.length} photo{files.length !== 1 ? "s" : ""} queued</span>
              <button
                type="button"
                style={styles.clearBtn}
                onClick={() => setFiles([])}
                disabled={isUploading}
              >
                Clear all
              </button>
            </div>
          )}

          {files.length > 0 && (
            <div style={styles.fileList}>
              {files.map((f, i) => (
                <div key={`${f.name}:${f.size}`} style={styles.fileRow}>
                  <img
                    src={URL.createObjectURL(f)}
                    alt={f.name}
                    style={styles.fileThumb}
                  />
                  <span style={styles.fileName}>{f.name}</span>
                  <button
                    type="button"
                    onClick={() => removeFile(i)}
                    style={styles.removeBtn}
                    disabled={isUploading}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Errors */}
          {failedNames.length > 0 && (
            <p style={styles.error}>
              Failed to upload: {failedNames.join(", ")}
            </p>
          )}

          <div style={styles.row}>
            <button
              type="button"
              onClick={onClose}
              style={styles.secondaryBtn}
              disabled={isUploading}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{ ...styles.primaryBtn, opacity: isUploading || !files.length ? 0.6 : 1 }}
              disabled={isUploading || !files.length}
            >
              {isUploading
                ? `Uploading ${progress!.done} / ${progress!.total}…`
                : `Upload ${files.length > 0 ? `${files.length} photo${files.length !== 1 ? "s" : ""}` : ""}`}
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
    borderRadius: "12px",
    padding: "28px",
    width: "100%",
    maxWidth: "480px",
    maxHeight: "90vh",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
    overflowY: "auto",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexShrink: 0,
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
    gap: "12px",
  },
  dropzone: {
    border: "2px dashed",
    borderRadius: "10px",
    padding: "32px 20px",
    textAlign: "center",
    cursor: "pointer",
    transition: "border-color 0.2s, background 0.2s",
  },
  dropzoneIcon: {
    fontSize: "32px",
    margin: "0 0 8px",
  },
  dropzoneText: {
    margin: "0 0 4px",
    fontSize: "14px",
    fontWeight: 500,
    color: "#1a1a1a",
  },
  dropzoneHint: {
    margin: "0 0 16px",
    fontSize: "12px",
    color: "#9aa0a6",
  },
  dropzoneBtns: {
    display: "flex",
    gap: "8px",
    justifyContent: "center",
  },
  browseBtn: {
    padding: "7px 16px",
    background: "#fff",
    border: "1px solid #dadce0",
    borderRadius: "6px",
    fontSize: "13px",
    fontWeight: 500,
    cursor: "pointer",
    color: "#1a1a1a",
  },
  queueHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  queueCount: {
    fontSize: "13px",
    fontWeight: 500,
    color: "#3c4043",
  },
  clearBtn: {
    background: "none",
    border: "none",
    fontSize: "12px",
    color: "#1a73e8",
    cursor: "pointer",
    padding: 0,
  },
  fileList: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
    maxHeight: "200px",
    overflowY: "auto",
    border: "1px solid #e8eaed",
    borderRadius: "8px",
    padding: "8px",
  },
  fileRow: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  fileThumb: {
    width: "36px",
    height: "36px",
    objectFit: "cover",
    borderRadius: "4px",
    flexShrink: 0,
  },
  fileName: {
    flex: 1,
    fontSize: "13px",
    color: "#3c4043",
    overflow: "hidden",
    whiteSpace: "nowrap",
    textOverflow: "ellipsis",
  },
  removeBtn: {
    background: "none",
    border: "none",
    fontSize: "13px",
    color: "#9aa0a6",
    cursor: "pointer",
    padding: "2px 4px",
    flexShrink: 0,
  },
  error: {
    margin: 0,
    color: "#d93025",
    fontSize: "13px",
  },
  row: {
    display: "flex",
    gap: "12px",
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
    transition: "opacity 0.2s",
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
};
