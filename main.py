import flet as ft
import sqlite3
from datetime import datetime

# --- Database Setup ---
def setup_database():
    conn = sqlite3.connect("premium_notes.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    return conn

# --- Main App ---
def main(page: ft.Page):
    page.title = "Premium Notepad"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 400
    page.window_height = 700
    page.padding = 0

    conn = setup_database()
    current_note_id = [None]

    notes_list_view = ft.ListView(expand=True, spacing=10, padding=15)
    
    editor_title = ft.TextField(
        hint_text="Enter Title...",
        text_size=22,
        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
        border=ft.InputBorder.NONE,
        content_padding=15
    )
    
    editor_content = ft.TextField(
        hint_text="Start typing your notes here...",
        multiline=True,
        expand=True,
        border=ft.InputBorder.NONE,
        content_padding=15
    )

    home_view = ft.Container(expand=True, visible=True)
    editor_view = ft.Container(expand=True, visible=False)

    def load_notes():
        notes_list_view.controls.clear()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, content, timestamp FROM notes ORDER BY id DESC")
        records = cursor.fetchall()
        
        if not records:
            notes_list_view.controls.append(
                ft.Row(
                    controls=[ft.Text("No notes found. Create one!", color="gray")],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            )

        for row in records:
            note_id, title, content, timestamp = row
            display_title = title if title else "Untitled Note"
            display_content = (content[:50] + "...") if len(content) > 50 else content

            note_card = ft.Card(
                elevation=4,
                margin=8,
                content=ft.Container(
                    padding=20,
                    content=ft.Column(
                        controls=[
                            ft.Text(display_title, weight=ft.FontWeight.BOLD, size=18),
                            ft.Text(display_content, color="white54", size=14),
                            ft.Text(timestamp, size=11, color="gray", italic=True)
                        ],
                        spacing=5
                    ),
                    on_click=lambda e, nid=note_id: open_editor(nid)
                )
            )
            notes_list_view.controls.append(note_card)
        
        page.update()

    def open_editor(note_id=None):
        current_note_id[0] = note_id
        editor_title.value = ""
        editor_content.value = ""
        
        if note_id:
            cursor = conn.cursor()
            cursor.execute("SELECT title, content FROM notes WHERE id=?", (note_id,))
            row = cursor.fetchone()
            if row:
                editor_title.value = row[0]
                editor_content.value = row[1]
                
        home_view.visible = False
        editor_view.visible = True
        page.update()

    def go_home(e):
        home_view.visible = True
        editor_view.visible = False
        page.update()

    def save_note(e):
        title = editor_title.value.strip() if editor_title.value else ""
        content = editor_content.value.strip() if editor_content.value else ""
        
        if not title and not content:
            go_home(None)
            return
            
        timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")
        cursor = conn.cursor()
        
        if current_note_id[0]:
            cursor.execute("UPDATE notes SET title=?, content=?, timestamp=? WHERE id=?", 
                           (title, content, timestamp, current_note_id[0]))
        else:
            cursor.execute("INSERT INTO notes (title, content, timestamp) VALUES (?, ?, ?)", 
                           (title, content, timestamp))
        
        conn.commit()
        load_notes()
        go_home(None)

    def delete_note(e):
        if current_note_id[0]:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes WHERE id=?", (current_note_id[0],))
            conn.commit()
            load_notes()
        go_home(None)

    # --- 100% Crash-Proof Custom Buttons (Using Containers) ---
    btn_add = ft.Container(
        content=ft.Text("+ CREATE NEW NOTE", color="white", weight=ft.FontWeight.BOLD),
        bgcolor="teal", padding=15, border_radius=8,
        on_click=lambda e: open_editor(None)
    )

    btn_back = ft.Container(
        content=ft.Text("< BACK", color="white", weight=ft.FontWeight.BOLD),
        bgcolor="#333333", padding=10, border_radius=5,
        on_click=go_home
    )

    btn_delete = ft.Container(
        content=ft.Text("DELETE", color="white", weight=ft.FontWeight.BOLD),
        bgcolor="red", padding=10, border_radius=5,
        on_click=delete_note
    )

    btn_save = ft.Container(
        content=ft.Text("SAVE", color="white", weight=ft.FontWeight.BOLD),
        bgcolor="teal", padding=10, border_radius=5,
        on_click=save_note
    )

    # --- Home Screen UI ---
    home_view.content = ft.Column(
        expand=True,
        controls=[
            ft.AppBar(
                title=ft.Text("My Notes", weight=ft.FontWeight.W_800),
                bgcolor="#1e1e1e"
            ),
            notes_list_view,
            ft.Row(
                controls=[btn_add],
                alignment=ft.MainAxisAlignment.CENTER
            ),
            ft.Container(height=15)
        ]
    )

    # --- Editor Screen UI ---
    editor_view.content = ft.Column(
        expand=True,
        controls=[
            # Custom Top Bar bypassing AppBar restrictions
            ft.Container(
                padding=10,
                bgcolor="#1e1e1e",
                content=ft.Row(
                    controls=[
                        btn_back,
                        ft.Container(expand=True), # Adds empty space in middle
                        btn_delete,
                        ft.Container(width=5),
                        btn_save
                    ]
                )
            ),
            ft.Container(
                content=ft.Column([editor_title, ft.Divider(height=1, color="gray"), editor_content], expand=True),
                padding=10,
                expand=True
            )
        ]
    )

    page.add(home_view, editor_view)
    load_notes()

if __name__ == "__main__":
    ft.app(target=main)