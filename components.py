
import streamlit as st


def render_footer():
    st.html("""
    <style>
    .cr-global-footer {
        margin-top: 42px;
        padding: 25px 15px 20px;
        border-top: 1px solid #E1EAF5;
        text-align: center;
        font-family: inherit;
    }

    .cr-global-footer-brand {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 9px;
        margin-bottom: 12px;
    }

    .cr-global-footer-icon {
        width: 27px;
        height: 27px;
        border-radius: 8px;
        background: #173B73;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 17px;
    }

    .cr-global-footer-name {
        color: #173B73;
        font-size: 17px;
        font-weight: 750;
    }

    .cr-global-footer-description {
        color: #71849D;
        font-size: 12px;
        line-height: 1.6;
        margin-bottom: 8px;
    }

    .cr-global-footer-copyright {
        color: #92A1B5;
        font-size: 11px;
    }
    </style>

    <footer class="cr-global-footer">
        <div class="cr-global-footer-brand">
            <span class="cr-global-footer-icon">◇</span>
            <span class="cr-global-footer-name">
                CyberRisk DSS
            </span>
        </div>

        <div class="cr-global-footer-description">
            Інформаційна система підтримки прийняття рішень
            щодо управління кіберризиками
        </div>

        <div class="cr-global-footer-copyright">
            © 2026 CyberRisk DSS · Усі права захищено
        </div>
    </footer>
    """)
