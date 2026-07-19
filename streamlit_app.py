import os
from typing import Any, Dict

import requests
import streamlit as st

DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="AI Travel Agent",
    page_icon="✈️",
    layout="wide",
)


def api_get(url: str, path: str) -> Dict[str, Any]:
    response = requests.get(f"{url.rstrip('/')}{path}", timeout=10)
    response.raise_for_status()
    return response.json()


def api_post_query(url: str, query: str) -> Dict[str, Any]:
    response = requests.post(
        f"{url.rstrip('/')}/query",
        json={"query": query},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def render_api_response(payload: Dict[str, Any]) -> None:
    response_type = payload.get("response_type", "general")
    data = payload.get("data")

    if response_type == "flight" and isinstance(data, dict):
        st.subheader("✈️ Flight recommendation")
        col1, col2, col3 = st.columns(3)
        col1.metric("Airline", data.get("airline", "N/A"))
        col2.metric("Departure", data.get("departure_time", "N/A"))
        col3.metric("Arrival", data.get("arrival_time", "N/A"))
        st.write(f"**Price:** ${data.get('price', 'N/A')}")
        st.write(
            f"**Direct flight:** {'Yes' if data.get('direct_flight') else 'No'}"
        )
        st.info(data.get("recommendation_reason", ""))

    elif response_type == "hotel" and isinstance(data, dict):
        st.subheader("🏨 Hotel recommendation")
        col1, col2 = st.columns(2)
        col1.metric("Hotel", data.get("name", "N/A"))
        col2.metric("Price / night", f"${data.get('price_per_night', 'N/A')}")
        st.write(f"**Location:** {data.get('location', 'N/A')}")
        amenities = data.get("amenities", [])
        if amenities:
            st.write("**Amenities:** " + ", ".join(amenities))
        st.info(data.get("recommendation_reason", ""))

    elif response_type == "travel_plan" and isinstance(data, dict):
        st.subheader(f"🌍 Travel plan: {data.get('destination', 'Destination')}")
        col1, col2 = st.columns(2)
        col1.metric("Duration", f"{data.get('duration_days', 'N/A')} days")
        col2.metric("Budget", f"${data.get('budget', 'N/A')}")

        activities = data.get("activities", [])
        if activities:
            st.write("**Recommended activities**")
            for index, activity in enumerate(activities, start=1):
                st.write(f"{index}. {activity}")

        notes = data.get("notes")
        if notes:
            st.info(notes)

    else:
        if isinstance(data, (dict, list)):
            st.json(data)
        else:
            st.write(data or payload.get("message", "No response received."))


st.title("✈️ AI Travel Agent")
st.caption("Streamlit frontend connected to the FastAPI multi-agent backend")

with st.sidebar:
    st.header("Backend settings")
    backend_url = st.text_input("FastAPI URL", value=DEFAULT_BACKEND_URL)

    if st.button("Check backend", use_container_width=True):
        try:
            health = api_get(backend_url, "/health")
            st.success(health.get("message", "Backend is running"))
        except requests.RequestException as exc:
            st.error(f"Backend connection failed: {exc}")

    st.divider()
    st.write("**Example questions**")
    st.code("Plan a 5-day trip to Tokyo with a $2000 budget")
    st.code("Find a hotel in Paris with a pool under $300 per night")
    st.code("Find a flight from New York to Chicago tomorrow")

    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and isinstance(message["content"], dict):
            render_api_response(message["content"])
        else:
            st.markdown(message["content"])

prompt = st.chat_input("Ask for a flight, hotel, weather, or complete travel plan...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Planning your trip..."):
            try:
                result = api_post_query(backend_url, prompt)
                render_api_response(result)
                st.session_state.messages.append(
                    {"role": "assistant", "content": result}
                )
            except requests.Timeout:
                error_message = (
                    "The backend took too long to respond. Check the model API and try again."
                )
                st.error(error_message)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_message}
                )
            except requests.ConnectionError:
                error_message = (
                    "Cannot connect to FastAPI. Start the backend on port 8000 first."
                )
                st.error(error_message)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_message}
                )
            except requests.HTTPError as exc:
                try:
                    detail = exc.response.json().get("detail", str(exc))
                except ValueError:
                    detail = str(exc)
                error_message = f"Backend error: {detail}"
                st.error(error_message)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_message}
                )
            except requests.RequestException as exc:
                error_message = f"Request failed: {exc}"
                st.error(error_message)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_message}
                )
