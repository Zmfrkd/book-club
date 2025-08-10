import streamlit as st
import requests
import json
import os




DATA_FILE = "users_data.json"

# --- Функции для работы с данными ---
def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

import os
import streamlit as st
import requests

@st.cache_data(ttl=86400)  # кэшируем сутки
def get_book_info(title: str):
    api_key = st.secrets.get("GOOGLE_BOOKS_API_KEY") or os.getenv("GOOGLE_BOOKS_API_KEY")

    def try_google(q: str):
        params = {
            "q": q,
            "maxResults": 30,
            "printType": "books",
            "orderBy": "relevance",
            "langRestrict": "ru",
        }
        PROXY_URL = "https://googlebooks-proxy.onrender.com/books"
        r = requests.get(PROXY_URL, params=params, timeout=12)
        r.raise_for_status()

        items = r.json().get("items", []) or []
        for it in items:
            v = it.get("volumeInfo", {}) or {}
            pc = v.get("pageCount")
            if isinstance(pc, int) and pc > 0:
                return {
                    "title": v.get("title", q),
                    "author": ", ".join(v.get("authors", [])) if v.get("authors") else "",
                    "description": v.get("description", "") or "",
                    "pageCount": pc,
                    "thumbnail": (v.get("imageLinks") or {}).get("thumbnail", "") or ""
                }
        return None


    # 1) Google Books
    try:
        for q in (f'intitle:"{title}"', title):
            res = try_google(q)
            if res:
                return res
    except requests.HTTPError as e:
        st.sidebar.error(f"Ошибка Google Books HTTP: {e}")
    except Exception as e:
        st.sidebar.error(f"Ошибка Google Books: {e}")

    # 2) Open Library fallback
    try:
        r = requests.get("https://openlibrary.org/search.json", params={"title": title}, timeout=10)
        r.raise_for_status()
        docs = r.json().get("docs", []) or []

        # Отладка — показываем весь ответ
        st.sidebar.subheader("📚 Open Library API")
        st.sidebar.write("Параметры запроса:", {"title": title})
        st.sidebar.write("HTTP статус:", r.status_code)
        st.sidebar.json(docs)

        for d in docs:
            n = d.get("number_of_pages_median") or d.get("number_of_pages")
            if isinstance(n, int) and n > 0:
                return {
                    "title": d.get("title", title),
                    "author": ", ".join(d.get("author_name", [])) if d.get("author_name") else "",
                    "description": "",
                    "pageCount": n,
                    "thumbnail": ""
                }
    except Exception as e:
        st.sidebar.error(f"Ошибка Open Library: {e}")

    return None


# --- Вспомогательные функции для синхронизации виджетов прогресса ---
def _keys_for_idx(idx):
    return (f"read_num_{idx}", f"read_slider_{idx}")

def sync_from_num(idx, total):
    num_key, slider_key = _keys_for_idx(idx)
    # clamp и синхронизация
    v = int(st.session_state[num_key])
    v = max(0, min(int(total), v))
    st.session_state[num_key] = v
    st.session_state[slider_key] = v

def sync_from_slider(idx):
    num_key, slider_key = _keys_for_idx(idx)
    st.session_state[num_key] = int(st.session_state[slider_key])

# --- Streamlit UI ---
st.set_page_config(page_title="Книжный клуб", layout="centered")

st.markdown("""
    <style>
    body { background-color: #CACAC7; color: #262626; }
    .stButton>button { background-color: #ddf62b; color: #262626; font-weight: bold; border-radius: 10px; }
    [data-baseweb="input"] input, .stTextInput input { color:#262626 !important; }
    </style>
    """, unsafe_allow_html=True)

# Проверка пользователя
if "user" not in st.session_state:
    st.warning("Пожалуйста, вернитесь на главную страницу и выберите имя.")
    st.stop()

user = st.session_state["user"]
all_users_data = load_user_data()
if user not in all_users_data:
    all_users_data[user] = []

st.session_state.user_books = all_users_data[user]

st.title(f"Страница {user}")

# --- Режимы ручного ввода ---
if "manual_entry_mode" not in st.session_state:
    st.session_state.manual_entry_mode = False

if "manual_full_entry_mode" not in st.session_state:
    st.session_state.manual_full_entry_mode = False

# --- Добавление книги через API ---
st.subheader("Добавить книгу")

with st.form("add_book_form"):
    book_title = st.text_input("Название книги")
    submitted = st.form_submit_button("Поиск книги")

    if submitted and book_title.strip():
        if any(book.get("title","").lower() == book_title.strip().lower() for book in st.session_state.user_books):
            st.warning("❗ Эта книга уже добавлена.")
        else:
            book_info = get_book_info(book_title)
            if book_info is None or book_info["pageCount"] == 0:
                st.warning("❗ Не удалось найти информацию о книге. Укажите количество страниц вручную ниже.")
                st.session_state.manual_entry_mode = True
                st.session_state.pending_title = book_title.strip()
            else:
                st.session_state.user_books.append({
                    "title": book_info["title"],
                    "author": book_info["author"],
                    "description": book_info["description"],
                    "thumbnail": book_info["thumbnail"],
                    "total": int(book_info["pageCount"]),
                    "read": 0,
                    "pages_source": "api"
                })
                all_users_data[user] = st.session_state.user_books
                save_user_data(all_users_data)
                st.success(f"✅ Книга «{book_info['title']}» добавлена ({book_info['pageCount']} стр.)")

# --- Кнопка: ручной ввод всей информации ---
st.markdown("---")
if st.button("➕ Добавить книгу вручную"):
    st.session_state.manual_full_entry_mode = True

# --- Ручной ввод количества страниц (если API не сработал) ---
if st.session_state.manual_entry_mode:
    manual_pages = st.number_input("Введите количество страниц вручную", min_value=1, max_value=3000, step=1)
    if st.button("Добавить вручную"):
        title = st.session_state.get("pending_title", "Без названия")
        st.session_state.user_books.append({
            "title": title,
            "total": int(manual_pages),
            "read": 0,
            "pages_source": "manual"
        })
        all_users_data[user] = st.session_state.user_books
        save_user_data(all_users_data)
        st.success(f"✅ Книга «{title}» добавлена ({int(manual_pages)} стр.)")
        st.session_state.manual_entry_mode = False

# --- Ручной ввод полной информации о книге ---
if st.session_state.manual_full_entry_mode:
    st.subheader("📘 Ручной ввод книги")

    with st.form("manual_full_form"):
        title = st.text_input("Название", key="manual_title")
        author = st.text_input("Автор", key="manual_author")
        total = st.number_input("Количество страниц", min_value=1, max_value=3000, step=1, key="manual_total")
        description = st.text_area("Описание (необязательно)", key="manual_desc")
        submitted_manual = st.form_submit_button("Добавить книгу")

        if submitted_manual and title.strip():
            st.session_state.user_books.append({
                "title": title.strip(),
                "author": author.strip(),
                "description": description.strip(),
                "thumbnail": "",
                "total": int(total),
                "read": 0,
                "pages_source": "manual"
            })
            all_users_data[user] = st.session_state.user_books
            save_user_data(all_users_data)
            st.success(f"✅ Книга «{title}» добавлена вручную.")
            st.session_state.manual_full_entry_mode = False

# --- Список книг и прогресс ---
st.subheader("Мои книги")

if st.session_state.user_books:
    for idx, book in enumerate(st.session_state.user_books):
        title = book.get("title", "Без названия")
        read = int(book.get("read", 0))
        total = int(book.get("total", 1))
        percent = int((read / total) * 100) if total else 0
        is_finished = read >= total
        bg_color = "#ddf62b" if is_finished else "#f2f2f2"

        with st.container():
            col1, col2 = st.columns([5, 2])
            with col1:
                st.markdown(f"""
                    <div style="padding: 10px; background-color: {bg_color}; border-radius: 10px;">
                        <b>{title}</b><br>
                        {read} / {total} стр. ({percent}%)
                    </div>
                """, unsafe_allow_html=True)

                if book.get("thumbnail"):
                    st.image(book["thumbnail"], width=100)
                if book.get("author"):
                    st.markdown(f"Автор: _{book['author']}_")
                if book.get("description"):
                    st.markdown(f"<div style='font-size:12px'>{book['description'][:300]}...</div>", unsafe_allow_html=True)

                # --- СИНХРОННЫЙ ПРОГРЕСС: number_input <-> slider ---
                num_key, slider_key = _keys_for_idx(idx)
                # Инициализируем состояние по умолчанию
                if num_key not in st.session_state:
                    st.session_state[num_key] = read
                if slider_key not in st.session_state:
                    st.session_state[slider_key] = read

                # Рисуем два виджета прогресса с коллбэками для синхронизации
                pg_col1, pg_col2 = st.columns([2, 5])
                with pg_col1:
                    st.number_input(
                        "Прочитано (ввести)",
                        min_value=0, max_value=total, step=1,
                        key=num_key,
                        on_change=sync_from_num,
                        args=(idx, total)
                    )
                with pg_col2:
                    st.slider(
                        "Обновить прогресс (перетащить)",
                        min_value=0, max_value=total, step=1,
                        key=slider_key,
                        on_change=sync_from_slider,
                        args=(idx,)
                    )

                # единое новое значение после синхронизации
                new_value = int(st.session_state[slider_key])
                if new_value != read:
                    # сохраняем в книгу
                    book["read"] = new_value
                    all_users_data[user] = st.session_state.user_books
                    save_user_data(all_users_data)
                    read = new_value
                    percent = int((read / total) * 100) if total else 0

                st.progress(percent)

            with col2:
                # --- Изменение количества страниц (даже если из API) ---
                with st.expander("✏️ Изменить страницы"):
                    new_total = st.number_input(
                        "Новое количество страниц",
                        min_value=1, max_value=3000, step=1, value=total,
                        key=f"total_edit_{idx}"
                    )
                    if st.button("Сохранить страницы", key=f"save_total_{idx}"):
                        book["total"] = int(new_total)
                        book["pages_source"] = "manual"  # помечаем, что переопределили вручную
                        # Подрезаем прогресс, если он стал больше общего
                        if book["read"] > book["total"]:
                            book["read"] = book["total"]
                            # и синхронизируем UI-виджеты
                            num_key, slider_key = _keys_for_idx(idx)
                            st.session_state[num_key] = int(book["read"])
                            st.session_state[slider_key] = int(book["read"])
                        all_users_data[user] = st.session_state.user_books
                        save_user_data(all_users_data)
                        st.success("Количество страниц обновлено.")

                # --- Удаление книги ---
                if st.button("🗑 Удалить книгу", key=f"del_{idx}"):
                    # чистим стейт виджетов, чтобы не конфликтовали ключи
                    num_key, slider_key = _keys_for_idx(idx)
                    if num_key in st.session_state: del st.session_state[num_key]
                    if slider_key in st.session_state: del st.session_state[slider_key]
                    del st.session_state.user_books[idx]
                    all_users_data[user] = st.session_state.user_books
                    save_user_data(all_users_data)
                    st.rerun()
else:
    st.info("Вы пока не добавили ни одной книги.")

# --- Статистика ---
st.subheader("Статистика")

total_read = sum(int(b.get("read", 0)) for b in st.session_state.user_books)
total_books = len(st.session_state.user_books)
finished_books = sum(1 for b in st.session_state.user_books if int(b.get("read", 0)) >= int(b.get("total", 1)))

st.markdown(f"**Всего книг:** {total_books}")
st.markdown(f"**Прочитано страниц:** {total_read}")
st.markdown(f"**Завершено книг:** {finished_books}")
