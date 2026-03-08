import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "../context/AuthContext";
import { getMyStatus } from "../api/users";
import type { UserStatus } from "../api/users";
import { listRooms } from "../api/rooms";
import type { Room } from "../api/rooms";
import FaceEnrollModal from "../components/FaceEnrollModal";
import FaceUnlockModal from "../components/FaceUnlockModal";
import CreateRoomModal from "../components/CreateRoomModal";

// Deterministic gradient from room id
const GRADIENTS = [
  "linear-gradient(135deg, #D97757 0%, #E8A882 100%)",
  "linear-gradient(135deg, #7B9E87 0%, #A8C4AF 100%)",
  "linear-gradient(135deg, #8B7BB5 0%, #B5A8D8 100%)",
  "linear-gradient(135deg, #C4914F 0%, #DDB882 100%)",
  "linear-gradient(135deg, #5B8FA8 0%, #8FBDD3 100%)",
  "linear-gradient(135deg, #A85B5B 0%, #D38B8B 100%)",
];

function roomGradient(id: number) {
  return GRADIENTS[id % GRADIENTS.length];
}

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [status, setStatus] = useState<UserStatus | null>(null);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loadingRooms, setLoadingRooms] = useState(true);
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [showCreateRoom, setShowCreateRoom] = useState(false);
  const [unlockTarget, setUnlockTarget] = useState<Room | null>(null);
  const [unlockedRooms, setUnlockedRooms] = useState<Set<number>>(new Set());

  useEffect(() => {
    getMyStatus().then(setStatus).catch(() => {});
    listRooms()
      .then(setRooms)
      .catch(() => {})
      .finally(() => setLoadingRooms(false));
  }, []);

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  function handleEnrollSuccess() {
    setShowEnrollModal(false);
    setStatus((s) => (s ? { ...s, face_enrolled: true } : s));
  }

  function handleRoomCreated(room: Room) {
    setRooms((prev) => [room, ...prev]);
    setShowCreateRoom(false);
  }

  function handleRoomClick(room: Room) {
    if (!room.is_private || unlockedRooms.has(room.id)) {
      navigate(`/rooms/${room.id}`);
      return;
    }
    if (!status?.face_enrolled) {
      setShowEnrollModal(true);
      return;
    }
    setUnlockTarget(room);
  }

  function handleUnlocked() {
    if (!unlockTarget) return;
    setUnlockedRooms((prev) => new Set(prev).add(unlockTarget.id));
    navigate(`/rooms/${unlockTarget.id}`);
    setUnlockTarget(null);
  }

  return (
    <div style={s.page}>
      {/* Header */}
      <header style={s.header}>
        <span style={s.logo}>MonkeyLocker</span>
        <div style={s.userArea}>
          {user?.profile_picture && (
            <img src={user.profile_picture} alt="avatar" style={s.avatar} />
          )}
          <span style={s.username}>{user?.username}</span>
          <button onClick={handleLogout} style={s.logoutBtn}>Sign out</button>
        </div>
      </header>

      <main style={s.main}>
        {/* Enroll banner */}
        {status && !status.face_enrolled && (
          <motion.div
            style={s.enrollBanner}
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <div>
              <p style={s.bannerTitle}>Enable face unlock</p>
              <p style={s.bannerText}>Enroll your face to unlock private rooms hands-free.</p>
            </div>
            <button onClick={() => setShowEnrollModal(true)} style={s.enrollBtn}>
              Enroll now
            </button>
          </motion.div>
        )}

        {/* Section header */}
        <div style={s.sectionHeader}>
          <div>
            <h2 style={s.sectionTitle}>Your Rooms</h2>
            <p style={s.sectionSub}>
              {rooms.length} room{rooms.length !== 1 ? "s" : ""}
            </p>
          </div>
          <button onClick={() => setShowCreateRoom(true)} style={s.createBtn}>
            + New Room
          </button>
        </div>

        {/* Room shelf */}
        {loadingRooms ? (
          <div style={s.shelfSkeleton}>
            {[1, 2, 3, 4].map((i) => <div key={i} style={s.skeletonCard} />)}
          </div>
        ) : rooms.length === 0 ? (
          <div style={s.emptyState}>
            <p style={s.emptyTitle}>No rooms yet</p>
            <p style={s.emptyText}>Create your first room to start sharing memories.</p>
            <button onClick={() => setShowCreateRoom(true)} style={s.createBtnLarge}>
              Create a room
            </button>
          </div>
        ) : (
          <div style={s.shelf}>
            {rooms.map((room, i) => (
              <motion.div
                key={room.id}
                style={s.card}
                onClick={() => handleRoomClick(room)}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: i * 0.06 }}
                whileHover={{ y: -4, boxShadow: "0 8px 24px rgba(47,42,37,0.14)" }}
              >
                {/* Card cover */}
                <div style={{ ...s.cardCover, background: roomGradient(room.id) }}>
                  <span style={s.cardInitial}>
                    {room.name.charAt(0).toUpperCase()}
                  </span>
                  {room.is_private && (
                    <span style={s.lockBadge}>🔒</span>
                  )}
                </div>

                {/* Card body */}
                <div style={s.cardBody}>
                  <p style={s.cardName}>{room.name}</p>
                  {room.description && (
                    <p style={s.cardDesc}>{room.description}</p>
                  )}
                  <p style={s.cardMeta}>
                    {new Date(room.created_at).toLocaleDateString("default", {
                      month: "short", day: "numeric", year: "numeric",
                    })}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </main>

      {showEnrollModal && (
        <FaceEnrollModal onClose={() => setShowEnrollModal(false)} onSuccess={handleEnrollSuccess} />
      )}
      {unlockTarget && (
        <FaceUnlockModal
          roomName={unlockTarget.name}
          onClose={() => setUnlockTarget(null)}
          onUnlocked={handleUnlocked}
        />
      )}
      {showCreateRoom && (
        <CreateRoomModal onClose={() => setShowCreateRoom(false)} onCreated={handleRoomCreated} />
      )}
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const s: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "var(--bg)" },

  header: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "0 40px", height: "64px", background: "var(--card)",
    borderBottom: "1px solid var(--border)", position: "sticky", top: 0, zIndex: 100,
  },
  logo: { fontWeight: 700, fontSize: "17px", color: "var(--accent)", letterSpacing: "-0.3px" },
  userArea: { display: "flex", alignItems: "center", gap: "12px" },
  avatar: { width: "34px", height: "34px", borderRadius: "50%", objectFit: "cover" },
  username: { fontSize: "14px", color: "var(--text-2)", fontWeight: 500 },
  logoutBtn: {
    background: "none", border: "1px solid var(--border)", borderRadius: "6px",
    padding: "6px 14px", fontSize: "13px", color: "var(--text-2)",
  },

  main: { maxWidth: "1400px", margin: "0 auto", padding: "40px 40px 60px" },

  enrollBanner: {
    background: "var(--card)", border: "1px solid var(--border)", borderRadius: "12px",
    padding: "20px 24px", display: "flex", justifyContent: "space-between",
    alignItems: "center", gap: "16px", marginBottom: "32px",
    borderLeft: "4px solid var(--accent)",
  },
  bannerTitle: { margin: "0 0 3px", fontWeight: 600, fontSize: "14px", color: "var(--text)" },
  bannerText: { margin: 0, fontSize: "13px", color: "var(--text-2)" },
  enrollBtn: {
    padding: "8px 20px", background: "var(--accent)", color: "#fff", border: "none",
    borderRadius: "8px", fontSize: "13px", fontWeight: 600, whiteSpace: "nowrap",
  },

  sectionHeader: {
    display: "flex", justifyContent: "space-between", alignItems: "flex-end",
    marginBottom: "20px",
  },
  sectionTitle: { fontSize: "22px", fontWeight: 700, color: "var(--text)", marginBottom: "2px" },
  sectionSub: { margin: 0, fontSize: "13px", color: "var(--text-2)" },
  createBtn: {
    padding: "9px 20px", background: "var(--accent)", color: "#fff", border: "none",
    borderRadius: "8px", fontSize: "13px", fontWeight: 600,
  },

  // Horizontal shelf
  shelf: {
    display: "flex", gap: "20px", overflowX: "auto", paddingBottom: "12px",
    scrollSnapType: "x mandatory",
  },
  card: {
    background: "var(--card)", borderRadius: "14px", border: "1px solid var(--border)",
    cursor: "pointer", flexShrink: 0, width: "240px",
    overflow: "hidden", scrollSnapAlign: "start",
    transition: "box-shadow 0.2s",
  },
  cardCover: {
    height: "120px", display: "flex", alignItems: "center",
    justifyContent: "space-between", padding: "14px 16px",
    position: "relative",
  },
  cardInitial: {
    fontSize: "42px", fontWeight: 700, color: "rgba(255,255,255,0.9)",
    lineHeight: 1,
  },
  lockBadge: { fontSize: "18px" },
  cardBody: { padding: "14px 16px 16px" },
  cardName: { margin: "0 0 4px", fontWeight: 600, fontSize: "14px", color: "var(--text)" },
  cardDesc: {
    margin: "0 0 8px", fontSize: "12px", color: "var(--text-2)", lineHeight: 1.4,
    overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2,
    WebkitBoxOrient: "vertical",
  },
  cardMeta: { margin: 0, fontSize: "11px", color: "var(--text-2)" },

  // Skeleton
  shelfSkeleton: { display: "flex", gap: "20px" },
  skeletonCard: {
    width: "240px", height: "200px", borderRadius: "14px",
    background: "linear-gradient(90deg, var(--border) 25%, #F5F0EA 50%, var(--border) 75%)",
    flexShrink: 0,
  },

  // Empty
  emptyState: {
    background: "var(--card)", border: "1px solid var(--border)", borderRadius: "12px",
    padding: "64px 24px", textAlign: "center", display: "flex",
    flexDirection: "column", alignItems: "center", gap: "10px",
  },
  emptyTitle: { fontSize: "16px", fontWeight: 600, color: "var(--text)" },
  emptyText: { margin: 0, fontSize: "14px", color: "var(--text-2)" },
  createBtnLarge: {
    marginTop: "8px", padding: "10px 28px", background: "var(--accent)", color: "#fff",
    border: "none", borderRadius: "8px", fontSize: "14px", fontWeight: 600,
  },
};
