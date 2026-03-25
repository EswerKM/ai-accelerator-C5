import streamlit as st
import time
import random
from datetime import datetime
import openai

# Page configuration
st.set_page_config(
    page_title="EswerBot - Your Personal Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables with defaults"""
    defaults = {
        "messages": [{"role": "assistant", "content": "Hello! I'm your assistant created by Eswer KM. How can I help you today?"}],
        "settings": {
            "assistant_name": "EswerBot",
            "max_history": 50,
            "show_timestamps": True
        },
        "stats": {
            "total_messages": 0,
            "session_start": datetime.now()
        }
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Initialize app
initialize_session_state()

# Initialize OpenRouter client
try:
    client = openai.OpenAI(
        api_key=st.secrets["openrouter"]["api_key"],
        base_url="https://openrouter.ai/api/v1"
    )
except KeyError:
    st.error("OpenRouter API key not found in secrets. Please add it to .streamlit/secrets.toml")
    st.stop()

# Helper functions
def add_message(role, content):
    """Add a message to chat history with timestamp"""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now()
    }
    st.session_state.messages.append(message)

    # Trim history if too long
    max_history = st.session_state.settings["max_history"]
    if len(st.session_state.messages) > max_history:
        # Keep first message (greeting) and trim from the middle
        st.session_state.messages = [st.session_state.messages[0]] + st.session_state.messages[-(max_history-1):]

def generate_response():
    """Generate a response using OpenRouter API"""
    messages_for_api = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages]

    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=messages_for_api
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

# Sidebar Configuration
with st.sidebar:
    st.header("🎛️ Configuration")

    # Assistant settings
    st.subheader("Assistant Settings")
    assistant_name = st.text_input(
        "Assistant Name:",
        value=st.session_state.settings["assistant_name"]
    )

    # Chat settings
    st.subheader("Chat Settings")
    max_history = st.slider(
        "Max Chat History:",
        min_value=10,
        max_value=100,
        value=st.session_state.settings["max_history"],
        help="Maximum number of messages to keep in chat history"
    )

    show_timestamps = st.checkbox(
        "Show Timestamps",
        value=st.session_state.settings["show_timestamps"]
    )

    # Update settings
    st.session_state.settings.update({
        "assistant_name": assistant_name,
        "max_history": max_history,
        "show_timestamps": show_timestamps
    })

    st.divider()

    # Statistics
    st.subheader("📊 Session Stats")
    session_duration = datetime.now() - st.session_state.stats["session_start"]
    st.metric("Session Duration", f"{session_duration.seconds // 60}m {session_duration.seconds % 60}s")
    st.metric("Messages Sent", st.session_state.stats["total_messages"])
    st.metric("Total Messages", len(st.session_state.messages))

    st.divider()

    # Actions
    st.subheader("🔧 Actions")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.messages = [
                {"role": "assistant", "content": f"Hello! I'm {assistant_name}. Chat cleared - let's start fresh!"}
            ]
            st.rerun()

    with col2:
        if st.button("📤 Export Chat", type="secondary"):
            chat_export = f"Chat Export - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            chat_export += "=" * 50 + "\n\n"

            for msg in st.session_state.messages:
                role = "You" if msg["role"] == "user" else assistant_name
                timestamp = msg.get("timestamp", datetime.now()).strftime("%H:%M")
                chat_export += f"[{timestamp}] {role}: {msg['content']}\n\n"

            st.download_button(
                "💾 Download",
                chat_export,
                file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )

# Main content area
st.title(f"{assistant_name}")
st.caption(f"History Limit: {max_history} messages")

# Chat display
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        role_display = "You" if message["role"] == "user" else assistant_name

        with st.chat_message(message["role"]):
            if show_timestamps and "timestamp" in message:
                timestamp = message["timestamp"].strftime("%H:%M:%S")
                st.caption(f"{role_display} - {timestamp}")

            st.write(message["content"])

# Chat input
if prompt := st.chat_input(f"Message {assistant_name}..."):
    # Add user message
    add_message("user", prompt)
    st.session_state.stats["total_messages"] += 1

    # Display user message
    with st.chat_message("user"):
        if show_timestamps:
            st.caption(f"You - {datetime.now().strftime('%H:%M:%S')}")
        st.write(prompt)

    # Generate and display assistant response
    with st.chat_message("assistant"):
        if show_timestamps:
            st.caption(f"{assistant_name} - {datetime.now().strftime('%H:%M:%S')}")

        # Show typing indicator
        with st.spinner(f"{assistant_name} is thinking..."):
            pass  # API call will take time

        # Generate response
        response = generate_response()
        st.write(response)

        # Add assistant response to history
        add_message("assistant", response)

        # Rerun to update the display
        st.rerun()

