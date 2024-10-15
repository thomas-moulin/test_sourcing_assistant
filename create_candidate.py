from pydantic import BaseModel, Field
from typing import Union, List
from openai import OpenAI

client = OpenAI()

system_content = """
You will be provided a conversation between a recruiter and a chatbot. The conversation is about describing a job position a recruiter is looking for and the ideal candidate for this position. 
You must convert the descriptin into the structure described in the response format.
Your goal is to output a json with the informations from the description following the response format

For the work experience block and education blocks, you must fill all the fields, you can invent the name of a company or instituion and enrich the description, when experience duration is provided, start date and end date should be consistent with the duration
"""
class WorkExperience(BaseModel):
    title: Union[str, None] = Field(description="Job Title")
    company: Union[str, None] = Field(description="Company name")
    location: Union[str, None] = Field(description="location of the job")
    contract_type: Union[str, None] = Field(description="Type of the contract")
    start_date: Union[str, None] = Field(description="Start date of the job")
    end_date: Union[str, None] = Field(description="End date of the job")
    description: Union[str, None] = Field(description="Description of the job")


class EducationExperience(BaseModel):
    title: Union[str, None] = Field(description="Degree name")
    level: Union[str, None] = Field(description="Level of the degree")
    institution: Union[str, None] = Field(description="Institution name")
    start_date: Union[str, None] = Field(description="Start date of the degree")
    end_date: Union[str, None] = Field(description="End date of the degree")


class NexJob(BaseModel):
    job_title: str = Field(description="Desired job title for the candidate")
    location: Union[str, None] = Field(description="Desired working location for the candidate")
    contract_type: Union[str, None] = Field(description="Desired contract type for the candidate")
    salary:  Union[str, None] = Field(description="Desired salary the candidate")


class CandidateProfile(BaseModel):
    next_job: NexJob
    work_experiences: List[WorkExperience] = Field(description="List of past work experiences")
    education_experiences: List[EducationExperience] = Field(description="List of diplomas")
    skills: List[str] = Field(description="List of skills")




def create_candidate(description):
    response = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": description},
        ],
        response_format=CandidateProfile
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    desc = """
Job Title: Senior Data Scientist
Location: Paris
Contract Type: Full-time
Salary: €60K
Job Details: Build a recommender system for a job board, manage 2 junior data scientists
Experience Required: 5 years in data science, 2 years managing juniors
Preferred Education: Master's
Soft Skills: Leadership, Communication, Problem-solving, Teamwork, Project Management
Hard Skills: Machine Learning, Python, SQL, Data Analysis, Recommender Systems

    """
    print(create_candidate(desc))