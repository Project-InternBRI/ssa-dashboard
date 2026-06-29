import os

file_path = "/Users/naufalrasydan/Documents/Workspace/Intern BRI/ssa-dashboard/ui/beranda_widget.py"

with open(file_path, "r") as f:
    content = f.read()

start_idx = content.find("    def _icon_label(self, emoji, bg, fg):")
end_idx = content.find("    # ── AKSES CEPAT ──")

if start_idx == -1 or end_idx == -1:
    print("Could not find start or end index!")
    exit(1)

replacement = """    def _icon_label(self, icon_filename, bg, fg):
        lbl = QLabel()
        lbl.setFixedSize(40, 40)
        lbl.setStyleSheet(f"background: {bg}; border-radius: 8px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if icon_filename:
            icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icons", icon_filename))
            lbl.setPixmap(QIcon(icon_path).pixmap(QSize(20, 20)))
        return lbl

    def _build_stats(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(20)

        # 1. STATUS FILE
        c1 = self._create_shadow_card()
        l1 = QVBoxLayout(c1)
        l1.setContentsMargins(20, 20, 20, 20)
        l1.setSpacing(8)
        
        h1 = QHBoxLayout()
        h1.addWidget(self._icon_label("file_homepage.svg", "#EFF6FF", "#2563EB"))
        h1.addSpacing(10)
        t1 = QLabel("STATUS FILE")
        t1.setStyleSheet("color: #475569; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        h1.addWidget(t1)
        h1.addStretch()
        l1.addLayout(h1)

        v1 = QLabel("0/3")
        v1.setStyleSheet("color: #2563EB; font-size: 32px; font-weight: bold;")
        s1 = QLabel("File Siap")
        s1.setStyleSheet("color: #1E293B; font-size: 13px; font-weight: bold; margin-bottom: 4px;")
        l1.addWidget(v1)
        l1.addWidget(s1)

        p1 = QProgressBar()
        p1.setFixedHeight(6)
        p1.setTextVisible(False)
        p1.setStyleSheet("QProgressBar { background: #E2E8F0; border-radius: 3px; border: none; } QProgressBar::chunk { background: #16A34A; border-radius: 3px; }")
        l1.addWidget(p1)

        def make_chk(txt):
            lay = QHBoxLayout()
            lbl = QLabel(txt)
            lbl.setStyleSheet("color: #475569; font-size: 11px; font-weight: 600;")
            chk = QLabel("X")
            chk.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: bold;")
            lay.addWidget(lbl)
            lay.addStretch()
            lay.addWidget(chk)
            return lay, chk

        lay_s, chk_s = make_chk("SSA Simpanan")
        lay_p, chk_p = make_chk("SSA Pinjaman")
        lay_r, chk_r = make_chk("RKA")
        l1.addLayout(lay_s)
        l1.addLayout(lay_p)
        l1.addLayout(lay_r)

        l1.addStretch()
        b1 = QHBoxLayout()
        d1 = QLabel("●")
        d1.setStyleSheet("color: #94A3B8; font-size: 12px;")
        ds1 = QLabel("Belum ada file")
        ds1.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold;")
        b1.addWidget(d1)
        b1.addWidget(ds1)
        b1.addStretch()
        l1.addLayout(b1)

        self._stats_refs["upload"] = {"val": v1, "prog": p1, "cs": chk_s, "cp": chk_p, "cr": chk_r, "dot": d1, "ds": ds1}
        row.addWidget(c1)

        # 2. KC TERDETEKSI
        c2 = self._create_shadow_card()
        l2 = QVBoxLayout(c2)
        l2.setContentsMargins(20, 20, 20, 20)
        l2.setSpacing(8)
        
        h2 = QHBoxLayout()
        h2.addWidget(self._icon_label("kc_homepage.svg", "#FEF3C7", "#D97706"))
        h2.addSpacing(10)
        t2 = QLabel("KC TERDETEKSI")
        t2.setStyleSheet("color: #475569; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        h2.addWidget(t2)
        h2.addStretch()
        l2.addLayout(h2)

        v2 = QLabel("0")
        v2.setStyleSheet("color: #D97706; font-size: 32px; font-weight: bold;")
        s2 = QLabel("KC Aktif")
        s2.setStyleSheet("color: #1E293B; font-size: 13px; font-weight: bold; margin-bottom: 20px;")
        l2.addWidget(v2)
        l2.addWidget(s2)

        p_lay = QHBoxLayout()
        p_ic = QLabel("👥")
        p_ic.setStyleSheet("font-size: 20px; color: #94A3B8;")
        p_lay.addWidget(p_ic)
        p_lay.addStretch()
        l2.addLayout(p_lay)

        p_txt = QLabel("Siap Diproses")
        p_txt.setStyleSheet("color: #1E293B; font-size: 12px; font-weight: bold;")
        l2.addWidget(p_txt)

        l2.addStretch()
        b2 = QHBoxLayout()
        d2 = QLabel("●")
        d2.setStyleSheet("color: #94A3B8; font-size: 12px;")
        ds2 = QLabel("Data KC terdeteksi")
        ds2.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold;")
        b2.addWidget(d2)
        b2.addWidget(ds2)
        b2.addStretch()
        l2.addLayout(b2)

        self._stats_refs["kc"] = {"val": v2, "dot": d2, "ds": ds2}
        row.addWidget(c2)

        # 3. PERIODE SSA
        c3 = self._create_shadow_card()
        l3 = QVBoxLayout(c3)
        l3.setContentsMargins(20, 20, 20, 20)
        l3.setSpacing(8)
        
        h3 = QHBoxLayout()
        h3.addWidget(self._icon_label("calendar_homepage.svg", "#DCFCE7", "#16A34A"))
        h3.addSpacing(10)
        t3 = QLabel("PERIODE SSA")
        t3.setStyleSheet("color: #475569; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        h3.addWidget(t3)
        h3.addStretch()
        l3.addLayout(h3)

        v3 = QLabel("—")
        v3.setStyleSheet("color: #16A34A; font-size: 32px; font-weight: bold;")
        s3 = QLabel("Periode Terakhir")
        s3.setStyleSheet("color: #1E293B; font-size: 13px; font-weight: bold; margin-bottom: 20px;")
        l3.addWidget(v3)
        l3.addWidget(s3)

        cal_lay = QHBoxLayout()
        cal_ic = QLabel("🗓️")
        cal_ic.setStyleSheet("font-size: 20px; color: #94A3B8;")
        cal_lay.addWidget(cal_ic)
        cal_lay.addStretch()
        l3.addLayout(cal_lay)

        cal_txt = QLabel("Periode Aktif")
        cal_txt.setStyleSheet("color: #1E293B; font-size: 12px; font-weight: bold;")
        l3.addWidget(cal_txt)

        l3.addStretch()
        b3 = QHBoxLayout()
        d3 = QLabel("●")
        d3.setStyleSheet("color: #94A3B8; font-size: 12px;")
        ds3 = QLabel("Belum tersedia")
        ds3.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold;")
        b3.addWidget(d3)
        b3.addWidget(ds3)
        b3.addStretch()
        l3.addLayout(b3)

        self._stats_refs["periode"] = {"val": v3, "dot": d3, "ds": ds3}
        row.addWidget(c3)

        # 4. STATUS DASHBOARD
        c4 = self._create_shadow_card()
        l4 = QVBoxLayout(c4)
        l4.setContentsMargins(20, 20, 20, 20)
        l4.setSpacing(8)
        
        h4 = QHBoxLayout()
        h4.addWidget(self._icon_label("status_homepage.svg", "#F3E8FF", "#9333EA"))
        h4.addSpacing(10)
        t4 = QLabel("STATUS DASHBOARD")
        t4.setStyleSheet("color: #475569; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        h4.addWidget(t4)
        h4.addStretch()
        l4.addLayout(h4)

        v4 = QLabel("WAIT")
        v4.setStyleSheet("color: #9333EA; font-size: 32px; font-weight: bold;")
        s4 = QLabel("Dashboard Siap")
        s4.setStyleSheet("color: #1E293B; font-size: 13px; font-weight: bold; margin-bottom: 20px;")
        l4.addWidget(v4)
        l4.addWidget(s4)

        clk_lay = QHBoxLayout()
        clk_ic = QLabel("🕒")
        clk_ic.setStyleSheet("font-size: 20px; color: #94A3B8;")
        clk_lay.addWidget(clk_ic)
        clk_lay.addStretch()
        l4.addLayout(clk_lay)

        clk_txt = QLabel("Terakhir Update\\n—")
        clk_txt.setStyleSheet("color: #1E293B; font-size: 12px; font-weight: bold;")
        l4.addWidget(clk_txt)

        l4.addStretch()
        b4 = QHBoxLayout()
        d4 = QLabel("●")
        d4.setStyleSheet("color: #94A3B8; font-size: 12px;")
        ds4 = QLabel("Belum di-generate")
        ds4.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold;")
        b4.addWidget(d4)
        b4.addWidget(ds4)
        b4.addStretch()
        l4.addLayout(b4)

        self._stats_refs["dash"] = {"val": v4, "time": clk_txt, "dot": d4, "ds": ds4}
        row.addWidget(c4)
        return row
"""

with open(file_path, "w") as f:
    f.write(content[:start_idx] + replacement + "\n" + content[end_idx:])

print("Successfully replaced.")
