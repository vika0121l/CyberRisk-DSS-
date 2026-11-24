
from pathlib import Path
from html import escape
from base64 import b64encode

import streamlit as st

from database import (
    initialize_database,
    get_assets,
    get_threats,
    add_threat,
    get_connection,
)
from components import render_footer


# ============================================================
# 1. ІНІЦІАЛІЗАЦІЯ ТА СТИЛІ
# ============================================================

initialize_database()

CSS = Path(__file__).resolve().parents[1] / "styles" / "threats.css"

if CSS.exists():
    st.markdown(
        f'<style>{CSS.read_text(encoding="utf-8")}</style>',
        unsafe_allow_html=True,
    )


CATEGORIES = [
    "Несанкціонований доступ",
    "Шкідливе програмне забезпечення",
    "Фішинг та соціальна інженерія",
    "Мережева атака",
    "Витік інформації",
    "Відмова в обслуговуванні",
    "Людський фактор",
    "Внутрішні загрози",
    "Помилки персоналу",
    "Експлуатація вразливостей",
    "Компрометація облікових даних",
    "Фізичні загрози",
    "Технічні збої",
    "Порушення електроживлення",
    "Інше",
]


# ============================================================
# 2. СТАН СТОРІНКИ
# ============================================================

if "threat_action" not in st.session_state:
    st.session_state.threat_action = None

# Одноразове зелене сповіщення після успішної операції та st.rerun().
# Стилизується в styles/threats.css (узгоджений стиль CyberRisk DSS).
completed_action = st.session_state.pop("threat_success", None)
if completed_action:
    st.toast(completed_action, icon=":material/check_circle:")


def toggle_threat_action(action):
    """Відкриття або закриття відповідної форми."""
    current_action = st.session_state.threat_action

    if current_action == action:
        st.session_state.threat_action = None
    else:
        st.session_state.threat_action = action




def stat_icon(name):
    """Іконки в тому самому стилі, що на сторінці «Інформаційні активи».
    SVG передаємо як data URI (Base64), щоб Streamlit не приховував іконки.
    """
    paths = {
        "threats": '<path d="M12 2 2 20h20L12 2Z"/><path d="M12 8v5M12 17h.01"/>',
        "assets": '<rect x="4" y="3" width="16" height="7" rx="2"/><rect x="4" y="14" width="16" height="7" rx="2"/><path d="M8 6.5h.01M8 17.5h.01"/>',
        "categories": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    }
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" '
        'viewBox="0 0 24 24" fill="none" stroke="#2867C8" '
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        f'{paths[name]}</svg>'
    )
    encoded = b64encode(svg.encode("utf-8")).decode("ascii")
    return f'<img src="data:image/svg+xml;base64,{encoded}" width="28" height="28" alt="">'

# ============================================================
# 3. ЗАВАНТАЖЕННЯ ДАНИХ
# ============================================================

assets = get_assets()
threats = get_threats()

asset_labels = {
    int(a[0]): str(a[1])
    for a in assets
}

asset_choices = {
    f"ID {a[0]} — {a[1]}": a[0]
    for a in assets
}

unique_assets = len({r[1] for r in threats})
unique_categories = len({r[3] for r in threats})


# ============================================================
# 4. ВЕРХНІЙ БАНЕР
# ============================================================

st.html("""
<div class="th-hero">
    <div>
        <div class="th-eyebrow">
            CYBERRISK DSS / СИСТЕМА ПІДТРИМКИ ПРИЙНЯТТЯ РІШЕНЬ
        </div>

        <h1>Загрози</h1>

        <p>
            Реєстрація, класифікація та облік загроз
            інформаційним активам підприємства
        </p>
    </div>

    <div class="th-hero-icon">
        <svg
            viewBox="0 0 64 64"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
        >
            <path d="M32 6 54 15v16c0 14-10 23-22 28C20 54 10 45 10 31V15L32 6Z"/>
            <path d="M32 20v17"/>
            <circle cx="32" cy="45" r="2" fill="currentColor" stroke="none"/>
        </svg>
    </div>
</div>
""")


# ============================================================
# 5. АНАЛІТИЧНІ ПОКАЗНИКИ — як в «Інформаційних активах»
# ============================================================

st.html(f"""
<div class="th-stats">
    <div class="th-stat">
        <div class="th-stat-icon">{stat_icon("threats")}</div>
        <div class="th-stat-copy">
            <div class="th-stat-label">Усього загроз</div>
            <div class="th-stat-value">{len(threats)}</div>
            <div class="th-stat-note">Зареєстровано в системі</div>
        </div>
    </div>
    <div class="th-stat">
        <div class="th-stat-icon">{stat_icon("assets")}</div>
        <div class="th-stat-copy">
            <div class="th-stat-label">Активи із загрозами</div>
            <div class="th-stat-value">{unique_assets}</div>
            <div class="th-stat-note">Із {len(assets)} зареєстрованих активів</div>
        </div>
    </div>
    <div class="th-stat">
        <div class="th-stat-icon">{stat_icon("categories")}</div>
        <div class="th-stat-copy">
            <div class="th-stat-label">Категорії загроз</div>
            <div class="th-stat-value">{unique_categories}</div>
            <div class="th-stat-note">Представлено в реєстрі</div>
        </div>
    </div>
</div>
""")


# ============================================================
# 6. ЗАГОЛОВОК РЕЄСТРУ — один рядок, як на сторінці активів
# ============================================================

st.html('<div class="th-section-title">▤ Реєстр кіберзагроз</div>')


# ============================================================
# 7. ПОШУК, ФІЛЬТРАЦІЯ, СОРТУВАННЯ І РЕЄСТР
# ============================================================

# Усі фільтри стосуються лише таблиці, а не статистичних карток.
# Запити до БД через get_threats() залишаються незмінними.


def category_style(category_name):
    """Колір позначає тип загрози, а не оцінку її небезпечності."""
    group_red = {"Шкідливе програмне забезпечення", "Витік інформації", "Компрометація облікових даних"}
    group_orange = {"Фішинг та соціальна інженерія", "Помилки персоналу", "Людський фактор"}
    group_violet = {"Мережева атака", "Відмова в обслуговуванні", "Експлуатація вразливостей"}
    group_teal = {"Фізичні загрози", "Технічні збої", "Порушення електроживлення"}
    if category_name in group_red:
        return "th-cat-red"
    if category_name in group_orange:
        return "th-cat-orange"
    if category_name in group_violet:
        return "th-cat-violet"
    if category_name in group_teal:
        return "th-cat-teal"
    return "th-cat-blue"


def filter_and_sort_threats(records, text, category, order):
    """Фільтрує записи get_threats(): (id, актив, загроза, категорія, опис)."""
    query = text.strip().casefold()
    filtered = [
        r for r in records
        if (category == "Усі категорії" or str(r[3]) == category)
        and (
            not query or query in " ".join(
                str(item or "") for item in (r[0], r[1], r[2], r[3], r[4])
            ).casefold()
        )
    ]
    if order == "Назва: А → Я":
        return sorted(filtered, key=lambda r: (str(r[2]).casefold(), int(r[0])))
    if order == "Назва: Я → А":
        return sorted(filtered, key=lambda r: (str(r[2]).casefold(), int(r[0])), reverse=True)
    if order == "ID: старі спочатку":
        return sorted(filtered, key=lambda r: int(r[0]))
    return sorted(filtered, key=lambda r: int(r[0]), reverse=True)


search_col, category_col, sort_col = st.columns([2.4, 1.4, 1.7], gap="small")

with search_col:
    search_text = st.text_input(
        "Пошук загрози",
        placeholder="Назва, актив, категорія, опис або ID...",
        key="th_search_text",
    )
with category_col:
    available_categories = sorted({str(r[3]) for r in threats if r[3]})
    selected_category = st.selectbox(
        "Категорія",
        ["Усі категорії"] + available_categories,
        key="th_category_filter",
    )
with sort_col:
    sort_order = st.selectbox(
        "Сортувати за",
        ["ID: нові спочатку", "ID: старі спочатку", "Назва: А → Я", "Назва: Я → А"],
        key="th_sort_order",
    )

visible_threats = filter_and_sort_threats(
    threats, search_text, selected_category, sort_order
)

if visible_threats:
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(r[0]))}</td>"
        f'<td class="th-name">{escape(str(r[2]))}</td>'
        f'<td>{escape(str(r[1] or "Невідомий актив"))}</td>'
        f'<td><span class="th-category {category_style(str(r[3]))}">{escape(str(r[3]))}</span></td>'
        f'<td>{escape(str(r[4] or "—"))}</td>'
        "</tr>"
        for r in visible_threats
    )
    st.html(
        """
        <div class="th-table-wrap">
            <table class="th-table">
                <thead><tr>
                    <th>ID</th><th>Назва загрози</th><th>Інформаційний актив</th>
                    <th>Категорія</th><th>Опис</th>
                </tr></thead>
                <tbody>
        """
        + rows
        + """
                </tbody>
            </table>
        </div>
        """
    )
elif not threats:
    st.info("Загрози ще не зареєстровані. Натисніть «Додати загрозу», щоб створити перший запис.")
else:
    st.info("За заданими умовами загроз не знайдено. Змініть пошуковий запит або категорію.")

st.caption(f"Показано загроз: {len(visible_threats)} із {len(threats)}")
st.html('<div class="th-rule"></div>')


# ============================================================
# 8. КНОПКИ КЕРУВАННЯ
# ============================================================

c1, c2, c3 = st.columns(3, gap="medium")

with c1:
    st.button(
        "＋ Додати загрозу",
        key="threat_action_add",
        type=(
            "primary"
            if st.session_state.threat_action == "add"
            else "secondary"
        ),
        use_container_width=True,
        on_click=toggle_threat_action,
        args=("add",),
    )

with c2:
    st.button(
        "✎ Редагувати загрозу",
        key="threat_action_edit",
        type=(
            "primary"
            if st.session_state.threat_action == "edit"
            else "secondary"
        ),
        use_container_width=True,
        disabled=not threats,
        on_click=toggle_threat_action,
        args=("edit",),
    )

with c3:
    st.button(
        "▣ Видалити загрозу",
        key="threat_action_delete",
        type=(
            "primary"
            if st.session_state.threat_action == "delete"
            else "secondary"
        ),
        use_container_width=True,
        disabled=not threats,
        on_click=toggle_threat_action,
        args=("delete",),
    )


# ============================================================
# 9. ФОРМА ДОДАВАННЯ ЗАГРОЗИ
# ============================================================

if st.session_state.threat_action == "add":

    if not assets:

        st.warning(
            "Спочатку зареєструйте інформаційний актив "
            "на сторінці «Інформаційні активи»."
        )

    else:

        with st.form("threat_add_form", clear_on_submit=True):

            asset_label = st.selectbox(
                "Інформаційний актив",
                list(asset_choices),
            )

            name = st.text_input(
                "Назва загрози"
            )

            category = st.selectbox(
                "Категорія загрози",
                CATEGORIES,
            )

            description = st.text_area(
                "Опис загрози"
            )

            submitted = st.form_submit_button(
                "Зберегти загрозу",
                type="primary",
                use_container_width=False,
            )

            if submitted:

                if not name.strip():

                    st.error(
                        "Вкажіть назву загрози."
                    )

                else:

                    try:
                        created_id = add_threat(
                            asset_choices[asset_label],
                            name.strip(),
                            category,
                            description.strip(),
                        )
                    except Exception as error:
                        st.error(f"Не вдалося додати загрозу: {error}")
                    else:
                        if created_id is None:
                            st.error("Не вдалося підтвердити створення загрози.")
                        else:
                            st.session_state.threat_success = (
                                "Кіберзагрозу успішно додано."
                            )
                            st.session_state.threat_action = None
                            st.rerun()


# ============================================================
# 10. ФОРМА РЕДАГУВАННЯ ЗАГРОЗИ
# ============================================================

elif st.session_state.threat_action == "edit":

    choices = {
        f"ID {r[0]} — {r[2]}": r[0]
        for r in threats
    }

    chosen = st.selectbox(
        "Оберіть загрозу",
        list(choices),
    )

    threat_id = choices[chosen]

    with get_connection() as conn:

        record = conn.execute(
            """
            SELECT asset_id, name, category, description
            FROM threats
            WHERE id = ?
            """,
            (threat_id,),
        ).fetchone()

    if record:

        asset_ids = list(asset_choices.values())

        with st.form("threat_edit_form"):

            asset_label = st.selectbox(
                "Інформаційний актив",
                list(asset_choices),
                index=(
                    asset_ids.index(record[0])
                    if record[0] in asset_ids
                    else 0
                ),
            )

            name = st.text_input(
                "Назва загрози",
                value=record[1],
            )

            category = st.selectbox(
                "Категорія загрози",
                CATEGORIES,
                index=(
                    CATEGORIES.index(record[2])
                    if record[2] in CATEGORIES
                    else len(CATEGORIES) - 1
                ),
            )

            description = st.text_area(
                "Опис загрози",
                value=record[3] or "",
            )

            submitted = st.form_submit_button(
                "Зберегти зміни",
                type="primary",
                use_container_width=False,
            )

            if submitted:

                if not name.strip():

                    st.error(
                        "Назва загрози не може бути порожньою."
                    )

                else:

                    new_asset_id = asset_choices[asset_label]

                    with get_connection() as conn:
                        linked_risks = conn.execute(
                            "SELECT COUNT(*) FROM risks WHERE threat_id = ?",
                            (threat_id,),
                        ).fetchone()[0]

                        if linked_risks > 0 and new_asset_id != record[0]:
                            update_blocked = True
                            updated_rows = 0
                        else:
                            update_blocked = False
                            cursor = conn.execute(
                                """
                                UPDATE threats
                                SET asset_id = ?, name = ?,
                                    category = ?, description = ?
                                WHERE id = ?
                                """,
                                (
                                    new_asset_id,
                                    name.strip(),
                                    category,
                                    description.strip(),
                                    threat_id,
                                ),
                            )
                            updated_rows = cursor.rowcount
                            conn.commit()

                    # Перезавантаження — лише після закриття з'єднання.
                    if update_blocked:
                        st.error(
                            "Не можна змінити інформаційний актив "
                            "загрози, яка вже використовується "
                            "в оцінюванні ризику."
                        )
                    elif updated_rows == 1:
                        st.session_state.threat_success = (
                            "Зміни кіберзагрози успішно збережено."
                        )
                        st.session_state.threat_action = None
                        st.rerun()
                    else:
                        st.error(
                            "Не вдалося оновити загрозу: запис не знайдено."
                        )


# ============================================================
# 11. ФОРМА ВИДАЛЕННЯ ЗАГРОЗИ
# ============================================================

elif st.session_state.threat_action == "delete":

    choices = {
        f"ID {r[0]} — {r[2]}": r[0]
        for r in threats
    }

    chosen = st.selectbox(
        "Оберіть загрозу для видалення",
        list(choices),
        key="th_delete_choice",
    )

    threat_id = choices[chosen]

    with get_connection() as conn:

        linked = conn.execute(
            """
            SELECT COUNT(*)
            FROM risks
            WHERE threat_id = ?
            """,
            (threat_id,),
        ).fetchone()[0]

    st.html("""
    <div class="th-delete-heading">
        <strong>Видалення загрози</strong>
        <span>
            Перевірка зв'язків та підтвердження операції
        </span>
    </div>
    """)

    if linked > 0:

        st.error(
            f"Видалення заблоковано. Ця загроза використовується "
            f"у {linked} оцінюваннях кіберризику. "
            "Спочатку видаліть або змініть пов'язані оцінки ризиків."
        )

    else:

        st.warning(
            "Обрана загроза не використовується "
            "в оцінюваннях ризиків. "
            "Після підтвердження її буде остаточно видалено."
        )

        confirm = st.checkbox(
            "Підтверджую видалення вибраної загрози",
            key=f"th_delete_confirm_{threat_id}",
        )

        if st.button(
            "Остаточно видалити",
            type="primary",
            disabled=not confirm,
            key="th_confirm_delete",
        ):

            with get_connection() as conn:
                linked_now = conn.execute(
                    "SELECT COUNT(*) FROM risks WHERE threat_id = ?",
                    (threat_id,),
                ).fetchone()[0]

                if linked_now == 0:
                    cursor = conn.execute(
                        "DELETE FROM threats WHERE id = ?",
                        (threat_id,),
                    )
                    deleted_rows = cursor.rowcount
                    conn.commit()
                else:
                    deleted_rows = 0

            if linked_now > 0:
                st.error(
                    "Видалення скасовано: загроза має "
                    "пов'язані оцінки ризиків."
                )
            elif deleted_rows == 1:
                st.session_state.threat_success = (
                    "Кіберзагрозу успішно видалено."
                )
                st.session_state.threat_action = None
                st.rerun()
            else:
                st.error("Загрозу не знайдено. Видалення не виконано.")


# ============================================================
# 12. ПОВІДОМЛЕННЯ — УЖЕ ПОКАЗАНО НА ПОЧАТКУ СТОРІНКИ
# ============================================================


# ============================================================
# 13. НИЖНІЙ РОЗДІЛЮВАЧ І ФУТЕР
# ============================================================

st.html('<div class="th-bottom-rule"></div>')

render_footer()
