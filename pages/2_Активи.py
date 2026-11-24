from pathlib import Path
from html import escape
from base64 import b64encode
import ipaddress

import streamlit as st

from database import (
    get_assets,
    add_asset,
    asset_ip_exists,
    update_asset,
    delete_asset,
    get_connection,
)
from components import render_footer

# ============================================================
# 1. НАЛАШТУВАННЯ СТОРІНКИ
# ============================================================

css_path = (
    Path(__file__).resolve().parent.parent
    / "styles"
    / "assets.css"
)

if css_path.exists():
    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )


# ============================================================
# 2. ДОПОМІЖНІ ФУНКЦІЇ
# ============================================================

ASSET_TYPES = [
    "Сервер",
    "Комп'ютер",
    "Мережеве обладнання",
    "База даних",
    "Програмне забезпечення",
    "Інше",
]

def valid_ip_address(value):
    """Перевіряє IPv4 або IPv6. Порожня адреса дозволена."""
    if not value:
        return True

    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def show_message():
    """Одноразове зелене спливаюче повідомлення після успішної операції.

    Використовуємо session_state, тому сповіщення не зникає під час
    st.rerun() і не повторюється під час наступних оновлень сторінки.
    """
    message = st.session_state.pop("assets_message", None)
    if message:
        st.toast(message, icon="✅")


def change_action(action):
    """Відкриває або закриває форму активу."""

    if st.session_state.assets_active_action == action:
        st.session_state.assets_active_action = None
    else:
        st.session_state.assets_active_action = action


def asset_label(asset):
    return f"{asset[0]} — {asset[1]}"


def render_html(html):
    """Render custom HTML without Markdown interpreting indentation as code."""
    compact_html = " ".join(line.strip() for line in html.splitlines() if line.strip())
    st.markdown(compact_html, unsafe_allow_html=True)


def get_asset_link_counts(asset_id):
    """Кількість записів, що блокують безпечне видалення активу.

    Запити лише читають дані; остаточна перевірка також є у database.delete_asset.
    """
    with get_connection() as connection:
        return {
            "threats": connection.execute(
                "SELECT COUNT(*) FROM threats WHERE asset_id = ?", (asset_id,)
            ).fetchone()[0],
            "vulnerabilities": connection.execute(
                "SELECT COUNT(*) FROM vulnerabilities WHERE asset_id = ?", (asset_id,)
            ).fetchone()[0],
            "risks": connection.execute(
                "SELECT COUNT(*) FROM risks WHERE asset_id = ?", (asset_id,)
            ).fetchone()[0],
        }


def filter_sort_assets(items, query="", criticality="Усі рівні", order="Критичність: 5 → 1"):
    """Пошук за всіма видимими полями, фільтр та стабільне сортування."""
    needle = query.strip().casefold()
    matching = []
    for asset in items:
        level = int(asset[5])
        if criticality != "Усі рівні" and level != int(criticality.split(" ")[0]):
            continue
        searchable = " ".join(str(x) for x in asset if x is not None).casefold()
        if needle and needle not in searchable:
            continue
        matching.append(asset)

    if order == "Критичність: 5 → 1":
        return sorted(matching, key=lambda item: (-int(item[5]), str(item[1]).casefold(), item[0]))
    if order == "Критичність: 1 → 5":
        return sorted(matching, key=lambda item: (int(item[5]), str(item[1]).casefold(), item[0]))
    if order == "Назва: А → Я":
        return sorted(matching, key=lambda item: (str(item[1]).casefold(), item[0]))
    if order == "Назва: Я → А":
        return sorted(matching, key=lambda item: (str(item[1]).casefold(), item[0]), reverse=True)
    return sorted(matching, key=lambda item: item[0])


def stat_icon(name):
    """Безпечне відображення SVG-іконки як зображення Base64."""
    paths = {
        "assets": '<rect x="4" y="3" width="16" height="7" rx="2"/><rect x="4" y="14" width="16" height="7" rx="2"/><path d="M8 6.5h.01M8 17.5h.01"/>',
        "critical": '<path d="M12 3 2 20h20L12 3Z"/><path d="M12 9v5M12 17h.01"/>',
        "segment": '<circle cx="12" cy="12" r="3"/><circle cx="4" cy="5" r="2"/><circle cx="20" cy="5" r="2"/><circle cx="12" cy="21" r="2"/><path d="m6 6 4 4m8-4-4 4m-2 5v4"/>',
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

total_assets = len(assets)

critical_assets = sum(
    1 for asset in assets
    if int(asset[5]) == 5
)

network_segments = len({
    str(asset[4]).strip()
    for asset in assets
    if asset[4] and str(asset[4]).strip()
})

if "assets_active_action" not in st.session_state:
    st.session_state.assets_active_action = None

# Одноразове спливаюче повідомлення після успішної операції.
show_message()


# ============================================================
# 4. ВЕРХНІЙ БАНЕР
# ============================================================

render_html("""
<div class="cr-hero">
  <div>
    <div class="cr-eyebrow">CYBERRISK DSS / СИСТЕМА ПІДТРИМКИ ПРИЙНЯТТЯ РІШЕНЬ</div>
    <h1>Інформаційні активи</h1>
    <p>Управління інформаційними активами організації</p>
  </div>
  <svg class="cr-server" viewBox="0 0 160 140" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
    <defs><linearGradient id="srv" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#377ac7"/><stop offset="1" stop-color="#102c5b"/></linearGradient></defs>
    <ellipse cx="80" cy="128" rx="72" ry="10" fill="#79b6ff" opacity=".12"/>
    <g stroke="#72adf6" stroke-width="1.5">
      <rect x="20" y="14" width="120" height="33" rx="7" fill="url(#srv)"/>
      <rect x="20" y="54" width="120" height="33" rx="7" fill="url(#srv)"/>
      <rect x="20" y="94" width="120" height="33" rx="7" fill="url(#srv)"/>
    </g>
    <g stroke="#8cc7ff" stroke-width="3" stroke-linecap="round"><path d="M33 30h36M33 70h36M33 110h36"/></g>
    <g fill="#4ce0ff"><circle cx="125" cy="30" r="4"/><circle cx="125" cy="70" r="4"/><circle cx="125" cy="110" r="4"/></g>
  </svg>
</div>
""")

# ============================================================
# 5. КАРТКИ СТАТИСТИКИ
# ============================================================

render_html(f"""
<div class="cr-stats">
  <div class="cr-stat-card">
    <div class="cr-stat-icon">{stat_icon("assets")}</div>
    <div><div class="cr-stat-label">Усього активів</div><div class="cr-stat-value">{total_assets}</div><div class="cr-stat-note">Зареєстровано в системі</div></div>
  </div>
  <div class="cr-stat-card">
    <div class="cr-stat-icon">{stat_icon("critical")}</div>
    <div><div class="cr-stat-label">Критичні активи</div><div class="cr-stat-value">{critical_assets}</div><div class="cr-stat-note">Рівень критичності 5</div></div>
  </div>
  <div class="cr-stat-card">
    <div class="cr-stat-icon">{stat_icon("segment")}</div>
    <div><div class="cr-stat-label">Мережеві сегменти</div><div class="cr-stat-value">{network_segments}</div><div class="cr-stat-note">Унікальні сегменти</div></div>
  </div>
</div>
""")


# ============================================================
# 6. РЕЄСТР ІНФОРМАЦІЙНИХ АКТИВІВ
# ============================================================

st.markdown(
    '<div class="cr-section-title">'
    '▤ Реєстр інформаційних активів'
    '</div>',
    unsafe_allow_html=True,
)

if assets:
    # Фільтри не змінюють БД: працюють тільки з поточним списком get_assets().
    search_col, level_col, sort_col = st.columns([2.4, 1.4, 1.7], gap="small")
    with search_col:
        search_query = st.text_input(
            "Пошук активу",
            placeholder="Назва, тип, IP, сегмент або опис...",
            key="assets_registry_search",
        )
    with level_col:
        selected_level = st.selectbox(
            "Критичність",
            ["Усі рівні", "5 — Критична", "4 — Висока", "3 — Середня", "2 — Низька", "1 — Дуже низька"],
            key="assets_registry_level",
        )
    with sort_col:
        selected_order = st.selectbox(
            "Сортувати за",
            ["Критичність: 5 → 1", "Критичність: 1 → 5", "Назва: А → Я", "Назва: Я → А", "ID"],
            key="assets_registry_sort",
        )

    visible_assets = filter_sort_assets(assets, search_query, selected_level, selected_order)
    criticality_names = {
        1: "Дуже низька",
        2: "Низька",
        3: "Середня",
        4: "Висока",
        5: "Критична",
    }

    if visible_assets:
        table_rows = []
        for asset in visible_assets:
            asset_id, name, asset_type, ip, segment, criticality, description = asset
            level = int(criticality)
            level_name = escape(criticality_names.get(level, "Невідома"))
            badge_class = f"cr-level-badge-{level}" if level in criticality_names else ""

            def safe(value):
                return escape(str(value)) if value is not None and str(value) else "—"

            table_rows.append(f"""
            <tr>
              <td>{safe(asset_id)}</td>
              <td class="cr-asset-name">{safe(name)}</td>
              <td>{safe(asset_type)}</td>
              <td>{safe(ip)}</td>
              <td>{safe(segment)}</td>
              <td><span class="cr-level-badge {badge_class}">
                <span class="cr-level-dot" aria-hidden="true"></span>
                {level_name} ({level})
              </span></td>
              <td>{safe(description)}</td>
            </tr>
            """)

        table_html = """
        <div class="cr-assets-table-wrap">
          <table class="cr-assets-table">
            <thead><tr>
              <th>ID</th><th>Інформаційний актив</th><th>Тип активу</th>
              <th>IP-адреса</th><th>Мережевий сегмент</th>
              <th>Рівень критичності</th><th>Опис</th>
            </tr></thead>
            <tbody>""" + "".join(table_rows) + """</tbody>
          </table>
        </div>
        """
        render_html(table_html)
    else:
        st.info("За заданими параметрами активів не знайдено. Змініть пошук або рівень критичності.")

    st.caption(f"Показано активів: {len(visible_assets)} із {total_assets}")
else:
    st.info("У базі даних поки немає зареєстрованих активів.")


# ============================================================
# 7. КНОПКИ КЕРУВАННЯ
# ============================================================

st.divider()

col_add, col_edit, col_delete = st.columns(
    3,
    gap="medium",
)

with col_add:
    st.button(
        "＋  Додати актив",
        key="assets_action_add",
        type=(
            "primary"
            if st.session_state.assets_active_action == "add"
            else "secondary"
        ),
        use_container_width=True,
        on_click=change_action,
        args=("add",),
    )

with col_edit:
    st.button(
        "✎  Редагувати актив",
        key="assets_action_edit",
        type=(
            "primary"
            if st.session_state.assets_active_action == "edit"
            else "secondary"
        ),
        use_container_width=True,
        on_click=change_action,
        args=("edit",),
    )

with col_delete:
    st.button(
        "▣  Видалити актив",
        key="assets_action_delete",
        type=(
            "primary"
            if st.session_state.assets_active_action == "delete"
            else "secondary"
        ),
        use_container_width=True,
        on_click=change_action,
        args=("delete",),
    )

st.markdown(
    '<div class="cr-action-separator"></div>',
    unsafe_allow_html=True,
)

# ============================================================
# 8. ДОДАВАННЯ НОВОГО АКТИВУ
# ============================================================

if st.session_state.assets_active_action == "add":


    with st.form(
        "new_asset_form",
        clear_on_submit=False,
    ):

        name = st.text_input(
            "Назва активу",
            placeholder="Наприклад: Сервер бази даних",
        )

        asset_type = st.selectbox(
            "Тип активу",
            ASSET_TYPES,
        )

        ip_address = st.text_input(
            "IP-адреса",
            placeholder="Наприклад: 192.168.10.10",
        )

        network_segment = st.text_input(
            "Мережевий сегмент",
            placeholder="Наприклад: VLAN 10",
        )

        criticality = st.slider(
            "Критичність активу",
            min_value=1,
            max_value=5,
            value=3,
        )

        description = st.text_area(
            "Опис активу",
            placeholder="Призначення активу в інфраструктурі",
        )

        submitted = st.form_submit_button(
            "Зберегти актив",
            type="primary",
        )

    if submitted:

        name = name.strip()
        ip_address = ip_address.strip()
        network_segment = network_segment.strip()
        description = description.strip()

        if not name:
            st.error(
                "Введіть назву інформаційного активу."
            )

        elif not valid_ip_address(ip_address):
            st.error(
                "Введіть коректну IP-адресу або залиште поле порожнім."
            )

        elif ip_address and asset_ip_exists(ip_address):
            st.error(
                "Актив із такою IP-адресою вже зареєстровано."
            )

        else:
            try:

                add_asset(
                    name,
                    asset_type,
                    ip_address,
                    network_segment,
                    criticality,
                    description,
                )

                st.session_state.assets_message = (
                    "Інформаційний актив успішно додано."
                )
                st.session_state.assets_active_action = None
                st.rerun()

            except Exception as error:
                st.error(
                    f"Помилка збереження активу: {error}"
                )


# ============================================================
# 9. РЕДАГУВАННЯ АКТИВУ
# ============================================================

elif st.session_state.assets_active_action == "edit":


    if not assets:

        st.info(
            "У системі немає активів для редагування."
        )

    else:

        selected_asset = st.selectbox(
            "Оберіть актив для редагування",
            options=assets,
            format_func=asset_label,
            key="edit_asset_select",
        )

        asset_id = selected_asset[0]

        # ID у ключі форми забезпечує оновлення
        # полів при виборі іншого активу.
        with st.form(
            key=f"edit_asset_form_{asset_id}"
        ):

            edit_name = st.text_input(
                "Назва активу",
                value=selected_asset[1],
                key=f"edit_name_{asset_id}",
            )

            edit_type = st.selectbox(
                "Тип активу",
                ASSET_TYPES,
                index=(
                    ASSET_TYPES.index(selected_asset[2])
                    if selected_asset[2] in ASSET_TYPES
                    else len(ASSET_TYPES) - 1
                ),
                key=f"edit_type_{asset_id}",
            )

            edit_ip = st.text_input(
                "IP-адреса",
                value=selected_asset[3] or "",
                key=f"edit_ip_{asset_id}",
            )

            edit_segment = st.text_input(
                "Мережевий сегмент",
                value=selected_asset[4] or "",
                key=f"edit_segment_{asset_id}",
            )

            edit_criticality = st.slider(
                "Критичність",
                min_value=1,
                max_value=5,
                value=int(selected_asset[5]),
                key=f"edit_criticality_{asset_id}",
            )

            edit_description = st.text_area(
                "Опис",
                value=selected_asset[6] or "",
                key=f"edit_description_{asset_id}",
            )

            save_changes = st.form_submit_button(
                "Зберегти зміни",
                type="primary",
            )

        if save_changes:

            edit_name = edit_name.strip()
            edit_ip = edit_ip.strip()
            edit_segment = edit_segment.strip()
            edit_description = edit_description.strip()

            if not edit_name:

                st.error(
                    "Назва активу не може бути порожньою."
                )

            elif not valid_ip_address(edit_ip):

                st.error(
                    "Введіть коректну IP-адресу."
                )

            else:

                # Перевірка IP з урахуванням ID:
                # власна адреса активу дозволена.
                duplicate_ip = any(
                    str(asset[3] or "").strip() == edit_ip
                    and asset[0] != asset_id
                    for asset in assets
                ) if edit_ip else False

                if duplicate_ip:

                    st.error(
                        "Ця IP-адреса вже належить іншому активу."
                    )

                else:

                    try:

                        updated = update_asset(
                            asset_id,
                            edit_name,
                            edit_type,
                            edit_ip,
                            edit_segment,
                            edit_criticality,
                            edit_description,
                        )

                        if not updated:
                            st.error("Актив не знайдено — зміни не збережено.")
                        else:
                            st.session_state.assets_message = (
                                "Інформаційний актив успішно відредаговано."
                            )
                            st.session_state.assets_active_action = None
                            st.rerun()

                    except Exception as error:

                        st.error(
                            f"Помилка редагування: {error}"
                        )


# ============================================================
# 10. ВИДАЛЕННЯ АКТИВУ
# ============================================================

elif st.session_state.assets_active_action == "delete":


    if not assets:

        st.info(
            "У системі немає активів для видалення."
        )

    else:

        selected_asset = st.selectbox(
            "Оберіть актив для видалення",
            options=assets,
            format_func=asset_label,
            key="delete_asset_select",
        )

        selected_asset_id = selected_asset[0]
        dependencies = get_asset_link_counts(selected_asset_id)
        has_dependencies = any(dependencies.values())

        if has_dependencies:
            st.error(
                "Видалення заблоковано: з цим активом пов'язані записи. "
                f"Загроз: {dependencies['threats']}; "
                f"вразливостей: {dependencies['vulnerabilities']}; "
                f"оцінок ризику: {dependencies['risks']}. "
                "Спочатку опрацюйте пов'язані записи у відповідних розділах."
            )
        else:
            st.info(
                "Пов'язаних загроз, вразливостей і ризиків немає. "
                "Актив можна видалити після підтвердження."
            )
        st.warning("Видалення активу є незворотною дією.")

        with st.form(key=f"delete_asset_form_{selected_asset_id}"):
            confirm_delete = st.checkbox(
                "Я підтверджую, що хочу видалити вибраний актив",
                disabled=has_dependencies,
            )
            delete_submitted = st.form_submit_button(
                "Видалити актив",
                type="primary",
                disabled=has_dependencies,
            )

        if delete_submitted:

            if not confirm_delete:

                st.error(
                    "Спочатку підтвердьте видалення активу."
                )

            else:

                try:

                    deleted = delete_asset(
                        selected_asset_id
                    )

                    if deleted:

                        st.session_state.assets_message = (
                            "Інформаційний актив успішно видалено."
                        )
                        st.session_state.assets_active_action = None
                        st.rerun()

                    else:

                        st.error(
                            "Актив не знайдено або його "
                            "не вдалося видалити."
                        )

                except Exception as error:

                    st.error(
                        f"Помилка видалення: {error}"
                    )
# ==========================================
# СПІЛЬНИЙ ФУТЕР CYBERRISK DSS
# ==========================================

render_footer()