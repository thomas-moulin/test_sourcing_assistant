import streamlit as st
from openai import OpenAI
import json
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from create_candidate import create_candidate
from create_job_description import create_job_description
from enum import Enum
from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser()

candidates_data_description = """
1. **Candidate ID**: Unique identifier for each candidate.
2. **Diploma Level**: Highest education degree attained by the candidate.
3. **Professional Headline**: A brief professional summary or title.
4. **Next Job Preferences**: Details regarding the candidate's next desired job, including:
   - Contract types desired (e.g., full-time, apprenticeship).
   - Experience levels preferred (e.g., zero to one year, one to three years).
   - Desired locations with specifics on city, country, latitude, longitude, and state.
   - Remote work preferences (e.g., full-time remote, partial remote).
   - Specific professions and custom professions they are interested in.
5. **Minimum Salary Expectation**: The minimum salary the candidate is expecting.
6. **Skills**: A list of skills the candidate possesses, each with potential multilinguistic names, references, and types (e.g., tool, skill).
7. **Work Experiences**: Details of the candidate's work history, including:
   - Contract type (e.g., full-time, internship).
   - Organization details, including name, logo URL, reference, and URL.
   - Profession and specific title within the job.
   - Job description and key tasks carried out.
   - Location of the job, including city and country details.
   - Skills utilized in each role.
   - Start and end dates of each job.
   - Whether the job was full remote.
8. **Educations**: Educational background of the candidate, including:
   - Degree level (e.g., Bachelor's, Master's).
   - Description of the degree or program.
   - Institution name.
   - Skills acquired during the education.
   - Start and end dates.
9. **Additional Fields**: For some entries, other fields such as certifications, specific achievements, or tools used in jobs.
"""

system_content_candidate_new = """
You are an experienced recruitment assistant. Your objective is to help a recruiter identify and build the key attributes and qualifications for the perfect candidate for a specific job opening by facilitating a structured conversation.

INSTRUCTIONS
You will be provided a job title, remote policy, job location, contract type and salary

Gather Candidates Requirements:
First ask the recruiter to add some details about the job opening. NO SUGGESTION on this PART
Then ask about preferred past experiences. NO SUGGESTION on this PART
Based on the information of job opening and past experience, ask for soft skills and hard skills the candidate should have. In order to help the recruiter, suggest the skills to the candidate (between 5 and 15 skills) in the suggestion fields. Ask in one questions all that information. PUT SUGGESTION ON THIS ONE. ONLY ONE QUESTION
Based on the information of job opening and past experience, ask education level.  PUT SUGGESTION ON THIS ONE

Summarize the information gathered to ensure accuracy and completeness.

Confirm with the recruiter that all important aspects have been covered and ask if there’s anything else they’d like to add.

to keep a chat based approach, gather the information in distinct question. 
Questions must be short and simple to keep the experience fluid. Talk like if it was on wattsapp

Once all informations are gathered the final output must be a complete summary of what the recruiter is looking for.

FINAL OUTPUT:
COMPLETE SUMMARY OF THE INFORMATION GATHERED 

The message must be concised.
KEEP IT SHORT AND SIMPLE


"""


class SuggestionType(str, Enum):
    skill = "skill"
    education = "education"
    #next_action = 'next_action'


class Suggestion(BaseModel):
    type: SuggestionType = Field(description="The type of suggestion")
    value: str = Field(description="The value associated with the suggestion type")


class Status(str, Enum):
    in_progress = "In progress"
    finish = "finish"


class ResponseModel(BaseModel):
    status: Status = Field(description="The status of the response, indicating whether the task is still ongoing or completed. When outputing the summary of the candidates. The status must pass to finish")
    response: str = Field(description="The text content of the response from the assistant. If the assistant suggests a skill, it must be in the suggestions fields. Do not repeat in the description what is proposed in suggestions. Each message should ask about one type of information and propose suggestions if relevant. For information about desired salary or past experience, it does not need to be in suggestions. When the user adds a new suggestion in free text, it does not need to be repeated in the next message.")
    suggestions: List[Suggestion] = Field(description="An array of suggestion objects, each containing a type and value. If multiple values for the same type exist, they must be in a distinct object.")

# Initialize OpenAI API key


client = OpenAI()


# Streamlit app
def main():
    st.title("AI SOURCING ASSISTANT")

    # Initialize session state for conversation
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": system_content_candidate_new + "\n" + candidates_data_description},
            {"role": "assistant", "content": "Start by typing the job title, location, contract and salary for the position you're recruiting for "}]
    if 'suggestions' not in st.session_state:
        st.session_state.suggestions = []
    if 'selected_suggestions' not in st.session_state:
        st.session_state.selected_suggestions = []
    if 'action_description' not in st.session_state:
        st.session_state.action_description = "in progress"
    if 'next_actions' not in st.session_state:
        st.session_state.next_actions = []

    # Display conversation history
    for msg in st.session_state.messages:
        if msg["role"] == "system":
            continue
        st.chat_message(msg["role"]).write(msg["content"])

    # User input field at the bottom
    user_input = st.chat_input("Type your message here...") if not st.session_state.suggestions else None

    if user_input:
        # Add user input to conversation
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        # Call OpenAI ChatCompletion
        response = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=st.session_state.messages,
            response_format=ResponseModel
        )

        # Process and display the response
        msg = response.choices[0].message.content
        print(msg)
        response_text = parser.parse(msg)["response"]
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.chat_message("assistant").write(response_text)

        # Update suggestions if available
        # Assuming the suggestions are embedded in a specific JSON format within the content
        content_data = json.loads(msg)
        st.session_state.suggestions = content_data.get('suggestions', [])
        st.session_state.selected_suggestions = []

    # Display suggestions and allow submission with a button
    if st.session_state.suggestions:
        st.session_state.selected_suggestions = st.multiselect(
            "Select suggestions to include in your response:",
            [f"{s['value']}" for s in st.session_state.suggestions]
        )

        if st.button("Submit Suggestions"):
            combined_input = ', '.join(st.session_state.selected_suggestions)
            st.session_state.messages.append({"role": "user", "content": combined_input})
            st.chat_message("user").write(combined_input)

            # Call OpenAI ChatCompletion again with the new input
            response = client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=st.session_state.messages,
                response_format=ResponseModel
            )

            msg = response.choices[0].message.content
            print(msg)
            response_text = parser.parse(msg)["response"]
            st.session_state.last_description = response_text
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.chat_message("assistant").write(response_text)

            # Update suggestions from the assistant's response
            content_data = json.loads(msg)
            st.session_state.suggestions = content_data.get('suggestions', [])

            # Clear selected suggestions after submission
            st.session_state.selected_suggestions = []

            if parser.parse(msg)["status"] == "finish":
                st.session_state.action_description = "finish"
            # Handle next actions

    # Handle next actions when status is finish
    if st.session_state.action_description == "finish":
        st.session_state.next_actions = st.multiselect(
            "Choose next actions:",
            ["create job description", "Generate fake candidate and look for similar"])
        if st.button("Submit next actions"):
            if "create job description" in st.session_state.next_actions:
                job_desc = create_job_description(str(st.session_state.messages))
                st.chat_message("assistant").write(job_desc)

            if "Generate fake candidate and look for similar" in st.session_state.next_actions:
                similar_profiles = create_candidate(str(st.session_state.messages))
                st.chat_message("assistant").write("Here is the candidate description")
                st.json(similar_profiles)

main()
