import streamlit as st
import json
import os



st.set_page_config(page_title="📈 Рейтинг участников", layout="centered")

# --- Стилизация ---
st.markdown("""
    <style>
    body {
        background-color: #CACAC7;
        color: #262626;
    }
    .card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
    }
    .leader {
        border-left: 8px solid #ddf62b;
    }
    .progress-bar {
        height: 14px;
        border-radius: 7px;
        background-color: #e0e0e0;
        margin-top: 5px;
        margin-bottom: 5px;
        overflow: hidden;
    }
    .progress {
        height: 100%;
        background-color: #ddf62b;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏆 Рейтинг участников")

# --- Загрузка данных ---
DATA_FILE = "users_data.json"

if not os.path.exists(DATA_FILE):
    st.info("Пока нет данных для отображения рейтинга.")
    st.stop()

with open(DATA_FILE, "r", encoding="utf-8") as f:
    all_users_data = json.load(f)

# --- Формирование рейтинга ---
rating = []

for name, books in all_users_data.items():
    read_pages = sum(b.get("read", 0) for b in books)
    total_pages = sum(b.get("total", 0) for b in books)
    finished_books = sum(1 for b in books if b.get("read") == b.get("total"))
    total_books = len(books)
    percent_read = int((read_pages / total_pages) * 100) if total_pages > 0 else 0

    rating.append({
        "name": name,
        "read": read_pages,
        "books": total_books,
        "finished": finished_books,
        "percent": percent_read
    })

# --- Сортировка по количеству прочитанного ---
rating_sorted = sorted(rating, key=lambda x: x["read"], reverse=True)

# --- Отображение карточек ---
for idx, user in enumerate(rating_sorted):
    highlight = "leader" if idx == 0 else ""
    st.markdown(f"""
        <div class="card {highlight}">
            <h4 style="margin-bottom: 4px;">{user['name']}</h4>
            <div style="font-size: 14px;">
                Прочитано: <b>{user['read']} стр.</b> &nbsp;|&nbsp;
                Книг всего: {user['books']} &nbsp;|&nbsp;
                Завершено: {user['finished']}
            </div>
            <div class="progress-bar">
                <div class="progress" style="width: {user['percent']}%;"></div>
            </div>
            <div style="font-size: 13px;">Прогресс: {user['percent']}%</div>
        </div>
    """, unsafe_allow_html=True)
