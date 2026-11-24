
import hashlib
from contextvars import ContextVar
from threading import Lock

import streamlit as st


# ==================================================
# 1. НАЛАШТУВАННЯ ЗАСТОСУНКУ
# ==================================================

st.set_page_config(
    page_title="CyberRisk DSS",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================
# 2. СТИЛЬ БІЧНОГО МЕНЮ
# ==================================================

st.markdown("""
<style>

/* ==========================================
   ОСНОВНА БІЧНА ПАНЕЛЬ
   ========================================== */

section[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #F8FBFF 0%,
        #F2F7FF 100%
    ) !important;

    border-right: 1px solid #D4E2F4 !important;

    box-shadow:
        3px 0 14px rgba(23, 59, 115, 0.035);
}

/* Єдиний світло-блакитний фон усіх шарів бічної панелі.
   Дочірні контейнери Streamlit іноді мають власний білий фон. */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"],
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
    background-color: #F2F7FF !important;
    background-image: linear-gradient(180deg, #F8FBFF 0%, #F2F7FF 100%) !important;
}

/* Внутрішня область меню */

section[data-testid="stSidebar"]
[data-testid="stSidebarUserContent"] {
    padding-top: 0.5rem !important;
    padding-bottom: 1rem !important;
}

/* Компактне розташування елементів */

section[data-testid="stSidebar"]
[data-testid="stVerticalBlock"] {
    gap: 0.15rem !important;
}

/* ==========================================
   ЛОГОТИП
   ========================================== */

.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0 14px;
}

.sidebar-brand-icon {
    width: 42px;
    height: 42px;
    min-width: 42px;

    border-radius: 12px;

    background: linear-gradient(
        135deg,
        #173B73,
        #2867C8
    );

    display: flex;
    align-items: center;
    justify-content: center;

    box-shadow:
        0 4px 12px rgba(40, 103, 200, 0.12);
}

.sidebar-brand-title {
    color: #173B73;
    font-size: 19px;
    font-weight: 750;
    line-height: 1.2;
}

.sidebar-brand-subtitle {
    color: #7287A3;
    font-size: 11px;
    margin-top: 4px;
}

/* ==========================================
   ЗАГОЛОВКИ ГРУП
   ========================================== */

.sidebar-section {
    color: #7790AF !important;

    font-size: 11px;
    font-weight: 750;

    letter-spacing: 0.06em;
    text-transform: uppercase;

    margin-top: 15px;
    margin-bottom: 5px;
}

/* ==========================================
   ПУНКТИ НАВІГАЦІЇ
   ========================================== */

section[data-testid="stSidebar"]
[data-testid="stPageLink"] a {
    color: #24466F !important;

    border-radius: 10px !important;

    padding: 0.55rem 0.7rem !important;

    border-left: 3px solid transparent !important;

    transition:
        background-color 0.2s ease,
        color 0.2s ease,
        border-color 0.2s ease;
}

/* Наведення курсора */

section[data-testid="stSidebar"]
[data-testid="stPageLink"] a:hover {
    background: #E7F0FD !important;
    color: #174B94 !important;
}

/* Активна сторінка */

section[data-testid="stSidebar"]
[data-testid="stPageLink"] a[aria-current="page"] {
    background: #E1EDFC !important;

    color: #173B73 !important;

    font-weight: 700 !important;

    border-left: 3px solid #3979CF !important;
}

/* Активна сторінка під час наведення */

section[data-testid="stSidebar"]
[data-testid="stPageLink"] a[aria-current="page"]:hover {
    background: #D8E8FB !important;
}

/* ==========================================
   НИЖНЯ ЧАСТИНА МЕНЮ
   ========================================== */

.sidebar-divider {
    height: 1px;
    background: #D8E5F5;
    margin: 14px 0 8px;
}

/* Підпис у меню */

section[data-testid="stSidebar"]
[data-testid="stCaptionContainer"] {
    color: #8A9CB4 !important;
}

/* ==========================================
   КНОПКА ЗГОРТАННЯ МЕНЮ
   ========================================== */

section[data-testid="stSidebar"]
button {
    color: #59799F;
}

section[data-testid="stSidebar"]
button:hover {
    color: #2867C8;
}

/* ==========================================
   АДАПТИВНІСТЬ
   ========================================== */

@media (max-width: 768px) {

    .sidebar-brand-title {
        font-size: 17px;
    }

    .sidebar-brand-icon {
        width: 38px;
        height: 38px;
        min-width: 38px;
    }

    .sidebar-section {
        font-size: 10px;
    }
}
/* Піднімаємо логотип і все бічне меню вище */

section[data-testid="stSidebar"]
[data-testid="stSidebarUserContent"] {
    padding-top: 0.5rem !important;
}

section[data-testid="stSidebar"]
[data-testid="stVerticalBlock"] {
    gap: 0.15rem !important;
}
/* Піднімаємо весь вміст бічного меню */

section[data-testid="stSidebar"]
[data-testid="stSidebarContent"] {
    padding-top: 0 !important;
}

section[data-testid="stSidebar"]
[data-testid="stSidebarUserContent"] {
    padding-top: 0 !important;
}

/* Точне коригування положення логотипа та меню */
section[data-testid="stSidebar"]
[data-testid="stSidebarUserContent"] > div {
    margin-top: -25px !important;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# 3. СТОРІНКИ СИСТЕМИ
# ==================================================

def title_to_url(title):
    return "section-" + hashlib.md5(
        title.encode("utf-8")
    ).hexdigest()[:10]


def planned_page(title, description, icon):

    def show_placeholder():
        st.title(title)
        st.info(description)
        st.caption("Розділ перебуває в розробці.")

    return st.Page(
        show_placeholder,
        title=title,
        icon=icon,
        url_path=title_to_url(title),
    )


# Головна панель

home = st.Page(
    "pages/1_Головна_панель.py",
    title="Головна панель",
    icon=":material/dashboard:",
)


# Інформаційні активи

assets = st.Page(
    "pages/2_Активи.py",
    title="Інформаційні активи",
    icon=":material/dns:",
)


# Загрози

threats = st.Page(
    "pages/3_Загрози.py",
    title="Загрози",
    icon=":material/gpp_maybe:",
)


# Вразливості

vulnerabilities = st.Page(
    "pages/4_Вразливості.py",
    title="Вразливості",
    icon=":material/bug_report:",
)


# Оцінювання ризиків

risk_assessment = st.Page(
    "pages/5_Оцінювання_ризиків.py",
    title="Оцінювання ризиків",
    icon=":material/calculate:",
)


# Матриця ризиків

risk_matrix = st.Page(
    "pages/6_Матриця_ризиків.py",
    title="Матриця ризиків",
    icon=":material/grid_on:",
)


# Заходи захисту

security_measures = st.Page(
    "pages/7_Заходи_захисту.py",
    title="Заходи захисту",
    icon=":material/security:",
)


# Порівняння заходів

measure_comparison = st.Page(
    "pages/8_Порівняння_заходів.py",
    title="Порівняння заходів",
    icon=":material/balance:",
)


# Залишковий ризик


residual_risk = st.Page(
    "pages/9_Залишковий_ризик.py",
    title="Залишковий ризик",
    icon=":material/monitoring:",
    url_path="Залишковий_ризик",
)



# Економічний аналіз

economic_analysis = st.Page(
    "pages/10_Економічний_аналіз.py",
    title="Економічний аналіз",
    icon=":material/payments:",
)


# Експериментальне дослідження

experiment = st.Page(
    "pages/11_Експериментальне_дослідження.py",
    title="Експериментальне дослідження",
    icon=":material/science:",
)

reports = st.Page(
    "pages/12_Звіти_та_результати.py",
    title="Звіти та результати",
    icon=":material/description:",
)



# ==================================================
# 4. РЕЄСТРАЦІЯ НАВІГАЦІЇ
# ==================================================

pages = {
    "Огляд системи": [
        home,
    ],

    "Аналіз кіберризиків": [
        assets,
        threats,
        vulnerabilities,
        risk_assessment,
        risk_matrix,
    ],

    "Управління ризиками": [
        security_measures,
        measure_comparison,
        residual_risk,
        economic_analysis,
    ],

    "Результати дослідження": [
        experiment,
        reports,
    ],
}


navigation = st.navigation(
    pages,
    position="hidden",
)


# ==================================================
# 5. ВЛАСНЕ БІЧНЕ МЕНЮ
# ==================================================

with st.sidebar:


    # ==========================================
    # ЛОГОТИП СИСТЕМИ
    # ==========================================

    # SVG перетворюємо на зображення Base64,
    # щоб логотип правильно відображався у Streamlit.

    import base64

    logo_svg = """
    <svg xmlns="http://www.w3.org/2000/svg"
         width="26" height="26"
         viewBox="0 0 24 24"
         fill="none"
         stroke="#FFFFFF"
         stroke-width="1.8"
         stroke-linecap="round"
         stroke-linejoin="round">
        <path d="M12 2 L20 6.5 L20 17.5 L12 22 L4 17.5 L4 6.5 Z"/>
        <path d="M8 12 L11 15 L16 9"/>
    </svg>
    """

    logo_base64 = base64.b64encode(
        logo_svg.encode("utf-8")
    ).decode("ascii")

    st.html(f"""
    <div class="sidebar-brand">
        <div class="sidebar-brand-icon">
            <img
                src="data:image/svg+xml;base64,{logo_base64}"
                width="26"
                height="26"
                alt="Логотип CyberRisk DSS"
            >
        </div>
        <div>
            <div class="sidebar-brand-title">
                CyberRisk DSS
            </div>
            <div class="sidebar-brand-subtitle">
                Управління кіберризиками
            </div>
        </div>
    </div>
    """)


    # ==========================================
    # ОГЛЯД СИСТЕМИ
    # ==========================================

    st.markdown(
        '<div class="sidebar-section">Огляд системи</div>',
        unsafe_allow_html=True,
    )

    st.page_link(
        home,
        label="Головна панель",
        icon=":material/dashboard:",
    )


    # ==========================================
    # АНАЛІЗ КІБЕРРИЗИКІВ
    # ==========================================

    st.markdown(
        '<div class="sidebar-section">Аналіз кіберризиків</div>',
        unsafe_allow_html=True,
    )

    st.page_link(
        assets,
        label="Інформаційні активи",
        icon=":material/dns:",
    )

    st.page_link(
        threats,
        label="Загрози",
        icon=":material/gpp_maybe:",
    )

    st.page_link(
        vulnerabilities,
        label="Вразливості",
        icon=":material/bug_report:",
    )

    st.page_link(
        risk_assessment,
        label="Оцінювання ризиків",
        icon=":material/calculate:",
    )

    st.page_link(
        risk_matrix,
        label="Матриця ризиків",
        icon=":material/grid_on:",
    )


    # ==========================================
    # УПРАВЛІННЯ РИЗИКАМИ
    # ==========================================

    st.markdown(
        '<div class="sidebar-section">Управління ризиками</div>',
        unsafe_allow_html=True,
    )

    st.page_link(
        security_measures,
        label="Заходи захисту",
        icon=":material/security:",
    )

    st.page_link(
        measure_comparison,
        label="Порівняння заходів",
        icon=":material/balance:",
    )

    st.page_link(
        residual_risk,
        label="Залишковий ризик",
        icon=":material/monitoring:",
    )

    st.page_link(
        economic_analysis,
        label="Економічний аналіз",
        icon=":material/payments:",
    )


    # ==========================================
    # РЕЗУЛЬТАТИ ДОСЛІДЖЕННЯ
    # ==========================================

    st.markdown(
        '<div class="sidebar-section">Результати дослідження</div>',
        unsafe_allow_html=True,
    )

    st.page_link(
        experiment,
        label="Експериментальне дослідження",
        icon=":material/science:",
    )

    st.page_link(
        reports,
        label="Звіти та результати",
        icon=":material/description:",
    )


    # ==========================================
    # НИЖНІЙ ПІДПИС
    # ==========================================

    st.markdown(
        '<div class="sidebar-divider"></div>',
        unsafe_allow_html=True,
    )

    st.html("""
<div style="
    color: #8192AA;
    font-size: 11px;
    padding: 4px 0 12px;
">
    © 2026 CyberRisk DSS
</div>
""")


# ==================================================
# 6. ЗАПУСК ВИБРАНОЇ СТОРІНКИ
# ==================================================

# ПОЧАТОК СПІЛЬНИХ РОЗМІРІВ СТОРІНОК
# Стилі подаються до запуску сторінки, навіть якщо вона викликає st.stop().
st.html("""
<style>
/* Єдина геометрія попередніх сторінок за еталоном експериментів.
   Не змінює кольори, іконки, меню, вміст або футери. */
.stApp [data-testid="stAppViewContainer"] [data-testid="stMain"] :is([data-testid="stMainBlockContainer"], .block-container)
    :is(.dash-hero, .cr-hero, .th-hero, .vu-hero, .ri-hero, .mx-hero,
        .sm-hero, .cmp-hero, .rr-hero, .ec-hero) {
    box-sizing: border-box !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: none !important;
    min-height: 156px !important;
    height: auto !important;
    max-height: none !important;
    padding: 24px 30px !important;
    margin-inline: 0 !important;
    margin-top: 0 !important;
}

.stApp [data-testid="stAppViewContainer"] [data-testid="stMain"] :is([data-testid="stMainBlockContainer"], .block-container):has(
    :is(.dash-hero, .cr-hero, .th-hero, .vu-hero, .ri-hero, .mx-hero,
        .sm-hero, .cmp-hero, .rr-hero, .ec-hero)
) {
    box-sizing: border-box !important;
    width: 100% !important;
    max-width: none !important;
    padding-inline: 1.25rem !important;
    padding-top: 2.85rem !important;
    margin-inline: auto !important;
}

@media (min-width: 1100px) {
    .stApp [data-testid="stAppViewContainer"] [data-testid="stMain"] :is([data-testid="stMainBlockContainer"], .block-container)
        :is(.dash-hero, .cr-hero, .th-hero, .vu-hero, .ri-hero, .mx-hero,
            .sm-hero, .cmp-hero, .rr-hero, .ec-hero) {
        height: 156px !important;
    }
    /* Великі ілюстрації вміщуються, але не замінюються. */
    .stApp [data-testid="stAppViewContainer"] [data-testid="stMain"]
        :is(.dash-hero, .cr-hero, .th-hero, .vu-hero, .ri-hero, .mx-hero,
            .sm-hero, .cmp-hero, .rr-hero, .ec-hero)
        > :is(img, svg, [class$="-hero-icon"], .dash-hero-symbol, .ec-symbol) {
        max-height: 108px !important;
    }
}

@media (max-width: 720px) {
    .stApp [data-testid="stAppViewContainer"] [data-testid="stMain"] :is([data-testid="stMainBlockContainer"], .block-container):has(
        :is(.dash-hero, .cr-hero, .th-hero, .vu-hero, .ri-hero, .mx-hero,
            .sm-hero, .cmp-hero, .rr-hero, .ec-hero)
    ) {
        padding-inline: .8rem !important;
        padding-top: 4.35rem !important;
    }
    .stApp [data-testid="stAppViewContainer"] [data-testid="stMain"] :is([data-testid="stMainBlockContainer"], .block-container)
        :is(.dash-hero, .cr-hero, .th-hero, .vu-hero, .ri-hero, .mx-hero,
            .sm-hero, .cmp-hero, .rr-hero, .ec-hero) {
        min-height: 128px !important;
        padding: 22px 20px !important;
    }
}

/* st.markdown() зі стилями перед банером не має займати місце в колонці.
   Приховуємо тільки службові блоки цих п'яти сторінок і тільки ДО банера.
   Тег style продовжує діяти — змінюється лише участь обгортки в розмітці. */
.stApp [data-testid="stMain"] :is([data-testid="stMainBlockContainer"], .block-container)
    :is([data-testid="stElementContainer"], .element-container):has(
        > :is([data-testid="stMarkdown"], .stMarkdown) :is([data-testid="stMarkdownContainer"], .stMarkdownContainer) > style:only-child,
        > :is([data-testid="stMarkdown"], .stMarkdown) :is([data-testid="stMarkdownContainer"], .stMarkdownContainer) > p:only-child > style:only-child,
        > :is([data-testid="stMarkdownContainer"], .stMarkdownContainer) > style:only-child
    ):has(~ :is([data-testid="stElementContainer"], .element-container)
        :is(.cr-hero, .th-hero, .vu-hero, .ri-hero, .mx-hero)
    ) {
    display: none !important;
}

/* Без службових блоків ці п'ять банерів підходять під шапку Streamlit.
   Один спільний відступ повертає їх на рівень експериментальної сторінки. */
@media (min-width: 721px) {
    .stApp [data-testid="stAppViewContainer"] [data-testid="stMain"]
        :is([data-testid="stMainBlockContainer"], .block-container):has(
            :is(.cr-hero, .th-hero, .vu-hero, .ri-hero, .mx-hero)
        ) {
        padding-top: 3.85rem !important;
    }
}

/* Спільний футер у кінці прокручуваної області. */
.stApp [data-testid="stAppViewContainer"] [data-testid="stMain"]
    :is([data-testid="stMainBlockContainer"], .block-container) {
    box-sizing: border-box !important;
    min-height: 100dvh !important;
    padding-bottom: max(.75rem, env(safe-area-inset-bottom)) !important;
    display: flex !important;
    flex-direction: column !important;
}

.stApp [data-testid="stAppViewContainer"] [data-testid="stMain"]
    :is([data-testid="stMainBlockContainer"], .block-container)
    > :is([data-testid="stVerticalBlock"], div:has(> [data-testid="stVerticalBlock"])),
.stApp [data-testid="stAppViewContainer"] [data-testid="stMain"]
    :is([data-testid="stMainBlockContainer"], .block-container)
    > div > [data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 0 auto !important;
    min-height: 0 !important;
}

/* Старі сторінки можуть мати порожні маркери футера. */
.stApp [data-testid="stAppViewContainer"] [data-testid="stMain"]
    :is([data-testid="stElementContainer"], .element-container):has(
        :is(.cd-footer-anchor, .exp-footer-anchor)
    ),
.stApp [data-testid="stAppViewContainer"] [data-testid="stMain"]
    .st-key-vu_page_footer,
.stApp [data-testid="stAppViewContainer"] [data-testid="stMain"]
    :is([data-testid="stLayoutWrapper"], [data-testid="stVerticalBlockBorderWrapper"]):has(
        > .st-key-vu_page_footer
    ) {
    display: none !important;
}

/* Відступ автоматично заповнює вільне місце над футером на коротких сторінках. */
.stApp [data-testid="stAppViewContainer"] [data-testid="stMain"]
    :is([data-testid="stMainBlockContainer"], .block-container)
    > [data-testid="stVerticalBlock"]
    > :is(.st-key-cr_global_footer, :has(.st-key-cr_global_footer)),
.stApp [data-testid="stAppViewContainer"] [data-testid="stMain"]
    :is([data-testid="stMainBlockContainer"], .block-container)
    > div > [data-testid="stVerticalBlock"]
    > :is(.st-key-cr_global_footer, :has(.st-key-cr_global_footer)),
.stApp [data-testid="stAppViewContainer"] [data-testid="stMain"]
    :is([data-testid="stMainBlockContainer"], .block-container)
    > :is(.st-key-cr_global_footer, :not(:has(> [data-testid="stVerticalBlock"])):has(> .st-key-cr_global_footer)) {
    flex: 0 0 auto !important;
    margin-top: auto !important;
    margin-bottom: 0 !important;
}

.stApp [data-testid="stAppViewContainer"] [data-testid="stMain"]
    .st-key-cr_global_footer {
    width: 100% !important;
    padding-top: 1rem !important;
    text-align: center !important;
}
.stApp [data-testid="stAppViewContainer"] [data-testid="stMain"]
    .st-key-cr_global_footer :is(.cr-footer, .dash-footer, .ec-footer) {
    position: static !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 18px 12px 7px !important;
    box-sizing: border-box !important;
    border-top: 1px solid #dfe8f4 !important;
    text-align: center !important;
}
.stApp [data-testid="stAppViewContainer"] [data-testid="stMain"]
    .st-key-cr_global_footer .cr-footer-brand {
    justify-content: center !important;
    text-align: center !important;
}
.stApp [data-testid="stAppViewContainer"] [data-testid="stMain"]
    .st-key-cr_global_footer :is(.cr-footer-copy, .cr-footer-description) {
    text-align: center !important;
}
</style>
""")
# КІНЕЦЬ СПІЛЬНИХ РОЗМІРІВ СТОРІНОК

def _shared_footer_renderer():
    """Зберігає оригінальний футер і пропускає локальні виклики лише в поточній сесії."""
    import components as site_components

    namespace = vars(site_components)
    gate = namespace.setdefault(
        "_cyberrisk_defer_footer", ContextVar("cyberrisk_defer_footer", default=False)
    )
    lock = namespace.setdefault("_cyberrisk_footer_lock", Lock())
    with lock:
        original = namespace.get("_cyberrisk_original_footer")
        if original is None:
            original = site_components.render_footer

            def render_when_not_deferred(*args, **kwargs):
                if not gate.get():
                    return original(*args, **kwargs)
                return None

            site_components.render_footer = render_when_not_deferred
            namespace["_cyberrisk_original_footer"] = original
    return gate, original


_defer_footer, _render_footer = _shared_footer_renderer()
_footer_token = _defer_footer.set(True)
try:
    navigation.run()
finally:
    _defer_footer.reset(_footer_token)
    # Один футер після вмісту, навіть якщо сторінка зупинилась через st.stop().
    with st.container(key="cr_global_footer"):
        _render_footer()
