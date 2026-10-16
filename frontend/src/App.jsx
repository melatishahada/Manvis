import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_URL = "";

const PERMISSIONS = {
  ADMIN: [
    "manual_visits",
    "history",
    "profile",
    "download_log",
    "users",
  ],
  USER: [
    "manual_visits",
    "history",
    "profile",
  ],
};

function App() {
  const [user, setUser] = useState(() => {
    const saved = sessionStorage.getItem("manvis_user");
    return saved ? JSON.parse(saved) : null;
  });
  const [activePage, setActivePage] = useState("reports");
  const [showProfile, setShowProfile] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [reports, setReports] = useState([]);
  const [downloadLogs, setDownloadLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  const ITEMS_PER_PAGE = 5;
  const permissions = useMemo(() => PERMISSIONS[user?.role] || [], [user]);
  const canAccess = (p) => permissions.includes(p);

  const loadReports = async () => {
    try {
      const r = await fetch(`${API_URL}/reports/history`);
      if (!r.ok) throw new Error("Gagal mengambil report history.");
      const data = await r.json();
      setReports(data.data || []);
    } catch (e) {
      console.error(e);
      setError("Tidak dapat mengambil report history.");
    }
  };

  const loadDownloadLogs = async () => {
  try {
    const r = await fetch(`${API_URL}/reports/download-log`);

    if (!r.ok) {
      throw new Error("Gagal mengambil download log.");
    }

    const data = await r.json();

    setDownloadLogs(data.data || []);
  } catch (e) {
    console.error(e);
    setError("Tidak dapat mengambil download log.");
  }
};

  const totalPages = Math.ceil(
  reports.length / ITEMS_PER_PAGE
);

const startIndex =
  (currentPage - 1) * ITEMS_PER_PAGE;

const paginatedReports = reports.slice(
  startIndex,
  startIndex + ITEMS_PER_PAGE
);

  useEffect(() => {
  if (!user) return;

  if (
    !canAccess(
      activePage === "home"
        ? "dashboard"
        : activePage
    )
  ) {
    setActivePage("reports");
  }

  loadReports();

  if (canAccess("download_log")) {
    loadDownloadLogs();
  }
}, [user]);

  const handleLogin = async (username, password) => {
  if (!username || !password) {
    return "Username dan password wajib diisi.";
  }

  try {
    const response = await fetch(`${API_URL}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: username.trim(),
        password,
      }),
    });

    const contentType = response.headers.get("content-type") || "";
    const raw = await response.text();

    let data = {};

    if (contentType.includes("application/json")) {
      try {
        data = JSON.parse(raw);
      } catch {
        data = {};
      }
    } else {
      data = {
        detail: raw,
      };
    }

    if (!response.ok) {
      throw new Error(
        data.detail ||
        data.message ||
        "Login gagal."
      );
    }

    if (!data.user) {
      throw new Error(
        "Response login dari server tidak lengkap."
      );
    }

    sessionStorage.setItem(
      "manvis_user",
      JSON.stringify(data.user)
    );

    setUser(data.user);
    setActivePage("reports");
    setShowProfile(false);
    setError("");

    return "";
  } catch (error) {
  console.error("LOGIN ERROR:", error);

  const message =
    typeof error === "string"
      ? error
      : error?.message
      ? error.message
      : JSON.stringify(error);

  return message || "Login gagal.";
}
};

  const handleLogout = () => {
    sessionStorage.removeItem("manvis_user");
    setUser(null);
    setShowProfile(false);
    setActivePage("reports");
    setReports([]);
  };

  const openModal = () => {
    setError(""); setStartDate(""); setEndDate(""); setShowModal(true);
  };
  const closeModal = () => {
    if (loading) return;
    setShowModal(false); setStartDate(""); setEndDate(""); setError("");
  };

  const downloadReport = (report) => {

  if (!user?.id) {
    setError("User login tidak ditemukan.");
    return;
  }

  setError("");

  const url =
    `${API_URL}/reports/history/` +
    `${report.id}/download` +
    `?user_id=${user.id}`;

  window.location.href = url;

  // Refresh history setelah jeda singkat,
  // supaya "Downloaded by" ter-update
  setTimeout(() => {
    loadReports();
  }, 1500);
};

const createReport = async (type) => {

  if (!startDate || !endDate) {
    setError("Tanggal awal dan akhir wajib diisi.");
    return;
  }

  try {
    setLoading(true);
    setError("");

    const historyResponse = await fetch(`${API_URL}/reports/history`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        start_date: startDate,
        end_date: endDate,
        report_type: type,
      }),
    });

    if (!historyResponse.ok) {
      const errData = await historyResponse.json().catch(() => ({}));
      throw new Error(errData.detail || "Gagal membuat report.");
    }

    await loadReports();
    closeModal();

  } catch (err) {
    console.error("CREATE REPORT ERROR:", err);
    setError(err.message || "Gagal membuat report.");
  } finally {
    setLoading(false);
  }
};

  if (!user) return <LoginPage onLogin={handleLogin} />;

  const initial = (user.name || "U").charAt(0).toUpperCase();

  return (
    <div className={`app-shell ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}>
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark">M</div>
          <div className="sidebar-brand-text"><strong>MANVIS</strong><span>Manual Visit Information System</span></div>
          <button className="sidebar-toggle" onClick={() => setSidebarCollapsed((v) => !v)}>{sidebarCollapsed ? "›" : "‹"}</button>
        </div>
        <nav className="sidebar-nav">
          <div className="nav-label">MENU</div>
          {canAccess("manual_visits") && <>
            <div className="nav-label nav-label-space">REPORT</div>
            <button className={`nav-item ${activePage === "reports" ? "active" : ""}`} onClick={() => setActivePage("reports")}><span className="nav-icon">▣</span><span className="nav-text">Manual Visit</span></button>
          </>}
          {canAccess("history") && <button className={`nav-item ${activePage === "history" ? "active" : ""}`} onClick={() => setActivePage("history")}><span className="nav-icon">▤</span><span className="nav-text">Report History</span></button>}
          {canAccess("download_log") && (
  <button
    className={`nav-item ${
      activePage === "download_log" ? "active" : ""
    }`}
    onClick={() => setActivePage("download_log")}
  >
    <span className="nav-icon">↓</span>
    <span className="nav-text">Download Log</span>
  </button>
)}
          {canAccess("users") && <button className={`nav-item ${activePage === "users" ? "active" : ""}`} onClick={() => setActivePage("users")}><span className="nav-icon">☺</span><span className="nav-text">Users</span></button>}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-user"><div className="avatar-small">{initial}</div><div className="sidebar-user-text"><strong>{user.name}</strong><span>{user.role}</span></div></div>
          <button className="sidebar-logout" onClick={handleLogout}><span className="logout-icon">↪</span><span className="nav-text">Logout</span></button>
        </div>
      </aside>

      <div className="main-shell">
        <header className="top-header">
          <div className="header-title"><span>Data Management</span><small>Manual Visit Information System</small></div>
          <div className="header-actions">
            <div className="profile-wrap">
              <button className="profile-trigger" onClick={() => setShowProfile((v) => !v)}><div className="avatar">{initial}</div><span>{user.name}</span><span className="chevron">⌄</span></button>
              {showProfile && <div className="profile-menu">
                <div className="profile-menu-head"><div className="avatar profile-avatar">{initial}</div><div><strong>{user.name}</strong><span>{user.role}</span></div></div>
                {canAccess("profile") && <button className="profile-menu-item" onClick={() => { setShowProfile(false); setActivePage("profile"); }}><span>♙</span>Profile</button>}
                <button className="profile-menu-item logout" onClick={handleLogout}><span>↪</span>Logout</button>
              </div>}
            </div>
          </div>
        </header>

        <main className="content">
          {activePage === "reports" && canAccess("manual_visits") && <ReportsPage reports={reports} error={error} onRun={openModal} onDownload={downloadReport} />}
          {activePage === "history" && canAccess("history") && <ReportsPage reports={reports} error={error} onRun={openModal} onDownload={downloadReport} historyOnly />}
          {activePage === "profile" && canAccess("profile") && <ProfilePage user={user} onLogout={handleLogout} />}
          {activePage === "users" && canAccess("users") && <UsersPage />}
          {activePage === "download_log" && canAccess("download_log") && ( <DownloadLogPage logs={downloadLogs} error={error}/> )} 
        </main> 
      </div>

      {showModal && canAccess("manual_visits") && <div className="modal-overlay" onMouseDown={(e) => e.target === e.currentTarget && closeModal()}>
        <div className="modal">
          <div className="modal-header"><div><h2>Run Report</h2><p>Pilih periode data yang ingin di-download.</p></div><button className="close-button" onClick={closeModal} disabled={loading}>×</button></div>
          <div className="date-grid">
            <div className="form-group"><label>Start Date</label><input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} disabled={loading} /></div>
            <div className="form-group"><label>End Date</label><input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} disabled={loading} /></div>
          </div>
          {error && <div className="error-message">{error}</div>}
          <div className="modal-actions"><button className="cancel-button" onClick={closeModal} disabled={loading}>Cancel</button><div className="format-buttons"><button className="csv-button" onClick={() => createReport("CSV")} disabled={loading}>{loading ? "Processing..." : "CSV"}</button><button className="excel-button" onClick={() => createReport("Excel")} disabled={loading}>{loading ? "Processing..." : "Excel"}</button></div></div>
        </div>
      </div>}
    </div>
  );
}

function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submitLogin = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    const result = await onLogin(
      username,
      password
    );

    if (result) {
      setError(result);
    }

    setLoading(false);
  };

  return (
    <div className="login-page">
      <div className="login-card">

        <div className="login-logo">
          <div className="brand-mark large">
            M
          </div>

          <div>
            <strong>MANVIS</strong>
            <span>
              Manual Visit Information System
            </span>
          </div>
        </div>

        <div className="login-heading">
          <h1>Welcome</h1>

          <p>
            Masuk untuk mengakses aplikasi MANVIS
          </p>
        </div>

        <form onSubmit={submitLogin}>

          <div className="form-group">
            <label>Username</label>

            <input
  type="text"
  placeholder="Masukkan username"
  value={username}
  onChange={(e) => setUsername(e.target.value)}
  required
/>
          </div>

          <div className="form-group login-password">
            <label>Password</label>

            <div className="password-input-wrap">

              <input
                type={
                  showPassword
                    ? "text"
                    : "password"
                }
                placeholder="Masukkan password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                autoComplete="current-password"
                disabled={loading}
              />

              <button
                type="button"
                className="password-toggle"
                onClick={() =>
                  setShowPassword(
                    (prev) => !prev
                  )
                }
                aria-label={
                  showPassword
                    ? "Sembunyikan password"
                    : "Tampilkan password"
                }
                title={
                  showPassword
                    ? "Sembunyikan password"
                    : "Tampilkan password"
                }
                disabled={loading}
              >
                {showPassword ? "◉" : "◌"}
              </button>

            </div>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button
            className="login-button"
            type="submit"
            disabled={loading}
          >
            {loading
              ? "Logging in..."
              : "Login"}
          </button>

        </form>

      </div>
    </div>
  );
}

function ReportsPage({
  reports,
  error,
  onRun,
  onDownload,
  historyOnly = false,
}) {

  const ITEMS_PER_PAGE = 5;

  const [currentPage, setCurrentPage] =
    useState(1);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");

  useEffect(() => {
  setCurrentPage(1);
}, [reports, historyOnly, search, typeFilter]);

  const filteredReports = reports.filter((report) => {
  const keyword = search.toLowerCase().trim();

  const matchesSearch =
    !keyword ||
    report.filename
      .toLowerCase()
      .includes(keyword);

  const matchesType =
    typeFilter === "ALL" ||
    report.type === typeFilter;

  return matchesSearch && matchesType;
});

  const totalPages = Math.ceil(
  filteredReports.length / ITEMS_PER_PAGE
);

  const startIndex =
    (currentPage - 1) *
    ITEMS_PER_PAGE;

  const paginatedReports =
    filteredReports.slice(
      startIndex,
      startIndex + ITEMS_PER_PAGE
    );

  const firstItem =
    reports.length === 0
      ? 0
      : startIndex + 1;

  const lastItem =
    Math.min(
      startIndex + ITEMS_PER_PAGE,
      reports.length
    );

  return (
    <>
      <div className="page-heading">

        <div>

          <div className="eyebrow">
            REPORT
          </div>

          <h1>
            {historyOnly
              ? "Report History"
              : "Manual Visit"}
          </h1>

          <p>
            {historyOnly
              ? "Daftar report yang pernah dibuat."
              : "Generate report Manual Visit."}
          </p>

        </div>

        {!historyOnly && (
          <button
            className="primary-button"
            onClick={onRun}
          >
            + Run Report
          </button>
        )}

      </div>

      <section className="reports-card">

        <div className="reports-card-header">

          <div>

            <h2>
              {historyOnly
                ? "Report History"
                : "Manual Visit Report"}
            </h2>

            <p>
              {historyOnly
                ? "Report yang sudah dibuat."
                : "Reports yang sudah dibuat."}
            </p>

          </div>

        </div>

        {historyOnly && (
  <div className="report-search">
    <div className="search-box">
      <span>⌕</span>

      <input
        type="text"
        placeholder="Cari nama report..."
        value={search}
        onChange={(e) =>
          setSearch(e.target.value)
        }
      />
    </div>

    <select
      value={typeFilter}
      onChange={(e) =>
        setTypeFilter(e.target.value)
      }
    >
      <option value="ALL">Semua</option>
      <option value="Excel">Excel</option>
      <option value="CSV">CSV</option>
    </select>
  </div>
)}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {reports.length === 0 ? (

          <div className="empty-report">

            <p>
              Belum ada report yang dibuat.
            </p>

            {!historyOnly && (
              <span>
                Klik Run untuk membuat report.
              </span>
            )}

          </div>

        ) : (

          <>

            <div className="report-list">

              {paginatedReports.map(
                (report) => (

                  <div
                    className="report-item"
                    key={report.id}
                  >

                    <div className="report-info">

                      <div className="file-icon">
                        {report.type === "Excel"
                          ? "XLS"
                          : "CSV"}
                      </div>

                      <div>

                        <h3>
                          {report.filename}
                        </h3>

                        <p>
                          {report.startDate}
                          {" — "}
                          {report.endDate}
                        </p>

                        <span className="report-created">
                          {report.type}
                          {" • "}
                          {report.createdAt
                            ? new Date(
                                report.createdAt
                              ).toLocaleString(
                                "id-ID"
                              )
                            : ""}
                        </span>

                        {report.downloadedBy &&
                          report.downloadedBy.length >
                            0 && (

                          <div className="download-history">

                            <div className="download-history-title">
                              Downloaded by:
                            </div>

                            {report.downloadedBy.map(
                              (download, index) => (

                                <div
                                  className="download-history-item"
                                  key={
                                    `${download.userId}-${download.downloadedAt}-${index}`
                                  }
                                >
                                  <span>
                                    {download.userName}
                                  </span>

                                  <small>
                                    {download.downloadedAt
                                      ? new Date(
                                          download.downloadedAt
                                        ).toLocaleString(
                                          "id-ID"
                                        )
                                      : ""}
                                  </small>
                                </div>

                              )
                            )}

                          </div>

                        )}

                      </div>

                    </div>

                    {!historyOnly && (


                      <button


                        className="download-button"


                        onClick={() => onDownload(report)}


                      >


                        Download


                      </button>


                    )}

                  </div>

                )
              )}

            </div>

            {totalPages > 1 && (

              <div className="pagination">

                <span className="pagination-info">
                  Menampilkan {firstItem}–{lastItem}
                  {" dari "}
                  {filteredReports.length} report
                </span>

                <div className="pagination-buttons">

                  <button
                    disabled={
                      currentPage === 1
                    }
                    onClick={() =>
                      setCurrentPage(
                        (page) =>
                          Math.max(
                            page - 1,
                            1
                          )
                      )
                    }
                  >
                    ‹
                  </button>

                  {Array.from(
                    {
                      length: totalPages,
                    },
                    (_, index) =>
                      index + 1
                  ).map((page) => (

                    <button
                      key={page}
                      className={
                        currentPage === page
                          ? "active"
                          : ""
                      }
                      onClick={() =>
                        setCurrentPage(page)
                      }
                    >
                      {page}
                    </button>

                  ))}

                  <button
                    disabled={
                      currentPage ===
                      totalPages
                    }
                    onClick={() =>
                      setCurrentPage(
                        (page) =>
                          Math.min(
                            page + 1,
                            totalPages
                          )
                      )
                    }
                  >
                    ›
                  </button>

                </div>

              </div>

            )}

          </>

        )}

      </section>
    </>
  );
}

function ProfilePage({ user, onLogout }) {
  const initial = (user.name || "U").charAt(0).toUpperCase();
  return <><div className="page-heading"><div><div className="eyebrow">ACCOUNT</div><h1>Profile</h1><p>Informasi akun yang sedang digunakan.</p></div></div>
    <section className="profile-card"><div className="profile-main"><div className="profile-large-avatar">{initial}</div><div><h2>{user.name}</h2><p>MANVIS Internal User</p></div></div>
      <div className="profile-details"><div><span>Name</span><strong>{user.name}</strong></div><div><span>Email</span><strong>{user.email}</strong></div><div><span>Role</span><strong>{user.role}</strong></div><div><span>System</span><strong>MANVIS</strong></div></div>
      <button className="logout-full-button" onClick={onLogout}>Logout</button>
    </section></>;
}

function DownloadLogPage({ logs, error }) {
  const [search, setSearch] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  const ITEMS_PER_PAGE = 5;

  const filteredLogs = logs.filter((log) => {
    const keyword = search.toLowerCase().trim();

    if (!keyword) return true;

    return (
      log.userName?.toLowerCase().includes(keyword) ||
      log.filename?.toLowerCase().includes(keyword) ||
      log.type?.toLowerCase().includes(keyword)
    );
  });

  const totalPages = Math.ceil(
    filteredLogs.length / ITEMS_PER_PAGE
  );

  const startIndex =
    (currentPage - 1) * ITEMS_PER_PAGE;

  const paginatedLogs = filteredLogs.slice(
    startIndex,
    startIndex + ITEMS_PER_PAGE
  );

  useEffect(() => {
    setCurrentPage(1);
  }, [search]);

  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            SYSTEM
          </div>

          <h1>Download Log</h1>

          <p>
            Riwayat user yang melakukan download report.
          </p>
        </div>
      </div>

      <section className="reports-card">

        <div className="reports-card-header">
          <div>
            <h2>Download Log</h2>
            <p>
              Catatan aktivitas download report.
            </p>
          </div>

          <div className="report-search">
            <div className="search-box">
              <span>⌕</span>

              <input
                type="text"
                placeholder="Cari user atau report..."
                value={search}
                onChange={(e) =>
                  setSearch(e.target.value)
                }
              />
            </div>
          </div>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {paginatedLogs.length === 0 ? (
          <div className="empty-report">
            <p>
              Belum ada aktivitas download.
            </p>
          </div>
        ) : (
          <>
            <div className="report-list">
              {paginatedLogs.map((log) => (
                <div
                  className="report-item"
                  key={log.id}
                >
                  <div className="report-info">
                    <div className="file-icon">
                      {log.type === "Excel"
                        ? "XLS"
                        : "CSV"}
                    </div>

                    <div>
                      <h3>{log.filename}</h3>

                      <p>
                        {log.userName}
                        {" • "}
                        {log.email}
                      </p>

                      <span className="report-created">
                        {log.type}
                        {" • "}
                        {log.downloadedAt
                          ? new Date(
                              log.downloadedAt
                            ).toLocaleString("id-ID")
                          : ""}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {totalPages > 1 && (
              <div className="pagination">
                <span className="pagination-info">
                  Menampilkan{" "}
                  {startIndex + 1}
                  {"–"}
                  {Math.min(
                    startIndex + ITEMS_PER_PAGE,
                    filteredLogs.length
                  )}
                  {" dari "}
                  {filteredLogs.length} log
                </span>

                <div className="pagination-buttons">
                  <button
                    disabled={currentPage === 1}
                    onClick={() =>
                      setCurrentPage((page) =>
                        Math.max(page - 1, 1)
                      )
                    }
                  >
                    ‹
                  </button>

                  {Array.from(
                    { length: totalPages },
                    (_, index) => index + 1
                  ).map((page) => (
                    <button
                      key={page}
                      className={
                        currentPage === page
                          ? "active"
                          : ""
                      }
                      onClick={() =>
                        setCurrentPage(page)
                      }
                    >
                      {page}
                    </button>
                  ))}

                  <button
                    disabled={
                      currentPage === totalPages
                    }
                    onClick={() =>
                      setCurrentPage((page) =>
                        Math.min(
                          page + 1,
                          totalPages
                        )
                      )
                    }
                  >
                    ›
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </section>
    </>
  );
}

function UsersPage() {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("USER");

  const loadUsers = async () => {
    try {
      const r = await fetch(`${API_URL}/users`);
      if (!r.ok) throw new Error("Gagal mengambil data users.");
      const data = await r.json();
      setUsers(data.data || []);
    } catch (e) {
      setError(e.message || "Gagal mengambil data users.");
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const resetForm = () => {
    setName("");
    setEmail("");
    setPassword("");
    setRole("USER");
    setShowForm(false);
  };

  const submitNewUser = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const r = await fetch(`${API_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password, role }),
      });

      const data = await r.json();

      if (!r.ok) {
        throw new Error(data.detail || "Gagal menambah user.");
      }

      await loadUsers();
      resetForm();
    } catch (err) {
      setError(err.message || "Gagal menambah user.");
    } finally {
      setLoading(false);
    }
  };

  const toggleActive = async (targetUser) => {
    try {
      const r = await fetch(`${API_URL}/users/${targetUser.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: targetUser.isActive ? 0 : 1 }),
      });

      if (!r.ok) throw new Error("Gagal mengubah status user.");
      await loadUsers();
    } catch (err) {
      setError(err.message || "Gagal mengubah status user.");
    }
  };

  const changeRole = async (targetUser, newRole) => {
    try {
      const r = await fetch(`${API_URL}/users/${targetUser.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: newRole }),
      });

      if (!r.ok) throw new Error("Gagal mengubah role user.");
      await loadUsers();
    } catch (err) {
      setError(err.message || "Gagal mengubah role user.");
    }
  };

  
const [userToDelete, setUserToDelete] = useState(null);
const [deleting, setDeleting] = useState(false);

const removeUser = async () => {
  if (!userToDelete || deleting) return;

  try {
    setDeleting(true);
    setError("");

    const r = await fetch(
      `${API_URL}/users/${userToDelete.id}`,
      { method: "DELETE" }
    );

    const data = await r.json().catch(() => ({}));

    if (!r.ok) {
      throw new Error(data.detail || "Gagal menghapus user.");
    }

    setUserToDelete(null);
    await loadUsers();
  } catch (err) {
    setError(err.message || "Gagal menghapus user.");
  } finally {
    setDeleting(false);
  }
};

  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">ACCOUNT</div>
          <h1>Users</h1>
          <p>Kelola akun pengguna sistem MANVIS.</p>
        </div>
        <button className="primary-button" onClick={() => setShowForm(true)}>
          + Tambah User
        </button>
      </div>

      <section className="reports-card">
        <div className="reports-card-header">
          <div>
            <h2>Daftar Users</h2>
            <p>Total {users.length} user terdaftar.</p>
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="report-list">
          {users.map((u) => (
            <div className="report-item" key={u.id}>
              <div className="report-info">
                <div className="file-icon">
                  {u.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h3>{u.name}</h3>
                  <p>{u.email}</p>
                  <span className="report-created">
                    {u.isActive ? "Aktif" : "Nonaktif"}
                  </span>
                </div>
              </div>

              <div className="report-actions" style={{ flexDirection: "row", alignItems: "center", gap: "8px" }}>
                <select
                  value={u.role}
                  onChange={(e) => changeRole(u, e.target.value)}
                  style={{ padding: "8px", borderRadius: "8px", border: "1px solid #d1d5db" }}
                >
                  <option value="ADMIN">ADMIN</option>
                  <option value="USER">USER</option>
                </select>
                <button className="download-button" onClick={() => toggleActive(u)}>
                  {u.isActive ? "Nonaktifkan" : "Aktifkan"}
                </button>
                <button
                  className="delete-user-button"
                  onClick={() => setUserToDelete(u)}
                >
                  Hapus
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {showForm && (
        <div className="modal-overlay" onMouseDown={(e) => e.target === e.currentTarget && resetForm()}>
          <div className="modal">
            <div className="modal-header">
              <div>
                <h2>Tambah User</h2>
                <p>Buat akun baru untuk sistem MANVIS.</p>
              </div>
              <button className="close-button" onClick={resetForm} disabled={loading}>×</button>
            </div>

            <form onSubmit={submitNewUser}>
              <div className="form-group" style={{ marginBottom: "12px" }}>
                <label>Nama</label>
                <input type="text" value={name} onChange={(e) => setName(e.target.value)} required disabled={loading} />
              </div>
              <div className="form-group" style={{ marginBottom: "12px" }}>
                <label>Email</label>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required disabled={loading} />
              </div>
              <div className="form-group" style={{ marginBottom: "12px" }}>
                <label>Password</label>
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required disabled={loading} />
              </div>
              <div className="form-group" style={{ marginBottom: "16px" }}>
                <label>Role</label>
                <select value={role} onChange={(e) => setRole(e.target.value)} disabled={loading} style={{ height: "42px", borderRadius: "8px", border: "1px solid #d1d5db", padding: "0 11px" }}>
                  <option value="USER">USER</option>
                  <option value="ADMIN">ADMIN</option>
                </select>
              </div>

              {error && <div className="error-message">{error}</div>}

              <div className="modal-actions">
                <button type="button" className="cancel-button" onClick={resetForm} disabled={loading}>Cancel</button>
                <button type="submit" className="excel-button" disabled={loading}>
                  {loading ? "Menyimpan..." : "Simpan"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      
{userToDelete && (
  <div
    className="modal-overlay"
    onMouseDown={(e) => {
      if (e.target === e.currentTarget && !deleting) {
        setUserToDelete(null);
      }
    }}
  >
    <div
      className="delete-user-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-user-title"
    >
      <div className="delete-user-icon">!</div>

      <h2 id="delete-user-title">Hapus User?</h2>

      <p className="delete-user-description">
        Apakah kamu yakin ingin menghapus akun ini?
        Tindakan ini mungkin tidak dapat dibatalkan.
      </p>

      <div className="delete-user-detail">
        <div className="delete-user-avatar">
          {(userToDelete.name || "U").charAt(0).toUpperCase()}
        </div>

        <div className="delete-user-info">
          <strong>{userToDelete.name}</strong>
          <span>{userToDelete.email}</span>
          <span className="delete-user-role">
            {userToDelete.role}
          </span>
        </div>
      </div>

      <div className="delete-user-actions">
        <button
          className="cancel-button"
          onClick={() => setUserToDelete(null)}
          disabled={deleting}
        >
          Batal
        </button>

        <button
          className="delete-user-confirm"
          onClick={removeUser}
          disabled={deleting}
        >
          {deleting ? "Menghapus..." : "Ya, Hapus User"}
        </button>
      </div>
    </div>
  </div>
)}
    </>
  );
}



export default App;
