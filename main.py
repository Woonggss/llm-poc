import random
from typing import Dict, List

import streamlit as st
from rag import get_answer
from config import CATEGORY_CONFIG


def main() -> None:
    st.set_page_config(page_title="LLM PoC Chat", page_icon="💬", layout="centered")
    initialize_session_state()
    render_system_prompt()

    user_prompt = st.chat_input("메시지를 입력하세요.")
    if user_prompt:
        handle_user_message(user_prompt)

    render_chat_history()


def initialize_session_state() -> None:
    if "filter_options" not in st.session_state:
        st.session_state.filter_options = {}
        for cfg in CATEGORY_CONFIG:
            pool = cfg["pool"]
            sample_count = min(cfg["sample_size"], len(pool))
            st.session_state.filter_options[cfg["key"]] = random.sample(
                pool, k=sample_count
            )

    for cfg in CATEGORY_CONFIG:
        selection_key = f"{cfg['key']}_selection"
        if selection_key not in st.session_state:
            st.session_state[selection_key] = None

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "active_controls_context" not in st.session_state:
        st.session_state.active_controls_context = "system"

def reload_checklist() -> None:
    """새 체크리스트를 샘플링하고 관련 세션 상태를 초기화."""
    st.session_state.filter_options = {}
    for cfg in CATEGORY_CONFIG:
        pool = cfg["pool"]
        sample_count = min(cfg["sample_size"], len(pool))
        st.session_state.filter_options[cfg["key"]] = random.sample(
            pool, k=sample_count
        )
    for cfg in CATEGORY_CONFIG:
        st.session_state[f"{cfg['key']}_selection"] = None

    for message in st.session_state.messages:
        if message.get("show_reload_button"):
            message["show_reload_button"] = False
        if message.get("show_checklist_controls"):
            message["show_checklist_controls"] = False

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": "체크리스트를 새로 불러왔어요. 아래에서 조건을 다시 선택해 주세요.",
            "show_checklist_controls": True,
        }
    )

    st.session_state.active_controls_context = f"msg_{len(st.session_state.messages) - 1}"


def render_filter_controls() -> None:
    for cfg in CATEGORY_CONFIG:
        state_key = f"{cfg['key']}_selection"
        valid_options = st.session_state.filter_options[cfg["key"]]
        stored_value = st.session_state.get(state_key)
        selected_value = stored_value if stored_value in valid_options else None
        st.session_state[state_key] = selected_value

        options = ["선택 안 함", *valid_options]
        current_label = selected_value if selected_value else "선택 안 함"
        chosen = st.selectbox(
            label=f"{cfg['label']} 조건",
            options=options,
            index=options.index(current_label),
            key=f"{state_key}_select",
            help="한 번에 하나만 선택할 수 있어요.",
        )
        st.session_state[state_key] = None if chosen == "선택 안 함" else chosen

def render_system_prompt() -> None:
    with st.chat_message("assistant"):
        st.markdown(
            "안녕하세요! 아래 체크리스트에서 성별, 나이, 제품군 조건을 선택해주세요."
        )

        if st.session_state.active_controls_context == "system":
            render_filter_controls()


def handle_user_message(user_text: str) -> None:
    st.session_state.messages.append({"role": "user", "content": user_text})

    with st.spinner("응답 생성 중...", show_time = True):
        rag_answer = get_answer(user_text)

    active_filters = get_active_filters()
    filters_summary = format_filter_summary(active_filters)

    response_lines = [
        "선택된 조건을 기준으로 아래 요청을 검토할게요:",
        filters_summary,
        "",
        "요청해주신 내용:",
        f"> {user_text}",
        "",
        "추천 결과:",
        rag_answer,
        "",
        "추가로 알려주실 내용이 있으면 계속 입력해주세요.",
    ]

    for message in st.session_state.messages:
        if message.get("show_reload_button"):
            message["show_reload_button"] = False
        if message.get("show_checklist_controls"):
            message["show_checklist_controls"] = False

    st.session_state.active_controls_context = None

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": "\n".join(line for line in response_lines if line is not None),
            "show_reload_button": True,
            "show_checklist_controls": False,
        }
    )

def get_active_filters() -> Dict[str, List[str]]:
    active: Dict[str, List[str]] = {}
    for cfg in CATEGORY_CONFIG:
        key = cfg["key"]
        options = st.session_state.filter_options[key]
        selection = st.session_state.get(f"{key}_selection")

        if selection in options:
            active[key] = [selection]
        else:
            active[key] = options
    return active


def format_filter_summary(active: Dict[str, List[str]]) -> str:
    summary_lines: List[str] = []
    for cfg in CATEGORY_CONFIG:
        key = cfg["key"]
        label = cfg["label"]
        options = st.session_state.filter_options[key]
        choices = active.get(key, [])

        if not options:
            summary_lines.append(f"- **{label}**: 선택 가능한 옵션이 없어요.")
            continue

        if len(choices) == len(options):
            summary_lines.append(f"- **{label}**: 전체")
        elif choices:
            summary_lines.append(f"- **{label}**: {', '.join(choices)}")
        else:
            summary_lines.append(f"- **{label}**: 선택 없음")

    return "\n".join(summary_lines)


def render_chat_history() -> None:
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("caption"):
                st.caption(message["caption"])
            if message["role"] == "assistant":
                context_key = f"msg_{idx}"
                if (
                    message.get("show_checklist_controls")
                    and st.session_state.active_controls_context == context_key
                ):
                    render_filter_controls()
                if message.get("show_reload_button"):
                    st.button(
                        "체크리스트 불러오기",
                        key=f"reload_checklist_msg_{idx}",
                        on_click=reload_checklist,
                    )


if __name__ == "__main__":
    main()
