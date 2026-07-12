"use client";
import { useState } from "react";

export default function Header() {
  const [open, setOpen] = useState(false);

  return (
    <header>
      <div className="header-inner">
        <a href="/" className="logo">DailyLotto</a>
        <button className="burger" onClick={() => setOpen(!open)} aria-label="Menu">
          <span className={`burger-line${open ? " open" : ""}`} />
          <span className={`burger-line${open ? " open" : ""}`} />
          <span className={`burger-line${open ? " open" : ""}`} />
        </button>
      </div>
      {open && (
        <div className="nav-dropdown" onClick={() => setOpen(false)}>
          <a href="/">Dashboard</a>
          <span className="nav-section">Tools</span>
          <a href="/checker">Checker</a>
        </div>
      )}
    </header>
  );
}
