import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import Masonry from "react-masonry-css";
import { getRoom } from "../api/rooms";
import type { RoomDetail } from "../api/rooms";
import { listImages, deleteImage, resolveImageUrl } from "../api/images";
import type { RoomImage } from "../api/images";
import { useAuth } from "../context/AuthContext";
import ImageUploadModal from "../components/ImageUploadModal";

// ── Helpers ───────────────────────────────────────────────────────────────────

function toMonthKey(iso: string) { return iso.slice(0, 7); }

function monthLabel(key: string) {
  const [y, m] = key.split("-");
  return new Date(Number(y), Number(m) - 1).toLocaleString("default", {
    month: "long", year: "numeric",
  });
}

function groupByMonth(images: RoomImage[]) {
  const groups: { key: string; label: string; items: RoomImage[] }[] = [];
  const idx = new Map<string, number>();
  for (const img of images) {
    const key = toMonthKey(img.uploaded_at);
    if (!idx.has(key)) { idx.set(key, groups.length); groups.push({ key, label: monthLabel(key), items: [] }); }
    groups[idx.get(key)!].items.push(img);
  }
  return groups;
}

const BREAKPOINTS = { default: 4, 1280: 3, 900: 2, 560: 1 };
const PER_PAGE_OPTIONS = [12, 24, 48, 96, 0];

// ── Component ─────────────────────────────────────────────────────────────────

export default function RoomPage() {
  const { roomId } = useParams<{ roomId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [room, setRoom] = useState<RoomDetail | null>(null);
  const [images, setImages] = useState<RoomImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedImage, setSelectedImage] = useState<RoomImage | null>(null);

  const [selectedMonth, setSelectedMonth] = useState("");
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");
  const [perPage, setPerPage] = useState(24);
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (!roomId) return;
    Promise.all([getRoom(Number(roomId)), listImages(Number(roomId))])
      .then(([r, imgs]) => { setRoom(r); setImages(imgs); })
      .catch(() => navigate("/dashboard", { replace: true }))
      .finally(() => setLoading(false));
  }, [roomId]);

  useEffect(() => { setPage(1); }, [selectedMonth, sortOrder, perPage]);

  const availableMonths = useMemo(() =>
    [...new Set(images.map((img) => toMonthKey(img.uploaded_at)))].sort((a, b) => b.localeCompare(a)),
    [images]
  );

  const filtered = useMemo(() => {
    let r = selectedMonth ? images.filter((img) => toMonthKey(img.uploaded_at) === selectedMonth) : [...images];
    r.sort((a, b) => { const d = a.uploaded_at.localeCompare(b.uploaded_at); return sortOrder === "desc" ? -d : d; });
    return r;
  }, [images, selectedMonth, sortOrder]);

  const totalPages = perPage === 0 ? 1 : Math.max(1, Math.ceil(filtered.length / perPage));

  const paginated = useMemo(() => {
    if (perPage === 0) return filtered;
    return filtered.slice((page - 1) * perPage, page * perPage);
  }, [filtered, page, perPage]);

  const groups = useMemo(() => groupByMonth(paginated), [paginated]);

  function handleUploaded(imgs: RoomImage[]) {
    setImages((prev) => [...imgs, ...prev]);
    setShowUpload(false);
  }

  async function handleDelete(imageId: number) {
    await deleteImage(imageId).catch(() => {});
    setImages((prev) => prev.filter((img) => img.id !== imageId));
    setSelectedImage(null);
  }

  if (loading) return <div style={s.loading}><p>Loading…</p></div>;
  if (!room) return null;

  return (
    <div style={s.page}>
      {/* Header */}
      <header style={s.header}>
        <button onClick={() => navigate("/dashboard")} style={s.backBtn}>← Back</button>
        <div style={s.headerCenter}>
          <h1 style={s.roomName}>{room.name}</h1>
          {room.is_private && <span style={s.privateBadge}>Private</span>}
        </div>
        <button onClick={() => setShowUpload(true)} style={s.uploadBtn}>+ Add Photos</button>
      </header>

      {/* Body: sidebar + content */}
      <div style={s.body}>

        {/* ── Sidebar ── */}
        <aside style={s.sidebar}>
          {room.description && <p style={s.sideDesc}>{room.description}</p>}

          <p style={s.sideLabel}>Month</p>
          <select value={selectedMonth} onChange={(e) => setSelectedMonth(e.target.value)} style={s.sideSelect}>
            <option value="">All time</option>
            {availableMonths.map((k) => <option key={k} value={k}>{monthLabel(k)}</option>)}
          </select>

          <p style={s.sideLabel}>Sort</p>
          <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value as "desc" | "asc")} style={s.sideSelect}>
            <option value="desc">Newest first</option>
            <option value="asc">Oldest first</option>
          </select>

          <p style={s.sideLabel}>Show</p>
          <select value={perPage} onChange={(e) => setPerPage(Number(e.target.value))} style={s.sideSelect}>
            {PER_PAGE_OPTIONS.map((n) => (
              <option key={n} value={n}>{n === 0 ? "All" : `${n} photos`}</option>
            ))}
          </select>

          <div style={s.sideStat}>
            <span style={s.sideStatNum}>{filtered.length}</span>
            <span style={s.sideStatLabel}>photo{filtered.length !== 1 ? "s" : ""}</span>
          </div>
        </aside>

        {/* ── Main content ── */}
        <main style={s.content}>
          {images.length === 0 ? (
            <div style={s.emptyState}>
              <p style={s.emptyTitle}>No photos yet</p>
              <p style={s.emptyText}>Be the first to add a memory.</p>
              <button onClick={() => setShowUpload(true)} style={s.emptyBtn}>Add a photo</button>
            </div>
          ) : filtered.length === 0 ? (
            <div style={s.emptyState}>
              <p style={s.emptyTitle}>No photos in {monthLabel(selectedMonth)}</p>
              <button onClick={() => setSelectedMonth("")} style={s.emptyBtn}>Show all</button>
            </div>
          ) : (
            <>
              {groups.map((group) => (
                <div key={group.key} style={s.group}>
                  <h2 style={s.groupLabel}>{group.label}</h2>
                  <Masonry
                    breakpointCols={BREAKPOINTS}
                    className="masonry-grid"
                    columnClassName="masonry-col"
                  >
                    {group.items.map((img, i) => (
                      <motion.div
                        key={img.id}
                        style={s.imgCard}
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.4, delay: (i % 8) * 0.04 }}
                        whileHover={{ scale: 1.02 }}
                        onClick={() => setSelectedImage(img)}
                      >
                        <img
                          src={resolveImageUrl(img.image_url)}
                          alt={img.caption ?? ""}
                          style={s.imgEl}
                          onError={(e) => {
                            (e.currentTarget as HTMLImageElement).style.display = "none";
                            const ph = e.currentTarget.nextSibling as HTMLElement | null;
                            if (ph) ph.style.display = "flex";
                          }}
                        />
                        <div style={{ ...s.imgBroken, display: "none" }}>Failed to load</div>
                        {img.caption && <p style={s.imgCaption}>{img.caption}</p>}
                      </motion.div>
                    ))}
                  </Masonry>
                </div>
              ))}

              {/* Pagination */}
              {totalPages > 1 && (
                <div style={s.pagination}>
                  <button style={s.pageBtn} disabled={page === 1} onClick={() => setPage((p) => p - 1)}>← Prev</button>
                  <span style={s.pageInfo}>Page {page} of {totalPages}</span>
                  <button style={s.pageBtn} disabled={page === totalPages} onClick={() => setPage((p) => p + 1)}>Next →</button>
                </div>
              )}
            </>
          )}
        </main>
      </div>

      {/* Lightbox */}
      {selectedImage && (
        <motion.div
          style={s.lightboxOverlay}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={() => setSelectedImage(null)}
        >
          <motion.div
            style={s.lightbox}
            initial={{ scale: 0.94, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.22 }}
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={resolveImageUrl(selectedImage.image_url)}
              alt={selectedImage.caption ?? ""}
              style={s.lightboxImg}
            />
            <div style={s.lightboxMeta}>
              {selectedImage.caption && <p style={s.lightboxCaption}>{selectedImage.caption}</p>}
              <p style={s.lightboxDate}>
                {new Date(selectedImage.uploaded_at).toLocaleString("default", {
                  month: "long", day: "numeric", year: "numeric",
                  hour: "2-digit", minute: "2-digit",
                })}
              </p>
              <div style={s.lightboxActions}>
                {selectedImage.uploaded_by === user?.id && (
                  <button onClick={() => handleDelete(selectedImage.id)} style={s.deleteBtn}>Delete</button>
                )}
                <button onClick={() => setSelectedImage(null)} style={s.closeBtn}>Close</button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}

      {showUpload && (
        <ImageUploadModal roomId={room.id} onClose={() => setShowUpload(false)} onUploaded={handleUploaded} />
      )}
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const s: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "var(--bg)" },
  loading: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-2)" },

  header: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    padding: "0 40px", height: "64px", background: "var(--card)",
    borderBottom: "1px solid var(--border)", position: "sticky", top: 0, zIndex: 100, gap: "16px",
  },
  backBtn: {
    background: "none", border: "none", fontSize: "14px", cursor: "pointer",
    color: "var(--text-2)", padding: "6px 0", whiteSpace: "nowrap", fontWeight: 500,
  },
  headerCenter: { display: "flex", alignItems: "center", gap: "10px", flex: 1, justifyContent: "center" },
  roomName: { fontSize: "17px", fontWeight: 700, color: "var(--text)" },
  privateBadge: {
    fontSize: "11px", padding: "3px 10px", background: "#F5EEE8",
    borderRadius: "20px", color: "var(--accent)", fontWeight: 600,
  },
  uploadBtn: {
    padding: "9px 20px", background: "var(--accent)", color: "#fff", border: "none",
    borderRadius: "8px", fontSize: "13px", fontWeight: 600, whiteSpace: "nowrap",
  },

  // Layout
  body: { display: "flex", alignItems: "flex-start", maxWidth: "1600px", margin: "0 auto", padding: "0 32px 60px" },

  // Sidebar
  sidebar: {
    width: "220px", flexShrink: 0, position: "sticky", top: "64px",
    height: "calc(100vh - 64px)", overflowY: "auto",
    padding: "28px 20px 28px 0", borderRight: "1px solid var(--border)",
    display: "flex", flexDirection: "column", gap: "4px",
  },
  sideDesc: { fontSize: "13px", color: "var(--text-2)", lineHeight: 1.5, marginBottom: "16px" },
  sideLabel: {
    margin: "16px 0 6px", fontSize: "10px", fontWeight: 700, color: "var(--text-2)",
    textTransform: "uppercase", letterSpacing: "0.8px",
  },
  sideSelect: {
    width: "100%", padding: "8px 10px", border: "1px solid var(--border)",
    borderRadius: "8px", fontSize: "13px", color: "var(--text)",
    background: "var(--card)", cursor: "pointer", appearance: "auto",
  },
  sideStat: {
    marginTop: "24px", padding: "16px", background: "#F5EEE8",
    borderRadius: "10px", textAlign: "center",
  },
  sideStatNum: { display: "block", fontSize: "28px", fontWeight: 700, color: "var(--accent)" },
  sideStatLabel: { fontSize: "12px", color: "var(--text-2)", fontWeight: 500 },

  // Content
  content: { flex: 1, minWidth: 0, padding: "28px 0 0 32px" },

  group: { marginBottom: "40px" },
  groupLabel: {
    fontSize: "13px", fontWeight: 700, color: "var(--text-2)", textTransform: "uppercase",
    letterSpacing: "0.6px", marginBottom: "14px", paddingBottom: "10px",
    borderBottom: "1px solid var(--border)",
  },

  // Image cards
  imgCard: {
    background: "var(--card)", borderRadius: "10px", overflow: "hidden",
    border: "1px solid var(--border)", cursor: "pointer",
  },
  imgEl: { width: "100%", display: "block" },
  imgBroken: {
    width: "100%", height: "120px", background: "#F5EEE8",
    alignItems: "center", justifyContent: "center", fontSize: "12px", color: "var(--text-2)",
  },
  imgCaption: {
    margin: 0, padding: "8px 12px", fontSize: "12px", color: "var(--text-2)",
    overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis",
    borderTop: "1px solid var(--border)",
  },

  // Pagination
  pagination: {
    display: "flex", alignItems: "center", justifyContent: "center",
    gap: "16px", marginTop: "40px",
  },
  pageBtn: {
    padding: "9px 20px", background: "var(--card)", border: "1px solid var(--border)",
    borderRadius: "8px", fontSize: "13px", cursor: "pointer", color: "var(--text)", fontWeight: 500,
  },
  pageInfo: { fontSize: "13px", color: "var(--text-2)" },

  // Empty
  emptyState: {
    background: "var(--card)", border: "1px solid var(--border)", borderRadius: "12px",
    padding: "64px 24px", textAlign: "center", display: "flex",
    flexDirection: "column", alignItems: "center", gap: "10px",
  },
  emptyTitle: { fontSize: "16px", fontWeight: 600, color: "var(--text)" },
  emptyText: { margin: 0, fontSize: "14px", color: "var(--text-2)" },
  emptyBtn: {
    marginTop: "8px", padding: "10px 28px", background: "var(--accent)", color: "#fff",
    border: "none", borderRadius: "8px", fontSize: "14px", fontWeight: 600,
  },

  // Lightbox
  lightboxOverlay: {
    position: "fixed", inset: 0, background: "rgba(47,42,37,0.85)",
    display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
  },
  lightbox: {
    background: "var(--card)", borderRadius: "14px", overflow: "hidden",
    maxWidth: "720px", width: "92%", display: "flex", flexDirection: "column",
    maxHeight: "90vh",
  },
  lightboxImg: { width: "100%", maxHeight: "540px", objectFit: "contain", background: "#000" },
  lightboxMeta: { padding: "16px 20px" },
  lightboxCaption: { margin: "0 0 4px", fontSize: "15px", color: "var(--text)", fontWeight: 500 },
  lightboxDate: { margin: "0 0 14px", fontSize: "12px", color: "var(--text-2)" },
  lightboxActions: { display: "flex", justifyContent: "flex-end", gap: "8px" },
  deleteBtn: {
    padding: "8px 18px", background: "transparent", color: "#C0392B",
    border: "1px solid #C0392B", borderRadius: "8px", fontSize: "13px", cursor: "pointer",
  },
  closeBtn: {
    padding: "8px 18px", background: "var(--text)", color: "#fff",
    border: "none", borderRadius: "8px", fontSize: "13px", cursor: "pointer",
  },
};
