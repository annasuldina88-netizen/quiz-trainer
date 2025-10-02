import streamlit as st
import pandas as pd
import os
import json
from pathlib import Path

# === Настройки ===
CATEGORIES_DIR = "categories"
PROGRESS_DIR = "progress"

# Создаём папки, если их нет
Path(CATEGORIES_DIR).mkdir(exist_ok=True)
Path(PROGRESS_DIR).mkdir(exist_ok=True)

# === Стили ===
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4edf9 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .main-header {
        text-align: center;
        color: #2c3e50;
        margin-bottom: 2rem;
    }
    .level-box {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin: 1rem 0;
    }
    .question-card {
        background: #f8fafc;
        padding: 1rem;
        border-left: 4px solid #3498db;
        margin: 0.8rem 0;
        border-radius: 8px;
    }
    .progress-text {
        font-weight: bold;
        color: #2980b9;
        font-size: 1.1em;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


# === Вспомогательные функции ===
def load_categories():
    """Загружает категории из Excel-файлов."""
    categories = {}
    for file in os.listdir(CATEGORIES_DIR):
        if file.endswith(".xlsx"):
            cat_name = os.path.splitext(file)[0]
            try:
                df = pd.read_excel(os.path.join(CATEGORIES_DIR, file))
                required = {'Уровень', 'Вопрос', 'Ответ'}
                if not required.issubset(df.columns):
                    st.warning(f"Файл {file} пропущен: нет нужных столбцов")
                    continue

                df = df.dropna(subset=['Уровень', 'Вопрос', 'Ответ'])
                df['Уровень'] = df['Уровень'].astype(int)

                levels = {}
                for _, row in df.iterrows():
                    lvl = row['Уровень']
                    question = str(row['Вопрос']).strip()
                    main_answer = str(row['Ответ']).strip()
                    alt_str = str(row.get('Альтернативы', '')).strip()

                    # Все правильные варианты в нижнем регистре
                    correct_answers = [main_answer.lower()]
                    if alt_str:
                        alts = [a.strip().lower() for a in alt_str.split(',') if a.strip()]
                        correct_answers.extend(alts)

                    if lvl not in levels:
                        levels[lvl] = []
                    levels[lvl].append({
                        'Вопрос': question,
                        'Ответ_для_показа': main_answer,
                        'Правильные': correct_answers
                    })
                categories[cat_name] = levels
            except Exception as e:
                st.error(f"Ошибка загрузки {file}: {e}")
    return categories


def get_progress_file(username):
    return os.path.join(PROGRESS_DIR, f"{username}.json")


def load_user_progress(username):
    file_path = get_progress_file(username)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_user_progress(username, progress):
    file_path = get_progress_file(username)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


# === Инициализация состояния ===
if 'username' not in st.session_state:
    st.session_state.username = None
if 'current_category' not in st.session_state:
    st.session_state.current_category = None
if 'current_level' not in st.session_state:
    st.session_state.current_level = None

# === Экран приветствия ===
if st.session_state.username is None:
    st.markdown("<h1 class='main-header'>🎬 КиноТренажёр</h1>", unsafe_allow_html=True)
    st.write("Добро пожаловать! Введите своё имя, чтобы сохранять прогресс.")

    username = st.text_input("Ваше имя (латиницей или кириллицей):", key="login")
    if st.button("Начать", type="primary"):
        if username.strip():
            st.session_state.username = username.strip()
            st.rerun()
        else:
            st.warning("Пожалуйста, введите имя.")
    st.stop()

# === Основной интерфейс ===
st.markdown(f"<h1 class='main-header'>Привет, {st.session_state.username}! 👋</h1>", unsafe_allow_html=True)

# Загрузка данных
categories = load_categories()
if not categories:
    st.error("⚠️ Папка `categories` пуста или не содержит Excel-файлов.")
    st.stop()

# Выбор категории
col1, col2 = st.columns([2, 1])
with col1:
    selected_cat = st.selectbox("Выберите категорию", list(categories.keys()))
with col2:
    if st.button("🔄 Обновить категории"):
        st.rerun()

# Кнопка начала
if st.button("🚀 Начать тренировку", type="primary"):
    st.session_state.current_category = selected_cat
    st.session_state.current_level = 1

# Отображение тренажёра
if st.session_state.current_category:
    cat = st.session_state.current_category
    levels = categories[cat]
    level_num = st.session_state.current_level

    # Загружаем прогресс пользователя
    user_progress = load_user_progress(st.session_state.username)
    cat_key = f"cat_{cat}"
    if cat_key not in user_progress:
        user_progress[cat_key] = {}

    # Определяем, какие уровни открыты
    max_level = max(levels.keys())
    unlocked_up_to = 1
    for lvl in range(1, max_level + 1):
        lvl_key = f"lvl_{lvl}"
        if lvl_key in user_progress[cat_key]:
            if user_progress[cat_key][lvl_key].get("correct", 0) >= 10:
                unlocked_up_to = lvl + 1 if lvl + 1 <= max_level else max_level
            else:
                break
        else:
            if lvl == 1:
                unlocked_up_to = 1
            break

    # Выбор уровня
    st.markdown(f"### 📚 Категория: **{cat}**")
    level_choice = st.selectbox(
        "Выберите уровень",
        options=[i for i in range(1, max_level + 1)],
        index=min(level_num - 1, unlocked_up_to - 1),
        format_func=lambda x: f"Уровень {x} {'🔓' if x <= unlocked_up_to else '🔒'}"
    )

    if level_choice > unlocked_up_to:
        st.warning("Этот уровень ещё не открыт. Пройдите предыдущий уровень с 10+ правильными ответами.")
        st.stop()

    st.session_state.current_level = level_choice
    questions = levels.get(level_choice, [])

    if not questions:
        st.error("Нет вопросов для этого уровня.")
        st.stop()

    # Прогресс по уровню
    lvl_key = f"lvl_{level_choice}"
    if lvl_key not in user_progress[cat_key]:
        user_progress[cat_key][lvl_key] = {
            "correct": 0,
            "total": len(questions),
            "mistakes": list(range(len(questions)))  # индексы неправильных
        }

    lvl_data = user_progress[cat_key][lvl_key]
    correct = lvl_data["correct"]
    total = lvl_data["total"]
    mistakes = set(lvl_data["mistakes"])

    # Показываем только неправильные вопросы при повторе
    if mistakes:
        questions_to_show = [(i, q) for i, q in enumerate(questions) if i in mistakes]
        st.info(f"🔁 Повтор: {len(questions_to_show)} вопросов из {total}")
    else:
        st.success("🎉 Уровень полностью пройден!")
        questions_to_show = []

    # Отображение прогресса
    st.markdown(f"<div class='progress-text'>Прогресс: {correct} / {total}</div>", unsafe_allow_html=True)
    st.progress(correct / total if total > 0 else 0)

    # Вопросы
    any_answered = False
    for idx, q in questions_to_show:
        with st.container():
            st.markdown(f"<div class='question-card'><strong>Вопрос {idx + 1}:</strong> {q['Вопрос']}</div>",
                        unsafe_allow_html=True)
            user_ans = st.text_input(f"Ваш ответ", key=f"ans_{level_choice}_{idx}", placeholder="Введите ответ...")

            if user_ans:
                any_answered = True
                if user_ans.lower() in q['Правильные']:
                    if idx in mistakes:
                        mistakes.remove(idx)
                        lvl_data["correct"] = total - len(mistakes)
                        save_user_progress(st.session_state.username, user_progress)
                    st.markdown("<div class='success-box'>✅ Верно!</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='error-box'>❌ Неверно. Правильный ответ: {q['Ответ_для_показа']}</div>",
                                unsafe_allow_html=True)

    # Если все вопросы пройдены
    if not mistakes:
        st.balloons()
        st.success("✨ Поздравляем! Уровень пройден полностью!")
        if level_choice < max_level:
            st.info("Следующий уровень будет открыт автоматически!")

    # Кнопки навигации
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🏠 В главное меню"):
            st.session_state.current_category = None
            st.rerun()
    with col2:
        if st.button("📚 Сменить категорию"):
            st.session_state.current_category = None
            st.rerun()
    with col3:
        if st.button("🔄 Другой уровень"):
            st.rerun()

# Кнопка выхода
st.divider()
if st.button("🚪 Выйти (сохранение автоматическое)"):
    st.session_state.username = None
    st.session_state.current_category = None
    st.rerun()