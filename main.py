import random
from typing import Dict, List

import streamlit as st


CATEGORY_CONFIG = [
    {
        "key": "gender",
        "label": "성별",
        "sample_size": 3,
        "pool": [
            "여성",
            "남성",
            "미지정"
        ],
    },
    {
        "key": "age",
        "label": "나이",
        "sample_size": 5,
        "pool": [
            "10대",
            "20-24세",
            "25-29세",
            "30대",
            "40대",
            "50대 이상",
        ],
    },
    {
        "key": "product",
        "label": "제품군",
        "sample_size": 7,
        "pool": [
            "스킨케어",
            "메이크업",
            "향수",
            "헤어케어",
            "바디케어",
            "남성용",
            "라이프스타일",
        ],
    },
]


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
        st.session_state.filter_options = {
            cfg["key"]: build_filter_options(cfg["pool"], cfg["sample_size"])
            for cfg in CATEGORY_CONFIG
        }

    for cfg in CATEGORY_CONFIG:
        selection_key = f"{cfg['key']}_selection"
        if selection_key not in st.session_state:
            st.session_state[selection_key] = []

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "active_controls_context" not in st.session_state:
        st.session_state.active_controls_context = "system"

def build_filter_options(pool: List[str], sample_size: int) -> List[str]:
    sample_count = min(sample_size, len(pool))
    sampled = random.sample(pool, k=sample_count)
    return sampled


def sanitize_selection(values: List[str], options: List[str]) -> List[str]:
    seen: List[str] = []
    for value in values:
        if value in options and value not in seen:
            seen.append(value)
    return seen


def reload_checklist() -> None:
    """새 체크리스트를 샘플링하고 관련 세션 상태를 초기화."""
    st.session_state.filter_options = {
        cfg["key"]: build_filter_options(cfg["pool"], cfg["sample_size"])
        for cfg in CATEGORY_CONFIG
    }
    for cfg in CATEGORY_CONFIG:
        st.session_state[f"{cfg['key']}_selection"] = []

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


def render_filter_controls(_: str | None = None) -> None:
    for cfg in CATEGORY_CONFIG:
        state_key = f"{cfg['key']}_selection"
        valid_options = st.session_state.filter_options[cfg["key"]]
        initial_value = sanitize_selection(
            list(st.session_state.get(state_key, [])), valid_options
        )
        st.session_state[state_key] = initial_value

        def _on_change(key: str = state_key, cfg_key: str = cfg["key"]) -> None:
            updated = sanitize_selection(
                list(st.session_state.get(key, [])),
                st.session_state.filter_options[cfg_key],
            )
            if updated != st.session_state[key]:
                st.session_state[key] = updated

        st.multiselect(
            label=f"{cfg['label']} 조건",
            options=valid_options,
            key=state_key,
            on_change=_on_change,
            help="여러 항목을 체크할 수 있어요.",
        )

def render_system_prompt() -> None:
    with st.chat_message("assistant"):
        st.markdown(
            "안녕하세요! 아래 체크리스트에서 성별, 나이, 제품군 조건을 선택해주세요."
        )

        if st.session_state.active_controls_context == "system":
            render_filter_controls("system")


def handle_user_message(user_text: str) -> None:
    st.session_state.messages.append({"role": "user", "content": user_text})

    active_filters = get_active_filters()
    filters_summary = format_filter_summary(active_filters)

    response_lines = [
        "선택된 조건을 기준으로 아래 요청을 검토할게요:",
        filters_summary,
        "",
        "요청해주신 내용:",
        f"> {user_text}",
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
        selection = st.session_state.get(f"{key}_selection", [])

        filtered = [opt for opt in selection if opt in options]
        active[key] = filtered if filtered else options
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
                if message.get("show_checklist_controls") and st.session_state.active_controls_context == context_key:
                    render_filter_controls(context_key)
                if message.get("show_reload_button"):
                    st.button(
                        "체크리스트 불러오기",
                        key=f"reload_checklist_msg_{idx}",
                        on_click=reload_checklist,
                    )


if __name__ == "__main__":
    main()
