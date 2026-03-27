import flet as ft
import requests
import time

SERVER_IP = "192.168.100.55"
SERVER_PORT = 2500
BASE_URL = f"http://{SERVER_IP}:{SERVER_PORT}"
USERS_URL = f"{BASE_URL}/users"
PETS_URL = f"{BASE_URL}/pets"
RECORDS_URL = f"{BASE_URL}/records"
VACCINES_URL = f"{BASE_URL}/vaccines"
BOOKINGS_URL = f"{BASE_URL}/bookings"

# ── THEME ─────────────────────────────────────────────────────────────────────
PRIMARY = "#FFC300"
DARK = "#1A1A1A"
MID = "#555555"
LIGHT = "#999999"
BG = "#FFFFFF"
BG2 = "#F5F5F5"
BORDER = "#EEEEEE"
GREEN = "#2E7D32"
ORANGE = "#F57F17"
BLUE = "#1565C0"
RED = "#C62828"
BUTTON_BG = "#FFD700"
BUTTON_FG = "#000000"

PET_ICONS = {
    "dog": "🐶", "cat": "🐱", "bird": "🐦",
    "rabbit": "🐰", "fish": "🐠", "hamster": "🐹",
}
PET_COLORS = ["#E8936A", "#5B8DB8", "#6AAF6E", "#9B6BB5", "#E8C46A", "#E87A7A", "#5BC8C8"]

STATUS_LABEL = {
    "pending": ("รอการอนุมัติ", ORANGE),
    "approved": ("อนุมัติแล้ว", BLUE),
    "rejected": ("ปฏิเสธ", RED),
    "staying": ("กำลังรับฝาก", GREEN),
    "completed": ("เสร็จสิ้น", MID),
}


def pet_icon(t: str) -> str:
    return PET_ICONS.get(t.lower().strip(), "🐾")


def pet_color(i: int) -> str:
    return PET_COLORS[i % len(PET_COLORS)]


def info_chip(label: str, color: str):
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
        border_radius=12,
        bgcolor=ft.Colors.with_opacity(0.12, color),
        content=ft.Text(label, size=11, color=color, weight=ft.FontWeight.BOLD),
    )


def status_chip(status: str):
    label, color = STATUS_LABEL.get(status, (status, MID))
    return info_chip(label, color)


def section_header(title, action_label=None, on_action=None):
    return ft.Container(
        padding=ft.padding.only(left=16, right=16, top=20, bottom=10),
        content=ft.Row(
            [
                ft.Row([
                    ft.Container(width=3, height=16, bgcolor=PRIMARY, border_radius=2),
                    ft.Container(width=8),
                    ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=DARK),
                ]),
                (btn(str(action_label), on_action, radius=6, height=34)
                 if action_label else ft.Container(width=0)),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def field_style():
    return dict(
        border_color=BORDER,
        focused_border_color=PRIMARY,
        border_radius=6,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        bgcolor=BG2,
        label_style=ft.TextStyle(color=LIGHT, size=12),
        text_style=ft.TextStyle(size=13, color=DARK),
    )


def btn(label, on_click, bgcolor=None, text_color="#FFFFFF", width=None,
        height=44, radius=8, icon=None, expand=False):
    bg = bgcolor or PRIMARY
    row_items = []
    if icon:
        row_items.append(ft.Icon(icon, color=text_color, size=16))
        row_items.append(ft.Container(width=6))
    row_items.append(ft.Text(label, size=13, weight=ft.FontWeight.BOLD, color=text_color))
    inner = ft.Container(
        width=width, height=height, expand=expand, border_radius=radius, bgcolor=bg,
        alignment=ft.alignment.Alignment(0, 0),
        content=ft.Row(row_items, alignment=ft.MainAxisAlignment.CENTER, spacing=0),
    )
    gd = ft.GestureDetector(on_tap=on_click, content=inner)
    if expand:
        return ft.Container(expand=True, content=gd)
    return gd


def back_bar(page, title, extra_actions=None):
    actions = extra_actions or []
    return ft.Container(
        bgcolor=DARK,
        padding=ft.padding.only(left=12, right=12, top=10, bottom=10),
        content=ft.Row([
            btn("กลับ", lambda e: (page.views.pop(), page.update()),
                bgcolor=BUTTON_BG, text_color=BUTTON_FG, height=38, radius=8,
                icon=ft.Icons.ARROW_BACK),
            ft.Container(expand=True),
            ft.Text(title, size=16, color="#FFF", weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            *actions,
        ]),
    )


def _profile_row(icon, label: str, value: str):
    return ft.Container(
        padding=ft.padding.symmetric(vertical=10),
        content=ft.Row([
            ft.Icon(icon, color=LIGHT, size=18),
            ft.Container(width=12),
            ft.Text(label, size=12, color=LIGHT, width=60),
            ft.Text(value, size=13, color=DARK, weight=ft.FontWeight.W_500, expand=True),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
    )


def _profile_row_widget(icon, label: str, value_widget):
    return ft.Container(
        padding=ft.padding.symmetric(vertical=10),
        content=ft.Row([
            ft.Icon(icon, color=LIGHT, size=18),
            ft.Container(width=12),
            ft.Text(label, size=12, color=LIGHT, width=60),
            value_widget,
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
    )


# ══════════════════════════════════════════════════════════════════════════════
def main(page: ft.Page):
    page.title = "Pet Hotel"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = BG
    page.padding = 0
    page.spacing = 0
    page.window.width = 390
    page.window.height = 844

    def is_landscape():
        return page.width > page.height

    state = {"user": None}
    all_pets: list = []
    pets_col = ft.Column(spacing=8)

    # ══════════════════════════════════════════════════════════════
    # ── VACCINE PAGE (admin & user view) ─────────────────────────
    # ══════════════════════════════════════════════════════════════
    def show_vaccines_page(pet: dict, is_admin: bool = False):
        pid = pet.get("id")
        pet_name = pet.get("name", "?")
        vac_list = ft.Column(spacing=8)

        def load_vaccines():
            vac_list.controls.clear()
            try:
                r = requests.get(f"{VACCINES_URL}/pet/{pid}", timeout=5)
                vacs = r.json() if r.status_code == 200 else []
            except Exception:
                vacs = []
            if not vacs:
                vac_list.controls.append(ft.Container(
                    padding=ft.padding.symmetric(vertical=32),
                    content=ft.Column([
                        ft.Icon(ft.Icons.VACCINES_OUTLINED, size=48, color=LIGHT),
                        ft.Text("ยังไม่มีข้อมูลวัคซีน", size=13, color=LIGHT),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ))
            else:
                for v in vacs:
                    def make_delete_v(vid):
                        def do(e):
                            try:
                                requests.delete(f"{VACCINES_URL}/{vid}", timeout=5)
                            except Exception:
                                pass
                            load_vaccines()
                            page.update()
                        return do

                    def make_edit_v(vdata):
                        def do(e):
                            fs = field_style()
                            tf_name = ft.TextField(label="ชื่อวัคซีน *", value=vdata.get("vaccine_name", ""), **fs)
                            tf_dose = ft.TextField(label="โดส", value=vdata.get("dose", "") or "", **fs)
                            tf_date = ft.TextField(label="วันที่ฉีด (YYYY-MM-DD)", value=vdata.get("vaccine_date", "") or "", **fs)
                            tf_next = ft.TextField(label="ครั้งถัดไป (YYYY-MM-DD)", value=vdata.get("next_due", "") or "", **fs)
                            tf_clinic = ft.TextField(label="คลินิก/โรงพยาบาล", value=vdata.get("clinic", "") or "", **fs)
                            tf_note = ft.TextField(label="หมายเหตุ", value=vdata.get("note", "") or "", multiline=True, min_lines=2, **fs)
                            st = ft.Text("", size=12)

                            def submit_ev(ev):
                                if not tf_name.value.strip():
                                    st.value = "⚠️ กรุณากรอกชื่อวัคซีน"
                                    page.update()
                                    return
                                st.value = "⏳ กำลังบันทึก..."
                                page.update()
                                try:
                                    res = requests.put(f"{VACCINES_URL}/{vdata['id']}", json={
                                        "pet_id": pid,
                                        "vaccine_name": tf_name.value.strip(),
                                        "dose": tf_dose.value.strip() or None,
                                        "vaccine_date": tf_date.value.strip() or None,
                                        "next_due": tf_next.value.strip() or None,
                                        "clinic": tf_clinic.value.strip() or None,
                                        "note": tf_note.value.strip() or None,
                                    }, timeout=5)
                                    if res.status_code == 200:
                                        edlg.open = False
                                        page.update()
                                        load_vaccines()
                                    else:
                                        st.value = f"❌ Error {res.status_code}"
                                        page.update()
                                except Exception:
                                    st.value = "❌ เชื่อมต่อไม่ได้"
                                    page.update()

                            edlg = ft.AlertDialog(
                                modal=True, bgcolor=BG,
                                shape=ft.RoundedRectangleBorder(radius=12),
                                inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
                                title=ft.Text("แก้ไขวัคซีน", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                                content=ft.Container(
                                    width=min(page.width - 48, 400),
                                    content=ft.Column([tf_name, tf_dose, tf_date, tf_next, tf_clinic, tf_note, st], spacing=10, tight=True),
                                ),
                                actions=[
                                    ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                                  on_click=lambda e: (setattr(edlg, "open", False), page.update())),
                                    btn("บันทึก", submit_ev, height=38, radius=6),
                                ],
                                actions_alignment=ft.MainAxisAlignment.END,
                            )
                            page.overlay.append(edlg)
                            edlg.open = True
                            page.update()
                        return do

                    next_due_str = v.get("next_due") or ""
                    vac_list.controls.append(ft.Container(
                        border_radius=10, bgcolor=BG,
                        border=ft.border.all(1, BORDER),
                        padding=ft.padding.all(12),
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.VACCINES, color=GREEN, size=18),
                                ft.Container(width=8),
                                ft.Text(v.get("vaccine_name", ""), size=13, weight=ft.FontWeight.BOLD, color=DARK, expand=True),
                                *(
                                    [ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color=PRIMARY, icon_size=18, on_click=make_edit_v(v)),
                                     ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=RED, icon_size=18, on_click=make_delete_v(v.get("id")))]
                                    if is_admin else []
                                ),
                            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            ft.Container(height=6),
                            ft.Row([
                                ft.Text(f"โดส: {v.get('dose') or '-'}", size=11, color=MID),
                                ft.Container(width=16),
                                ft.Text(f"วันที่ฉีด: {v.get('vaccine_date') or '-'}", size=11, color=MID),
                            ]),
                            ft.Row([
                                ft.Text(f"ครั้งถัดไป: {next_due_str or '-'}", size=11, color=ORANGE if next_due_str else MID),
                                ft.Container(width=16),
                                ft.Text(f"คลินิก: {v.get('clinic') or '-'}", size=11, color=MID),
                            ]),
                            *(
                                [ft.Text(f"หมายเหตุ: {v.get('note')}", size=11, color=LIGHT)]
                                if v.get("note") else []
                            ),
                        ], spacing=4),
                    ))
            page.update()

        def open_add_vaccine(e):
            fs = field_style()
            tf_name = ft.TextField(label="ชื่อวัคซีน *", **fs)
            tf_dose = ft.TextField(label="โดส (เช่น ครั้งที่ 1)", **fs)
            tf_date = ft.TextField(label="วันที่ฉีด (YYYY-MM-DD)", **fs)
            tf_next = ft.TextField(label="ครั้งถัดไป (YYYY-MM-DD)", **fs)
            tf_clinic = ft.TextField(label="คลินิก/โรงพยาบาล", **fs)
            tf_note = ft.TextField(label="หมายเหตุ", multiline=True, min_lines=2, **fs)
            st = ft.Text("", size=12)

            def submit(ev):
                if not tf_name.value.strip():
                    st.value = "⚠️ กรุณากรอกชื่อวัคซีน"
                    page.update()
                    return
                st.value = "⏳ กำลังบันทึก..."
                page.update()
                try:
                    res = requests.post(VACCINES_URL, json={
                        "pet_id": pid,
                        "vaccine_name": tf_name.value.strip(),
                        "dose": tf_dose.value.strip() or None,
                        "vaccine_date": tf_date.value.strip() or None,
                        "next_due": tf_next.value.strip() or None,
                        "clinic": tf_clinic.value.strip() or None,
                        "note": tf_note.value.strip() or None,
                    }, timeout=5)
                    if res.status_code in (200, 201):
                        adlg.open = False
                        page.update()
                        load_vaccines()
                    else:
                        st.value = f"❌ Error {res.status_code}"
                        page.update()
                except Exception:
                    st.value = "❌ เชื่อมต่อไม่ได้"
                    page.update()

            adlg = ft.AlertDialog(
                modal=True, bgcolor=BG,
                shape=ft.RoundedRectangleBorder(radius=12),
                inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
                title=ft.Text("เพิ่มวัคซีน", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                content=ft.Container(
                    width=min(page.width - 48, 400),
                    content=ft.Column([tf_name, tf_dose, tf_date, tf_next, tf_clinic, tf_note, st], spacing=10, tight=True),
                ),
                actions=[
                    ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                  on_click=lambda e: (setattr(adlg, "open", False), page.update())),
                    btn("บันทึก", submit, height=38, radius=6),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(adlg)
            adlg.open = True
            page.update()

        load_vaccines()
        extra = [btn("+ วัคซีน", open_add_vaccine, height=34, radius=6)] if is_admin else []
        page.views.append(ft.View(
            route=f"/vaccines/{pid}",
            bgcolor=BG2, padding=0,
            controls=[ft.Column(expand=True, spacing=0, controls=[
                back_bar(page, f"วัคซีน — {pet_name}", extra_actions=extra),
                ft.Container(expand=True, padding=ft.padding.all(16),
                             content=ft.Column(controls=[vac_list], scroll=ft.ScrollMode.AUTO, expand=True)),
            ])],
        ))
        page.update()

    # ══════════════════════════════════════════════════════════════
    # ── RECORDS PAGE ──────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════
    def show_records_page(pet: dict, on_updated=None):
        pid = pet.get("id")
        pet_name = pet.get("name", "?")
        rec_list = ft.Column(spacing=8)

        def load_records():
            rec_list.controls.clear()
            try:
                r = requests.get(RECORDS_URL, timeout=5)
                recs = [x for x in r.json() if x.get("pet_id") == pid]
            except Exception:
                recs = []
            if not recs:
                rec_list.controls.append(ft.Container(
                    padding=ft.padding.symmetric(vertical=32),
                    content=ft.Column([
                        ft.Icon(ft.Icons.ARTICLE_OUTLINED, size=48, color=LIGHT),
                        ft.Text("ยังไม่มีบันทึก", size=13, color=LIGHT),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ))
            else:
                for rec in recs:
                    rtype = rec.get("record_type", "")
                    chip_color = GREEN if rtype == "health" else ORANGE if rtype == "grooming" else BLUE

                    def make_delete(rid):
                        def do(e):
                            try:
                                requests.delete(f"{RECORDS_URL}/{rid}", timeout=5)
                            except Exception:
                                pass
                            load_records()
                            if on_updated:
                                on_updated()
                            page.update()
                        return do

                    def make_edit(rec_data):
                        def do(e):
                            fs = field_style()
                            tf_type = ft.Dropdown(
                                label="ประเภท *", value=rec_data.get("record_type", ""),
                                options=[ft.dropdown.Option("health", "สุขภาพ"),
                                         ft.dropdown.Option("grooming", "ดูแลขน"),
                                         ft.dropdown.Option("other", "อื่นๆ")],
                                border_color=BORDER, focused_border_color=PRIMARY, border_radius=6,
                                bgcolor=BG2, label_style=ft.TextStyle(color=LIGHT, size=12),
                                text_style=ft.TextStyle(size=13, color=DARK),
                            )
                            tf_title = ft.TextField(label="หัวข้อ *", value=rec_data.get("title", ""), **fs)
                            tf_desc = ft.TextField(label="รายละเอียด", value=rec_data.get("description", "") or "", multiline=True, min_lines=2, **fs)
                            tf_date = ft.TextField(label="วันที่ (YYYY-MM-DD)", value=rec_data.get("record_date", "") or "", **fs)
                            st = ft.Text("", size=12)

                            def submit_edit(ev):
                                if not tf_title.value.strip() or not tf_type.value:
                                    st.value = "⚠️ กรุณากรอกข้อมูลให้ครบ"
                                    page.update()
                                    return
                                try:
                                    res = requests.put(f"{RECORDS_URL}/{rec_data['id']}", json={
                                        "pet_id": pid, "record_type": tf_type.value,
                                        "title": tf_title.value.strip(),
                                        "description": tf_desc.value.strip() or None,
                                        "record_date": tf_date.value.strip() or None,
                                    }, timeout=5)
                                    if res.status_code == 200:
                                        edit_dlg.open = False
                                        page.update()
                                        load_records()
                                        if on_updated:
                                            on_updated()
                                    else:
                                        st.value = f"❌ Error {res.status_code}"
                                        page.update()
                                except Exception:
                                    st.value = "❌ เชื่อมต่อไม่ได้"
                                    page.update()

                            edit_dlg = ft.AlertDialog(
                                modal=True, bgcolor=BG,
                                shape=ft.RoundedRectangleBorder(radius=12),
                                inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
                                title=ft.Text("แก้ไขบันทึก", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                                content=ft.Container(
                                    width=min(page.width - 48, 400),
                                    content=ft.Column([tf_type, tf_title, tf_desc, tf_date, st], spacing=10, tight=True),
                                ),
                                actions=[
                                    ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                                  on_click=lambda e: (setattr(edit_dlg, "open", False), page.update())),
                                    btn("บันทึก", submit_edit, height=38, radius=6),
                                ],
                                actions_alignment=ft.MainAxisAlignment.END,
                            )
                            page.overlay.append(edit_dlg)
                            edit_dlg.open = True
                            page.update()
                        return do

                    def make_detail(rd):
                        def show_detail(e):
                            rtype_d = rd.get("record_type", "")
                            chip_color_d = GREEN if rtype_d == "health" else ORANGE if rtype_d == "grooming" else BLUE
                            detail_dlg = ft.AlertDialog(
                                modal=True, bgcolor=BG,
                                shape=ft.RoundedRectangleBorder(radius=12),
                                inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
                                title=ft.Row([
                                    ft.Container(width=4, height=18, border_radius=2, bgcolor=chip_color_d),
                                    ft.Container(width=8),
                                    ft.Text(rd.get("title", ""), size=15, weight=ft.FontWeight.BOLD, color=DARK, expand=True),
                                ]),
                                content=ft.Container(
                                    width=min(page.width - 48, 400),
                                    content=ft.Column([
                                        info_chip(rtype_d, chip_color_d),
                                        ft.Container(height=8),
                                        ft.Row([
                                            ft.Icon(ft.Icons.CALENDAR_TODAY_OUTLINED, color=LIGHT, size=15),
                                            ft.Container(width=6),
                                            ft.Text(rd.get("record_date", "") or "-", size=13, color=MID),
                                        ]),
                                        ft.Container(height=8),
                                        ft.Text("รายละเอียด", size=12, color=LIGHT, weight=ft.FontWeight.BOLD),
                                        ft.Container(height=4),
                                        ft.Text(
                                            rd.get("description") or "ไม่มีรายละเอียดเพิ่มเติม",
                                            size=13, color=DARK if rd.get("description") else LIGHT,
                                        ),
                                    ], spacing=4, tight=True),
                                ),
                                actions=[
                                    ft.TextButton("ปิด", style=ft.ButtonStyle(color=LIGHT),
                                                  on_click=lambda e: (setattr(detail_dlg, "open", False), page.update())),
                                ],
                                actions_alignment=ft.MainAxisAlignment.END,
                            )
                            page.overlay.append(detail_dlg)
                            detail_dlg.open = True
                            page.update()
                        return show_detail

                    rec_list.controls.append(ft.GestureDetector(
                        on_tap=make_detail(rec),
                        content=ft.Container(
                            border_radius=10, bgcolor=BG, border=ft.border.all(1, BORDER),
                            padding=ft.padding.all(12),
                            content=ft.Row([
                                ft.Container(width=3, height=40, border_radius=3, bgcolor=chip_color),
                                ft.Container(width=8),
                                ft.Column([
                                    ft.Text(rec.get("title", ""), size=13, weight=ft.FontWeight.BOLD, color=DARK),
                                    ft.Text(rec.get("record_date", "") or rtype, size=11, color=LIGHT),
                                ], spacing=2, expand=True),
                                info_chip(rtype, chip_color),
                                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=LIGHT, size=16),
                                ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color=PRIMARY, icon_size=18, on_click=make_edit(rec)),
                                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=RED, icon_size=18, on_click=make_delete(rec.get("id"))),
                            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ),
                    ))
            page.update()

        def open_add_record(e):
            fs = field_style()
            tf_type = ft.Dropdown(
                label="ประเภท *",
                options=[ft.dropdown.Option("health", "🩺 สุขภาพ"),
                         ft.dropdown.Option("grooming", "✂️ ดูแลขน"),
                         ft.dropdown.Option("other", "📝 อื่นๆ")],
                border_color=BORDER, focused_border_color=PRIMARY, border_radius=6,
                bgcolor=BG2, label_style=ft.TextStyle(color=LIGHT, size=12),
                text_style=ft.TextStyle(size=13, color=DARK),
            )
            tf_title = ft.TextField(label="หัวข้อ *", **fs)
            tf_desc = ft.TextField(label="รายละเอียด", multiline=True, min_lines=2, **fs)
            tf_date = ft.TextField(label="วันที่ (YYYY-MM-DD)", **fs)
            st = ft.Text("", size=12)

            def submit(ev):
                if not tf_title.value.strip() or not tf_type.value:
                    st.value = "⚠️ กรุณากรอกประเภทและหัวข้อ"
                    page.update()
                    return
                try:
                    res = requests.post(RECORDS_URL, json={
                        "pet_id": pid, "record_type": tf_type.value,
                        "title": tf_title.value.strip(),
                        "description": tf_desc.value.strip() or None,
                        "record_date": tf_date.value.strip() or None,
                    }, timeout=5)
                    if res.status_code in (200, 201):
                        adlg.open = False
                        page.update()
                        load_records()
                        if on_updated:
                            on_updated()
                    else:
                        st.value = f"❌ Error {res.status_code}"
                        page.update()
                except Exception:
                    st.value = "❌ เชื่อมต่อไม่ได้"
                    page.update()

            adlg = ft.AlertDialog(
                modal=True, bgcolor=BG,
                shape=ft.RoundedRectangleBorder(radius=12),
                inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
                title=ft.Text("เพิ่มบันทึก", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                content=ft.Container(
                    width=min(page.width - 48, 400),
                    content=ft.Column([tf_type, tf_title, tf_desc, tf_date, st], spacing=10, tight=True),
                ),
                actions=[
                    ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                  on_click=lambda e: (setattr(adlg, "open", False), page.update())),
                    btn("บันทึก", submit, height=38, radius=6),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(adlg)
            adlg.open = True
            page.update()

        load_records()
        page.views.append(ft.View(
            route=f"/records/{pid}", bgcolor=BG2, padding=0,
            controls=[ft.Column(expand=True, spacing=0, controls=[
                back_bar(page, f"บันทึก — {pet_name}",
                         extra_actions=[btn("+ เพิ่ม", open_add_record, height=34, radius=6)]),
                ft.Container(expand=True, padding=ft.padding.all(16),
                             content=ft.Column(controls=[rec_list], scroll=ft.ScrollMode.AUTO, expand=True)),
            ])],
        ))
        page.update()

    # ══════════════════════════════════════════════════════════════
    # ── PET DETAIL ────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════
    def show_pet_detail(pet: dict, idx: int):
        is_admin = (state["user"] or {}).get("role") == "admin"
        owner_id = (state["user"] or {}).get("id", 1)
        color = pet_color(idx)
        icon_txt = pet_icon(pet.get("type", ""))

        pet_name_txt = ft.Text(pet.get("name", ""), size=20, weight=ft.FontWeight.BOLD, color=DARK, text_align="center")
        type_chip_w = ft.Container(
            padding=ft.padding.symmetric(horizontal=8, vertical=3), border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.12, color),
            content=ft.Text(pet.get("type", "").capitalize(), size=11, color=color, weight=ft.FontWeight.BOLD),
        )
        age_chip_w = ft.Container(
            padding=ft.padding.symmetric(horizontal=8, vertical=3), border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.12, MID),
            content=ft.Text(f"อายุ {pet.get('age', 0)} ปี", size=11, color=MID, weight=ft.FontWeight.BOLD),
        )
        vaccine_txt_w = ft.Text(pet.get("vaccine", "") or "-", size=13, color=DARK, weight=ft.FontWeight.W_500, expand=True)
        recent_rec_col = ft.Column(spacing=6)

        def load_recent_records():
            recent_rec_col.controls.clear()
            try:
                r = requests.get(RECORDS_URL, timeout=5)
                recs = [x for x in r.json() if x.get("pet_id") == pet.get("id")]
                recs = recs[-3:]
            except Exception:
                recs = []
            if not recs:
                recent_rec_col.controls.append(ft.Text("ยังไม่มีบันทึก", size=12, color=LIGHT))
            else:
                for rec in recs:
                    rtype = rec.get("record_type", "")
                    chip_color = GREEN if rtype == "health" else ORANGE if rtype == "grooming" else BLUE
                    recent_rec_col.controls.append(ft.Container(
                        border_radius=8, bgcolor=BG2, border=ft.border.all(1, BORDER),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        content=ft.Row([
                            ft.Container(width=3, height=36, border_radius=3, bgcolor=chip_color),
                            ft.Container(width=8),
                            ft.Column([
                                ft.Text(rec.get("title", ""), size=12, weight=ft.FontWeight.BOLD, color=DARK),
                                ft.Text(rec.get("record_date", "") or rtype, size=10, color=LIGHT),
                            ], spacing=1, expand=True),
                            info_chip(rtype, chip_color),
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ))
            page.update()

        def open_edit(e):
            fs = field_style()
            tf_name = ft.TextField(label="ชื่อสัตว์เลี้ยง *", value=pet.get("name", ""), **fs)
            tf_type = ft.Dropdown(
                label="ประเภท *", value=pet.get("type", ""),
                options=[ft.dropdown.Option("dog", "🐶 Dog"), ft.dropdown.Option("cat", "🐱 Cat"),
                         ft.dropdown.Option("bird", "🐦 Bird"), ft.dropdown.Option("rabbit", "🐰 Rabbit"),
                         ft.dropdown.Option("fish", "🐠 Fish"), ft.dropdown.Option("hamster", "🐹 Hamster")],
                border_color=BORDER, focused_border_color=PRIMARY, border_radius=6,
                bgcolor=BG2, label_style=ft.TextStyle(color=LIGHT, size=12), text_style=ft.TextStyle(size=13, color=DARK),
            )
            tf_age = ft.TextField(label="อายุ (ปี) *", value=str(pet.get("age", "")), keyboard_type=ft.KeyboardType.NUMBER, **fs)
            tf_img = ft.TextField(label="ลิ้งรูปภาพ (URL)", value=pet.get("image_url", "") or "", **fs)
            tf_vaccine = ft.TextField(label="วัคซีน (เช่น rabies, DHPP ...)", value=pet.get("vaccine", "") or "", **fs)
            st = ft.Text("", size=12, color=LIGHT)

            def submit(ev):
                if not tf_name.value.strip() or not tf_type.value:
                    st.value = "⚠️ กรุณากรอกชื่อและประเภท"
                    st.color = PRIMARY
                    page.update()
                    return
                try:
                    age_v = int(tf_age.value.strip())
                except ValueError:
                    st.value = "⚠️ อายุต้องเป็นตัวเลข"
                    page.update()
                    return
                try:
                    res = requests.put(f"{PETS_URL}/{pet['id']}", json={
                        "user_id": owner_id, "name": tf_name.value.strip(), "type": tf_type.value,
                        "age": age_v, "image_url": tf_img.value.strip() or None,
                        "vaccine": tf_vaccine.value.strip() or None,
                    }, timeout=5)
                    if res.status_code == 200:
                        pet.update({"name": tf_name.value.strip(), "type": tf_type.value, "age": age_v,
                                    "image_url": tf_img.value.strip() or None, "vaccine": tf_vaccine.value.strip() or None})
                        pet_name_txt.value = pet["name"]
                        type_chip_w.content.value = pet["type"].capitalize()
                        age_chip_w.content.value = f"อายุ {pet['age']} ปี"
                        vaccine_txt_w.value = pet["vaccine"] or "-"
                        dlg.open = False
                        page.update()
                        load_all_pets()
                    else:
                        st.value = f"❌ Error {res.status_code}"
                        page.update()
                except Exception:
                    st.value = "❌ เชื่อมต่อไม่ได้"
                    page.update()

            dlg = ft.AlertDialog(
                modal=True, bgcolor=BG, shape=ft.RoundedRectangleBorder(radius=12),
                inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
                title=ft.Text("แก้ไขข้อมูลสัตว์เลี้ยง", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                content=ft.Container(width=min(page.width - 48, 400),
                                     content=ft.Column([tf_name, tf_type, tf_age, tf_img, tf_vaccine, st], spacing=10, tight=True)),
                actions=[ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                       on_click=lambda e: (setattr(dlg, "open", False), page.update())),
                         btn("บันทึก", submit, height=38, radius=6)],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(dlg)
            dlg.open = True
            page.update()

        def confirm_delete(e):
            def do_delete(ev):
                try:
                    requests.delete(f"{PETS_URL}/{pet['id']}", timeout=5)
                except Exception:
                    pass
                conf.open = False
                page.update()
                page.views.pop()
                page.update()
                load_all_pets()

            conf = ft.AlertDialog(
                modal=True, bgcolor=BG, shape=ft.RoundedRectangleBorder(radius=12),
                inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
                title=ft.Text("ยืนยันการลบ", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                content=ft.Text(f"ต้องการลบ \"{pet.get('name', '')}\" ใช่หรือไม่?", size=13, color=MID),
                actions=[ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                       on_click=lambda e: (setattr(conf, "open", False), page.update())),
                         btn("ลบ", do_delete, height=38, radius=6)],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(conf)
            conf.open = True
            page.update()

        img_url = pet.get("image_url", "") or ""
        cover_w = (
            ft.Container(width=110, height=110, border_radius=55, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                         content=ft.Image(src=img_url, width=110, height=110, fit="cover",
                                          error_content=ft.Text(icon_txt, size=40, text_align="center")))
            if img_url.strip() else
            ft.Container(width=110, height=110, border_radius=55, bgcolor=color,
                         content=ft.Text(icon_txt, size=48, text_align="center"),
                         alignment=ft.alignment.Alignment(0, 0))
        )

        load_recent_records()

        # Quick action buttons for detail page
        action_btns = [
            btn("📋 บันทึก", lambda e: show_records_page(pet, on_updated=load_recent_records), height=38, radius=8,
                bgcolor=BG2, text_color=DARK, expand=True),
            ft.Container(width=8),
            btn("💉 วัคซีน", lambda e: show_vaccines_page(pet, is_admin), height=38, radius=8,
                bgcolor=BG2, text_color=DARK, expand=True),
        ]
        if not is_admin:
            action_btns += [
                ft.Container(width=8),
                btn("🏨 จอง", lambda e: show_booking_page(pet), height=38, radius=8,
                    bgcolor=PRIMARY, text_color=DARK, expand=True),
            ]
        else:
            action_btns += [
                ft.Container(width=8),
                btn("📅 การจอง", lambda e: show_admin_pet_bookings_page(pet), height=38, radius=8,
                    bgcolor=PRIMARY, text_color=DARK, expand=True),
            ]

        extra_actions_bar = []
        if is_admin:
            extra_actions_bar = [
                btn("✏️", open_edit, height=34, radius=6, bgcolor=BG2, text_color=DARK),
                ft.Container(width=6),
                btn("🗑️", confirm_delete, height=34, radius=6, bgcolor="#FFEBEE", text_color=RED),
            ]

        page.views.append(ft.View(
            route=f"/pet/{pet.get('id')}", bgcolor=BG2, padding=0,
            controls=[ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=0, controls=[
                back_bar(page, "รายละเอียดสัตว์เลี้ยง", extra_actions=extra_actions_bar),
                ft.Container(
                    bgcolor=BG, margin=ft.margin.symmetric(horizontal=16, vertical=16),
                    border_radius=16, border=ft.border.all(1, BORDER),
                    padding=ft.padding.all(20),
                    content=ft.Column([
                        ft.Row([cover_w], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Container(height=12),
                        ft.Row([pet_name_txt], alignment=ft.MainAxisAlignment.CENTER),
                        ft.Container(height=8),
                        ft.Row([type_chip_w, ft.Container(width=6), age_chip_w],
                               alignment=ft.MainAxisAlignment.CENTER),
                        ft.Divider(height=20, color=BORDER),
                        _profile_row_widget(ft.Icons.VACCINES_OUTLINED, "วัคซีน", vaccine_txt_w),
                        ft.Divider(height=20, color=BORDER),
                        ft.Row(action_btns, expand=True),
                    ], spacing=0),
                ),
                ft.Container(
                    margin=ft.margin.symmetric(horizontal=16),
                    padding=ft.padding.all(16),
                    bgcolor=BG, border_radius=14, border=ft.border.all(1, BORDER),
                    content=ft.Column([
                        ft.Row([
                            ft.Text("บันทึกล่าสุด", size=14, weight=ft.FontWeight.BOLD, color=DARK, expand=True),
                            ft.GestureDetector(
                                on_tap=lambda e: show_records_page(pet, on_updated=load_recent_records),
                                content=ft.Text("ดูทั้งหมด →", size=12, color=PRIMARY),
                            ),
                        ]),
                        ft.Container(height=8),
                        recent_rec_col,
                    ], spacing=0),
                ),
                ft.Container(height=32),
            ])],
        ))
        page.update()

    # ══════════════════════════════════════════════════════════════
    # ── PAYMENT PAGE ──────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════
    def show_payment_page(booking_id: int, pet: dict, check_in: str, check_out: str, total_price: float):
        fs = field_style()
        slip_url_tf = ft.TextField(
            label="ลิ้งสลิปการโอนเงิน (URL) *",
            hint_text="https://i.imgur.com/... หรือ URL รูปสลิป",
            prefix_icon=ft.Icons.LINK,
            **fs,
        )

        # preview container — อัปเดตเมื่อกด "ดูตัวอย่าง"
        preview_box = ft.Container(
            border_radius=10,
            border=ft.border.all(1, BORDER),
            bgcolor=BG2,
            padding=ft.padding.all(14),
            content=ft.Column([
                ft.Icon(ft.Icons.IMAGE_OUTLINED, color=LIGHT, size=32),
                ft.Text("กรอก URL แล้วกด 'ดูตัวอย่าง'", size=11, color=LIGHT),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
        )

        def preview_slip(e):
            url = slip_url_tf.value.strip()
            if not url:
                preview_box.content = ft.Column([
                    ft.Icon(ft.Icons.IMAGE_OUTLINED, color=LIGHT, size=32),
                    ft.Text("กรุณากรอก URL ก่อน", size=11, color=PRIMARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)
            else:
                preview_box.content = ft.Column([
                    ft.Image(src=url, width=220, height=220, fit="contain",
                             border_radius=8,
                             error_content=ft.Column([
                                 ft.Icon(ft.Icons.BROKEN_IMAGE_OUTLINED, color=LIGHT, size=32),
                                 ft.Text("โหลดรูปไม่ได้ — แต่ URL จะถูกบันทึกไว้", size=10, color=LIGHT),
                             ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)),
                    ft.Text("✅ URL บันทึกแล้ว", size=11, color=GREEN, weight=ft.FontWeight.BOLD),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)
            page.update()

        st = ft.Text("", size=13, color=MID)

        def submit_payment(e):
            slip = slip_url_tf.value.strip()
            if not slip:
                st.value = "⚠️ กรุณากรอก URL สลิปก่อน"
                st.color = PRIMARY
                page.update()
                return
            st.value = "⏳ กำลังส่งข้อมูล..."
            st.color = LIGHT
            page.update()
            try:
                res = requests.put(f"{BOOKINGS_URL}/{booking_id}/payment", json={
                    "payment_slip": slip,
                    "payment_status": "paid",
                }, timeout=5)
                if res.status_code == 200:
                    st.value = "✅ ส่งสลิปสำเร็จ! รอแอดมินอนุมัติ"
                    st.color = GREEN
                    page.update()
                    time.sleep(1.2)
                    page.views.clear()
                    page.views.append(home_view)
                    page.update()
                    load_all_pets()
                else:
                    st.value = f"❌ Error {res.status_code}"
                    st.color = RED
                    page.update()
            except Exception:
                st.value = "❌ เชื่อมต่อไม่ได้"
                st.color = RED
                page.update()

        page.views.append(ft.View(
            route="/payment", bgcolor=BG2, padding=0,
            controls=[ft.Column(expand=True, spacing=0, controls=[
                back_bar(page, "ชำระเงิน"),
                ft.Container(expand=True, padding=ft.padding.all(20),
                             content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=16, controls=[
                                 # summary card
                                 ft.Container(
                                     bgcolor=BG, border_radius=14, border=ft.border.all(1, BORDER),
                                     padding=ft.padding.all(20),
                                     content=ft.Column([
                                         ft.Text("สรุปการจอง", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                                         ft.Container(height=12),
                                         _profile_row(ft.Icons.PETS, "สัตว์เลี้ยง", pet.get("name", "")),
                                         ft.Divider(height=1, color=BORDER),
                                         _profile_row(ft.Icons.CALENDAR_TODAY_OUTLINED, "เช็คอิน", check_in),
                                         ft.Divider(height=1, color=BORDER),
                                         _profile_row(ft.Icons.CALENDAR_MONTH_OUTLINED, "เช็คเอาท์", check_out),
                                         ft.Divider(height=1, color=BORDER),
                                         ft.Container(
                                             padding=ft.padding.symmetric(vertical=10),
                                             content=ft.Row([
                                                 ft.Icon(ft.Icons.ATTACH_MONEY, color=LIGHT, size=18),
                                                 ft.Container(width=12),
                                                 ft.Text("ยอดรวม", size=12, color=LIGHT, width=60),
                                                 ft.Text(f"{total_price:.0f} บาท", size=16,
                                                         weight=ft.FontWeight.BOLD, color=GREEN),
                                             ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                         ),
                                     ], spacing=0),
                                 ),
                                 # payment info
                                 ft.Container(
                                     bgcolor=BG, border_radius=14, border=ft.border.all(1, BORDER),
                                     padding=ft.padding.all(20),
                                     content=ft.Column([
                                         ft.Text("ข้อมูลการชำระเงิน", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                                         ft.Container(height=12),
                                         ft.Container(
                                             bgcolor=ft.Colors.with_opacity(0.08, PRIMARY),
                                             border_radius=10,
                                             border=ft.border.all(1, ft.Colors.with_opacity(0.2, PRIMARY)),
                                             padding=ft.padding.all(16),
                                             content=ft.Column([
                                                 ft.Row([ft.Icon(ft.Icons.QR_CODE_2, color=PRIMARY, size=20),
                                                         ft.Container(width=8),
                                                         ft.Text("โอนผ่าน PromptPay / QR Code", size=13, color=DARK, weight=ft.FontWeight.BOLD)]),
                                                 ft.Container(height=8),
                                                 ft.Text("เลขบัญชี: 0xx-xxx-xxxx", size=13, color=MID),
                                                 ft.Text("ชื่อ: จุ้มปุ๊ค Pet Hotel", size=13, color=MID),
                                             ], spacing=4),
                                         ),
                                         ft.Container(height=16),
                                         ft.Text("แนบสลิปการโอนเงิน *", size=13, weight=ft.FontWeight.BOLD, color=DARK),
                                         ft.Container(height=4),
                                         ft.Text("อัปโหลดรูปสลิปไปที่ imgur.com หรือ imgbb.com แล้วนำ URL มากรอก",
                                                  size=11, color=LIGHT),
                                         ft.Container(height=8),
                                         slip_url_tf,
                                         ft.Container(height=8),
                                         btn("🔍 ดูตัวอย่างสลิป", preview_slip, height=40, radius=8,
                                             bgcolor=BG2, text_color=DARK, expand=True),
                                         ft.Container(height=8),
                                         preview_box,
                                         ft.Container(height=4),
                                         st,
                                     ], spacing=0),
                                 ),
                                 btn("✅ ยืนยันการชำระเงิน", submit_payment, height=50, radius=12, expand=True),
                             ])),
            ])],
        ))
        page.update()

    # ══════════════════════════════════════════════════════════════
    # ── BOOKING PAGE (user) ───────────────────────────────────────
    # ══════════════════════════════════════════════════════════════
    def show_booking_page(pet: dict):
        user_id = (state["user"] or {}).get("id", 1)
        fs = field_style()
        tf_checkin = ft.TextField(label="วันเช็คอิน (YYYY-MM-DD) *", **fs)
        tf_checkout = ft.TextField(label="วันเช็คเอาท์ (YYYY-MM-DD) *", **fs)
        tf_note = ft.TextField(label="หมายเหตุ (เช่น อาหารพิเศษ, ยา)", multiline=True, min_lines=2, **fs)
        tf_price = ft.TextField(label="ราคาโดยประมาณ (บาท)", value="500",
                                keyboard_type=ft.KeyboardType.NUMBER, **fs)
        st = ft.Text("", size=13)

        def submit_booking(e):
            ci = tf_checkin.value.strip()
            co = tf_checkout.value.strip()
            if not ci or not co:
                st.value = "⚠️ กรุณากรอกวันเช็คอินและเช็คเอาท์"
                st.color = PRIMARY
                page.update()
                return
            try:
                price = float(tf_price.value.strip() or "0")
            except ValueError:
                price = 0.0
            st.value = "⏳ กำลังสร้างการจอง..."
            st.color = LIGHT
            page.update()
            try:
                res = requests.post(BOOKINGS_URL, json={
                    "user_id": user_id, "pet_id": pet["id"],
                    "check_in": ci, "check_out": co,
                    "note": tf_note.value.strip() or None,
                    "total_price": price,
                    "payment_status": "unpaid",
                }, timeout=10)
                if res.status_code in (200, 201):
                    bid = res.json().get("id")
                    st.value = "✅ สร้างการจองสำเร็จ! ไปชำระเงิน..."
                    st.color = GREEN
                    page.update()
                    time.sleep(0.8)
                    show_payment_page(bid, pet, ci, co, price)
                else:
                    st.value = f"❌ Error {res.status_code}: {res.text[:60]}"
                    st.color = RED
                    page.update()
            except requests.exceptions.ConnectionError:
                st.value = f"❌ เชื่อมต่อไม่ได้ — ตรวจสอบ IP: {SERVER_IP}:{SERVER_PORT}"
                st.color = RED
                page.update()
            except requests.exceptions.Timeout:
                st.value = "❌ Server ตอบสนองช้าเกินไป (timeout)"
                st.color = RED
                page.update()
            except Exception as ex:
                st.value = f"❌ {type(ex).__name__}: {str(ex)[:50]}"
                st.color = RED
                page.update()

        page.views.append(ft.View(
            route="/booking", bgcolor=BG2, padding=0,
            controls=[ft.Column(expand=True, spacing=0, controls=[
                back_bar(page, f"จองรับฝาก — {pet.get('name', '')}"),
                ft.Container(expand=True, padding=ft.padding.all(20),
                             content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=16, controls=[
                                 ft.Container(
                                     bgcolor=BG, border_radius=14, border=ft.border.all(1, BORDER),
                                     padding=ft.padding.all(20),
                                     content=ft.Column([
                                         ft.Text("ข้อมูลการจอง", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                                         ft.Container(height=12),
                                         ft.Row([
                                             ft.Container(
                                                 width=48, height=48, border_radius=24,
                                                 bgcolor=pet_color(0),
                                                 alignment=ft.alignment.Alignment(0, 0),
                                                 content=ft.Text(pet_icon(pet.get("type", "")), size=22),
                                             ),
                                             ft.Container(width=12),
                                             ft.Column([
                                                 ft.Text(pet.get("name", ""), size=14, weight=ft.FontWeight.BOLD, color=DARK),
                                                 ft.Text(pet.get("type", "").capitalize(), size=12, color=MID),
                                             ], spacing=2),
                                         ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                         ft.Container(height=16),
                                         tf_checkin,
                                         ft.Container(height=10),
                                         tf_checkout,
                                         ft.Container(height=10),
                                         tf_price,
                                         ft.Container(height=10),
                                         tf_note,
                                         ft.Container(height=4),
                                         st,
                                     ], spacing=0),
                                 ),
                                 btn("ถัดไป → ชำระเงิน", submit_booking, height=50, radius=12, expand=True),
                             ])),
            ])],
        ))
        page.update()

    # ══════════════════════════════════════════════════════════════
    # ── MY BOOKINGS PAGE (user) ───────────────────────────────────
    # ══════════════════════════════════════════════════════════════
    def show_my_bookings_page(e=None):
        user_id = (state["user"] or {}).get("id", 1)
        book_list = ft.Column(spacing=10)

        def load_bookings():
            book_list.controls.clear()
            try:
                r = requests.get(f"{BOOKINGS_URL}/user/{user_id}", timeout=5)
                books = r.json() if r.status_code == 200 else []
            except Exception:
                books = []
            if not books:
                book_list.controls.append(ft.Container(
                    padding=ft.padding.symmetric(vertical=40),
                    content=ft.Column([
                        ft.Icon(ft.Icons.HOTEL_OUTLINED, size=48, color=LIGHT),
                        ft.Text("ยังไม่มีประวัติการจอง", size=14, color=LIGHT),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                ))
            else:
                for b in books:
                    s_label, s_color = STATUS_LABEL.get(b.get("status", ""), (b.get("status", ""), MID))
                    is_unpaid = b.get("payment_status") != "paid"
                    has_slip = bool(b.get("payment_slip"))

                    def make_pay_action(bdata):
                        def go_pay(e):
                            # Re-open payment page for this booking
                            dummy_pet = {"name": bdata.get("pet_name", ""), "type": bdata.get("pet_type", "")}
                            show_payment_page(
                                bdata.get("id"), dummy_pet,
                                bdata.get("check_in", ""), bdata.get("check_out", ""),
                                float(bdata.get("total_price", 0)),
                            )
                        return go_pay

                    def make_cancel_action(bdata):
                        def do_cancel(e):
                            def confirm_cancel(ce):
                                cdlg.open = False
                                page.update()
                                try:
                                    requests.put(f"{BOOKINGS_URL}/{bdata.get('id')}/status",
                                                 json={"status": "rejected"}, timeout=5)
                                except Exception:
                                    pass
                                load_bookings()
                                page.update()

                            cdlg = ft.AlertDialog(
                                modal=True, bgcolor=BG, shape=ft.RoundedRectangleBorder(radius=12),
                                inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
                                title=ft.Text("ยืนยันการยกเลิก", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                                content=ft.Text(
                                    f"ต้องการยกเลิกการจอง \"{bdata.get('pet_name', '')}\" "
                                    f"({bdata.get('check_in', '')} → {bdata.get('check_out', '')}) ใช่ไหม?",
                                    size=13, color=MID,
                                ),
                                actions=[
                                    ft.TextButton("ไม่ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                                  on_click=lambda ev: (setattr(cdlg, "open", False), page.update())),
                                    ft.TextButton("ยืนยันยกเลิก", style=ft.ButtonStyle(color=RED),
                                                  on_click=confirm_cancel),
                                ],
                                actions_alignment=ft.MainAxisAlignment.END,
                            )
                            page.overlay.append(cdlg)
                            cdlg.open = True
                            page.update()
                        return do_cancel

                    can_cancel = b.get("status") in ("pending", "approved")

                    book_list.controls.append(ft.Container(
                        bgcolor=BG, border_radius=12, border=ft.border.all(1, BORDER),
                        padding=ft.padding.all(14),
                        content=ft.Column([
                            ft.Row([
                                ft.Text(b.get("pet_name", "สัตว์เลี้ยง"), size=14, weight=ft.FontWeight.BOLD, color=DARK, expand=True),
                                info_chip(s_label, s_color),
                            ]),
                            ft.Container(height=6),
                            ft.Row([
                                ft.Icon(ft.Icons.CALENDAR_TODAY_OUTLINED, size=14, color=LIGHT),
                                ft.Container(width=4),
                                ft.Text(f"{b.get('check_in', '')} → {b.get('check_out', '')}", size=12, color=MID),
                            ]),
                            ft.Row([
                                ft.Icon(ft.Icons.ATTACH_MONEY, size=14, color=LIGHT),
                                ft.Container(width=4),
                                ft.Text(f"{b.get('total_price', 0):.0f} บาท", size=12, color=MID),
                                ft.Container(expand=True),
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                    border_radius=8,
                                    bgcolor=ft.Colors.with_opacity(0.1, GREEN if not is_unpaid else ORANGE),
                                    content=ft.Text(
                                        "ชำระแล้ว" if not is_unpaid else "ยังไม่ชำระ",
                                        size=11, color=GREEN if not is_unpaid else ORANGE,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ),
                            ]),
                            *(
                                [ft.Container(height=4), ft.Text(f"หมายเหตุ: {b.get('note')}", size=11, color=LIGHT)]
                                if b.get("note") else []
                            ),
                            *(
                                [ft.Container(height=4),
                                 ft.Text(f"📎 สลิป: {b.get('payment_slip', '')[:40]}...", size=10, color=MID)]
                                if has_slip else []
                            ),
                            # ── ปุ่มชำระเงินถ้ายังไม่จ่าย ──
                            *(
                                [ft.Container(height=8),
                                 btn("💳 ชำระเงิน / แนบสลิป", make_pay_action(b),
                                     height=36, radius=8, bgcolor=PRIMARY, text_color=DARK, expand=True)]
                                if is_unpaid and b.get("status") not in ("rejected", "completed") else []
                            ),
                            # ── ปุ่มยกเลิกการจอง ──
                            *(
                                [ft.Container(height=6),
                                 btn("🚫 ยกเลิกการจอง", make_cancel_action(b),
                                     height=36, radius=8, bgcolor=ft.Colors.with_opacity(0.08, RED),
                                     text_color=RED, expand=True)]
                                if can_cancel else []
                            ),
                        ], spacing=4),
                    ))
            page.update()

        def clear_all_bookings(e):
            # นับเฉพาะที่ยกเลิก/เสร็จแล้ว
            cancellable = [b for b in getattr(clear_all_bookings, "_books", [])
                           if b.get("status") in ("rejected", "completed")]
            if not cancellable:
                # ถ้าไม่มีข้อมูล ถามทั่วไป
                pass

            def confirm_clear(ce):
                cldlg.open = False
                page.update()
                # ลบเฉพาะที่ rejected/completed
                try:
                    r = requests.get(f"{BOOKINGS_URL}/user/{user_id}", timeout=5)
                    books_all = r.json() if r.status_code == 200 else []
                except Exception:
                    books_all = []
                for b in books_all:
                    if b.get("status") in ("rejected", "completed"):
                        try:
                            requests.delete(f"{BOOKINGS_URL}/{b.get('id')}", timeout=5)
                        except Exception:
                            pass
                load_bookings()
                page.update()

            cldlg = ft.AlertDialog(
                modal=True, bgcolor=BG, shape=ft.RoundedRectangleBorder(radius=12),
                inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
                title=ft.Text("ล้างประวัติการจอง", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                content=ft.Text(
                    "จะลบเฉพาะการจองที่ 'ปฏิเสธ' และ 'เสร็จสิ้น' ออกจากประวัติ\nการจองที่ยังดำเนินอยู่จะไม่ถูกลบ",
                    size=13, color=MID,
                ),
                actions=[
                    ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                  on_click=lambda ev: (setattr(cldlg, "open", False), page.update())),
                    ft.TextButton("ล้างประวัติ", style=ft.ButtonStyle(color=RED),
                                  on_click=confirm_clear),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(cldlg)
            cldlg.open = True
            page.update()

        load_bookings()
        page.views.append(ft.View(
            route="/mybookings", bgcolor=BG2, padding=0,
            controls=[ft.Column(expand=True, spacing=0, controls=[
                back_bar(page, "ประวัติการจอง",
                         extra_actions=[btn("🗑️ ล้าง", clear_all_bookings, height=34, radius=6,
                                           bgcolor="#FFEBEE", text_color=RED)]),
                ft.Container(expand=True, padding=ft.padding.all(16),
                             content=ft.Column(controls=[book_list], scroll=ft.ScrollMode.AUTO, expand=True)),
            ])],
        ))
        page.update()

    # ══════════════════════════════════════════════════════════════
    # ── HELPER: SHOW SLIP DIALOG ──────────────────────────────────
    # ══════════════════════════════════════════════════════════════
    def _show_slip_dialog(slip_url: str):
        dlg_holder = [None]

        def close_dlg(e):
            if dlg_holder[0]:
                dlg_holder[0].open = False
                page.update()

        dlg = ft.AlertDialog(
            modal=True, bgcolor=BG,
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Text("สลิปการชำระเงิน", size=14, weight=ft.FontWeight.BOLD, color=DARK),
            content=ft.Container(
                width=min(page.width - 48, 360),
                content=ft.Column([
                    ft.Image(src=slip_url, width=280, height=280, fit="contain",
                             border_radius=8,
                             error_content=ft.Column([
                                 ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED, color=LIGHT, size=32),
                                 ft.Text("ไม่สามารถแสดงรูปได้", size=11, color=LIGHT),
                                 ft.Text(slip_url[:60], size=9, color=LIGHT),
                             ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            actions=[ft.TextButton("ปิด", style=ft.ButtonStyle(color=LIGHT), on_click=close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        dlg_holder[0] = dlg
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ══════════════════════════════════════════════════════════════
    # ── ADMIN: BOOKING DETAIL (per pet) ───────────────────────────
    # ══════════════════════════════════════════════════════════════
    def show_admin_pet_bookings_page(pet: dict):
        """หน้าการจองของสัตว์เลี้ยงตัวนั้นๆ สำหรับแอดมิน"""
        pid = pet.get("id")
        pet_name = pet.get("name", "?")
        book_list = ft.Column(spacing=10)

        def load_bookings():
            book_list.controls.clear()
            try:
                r = requests.get(BOOKINGS_URL, timeout=5)
                all_books = r.json() if r.status_code == 200 else []
                books = [b for b in all_books if b.get("pet_id") == pid]
            except Exception:
                books = []

            if not books:
                book_list.controls.append(ft.Container(
                    padding=ft.padding.symmetric(vertical=40),
                    content=ft.Column([
                        ft.Icon(ft.Icons.HOTEL_OUTLINED, size=48, color=LIGHT),
                        ft.Text("ยังไม่มีการจองสำหรับสัตว์เลี้ยงตัวนี้", size=14, color=LIGHT),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                ))
            else:
                for b in books:
                    s_label, s_color = STATUS_LABEL.get(b.get("status", ""), (b.get("status", ""), MID))

                    def make_status_change_pet(bid):
                        def do(e):
                            real_opts = [
                                ("อนุมัติ", "approved", GREEN),
                                ("ปฏิเสธ", "rejected", RED),
                                ("กำลังรับฝาก", "staying", BLUE),
                                ("เสร็จสิ้น", "completed", MID),
                            ]
                            opt_widgets = []
                            conf_holder = [None]

                            for lbl, val, col in real_opts:
                                def make_opt(v):
                                    def set_status(ev):
                                        if conf_holder[0]:
                                            conf_holder[0].open = False
                                            page.update()
                                        try:
                                            requests.put(f"{BOOKINGS_URL}/{bid}/status", json={"status": v}, timeout=5)
                                        except Exception:
                                            pass
                                        load_bookings()
                                        load_all_pets()
                                        page.update()
                                    return set_status
                                opt_widgets.append(ft.TextButton(lbl, style=ft.ButtonStyle(color=col), on_click=make_opt(val)))

                            conf = ft.AlertDialog(
                                modal=True, bgcolor=BG, shape=ft.RoundedRectangleBorder(radius=12),
                                inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
                                title=ft.Text("เปลี่ยนสถานะการจอง", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                                content=ft.Text("เลือกสถานะใหม่:", size=13, color=MID),
                                actions=[ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                                       on_click=lambda e: (setattr(conf_holder[0], "open", False), page.update())),
                                         *opt_widgets],
                                actions_alignment=ft.MainAxisAlignment.END,
                            )
                            conf_holder[0] = conf
                            page.overlay.append(conf)
                            conf.open = True
                            page.update()
                        return do

                    # ── ปุ่มคืนสัตว์เลี้ยง (แสดงเมื่อ staying) ──
                    is_staying = b.get("status") == "staying"

                    def make_return_action(bid2):
                        def do_return(e):
                            rdlg_holder = [None]

                            def confirm_return(ce):
                                if rdlg_holder[0]:
                                    rdlg_holder[0].open = False
                                    page.update()
                                try:
                                    requests.put(f"{BOOKINGS_URL}/{bid2}/status", json={"status": "completed"}, timeout=5)
                                except Exception:
                                    pass
                                load_bookings()
                                load_all_pets()
                                page.update()

                            rdlg = ft.AlertDialog(
                                modal=True, bgcolor=BG, shape=ft.RoundedRectangleBorder(radius=12),
                                inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
                                title=ft.Text("คืนสัตว์เลี้ยง", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                                content=ft.Text("ยืนยันการคืนสัตว์เลี้ยงและเปลี่ยนสถานะเป็น 'เสร็จสิ้น'?", size=13, color=MID),
                                actions=[
                                    ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                                  on_click=lambda e: (setattr(rdlg_holder[0], "open", False), page.update())),
                                    ft.TextButton("✅ ยืนยันคืนสัตว์เลี้ยง", style=ft.ButtonStyle(color=GREEN),
                                                  on_click=confirm_return),
                                ],
                                actions_alignment=ft.MainAxisAlignment.END,
                            )
                            rdlg_holder[0] = rdlg
                            page.overlay.append(rdlg)
                            rdlg.open = True
                            page.update()
                        return do_return

                    book_list.controls.append(ft.Container(
                        bgcolor=BG, border_radius=12, border=ft.border.all(1, BORDER),
                        padding=ft.padding.all(14),
                        content=ft.Column([
                            ft.Row([
                                ft.Column([
                                    ft.Text(f"🐾 {pet_name} ({pet.get('type', '')})",
                                            size=13, weight=ft.FontWeight.BOLD, color=DARK),
                                    ft.Text(f"👤 {b.get('user_name', '?')} — {b.get('user_email', '')}",
                                            size=11, color=MID),
                                ], spacing=2, expand=True),
                                info_chip(s_label, s_color),
                            ]),
                            ft.Divider(height=12, color=BORDER),
                            ft.Row([
                                ft.Icon(ft.Icons.CALENDAR_TODAY_OUTLINED, size=13, color=LIGHT),
                                ft.Container(width=4),
                                ft.Text(f"{b.get('check_in', '')} → {b.get('check_out', '')}", size=11, color=MID, expand=True),
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3), border_radius=8,
                                    bgcolor=ft.Colors.with_opacity(0.1, GREEN if b.get("payment_status") == "paid" else ORANGE),
                                    content=ft.Text(
                                        "ชำระแล้ว" if b.get("payment_status") == "paid" else "ยังไม่ชำระ",
                                        size=10, color=GREEN if b.get("payment_status") == "paid" else ORANGE,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ),
                            ]),
                            ft.Row([
                                ft.Text(f"💰 {b.get('total_price', 0):.0f} บาท", size=11, color=MID, expand=True),
                                btn("เปลี่ยนสถานะ", make_status_change_pet(b.get("id")), height=30, radius=6,
                                    bgcolor=PRIMARY, text_color=DARK),
                            ]),
                            # คืนสัตว์เลี้ยง
                            *(
                                [ft.Container(height=6),
                                 ft.GestureDetector(
                                     on_tap=make_return_action(b.get("id")),
                                     content=ft.Container(
                                         height=40, border_radius=8, bgcolor=GREEN,
                                         alignment=ft.alignment.Alignment(0, 0),
                                         content=ft.Text("🏠 คืนสัตว์เลี้ยง", size=13,
                                                         weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                                     ),
                                 )]
                                if is_staying else []
                            ),
                            # สลิป
                            *(
                                [ft.Container(height=4),
                                 ft.GestureDetector(
                                     on_tap=(lambda su: lambda e: _show_slip_dialog(su))(b.get("payment_slip", "")),
                                     content=ft.Container(
                                         border_radius=6, bgcolor=ft.Colors.with_opacity(0.08, BLUE),
                                         padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                         content=ft.Row([
                                             ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, color=BLUE, size=13),
                                             ft.Container(width=4),
                                             ft.Text("ดูสลิป", size=11, color=BLUE, weight=ft.FontWeight.BOLD),
                                         ], spacing=0),
                                     ),
                                 )]
                                if b.get("payment_slip") else
                                [ft.Container(height=4),
                                 ft.Text("📋 ยังไม่มีสลิป", size=10, color=LIGHT)]
                            ),
                        ], spacing=6),
                    ))
            page.update()

        load_bookings()
        page.views.append(ft.View(
            route=f"/admin/pet/{pid}/bookings", bgcolor=BG2, padding=0,
            controls=[ft.Column(expand=True, spacing=0, controls=[
                back_bar(page, f"การจองของ {pet_name}"),
                ft.Container(expand=True, padding=ft.padding.all(16),
                             content=ft.Column(controls=[book_list], scroll=ft.ScrollMode.AUTO, expand=True)),
            ])],
        ))
        page.update()

    # ══════════════════════════════════════════════════════════════
    # ── ADMIN: ALL BOOKINGS ────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════
    def show_admin_bookings_page(e=None):
        book_list = ft.Column(spacing=10)

        def load_bookings():
            book_list.controls.clear()
            try:
                r = requests.get(BOOKINGS_URL, timeout=5)
                books = r.json() if r.status_code == 200 else []
            except Exception:
                books = []
            if not books:
                book_list.controls.append(ft.Container(
                    padding=ft.padding.symmetric(vertical=40),
                    content=ft.Column([
                        ft.Icon(ft.Icons.HOTEL_OUTLINED, size=48, color=LIGHT),
                        ft.Text("ยังไม่มีการจอง", size=14, color=LIGHT),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                ))
            else:
                for b in books:
                    s_label, s_color = STATUS_LABEL.get(b.get("status", ""), (b.get("status", ""), MID))

                    def make_status_change(bid):
                        def do(e):
                            opts = [
                                ("ยกเลิก/ปฏิเสธ", "rejected", RED),
                                ("อนุมัติ", "approved", GREEN),
                                ("ปฏิเสธ", "rejected", RED),
                                ("กำลังรับฝาก", "staying", BLUE),
                                ("เสร็จสิ้น", "completed", MID),
                            ]
                            # real opts without duplicate
                            real_opts = [
                                ("อนุมัติ", "approved", GREEN),
                                ("ปฏิเสธ", "rejected", RED),
                                ("กำลังรับฝาก", "staying", BLUE),
                                ("เสร็จสิ้น", "completed", MID),
                            ]
                            opt_widgets = []
                            conf_holder = [None]

                            for lbl, val, col in real_opts:
                                def make_opt(v):
                                    def set_status(ev):
                                        if conf_holder[0]:
                                            conf_holder[0].open = False
                                            page.update()
                                        try:
                                            requests.put(f"{BOOKINGS_URL}/{bid}/status", json={"status": v}, timeout=5)
                                        except Exception:
                                            pass
                                        load_bookings()
                                        load_all_pets()
                                        page.update()
                                    return set_status
                                opt_widgets.append(ft.TextButton(lbl, style=ft.ButtonStyle(color=col), on_click=make_opt(val)))

                            conf = ft.AlertDialog(
                                modal=True, bgcolor=BG, shape=ft.RoundedRectangleBorder(radius=12),
                                inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
                                title=ft.Text("เปลี่ยนสถานะการจอง", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                                content=ft.Text("เลือกสถานะใหม่:", size=13, color=MID),
                                actions=[ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                                       on_click=lambda e: (setattr(conf_holder[0], "open", False), page.update())),
                                         *opt_widgets],
                                actions_alignment=ft.MainAxisAlignment.END,
                            )
                            conf_holder[0] = conf
                            page.overlay.append(conf)
                            conf.open = True
                            page.update()
                        return do

                    book_list.controls.append(ft.Container(
                        bgcolor=BG, border_radius=12, border=ft.border.all(1, BORDER),
                        padding=ft.padding.all(14),
                        content=ft.Column([
                            ft.Row([
                                ft.Column([
                                    ft.Text(f"🐾 {b.get('pet_name', '?')} ({b.get('pet_type', '')})",
                                            size=13, weight=ft.FontWeight.BOLD, color=DARK),
                                    ft.Text(f"👤 {b.get('user_name', '?')} — {b.get('user_email', '')}",
                                            size=11, color=MID),
                                ], spacing=2, expand=True),
                                info_chip(s_label, s_color),
                            ]),
                            ft.Divider(height=12, color=BORDER),
                            ft.Row([
                                ft.Icon(ft.Icons.CALENDAR_TODAY_OUTLINED, size=13, color=LIGHT),
                                ft.Container(width=4),
                                ft.Text(f"{b.get('check_in', '')} → {b.get('check_out', '')}", size=11, color=MID, expand=True),
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=8, vertical=3), border_radius=8,
                                    bgcolor=ft.Colors.with_opacity(0.1, GREEN if b.get("payment_status") == "paid" else ORANGE),
                                    content=ft.Text(
                                        "ชำระแล้ว" if b.get("payment_status") == "paid" else "ยังไม่ชำระ",
                                        size=10, color=GREEN if b.get("payment_status") == "paid" else ORANGE,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ),
                            ]),
                            ft.Row([
                                ft.Text(f"💰 {b.get('total_price', 0):.0f} บาท", size=11, color=MID, expand=True),
                                btn("เปลี่ยนสถานะ", make_status_change(b.get("id")), height=30, radius=6,
                                    bgcolor=PRIMARY, text_color=DARK),
                            ]),
                            # ── แสดงสลิปถ้ามี ──
                            *(
                                [ft.Container(height=4),
                                 ft.GestureDetector(
                                     on_tap=(lambda slip_url: lambda e: _show_slip_dialog(slip_url))(b.get("payment_slip", "")),
                                     content=ft.Container(
                                         border_radius=6, bgcolor=ft.Colors.with_opacity(0.08, BLUE),
                                         padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                         content=ft.Row([
                                             ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, color=BLUE, size=13),
                                             ft.Container(width=4),
                                             ft.Text("ดูสลิป", size=11, color=BLUE, weight=ft.FontWeight.BOLD),
                                         ], spacing=0),
                                     ),
                                 )]
                                if b.get("payment_slip") else
                                [ft.Container(height=4),
                                 ft.Text("📋 ยังไม่มีสลิป", size=10, color=LIGHT)]
                            ),
                        ], spacing=6),
                    ))
            page.update()

        load_bookings()
        page.views.append(ft.View(
            route="/admin/bookings", bgcolor=BG2, padding=0,
            controls=[ft.Column(expand=True, spacing=0, controls=[
                back_bar(page, "จัดการการจอง"),
                ft.Container(expand=True, padding=ft.padding.all(16),
                             content=ft.Column(controls=[book_list], scroll=ft.ScrollMode.AUTO, expand=True)),
            ])],
        ))
        page.update()

    # ══════════════════════════════════════════════════════════════
    # ── ADMIN: ALL USERS & PETS ───────────────────────────────────
    # ══════════════════════════════════════════════════════════════
    def show_admin_users_page(e=None):
        user_list = ft.Column(spacing=10)

        def load_users():
            user_list.controls.clear()
            try:
                r_users = requests.get(USERS_URL, timeout=5)
                r_pets = requests.get(PETS_URL, timeout=5)
                users = r_users.json() if r_users.status_code == 200 else []
                all_p = r_pets.json() if r_pets.status_code == 200 else []
            except Exception:
                users, all_p = [], []

            for u in users:
                uid = u.get("id")
                u_pets = [p for p in all_p if p.get("user_id") == uid]
                pet_names = ", ".join(p.get("name", "") for p in u_pets) if u_pets else "ยังไม่มีสัตว์เลี้ยง"
                role_color = RED if u.get("role") == "admin" else BLUE

                def make_edit_user(udata):
                    def do(ev):
                        fs = field_style()
                        tf_name = ft.TextField(label="ชื่อ *", value=udata.get("name", ""), **fs)
                        tf_email = ft.TextField(label="อีเมล *", value=udata.get("email", ""),
                                                keyboard_type=ft.KeyboardType.EMAIL, **fs)
                        tf_pass = ft.TextField(label="รหัสผ่านใหม่ (เว้นว่างถ้าไม่เปลี่ยน)",
                                               password=True, can_reveal_password=True, **fs)
                        dd_role = ft.Dropdown(
                            label="Role",
                            value=udata.get("role", "user"),
                            options=[ft.dropdown.Option("user", "👤 User"),
                                     ft.dropdown.Option("admin", "👑 Admin")],
                            border_color=BORDER, focused_border_color=PRIMARY, border_radius=6,
                            bgcolor=BG2, label_style=ft.TextStyle(color=LIGHT, size=12),
                            text_style=ft.TextStyle(size=13, color=DARK),
                        )
                        st_e = ft.Text("", size=12)

                        def save(sev):
                            if not tf_name.value.strip() or not tf_email.value.strip():
                                st_e.value = "⚠️ กรุณากรอกชื่อและอีเมล"
                                st_e.color = PRIMARY
                                page.update()
                                return
                            pwd = tf_pass.value.strip() or udata.get("password", "")
                            try:
                                res = requests.put(f"{USERS_URL}/{udata.get('id')}", json={
                                    "name": tf_name.value.strip(),
                                    "email": tf_email.value.strip(),
                                    "password": pwd,
                                    "role": dd_role.value or "user",
                                }, timeout=5)
                                if res.status_code == 200:
                                    edlg.open = False
                                    page.update()
                                    load_users()
                                else:
                                    st_e.value = f"❌ Error {res.status_code}"
                                    page.update()
                            except Exception:
                                st_e.value = "❌ เชื่อมต่อไม่ได้"
                                page.update()

                        edlg = ft.AlertDialog(
                            modal=True, bgcolor=BG, shape=ft.RoundedRectangleBorder(radius=12),
                            inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
                            title=ft.Text("แก้ไขผู้ใช้", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                            content=ft.Container(width=min(page.width - 48, 400),
                                                 content=ft.Column([tf_name, tf_email, tf_pass, dd_role, st_e],
                                                                   spacing=10, tight=True)),
                            actions=[
                                ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                              on_click=lambda e: (setattr(edlg, "open", False), page.update())),
                                btn("บันทึก", save, height=38, radius=6),
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                        )
                        page.overlay.append(edlg)
                        edlg.open = True
                        page.update()
                    return do

                def make_delete_user(udata):
                    def do(ev):
                        def confirm_del(cev):
                            try:
                                requests.delete(f"{USERS_URL}/{udata.get('id')}", timeout=5)
                            except Exception:
                                pass
                            cdlg.open = False
                            page.update()
                            load_users()

                        cdlg = ft.AlertDialog(
                            modal=True, bgcolor=BG, shape=ft.RoundedRectangleBorder(radius=12),
                            inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
                            title=ft.Text("ยืนยันการลบ", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                            content=ft.Text(f"ต้องการลบผู้ใช้ \"{udata.get('name', '')}\" ใช่ไหม?",
                                            size=13, color=MID),
                            actions=[
                                ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                              on_click=lambda e: (setattr(cdlg, "open", False), page.update())),
                                ft.TextButton("ลบ", style=ft.ButtonStyle(color=RED), on_click=confirm_del),
                            ],
                            actions_alignment=ft.MainAxisAlignment.END,
                        )
                        page.overlay.append(cdlg)
                        cdlg.open = True
                        page.update()
                    return do

                user_list.controls.append(ft.Container(
                    bgcolor=BG, border_radius=12, border=ft.border.all(1, BORDER),
                    padding=ft.padding.all(14),
                    content=ft.Row([
                        ft.Container(
                            width=44, height=44, border_radius=22, bgcolor=PRIMARY,
                            alignment=ft.alignment.Alignment(0, 0),
                            content=ft.Text(u.get("name", "?")[:1].upper(), size=18, weight=ft.FontWeight.BOLD, color=DARK),
                        ),
                        ft.Container(width=12),
                        ft.Column([
                            ft.Row([
                                ft.Text(u.get("name", ""), size=13, weight=ft.FontWeight.BOLD, color=DARK),
                                ft.Container(width=6),
                                info_chip(u.get("role", "user"), role_color),
                            ]),
                            ft.Text(u.get("email", ""), size=11, color=MID),
                            ft.Text(f"🐾 {pet_names}", size=11, color=LIGHT),
                        ], spacing=2, expand=True),
                        ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color=PRIMARY, icon_size=18,
                                      tooltip="แก้ไข", on_click=make_edit_user(u)),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=RED, icon_size=18,
                                      tooltip="ลบ", on_click=make_delete_user(u)),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ))
            page.update()

        def open_add_user(e):
            fs = field_style()
            tf_name = ft.TextField(label="ชื่อ *", **fs)
            tf_email = ft.TextField(label="อีเมล *", keyboard_type=ft.KeyboardType.EMAIL, **fs)
            tf_pass = ft.TextField(label="รหัสผ่าน *", password=True, can_reveal_password=True, **fs)
            dd_role = ft.Dropdown(
                label="Role",
                value="user",
                options=[ft.dropdown.Option("user", "👤 User"),
                         ft.dropdown.Option("admin", "👑 Admin")],
                border_color=BORDER, focused_border_color=PRIMARY, border_radius=6,
                bgcolor=BG2, label_style=ft.TextStyle(color=LIGHT, size=12),
                text_style=ft.TextStyle(size=13, color=DARK),
            )
            st_a = ft.Text("", size=12)

            def save_new(ev):
                if not tf_name.value.strip() or not tf_email.value.strip() or not tf_pass.value.strip():
                    st_a.value = "⚠️ กรุณากรอกข้อมูลให้ครบ"
                    st_a.color = PRIMARY
                    page.update()
                    return
                st_a.value = "⏳ กำลังบันทึก..."
                page.update()
                try:
                    res = requests.post(USERS_URL, json={
                        "name": tf_name.value.strip(),
                        "email": tf_email.value.strip(),
                        "password": tf_pass.value.strip(),
                        "role": dd_role.value or "user",
                    }, timeout=5)
                    if res.status_code in (200, 201):
                        st_a.value = "✅ เพิ่มสำเร็จ!"
                        st_a.color = GREEN
                        page.update()
                        time.sleep(0.4)
                        adlg.open = False
                        page.update()
                        load_users()
                    else:
                        st_a.value = f"❌ Error {res.status_code}"
                        page.update()
                except Exception:
                    st_a.value = "❌ เชื่อมต่อไม่ได้"
                    page.update()

            adlg = ft.AlertDialog(
                modal=True, bgcolor=BG, shape=ft.RoundedRectangleBorder(radius=12),
                inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
                title=ft.Text("เพิ่มผู้ใช้ใหม่", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                content=ft.Container(width=min(page.width - 48, 400),
                                     content=ft.Column([tf_name, tf_email, tf_pass, dd_role, st_a],
                                                       spacing=10, tight=True)),
                actions=[
                    ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                  on_click=lambda e: (setattr(adlg, "open", False), page.update())),
                    btn("บันทึก", save_new, height=38, radius=6),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(adlg)
            adlg.open = True
            page.update()

        load_users()
        page.views.append(ft.View(
            route="/admin/users", bgcolor=BG2, padding=0,
            controls=[ft.Column(expand=True, spacing=0, controls=[
                back_bar(page, "ผู้ใช้ทั้งหมด",
                         extra_actions=[btn("+ เพิ่ม", open_add_user, height=34, radius=6)]),
                ft.Container(expand=True, padding=ft.padding.all(16),
                             content=ft.Column(controls=[user_list], scroll=ft.ScrollMode.AUTO, expand=True)),
            ])],
        ))
        page.update()

    # ══════════════════════════════════════════════════════════════
    # ── LOAD PETS ─────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════
    def open_delete_pet_dialog(pet: dict):
        def do_delete(e):
            try:
                requests.delete(f"{PETS_URL}/{pet['id']}", timeout=5)
            except Exception:
                pass
            conf.open = False
            page.update()
            load_all_pets()

        conf = ft.AlertDialog(
            modal=True, bgcolor=BG, shape=ft.RoundedRectangleBorder(radius=12),
            inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
            title=ft.Text("ลบสัตว์เลี้ยง", size=15, weight=ft.FontWeight.BOLD, color=DARK),
            content=ft.Text(f"ต้องการลบ \"{pet.get('name', '')}\" ออกจากระบบใช่ไหม?", size=13, color=MID),
            actions=[
                ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                              on_click=lambda e: (setattr(conf, "open", False), page.update())),
                ft.TextButton("ลบ", style=ft.ButtonStyle(color=RED), on_click=do_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(conf)
        conf.open = True
        page.update()

    def open_edit_pet_dialog(pet: dict):
        fs = field_style()
        tf_name = ft.TextField(label="ชื่อสัตว์เลี้ยง *", value=pet.get("name", ""), **fs)
        tf_type = ft.Dropdown(
            label="ประเภท *", value=pet.get("type", ""),
            options=[ft.dropdown.Option("dog", "🐶 Dog"), ft.dropdown.Option("cat", "🐱 Cat"),
                     ft.dropdown.Option("bird", "🐦 Bird"), ft.dropdown.Option("rabbit", "🐰 Rabbit"),
                     ft.dropdown.Option("fish", "🐠 Fish"), ft.dropdown.Option("hamster", "🐹 Hamster")],
            border_color=BORDER, focused_border_color=PRIMARY, border_radius=6,
            bgcolor=BG2, label_style=ft.TextStyle(color=LIGHT, size=12), text_style=ft.TextStyle(size=13, color=DARK),
        )
        tf_age = ft.TextField(label="อายุ (ปี) *", value=str(pet.get("age", "")), keyboard_type=ft.KeyboardType.NUMBER, **fs)
        tf_img = ft.TextField(label="ลิ้งรูปภาพ (optional)", value=pet.get("image_url", "") or "", **fs)
        tf_vaccine = ft.TextField(label="วัคซีน (เช่น rabies, DHPP ...)", value=pet.get("vaccine", "") or "", **fs)
        st = ft.Text("", size=12)

        def submit_edit(e):
            n = tf_name.value.strip()
            t = tf_type.value
            a = tf_age.value.strip()
            if not n or not t or not a:
                st.value = "⚠️ กรุณากรอกข้อมูลให้ครบ"
                page.update()
                return
            try:
                age_v = int(a)
            except ValueError:
                st.value = "⚠️ อายุต้องเป็นตัวเลข"
                page.update()
                return
            try:
                res = requests.put(f"{PETS_URL}/{pet['id']}", json={
                    "user_id": pet.get("user_id"), "name": n, "type": t, "age": age_v,
                    "image_url": tf_img.value.strip() or None, "vaccine": tf_vaccine.value.strip() or None,
                }, timeout=5)
                if res.status_code == 200:
                    st.value = "✅ แก้ไขสำเร็จ!"
                    st.color = GREEN
                    page.update()
                    time.sleep(0.3)
                    edit_dlg.open = False
                    page.update()
                    load_all_pets()
                else:
                    st.value = f"❌ Error {res.status_code}"
                    st.color = PRIMARY
                    page.update()
            except Exception:
                st.value = "❌ เชื่อมต่อไม่ได้"
                st.color = PRIMARY
                page.update()

        edit_dlg = ft.AlertDialog(
            modal=True, bgcolor=BG, shape=ft.RoundedRectangleBorder(radius=12),
            inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
            title=ft.Text("แก้ไขข้อมูลสัตว์เลี้ยง", size=15, weight=ft.FontWeight.BOLD, color=DARK),
            content=ft.Container(width=min(page.width - 48, 400),
                                 content=ft.Column([tf_name, tf_type, tf_age, tf_img, tf_vaccine, st], spacing=10, tight=True)),
            actions=[ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                   on_click=lambda e: (setattr(edit_dlg, "open", False), page.update())),
                     btn("บันทึก", submit_edit, height=38, radius=6)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(edit_dlg)
        edit_dlg.open = True
        page.update()

    def load_all_pets():
        pets_col.controls.clear()
        user = state["user"] or {}
        is_admin = user.get("role") == "admin"
        uid = user.get("id")

        try:
            if is_admin:
                r = requests.get(PETS_URL, timeout=5)
            else:
                r = requests.get(f"{PETS_URL}/user/{uid}", timeout=5)
            pets = r.json() if r.status_code == 200 else []
        except Exception:
            pets = []

        # ดึงสถานะการจองทั้งหมดถ้าเป็นแอดมิน หรือดึงของ user
        pet_booking_status: dict = {}
        try:
            if is_admin:
                rb = requests.get(BOOKINGS_URL, timeout=5)
            else:
                rb = requests.get(f"{BOOKINGS_URL}/user/{uid}", timeout=5)
            all_books = rb.json() if rb.status_code == 200 else []
            # priority: staying > approved > pending (เอาสถานะที่ active ที่สำคัญที่สุด)
            priority = {"staying": 4, "approved": 3, "pending": 2, "completed": 1}
            for b in all_books:
                pid_b = b.get("pet_id")
                bstatus = b.get("status", "")
                if bstatus in priority:
                    current = pet_booking_status.get(pid_b)
                    if current is None or priority.get(bstatus, 0) > priority.get(current, 0):
                        pet_booking_status[pid_b] = bstatus
        except Exception:
            pass

        all_pets.clear()
        all_pets.extend(pets)

        if not pets:
            pets_col.controls.append(ft.Container(
                padding=ft.padding.symmetric(vertical=40),
                content=ft.Column([
                    ft.Icon(ft.Icons.PETS, size=48, color=LIGHT),
                    ft.Text("ยังไม่มีสัตว์เลี้ยง", size=14, color=LIGHT),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            ))
        else:
            for i, pet in enumerate(pets):
                color = pet_color(i)
                icon_txt = pet_icon(pet.get("type", ""))
                img_url = pet.get("image_url", "") or ""
                av = (
                    ft.Container(width=56, height=56, border_radius=28, clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                                 content=ft.Image(src=img_url, width=56, height=56, fit="cover",
                                                  error_content=ft.Text(icon_txt, size=24, text_align="center")))
                    if img_url.strip() else
                    ft.Container(width=56, height=56, border_radius=28, bgcolor=color,
                                 content=ft.Text(icon_txt, size=26, text_align="center"),
                                 alignment=ft.alignment.Alignment(0, 0))
                )

                # admin label per pet
                owner_chip = (
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=8,
                        bgcolor=ft.Colors.with_opacity(0.1, BLUE),
                        content=ft.Text(f"user#{pet.get('user_id', '')}", size=9, color=BLUE),
                    ) if is_admin else ft.Container(width=0)
                )

                # badge สถานะการจองปัจจุบัน
                pet_bstatus = pet_booking_status.get(pet.get("id"))
                booking_badge = status_chip(pet_bstatus) if pet_bstatus else ft.Container(width=0)

                # action buttons differ by role
                row_actions = []
                if is_admin:
                    row_actions = [
                        ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color=PRIMARY, icon_size=20,
                                      tooltip="แก้ไข", on_click=lambda e, p=pet: open_edit_pet_dialog(p)),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=RED, icon_size=20,
                                      tooltip="ลบ", on_click=lambda e, p=pet: open_delete_pet_dialog(p)),
                    ]
                else:
                    row_actions = [
                        ft.IconButton(ft.Icons.HOTEL_OUTLINED, icon_color=BLUE, icon_size=20,
                                      tooltip="จองรับฝาก", on_click=lambda e, p=pet: show_booking_page(p)),
                        ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color=PRIMARY, icon_size=20,
                                      tooltip="แก้ไข", on_click=lambda e, p=pet: open_edit_pet_dialog(p)),
                    ]

                # ทั้ง admin และ user กดที่ card → ไปรายละเอียดสัตว์เลี้ยง
                on_card_tap = (lambda p, idx: lambda e: show_pet_detail(p, idx))(pet, i)

                pets_col.controls.append(ft.Container(
                    border_radius=12, bgcolor=BG, border=ft.border.all(1, BORDER),
                    padding=ft.padding.all(12),
                    content=ft.Row([
                        ft.GestureDetector(
                            on_tap=on_card_tap,
                            content=ft.Row([
                                av,
                                ft.Container(width=12),
                                ft.Column([
                                    ft.Text(pet.get("name", ""), size=14, weight=ft.FontWeight.BOLD, color=DARK),
                                    ft.Container(height=4),
                                    ft.Row([
                                        info_chip(pet.get("type", "").capitalize(), color),
                                        info_chip(f"อายุ {pet.get('age', 0)} ปี", MID),
                                        owner_chip,
                                        booking_badge,
                                    ], spacing=6, wrap=True),
                                ], spacing=2, expand=True),
                            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                            expand=True,
                        ),
                        *row_actions,
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ))
        page.update()

    # ══════════════════════════════════════════════════════════════
    # ── ADD PET DIALOG ────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════
    def open_add_pet_dialog(e):
        user_id = state["user"]["id"] if state["user"] else 1
        fs = field_style()
        tf_name = ft.TextField(label="ชื่อสัตว์เลี้ยง *", **fs)
        tf_type = ft.Dropdown(
            label="ประเภท *",
            options=[ft.dropdown.Option("dog", "🐶 Dog"), ft.dropdown.Option("cat", "🐱 Cat"),
                     ft.dropdown.Option("bird", "🐦 Bird"), ft.dropdown.Option("rabbit", "🐰 Rabbit"),
                     ft.dropdown.Option("fish", "🐠 Fish"), ft.dropdown.Option("hamster", "🐹 Hamster")],
            border_color=BORDER, focused_border_color=PRIMARY, border_radius=6,
            bgcolor=BG2, label_style=ft.TextStyle(color=LIGHT, size=12), text_style=ft.TextStyle(size=13, color=DARK),
        )
        tf_age = ft.TextField(label="อายุ (ปี) *", keyboard_type=ft.KeyboardType.NUMBER, **fs)
        tf_img = ft.TextField(label="ลิ้งรูปภาพ (optional)", **fs)
        tf_vaccine = ft.TextField(label="วัคซีน (เช่น rabies, DHPP ...)", **fs)
        st = ft.Text("", size=12)

        def submit(e):
            n = tf_name.value.strip()
            t = tf_type.value
            a = tf_age.value.strip()
            if not n or not t or not a:
                st.value = "⚠️ กรุณากรอกข้อมูลให้ครบ"
                page.update()
                return
            try:
                age_v = int(a)
            except ValueError:
                st.value = "⚠️ อายุต้องเป็นตัวเลข"
                page.update()
                return
            st.value = "⏳ กำลังบันทึก..."
            page.update()
            try:
                res = requests.post(PETS_URL, json={
                    "user_id": user_id, "name": n, "type": t, "age": age_v,
                    "image_url": tf_img.value.strip() or None, "vaccine": tf_vaccine.value.strip() or None,
                }, timeout=5)
                if res.status_code in (200, 201):
                    st.value = "✅ เพิ่มสำเร็จ!"
                    st.color = GREEN
                    page.update()
                    time.sleep(0.4)
                    dlg.open = False
                    page.update()
                    load_all_pets()
                else:
                    st.value = f"❌ Error {res.status_code}"
                    st.color = PRIMARY
                    page.update()
            except Exception:
                st.value = "❌ เชื่อมต่อไม่ได้"
                st.color = PRIMARY
                page.update()

        dlg = ft.AlertDialog(
            modal=True, bgcolor=BG, shape=ft.RoundedRectangleBorder(radius=12),
            inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
            title=ft.Text("เพิ่มสัตว์เลี้ยงใหม่", size=15, weight=ft.FontWeight.BOLD, color=DARK),
            content=ft.Container(width=min(page.width - 48, 400),
                                 content=ft.Column([tf_name, tf_type, tf_age, tf_img, tf_vaccine, st], spacing=10, tight=True)),
            actions=[ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                   on_click=lambda e: (setattr(dlg, "open", False), page.update())),
                     btn("บันทึก", submit, height=38, radius=6)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # ══════════════════════════════════════════════════════════════
    # ── PROFILE PAGE ──────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════
    def show_profile_page(e):
        user = state["user"] or {}
        name_val = ft.Text(user.get("name", "-"), size=13, color=DARK, weight=ft.FontWeight.W_500, expand=True)
        email_val = ft.Text(user.get("email", "-"), size=13, color=DARK, weight=ft.FontWeight.W_500, expand=True)
        avatar_letter = ft.Text(user.get("name", "?")[:1].upper(), size=36, weight=ft.FontWeight.BOLD, color=DARK)
        avatar_name_txt = ft.Text(user.get("name", ""), size=18, weight=ft.FontWeight.BOLD, color="#FFF")
        avatar_email_txt = ft.Text(user.get("email", ""), size=12, color=LIGHT)
        role_txt = ft.Text(
            "👑 แอดมิน" if user.get("role") == "admin" else "👤 ผู้ใช้งาน",
            size=11, color=RED if user.get("role") == "admin" else BLUE, weight=ft.FontWeight.BOLD,
        )

        def do_logout(e):
            state["user"] = None
            pets_col.controls.clear()
            page.views.clear()
            page.views.append(build_login_view())
            page.update()

        def open_edit_profile(e):
            fs = field_style()
            tf_name = ft.TextField(label="ชื่อ *", value=user.get("name", ""), autofocus=True, **fs)
            tf_email = ft.TextField(label="อีเมล *", value=user.get("email", ""), keyboard_type=ft.KeyboardType.EMAIL, **fs)
            tf_phone = ft.TextField(label="เบอร์โทรศัพท์", value=user.get("phone", "") or "",
                                    keyboard_type=ft.KeyboardType.PHONE, **fs)
            tf_password = ft.TextField(label="รหัสผ่านใหม่ (เว้นว่างถ้าไม่เปลี่ยน)", password=True, can_reveal_password=True, **fs)
            status_txt = ft.Text("", size=12, color=DARK)

            def save_profile(ev):
                new_name = tf_name.value.strip()
                new_email = tf_email.value.strip()
                new_phone = tf_phone.value.strip()
                new_pass = tf_password.value.strip()
                if not new_name or not new_email:
                    status_txt.value = "⚠️ กรุณากรอกชื่อและอีเมล"
                    status_txt.color = PRIMARY
                    page.update()
                    return
                password_to_send = new_pass if new_pass else user.get("password", "")
                try:
                    resp = requests.put(f"{USERS_URL}/{user.get('id')}", json={
                        "name": new_name, "email": new_email,
                        "password": password_to_send, "role": user.get("role", "user"),
                        "phone": new_phone or None,
                    }, timeout=5)
                    if resp.status_code == 200:
                        user["name"] = new_name
                        user["email"] = new_email
                        user["phone"] = new_phone
                        if new_pass:
                            user["password"] = new_pass
                        state["user"] = user
                        user_name_txt.value = new_name
                        user_email_txt.value = new_email
                        name_val.value = new_name
                        email_val.value = new_email
                        avatar_letter.value = new_name[:1].upper()
                        avatar_name_txt.value = new_name
                        avatar_email_txt.value = new_email
                        dlg.open = False
                        page.update()
                    else:
                        status_txt.value = f"❌ เกิดข้อผิดพลาด {resp.status_code}"
                        status_txt.color = PRIMARY
                        page.update()
                except Exception:
                    status_txt.value = "❌ ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้"
                    status_txt.color = PRIMARY
                    page.update()

            dlg = ft.AlertDialog(
                modal=True, bgcolor=BG, shape=ft.RoundedRectangleBorder(radius=12),
                inset_padding=ft.padding.symmetric(horizontal=16, vertical=24),
                title=ft.Text("แก้ไขข้อมูลผู้ใช้", size=15, weight=ft.FontWeight.BOLD, color=DARK),
                content=ft.Container(width=min(page.width - 48, 380),
                                     content=ft.Column([tf_name, tf_email, tf_phone, tf_password, status_txt],
                                                       spacing=10, tight=True)),
                actions=[ft.TextButton("ยกเลิก", style=ft.ButtonStyle(color=LIGHT),
                                       on_click=lambda e: (setattr(dlg, "open", False), page.update())),
                         btn("บันทึก", save_profile, height=38, radius=6)],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(dlg)
            dlg.open = True
            page.update()

        page.views.append(ft.View(
            route="/profile", bgcolor=BG2, padding=0,
            controls=[ft.Column(expand=True, spacing=0, controls=[
                back_bar(page, "ข้อมูลผู้ใช้"),
                ft.Container(bgcolor=DARK, padding=ft.padding.symmetric(vertical=28),
                             content=ft.Column([
                                 ft.Container(width=80, height=80, border_radius=40, bgcolor=PRIMARY,
                                              alignment=ft.alignment.Alignment(0, 0), content=avatar_letter),
                                 ft.Container(height=10),
                                 avatar_name_txt, avatar_email_txt, role_txt,
                             ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)),
                ft.Container(height=16),
                ft.Container(
                    margin=ft.margin.symmetric(horizontal=16),
                    padding=ft.padding.all(20), border_radius=14, bgcolor=BG,
                    border=ft.border.all(1, BORDER),
                    content=ft.Column([
                        _profile_row_widget(ft.Icons.PERSON_OUTLINE, "ชื่อ", name_val),
                        ft.Divider(height=1, color=BORDER),
                        _profile_row_widget(ft.Icons.EMAIL_OUTLINED, "อีเมล", email_val),
                        ft.Divider(height=1, color=BORDER),
                        _profile_row(ft.Icons.PHONE_OUTLINED, "โทร", user.get("phone", "") or "-"),
                        ft.Divider(height=1, color=BORDER),
                        _profile_row(ft.Icons.BADGE_OUTLINED, "Role", user.get("role", "user")),
                        ft.Divider(height=1, color=BORDER),
                        _profile_row(ft.Icons.TAG, "ID", str(user.get("id", "-"))),
                    ], spacing=0),
                ),
                ft.Container(height=12),
                ft.Container(
                    margin=ft.margin.symmetric(horizontal=16),
                    padding=ft.padding.all(16), border_radius=14, bgcolor=BG,
                    border=ft.border.all(1, BORDER),
                    content=ft.Column([
                        ft.GestureDetector(
                            on_tap=open_edit_profile,
                            content=ft.Row([
                                ft.Icon(ft.Icons.EDIT_OUTLINED, color=DARK, size=18),
                                ft.Container(width=12),
                                ft.Text("แก้ไขข้อมูลส่วนตัว", size=13, color=DARK, expand=True),
                                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=LIGHT, size=18),
                            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ),
                        *(
                            [ft.Divider(height=16, color=BORDER),
                             ft.GestureDetector(
                                 on_tap=show_my_bookings_page,
                                 content=ft.Row([
                                     ft.Icon(ft.Icons.HOTEL_OUTLINED, color=BLUE, size=18),
                                     ft.Container(width=12),
                                     ft.Text("ประวัติการจอง", size=13, color=DARK, expand=True),
                                     ft.Icon(ft.Icons.CHEVRON_RIGHT, color=LIGHT, size=18),
                                 ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                             )]
                            if user.get("role") != "admin" else []
                        ),
                        *(
                            [ft.Divider(height=16, color=BORDER),
                             ft.GestureDetector(
                                 on_tap=show_admin_bookings_page,
                                 content=ft.Row([
                                     ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED, color=RED, size=18),
                                     ft.Container(width=12),
                                     ft.Text("จัดการการจองทั้งหมด", size=13, color=DARK, expand=True),
                                     ft.Icon(ft.Icons.CHEVRON_RIGHT, color=LIGHT, size=18),
                                 ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                             ),
                             ft.Divider(height=16, color=BORDER),
                             ft.GestureDetector(
                                 on_tap=show_admin_users_page,
                                 content=ft.Row([
                                     ft.Icon(ft.Icons.PEOPLE_OUTLINE, color=RED, size=18),
                                     ft.Container(width=12),
                                     ft.Text("จัดการผู้ใช้", size=13, color=DARK, expand=True),
                                     ft.Icon(ft.Icons.CHEVRON_RIGHT, color=LIGHT, size=18),
                                 ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                             )]
                            if user.get("role") == "admin" else []
                        ),
                        ft.Divider(height=16, color=BORDER),
                        ft.GestureDetector(
                            on_tap=do_logout,
                            content=ft.Row([
                                ft.Icon(ft.Icons.LOGOUT, color=RED, size=18),
                                ft.Container(width=12),
                                ft.Text("ออกจากระบบ", size=13, color=RED, weight=ft.FontWeight.BOLD, expand=True),
                            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ),
                    ], spacing=0),
                ),
            ])],
        ))
        page.update()

    # ══════════════════════════════════════════════════════════════
    # ── HOME VIEW ─────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════
    user_name_txt = ft.Text("", size=15, weight=ft.FontWeight.BOLD, color="#FFF")
    user_email_txt = ft.Text("", size=11, color="#CCCCCC")

    header = ft.Container(
        bgcolor=DARK,
        padding=ft.padding.symmetric(horizontal=16, vertical=14),
        content=ft.Row([
            ft.Column([
                ft.Row([ft.Text("🐾", size=18), ft.Container(width=6),
                        ft.Text("PET HOTEL", size=17, weight=ft.FontWeight.BOLD, color="#FFF")]),
                ft.Text("Your Pet Dashboard", size=10, color=LIGHT),
            ], spacing=3),
            ft.Container(expand=True),
            ft.GestureDetector(
                on_tap=show_profile_page,
                content=ft.Row([
                    ft.Column([user_name_txt, user_email_txt], spacing=2,
                              horizontal_alignment=ft.CrossAxisAlignment.END),
                    ft.Container(width=8),
                    ft.Container(width=38, height=38, border_radius=19, bgcolor=PRIMARY,
                                 border=ft.border.all(2, "#FFFFFF"),
                                 alignment=ft.alignment.Alignment(0, 0),
                                 content=ft.Icon(ft.Icons.PERSON, color=DARK, size=22), tooltip="โปรไฟล์"),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            ),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
    )

    hero = ft.Container(
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, -1), end=ft.alignment.Alignment(1, 1),
            colors=["#1A1A1A", "#2D2D2D"],
        ),
        padding=ft.padding.only(left=20, right=16, top=24, bottom=24),
        content=ft.Row([
            ft.Column([
                ft.Container(bgcolor=PRIMARY, border_radius=3,
                             padding=ft.padding.symmetric(horizontal=8, vertical=3),
                             content=ft.Text("🐾 PET HOTEL", size=9, color="#000000", weight=ft.FontWeight.BOLD)),
                ft.Container(height=10),
                ft.Text("ยินดีตอนรับสู่\nจุ้มปุ๊คโฮเทล", size=21, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
            ], expand=True, spacing=0),
            ft.Container(width=12),
            ft.Text("🐶🐱\n🐰🐦", size=38, text_align="center"),
        ]),
    )

    def build_home_body():
        user = state["user"] or {}
        is_admin = user.get("role") == "admin"

        # Admin quick actions row
        admin_quick = ft.Container(
            visible=is_admin,
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            content=ft.Row([
                btn("📋 การจองทั้งหมด", show_admin_bookings_page, height=38, radius=8,
                    bgcolor=DARK, text_color="#FFF", expand=True),
                ft.Container(width=8),
                btn("👥 ผู้ใช้", show_admin_users_page, height=38, radius=8,
                    bgcolor=DARK, text_color="#FFF", expand=True),
            ]),
        )

        # User quick actions — ซ่อน (user เข้าประวัติได้จากโปรไฟล์)
        user_quick = ft.Container(visible=False)

        portrait_body = ft.Column([
            header,
            hero,
            admin_quick,
            user_quick,
            section_header(
                "สัตว์เลี้ยงทั้งหมด" if is_admin else "สัตว์เลี้ยงทั้งหมด",
                action_label="+ เพิ่ม", on_action=open_add_pet_dialog,
            ),
            ft.Container(padding=ft.padding.only(left=16, right=16, bottom=120), content=pets_col),
        ], scroll=ft.ScrollMode.AUTO, spacing=0, expand=True)

        return portrait_body

    home_view = ft.View(
        route="/home", bgcolor=BG2, padding=0,
        controls=[ft.Stack([build_home_body()], expand=True)],
    )

    def refresh_home_layout(e=None):
        if not home_view.controls:
            return
        home_view.controls[0].content = build_home_body()
        page.update()

    page.on_resized = refresh_home_layout

    # ── auto-refresh สถานะทุก 15 วินาที (user เห็นสถานะอัปเดตจาก admin) ──
    import threading

    def _auto_refresh():
        while True:
            time.sleep(15)
            if state["user"]:
                try:
                    load_all_pets()
                except Exception:
                    pass

    _t = threading.Thread(target=_auto_refresh, daemon=True)
    _t.start()

    # ══════════════════════════════════════════════════════════════
    # ── LOGIN VIEW ────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════
    def build_login_view():
        tf_style = dict(
            border_color="#444", focused_border_color=PRIMARY, border_radius=8,
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
            bgcolor="#242424", label_style=ft.TextStyle(color="#AAA", size=13),
            text_style=ft.TextStyle(size=14, color="#FFFFFF"),
            cursor_color=PRIMARY, selection_color=ft.Colors.with_opacity(0.3, PRIMARY),
            color="#FFFFFF",
        )
        tf_email = ft.TextField(label="อีเมล", prefix_icon=ft.Icons.EMAIL_OUTLINED,
                                keyboard_type=ft.KeyboardType.EMAIL, **tf_style)
        tf_password = ft.TextField(label="รหัสผ่าน", prefix_icon=ft.Icons.LOCK_OUTLINE,
                                   password=True, can_reveal_password=True, **tf_style)
        error_txt = ft.Text("", size=12, color=PRIMARY, text_align="center")

        def do_login(e):
            email = tf_email.value.strip()
            pwd = tf_password.value.strip()
            if not email or not pwd:
                error_txt.value = "⚠️ กรุณากรอกอีเมลและรหัสผ่าน"
                page.update()
                return
            error_txt.value = "⏳ กำลังเข้าสู่ระบบ..."
            error_txt.color = LIGHT
            page.update()
            try:
                resp = requests.get(USERS_URL, timeout=5)
                if resp.status_code == 200:
                    users = resp.json()
                    matched = next(
                        (u for u in users if u.get("email", "").lower() == email.lower()
                         and str(u.get("password", "")) == pwd),
                        None,
                    )
                    if matched:
                        state["user"] = matched
                        user_name_txt.value = matched.get("name", "")
                        user_email_txt.value = matched.get("email", "")
                        error_txt.value = ""
                        pets_col.controls.clear()
                        # rebuild home for this role
                        home_view.controls[0].content = build_home_body()
                        page.views.clear()
                        page.views.append(home_view)
                        page.update()
                        load_all_pets()
                    else:
                        error_txt.value = "❌ อีเมลหรือรหัสผ่านไม่ถูกต้อง"
                        error_txt.color = PRIMARY
                        page.update()
                else:
                    error_txt.value = f"❌ เซิร์ฟเวอร์ตอบกลับ: {resp.status_code}"
                    error_txt.color = PRIMARY
                    page.update()
            except Exception:
                error_txt.value = "❌ เชื่อมต่อเซิร์ฟเวอร์ไม่ได้"
                error_txt.color = PRIMARY
                page.update()

        def deco(color, icon, angle, **pos):
            return ft.Container(
                **pos, rotate=ft.Rotate(angle=angle), opacity=0.18,
                content=ft.Container(
                    width=54, height=72, border_radius=4,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.Alignment(-1, -1), end=ft.alignment.Alignment(1, 1),
                        colors=[color, DARK],
                    ),
                    content=ft.Text(icon, size=22, text_align="center"),
                    alignment=ft.alignment.Alignment(0, 0),
                ),
            )

        return ft.View(
            route="/", bgcolor="#111", padding=0,
            controls=[ft.Stack(expand=True, controls=[
                deco("#E8936A", "🐶", -0.3, right=-10, top=60),
                deco("#5B8DB8", "🐱", 0.25, left=-8, top=180),
                deco("#9B6BB5", "🐾", -0.15, right=10, top=340),
                deco("#6AAF6E", "🌿", 0.35, left=5, bottom=200),
                deco("#E8C46A", "⭐", -0.2, right=-5, bottom=120),
                ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=0, controls=[
                    ft.Container(
                        padding=ft.padding.only(left=28, right=28, top=72, bottom=32),
                        content=ft.Column([
                            ft.Row([
                                ft.Container(width=44, height=44, border_radius=12, bgcolor=PRIMARY,
                                             content=ft.Text("🐾", size=22, text_align="center"),
                                             alignment=ft.alignment.Alignment(0, 0)),
                                ft.Container(width=12),
                                ft.Column([
                                    ft.Text("PET HOTEL", size=22, weight=ft.FontWeight.BOLD, color="#FFF"),
                                    ft.Text("Your pet hotel dashboard", size=11, color="#666"),
                                ], spacing=1),
                            ]),
                            ft.Container(height=36),
                            ft.Text("ยินดีต้อนรับกลับ 👋", size=24, weight=ft.FontWeight.BOLD, color="#FFF"),
                            ft.Container(height=6),
                            ft.Text("เข้าสู่ระบบเพื่อจัดการโรงแรมสัตว์ของคุณ", size=13, color="#AAAAAA"),
                        ], spacing=0),
                    ),
                    ft.Container(
                        margin=ft.margin.symmetric(horizontal=20),
                        padding=ft.padding.all(24), border_radius=16,
                        bgcolor="#1C1C1C", border=ft.border.all(1, "#2A2A2A"),
                        shadow=ft.BoxShadow(spread_radius=0, blur_radius=30,
                                            color=ft.Colors.with_opacity(0.5, "#000"), offset=ft.Offset(0, 8)),
                        content=ft.Column([
                            tf_email, ft.Container(height=12), tf_password,
                            ft.Container(height=4), error_txt, ft.Container(height=8),
                            btn("เข้าสู่ระบบ", do_login, height=50, radius=10,
                                icon=ft.Icons.ARROW_FORWARD, expand=True),
                        ], spacing=0),
                    ),
                    ft.Container(
                        margin=ft.margin.only(left=20, right=20, top=16, bottom=24),
                        padding=ft.padding.symmetric(horizontal=16, vertical=10),
                        border_radius=8,
                        bgcolor=ft.Colors.with_opacity(0.06, PRIMARY),
                        border=ft.border.all(1, ft.Colors.with_opacity(0.15, PRIMARY)),
                        content=ft.Row([
                            ft.Icon(ft.Icons.INFO_OUTLINE, color=PRIMARY, size=14),
                            ft.Container(width=8),
                            ft.Text("ใช้ email และ password จากตาราง users ในฐานข้อมูล",
                                    size=11, color="#BBBBBB"),
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ),
                ]),
            ])],
        )

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            page.update()

    page.on_view_pop = view_pop
    page.views.append(build_login_view())
    page.update()


ft.app(main)