import streamlit as st
from openai import OpenAI
import time
import json

# Initialize client
client = OpenAI(default_headers={"OpenAI-Beta": "assistants=v2"})

ASSISTANT_ID = "asst_HvJybLbmLcpenE4Q5dFBNZVh"

# Function to submit a message
def submit_message(assistant_id, thread, user_message):
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=user_message
    )
    return client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )

# Function to get the response
def get_response(thread):
    return list(client.beta.threads.messages.list(thread_id=thread.id, order="desc"))

# Function to create a thread and run
def create_thread_and_run(user_input):
    thread = client.beta.threads.create()
    run = submit_message(ASSISTANT_ID, thread, user_input)
    return thread, run

# Function to wait for the run to complete
def wait_on_run(run, thread):
    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

# Streamlit app
# Streamlit app
# Streamlit app
# Streamlit app
def main():
    st.title("AI SOURCING ASSISTANT")

    # Initialize session state for conversation
    if 'thread' not in st.session_state:
        st.session_state.thread = None
    if 'run' not in st.session_state:
        st.session_state.run = None
    if 'messages' not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Start by typing the job title, location, contract and salary for the position you're recruiting for "}]
    if 'suggestions' not in st.session_state:
        st.session_state.suggestions = []
    if 'selected_suggestions' not in st.session_state:
        st.session_state.selected_suggestions = []

    # Display conversation history
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # Ensure previous run is completed before allowing new input
    if st.session_state.run:
        st.session_state.run = wait_on_run(st.session_state.run, st.session_state.thread)

    # User input field at the bottom
    user_input = st.chat_input("Type your message here...") if not st.session_state.suggestions else None

    if user_input:
        # Create a new thread if not exists
        if st.session_state.thread is None:
            st.session_state.thread, st.session_state.run = create_thread_and_run(user_input)
        else:
            # Ensure previous run is completed
            st.session_state.run = wait_on_run(st.session_state.run, st.session_state.thread)
            st.session_state.run = submit_message(ASSISTANT_ID, st.session_state.thread, user_input)

        # Wait for the run to complete
        st.session_state.run = wait_on_run(st.session_state.run, st.session_state.thread)

        # Add user input to conversation
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        # Fetch and display the last response
        messages = get_response(st.session_state.thread)
        if messages:
            # Assuming the first message is the latest due to ordering "desc"
            last_message_content = json.loads(messages[0].content[0].text.value)
            response_text = last_message_content['response']
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.chat_message("assistant").write(response_text)

            # Update and display suggestions
            st.session_state.suggestions = last_message_content.get('suggestions', [])

        # Reset user input by setting the session state
        #st.session_state.user_input = ""

    # Always display suggestions if available and wait for user to submit them
    if st.session_state.suggestions:
        st.session_state.selected_suggestions = st.multiselect(
            "Select suggestions to include in your response or type your suggestion in the chat:",
            [f"{s['value']}" for s in st.session_state.suggestions]
        )

        if st.button("Submit Suggestions"):
            combined_input = ', '.join(st.session_state.selected_suggestions)
            st.session_state.run = wait_on_run(st.session_state.run, st.session_state.thread)
            st.session_state.run = submit_message(ASSISTANT_ID, st.session_state.thread, combined_input)
            st.session_state.run = wait_on_run(st.session_state.run, st.session_state.thread)
            st.session_state.messages.append({"role": "user", "content": combined_input})
            st.chat_message("user").write(combined_input)

            messages = get_response(st.session_state.thread)
            if messages:
                # Assuming the first message is the latest due to ordering "desc"
                last_message_content = json.loads(messages[0].content[0].text.value)
                response_text = last_message_content['response']
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                st.chat_message("assistant").write(response_text)

                st.session_state.suggestions = last_message_content.get('suggestions', [])

            # Clear inputs after submission
            st.session_state.suggestions = []
            st.session_state.selected_suggestions = []

        # # Free text input
        # additional_input = st.chat_input("Or add your own input:")
        #
        # if additional_input:
        #     # Ensure previous run is completed before a new one
        #     combined_input = ', '.join(st.session_state.selected_suggestions) + " " + additional_input
        #     st.session_state.run = wait_on_run(st.session_state.run, st.session_state.thread)
        #     st.session_state.run = submit_message(ASSISTANT_ID, st.session_state.thread, combined_input)
        #     st.session_state.run = wait_on_run(st.session_state.run, st.session_state.thread)
        #     st.session_state.messages.append({"role": "user", "content": combined_input})
        #     st.chat_message("user").write(combined_input)
        #     # Clear inputs after submission
        #     st.session_state.suggestions = []
        #     st.session_state.selected_suggestions = []
        #     st.session_state.user_input = "ok"

    #
    # # Final action button
    # if st.button("Finish Interaction"):
    #     st.write("Finalizing interaction...")
    #     # Logic for finalizing the interaction
    #     # Reset session state if needed
    #     st.session_state.thread = None
    #     st.session_state.run = None
    #     st.session_state.interaction = ""
