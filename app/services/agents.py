import json
from app.services.agent_instructions import (
    DISTRACTOR_GENERATOR_INSTRUCTIONS,
    FORMATTER_INSTRUCTIONS,
    QUALITY_CHECKER_INSTRUCTIONS,
    QUESTION_GENERATOR_INSTRUCTIONS,
    RESEARCHER_INSTRUCTIONS,
)
from google.adk.agents import LlmAgent, LoopAgent
from google.adk.tools import google_search
from google.adk.runners import Runner
from google.genai.types import Content, Part
from google.adk.sessions import InMemorySessionService

LLM_MODEL = "gemini-2.0-flash"

# Research Agent - Gathers information on the quiz topic
research_agent = LlmAgent(
    name="QuizResearcher",
    model=LLM_MODEL,
    instruction=RESEARCHER_INSTRUCTIONS,
    tools=[google_search],
    description="Researches the topic thoroughly to gather accurate information for quiz questions",
    output_key="research_results",
)

# Question Generator Agent - Creates quiz questions based on research
question_generator_agent = LlmAgent(
    name="QuestionGenerator",
    model=LLM_MODEL,
    instruction=QUESTION_GENERATOR_INSTRUCTIONS,
    description="Creates quiz questions with varying difficulty levels based on research results",
    output_key="quiz_questions",
)

# Distractor Generator Agent - Creates plausible wrong answers for multiple choice
distractor_generator_agent = LlmAgent(
    name="DistractorGenerator",
    model=LLM_MODEL,
    instruction=DISTRACTOR_GENERATOR_INSTRUCTIONS,
    description="Creates plausible wrong answers that help test understanding without being too obvious",
    output_key="quiz_with_distractors",
)

# Formatter Agent - Formats the final quiz
formatter_agent = LlmAgent(
    name="QuizFormatter",
    model=LLM_MODEL,
    instruction=FORMATTER_INSTRUCTIONS,
    description="Formats the quiz into a cohesive, well-structured document ready for use",
    output_key="final_quiz",
)

# # Quality Checker Agent - Reviews the quiz for accuracy and quality
# quality_checker_agent = LlmAgent(
#     name="QualityChecker",
#     model=LLM_MODEL,
#     instruction=QUALITY_CHECKER_INSTRUCTIONS,
#     description="Reviews questions for factual accuracy, clarity, and appropriate difficulty",
#     output_key="quality_check_results",
# )

# Main Quiz Generator Agent using LoopAgent for iterative refinement
quiz_generator_agent = LoopAgent(
    name="quiz_generator_agent",
    max_iterations=2,
    sub_agents=[research_agent, question_generator_agent, distractor_generator_agent, formatter_agent],
)

# Root Agent for the Runner
root_agent = quiz_generator_agent

async def call_loop_agent(user_input: str) -> str:
    session_service = InMemorySessionService()
    runner = Runner(agent=quiz_generator_agent, app_name="LAb47", session_service=session_service)

    # Create session
    session_id = "112233"
    user_id = "12345"
    session = session_service.create_session(
        app_name="LAb47",
        user_id=user_id,
        session_id=session_id
    )

    content = Content(role='user', parts=[Part(text=user_input)])

    # Run the agents
    events = runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    )
    
    # Process the final response
    final_response = None
    for event in events:
        if event.is_final_response():
            raw_text = event.content.parts[0].text
            print(f"Raw agent response: {raw_text}")
            
            # Check if the response is in JSON format
            if raw_text.startswith("```json") or raw_text.startswith("{"):
                try:
                    # Extract JSON content if it's in a code block
                    if raw_text.startswith("```json"):
                        json_text = raw_text.split("```json\n", 1)[1].rsplit("```", 1)[0]
                    else:
                        json_text = raw_text
                    
                    # Parse the JSON
                    response_json = json.loads(json_text)
                    
                    # If the final_quiz field exists in the JSON, return that
                    if "final_quiz" in response_json:
                        return response_json["final_quiz"]
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON response: {e}")

            # If we couldn't extract structured content, return the raw text
            final_response = raw_text
    
    # If we got a final response, return it
    if final_response:
        return final_response
            
    # Check session state as a fallback
    updated_session = session_service.get_session(
        app_name="LAb47",
        user_id=user_id,
        session_id=session_id
    )
    
    if updated_session and "final_quiz" in updated_session.state:
        return updated_session.state["final_quiz"]
    
    # Collect agent messages as another fallback
    agent_conversation = []
    for event in events:
        if hasattr(event, 'agent_name') and hasattr(event, 'content'):
            agent_name = event.agent_name
            agent_message = event.content.parts[0].text if event.content and event.content.parts else ""
            if agent_message:
                agent_conversation.append(f"Agent {agent_name}: {agent_message}")
    
    if agent_conversation:
        return "\n\n".join(agent_conversation)
    
    # Last fallback
    return "Quiz generation in progress. Please check back for results."