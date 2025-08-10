import streamlit as st

# Настройка базовой цветовой схемы
st.markdown("""
    <style>
    body {
        background-color: #CACAC7;
        color: #262626;
    }
    .stButton>button {
        background-color: #ddf62b;
        color: #262626;
        font-weight: bold;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Заголовок
st.title("📚 Книжный клуб «Вертикаль»")

# Подзаголовок
st.subheader("Выберите своё имя, чтобы продолжить:")

# Список участников
members = ["Лилия", "Олег", "Валерия", "Стас", "Наталья", "Лера"]

# Выпадающий список
selected_name = st.selectbox("Участник:", members)

# Кнопка продолжения
if st.button("Перейти к своим книгам"):
    st.session_state["user"] = selected_name
    st.switch_page("pages/user_page.py")  # Переход на персональную страницу
