import os

from crewai import Agent, Crew, LLM, Process, Task
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------------
# LLM factory
# ------------------------------------------------------------------

def _llm(model_name: str, max_tokens: int = 500) -> LLM:
    return LLM(
        model=f"openai/{model_name}",
        base_url=os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1"),
        api_key=os.getenv("FEATHERLESS_API_KEY"),
        temperature=0.2,
        max_tokens=max_tokens,
    )


# ------------------------------------------------------------------
# CrewAI Agents
# ------------------------------------------------------------------

orchestrator_agent = Agent(
    role="Urban Operations Orchestrator",
    goal="Coordinate all agents to manage mass event crises in Milan",
    backstory="Expert systems coordinator for Olympic-scale events",
    llm=_llm("deepseek-ai/DeepSeek-V3.1"),
    verbose=True,
)

perception_agent = Agent(
    role="Crowd Perception Analyst",
    goal="Detect and analyze crowd anomalies from sensor data",
    backstory="Computer vision expert monitoring San Siro stadium",
    llm=_llm("mistralai/Mistral-Nemo-Instruct-2407"),
    verbose=True,
)

forecast_agent = Agent(
    role="Crisis Forecast Analyst",
    goal="Predict crowd crises 5-15 minutes before they happen",
    backstory="Urban simulation expert using SUMO traffic models",
    llm=_llm("deepseek-ai/DeepSeek-V3.2", max_tokens=400),
    verbose=True,
)

mobility_agent = Agent(
    role="Traffic Mobility Controller",
    goal="Reroute traffic to prevent congestion",
    backstory="Milan traffic control specialist",
    llm=_llm("Qwen/Qwen2.5-7B-Instruct", max_tokens=400),
    verbose=True,
)

transit_agent = Agent(
    role="Public Transit Coordinator",
    goal="Deploy emergency bus services when metro fails",
    backstory="ATM Milan transit operations expert",
    llm=_llm("Qwen/Qwen2.5-7B-Instruct", max_tokens=400),
    verbose=True,
)

safety_agent = Agent(
    role="Public Safety Commander",
    goal="Coordinate emergency response and open evacuation corridors",
    backstory="Emergency response coordinator for mass events",
    llm=_llm("mistralai/Mistral-Nemo-Instruct-2407", max_tokens=600),
    verbose=True,
)

communications_agent = Agent(
    role="Public Communications Officer",
    goal="Broadcast multilingual safety alerts to citizens",
    backstory="Crisis communications expert for Italian public events",
    llm=_llm("mistralai/Mistral-Nemo-Instruct-2407", max_tokens=300),
    verbose=True,
)


# ------------------------------------------------------------------
# CrewAI Tasks
# ------------------------------------------------------------------

perception_task = Task(
    description=(
        "Scenario: {scenario}\n\n"
        "Analyze the crowd situation at Gate 4. Assess density, movement patterns, and anomaly severity. "
        "Output valid JSON only."
    ),
    expected_output='JSON with fields: observation, severity (0.0-1.0), location, type (crowd_anomaly|congestion|security|infrastructure)',
    agent=perception_agent,
)

forecast_task = Task(
    description=(
        "Scenario: {scenario}\n\n"
        "Based on current crowd conditions at Gate 4, predict what crisis will unfold in the next 10 minutes. "
        "Output valid JSON only."
    ),
    expected_output='JSON with fields: prediction, time_horizon_minutes, confidence (0.0-1.0), recommended_action, severity (0.0-1.0)',
    agent=forecast_agent,
)

mobility_task = Task(
    description=(
        "Scenario: {scenario}\n\n"
        "Design a traffic rerouting plan to divert vehicles away from Gate 4 and the surrounding streets. "
        "Output valid JSON only."
    ),
    expected_output='JSON with fields: action (reroute|signal_change|road_closure|bus_lane), target_street, alternative_route, estimated_improvement, implementation_time_seconds',
    agent=mobility_agent,
)

transit_task = Task(
    description=(
        "Scenario: {scenario}\n\n"
        "Design an emergency bus deployment plan to replace the failed M5 metro line and absorb crowd overflow. "
        "Output valid JSON only."
    ),
    expected_output='JSON with fields: action (deploy_buses|extend_service|create_shuttle), route, vehicles_needed, capacity, pickup_points, estimated_wait_minutes',
    agent=transit_agent,
)

safety_task = Task(
    description=(
        "Scenario: {scenario}\n\n"
        "Assess the public safety risk at Gate 4 and design an emergency response plan including corridor routing. "
        "Output valid JSON only."
    ),
    expected_output='JSON with fields: risk_level (low|medium|high|critical), action (open_corridor|dispatch_ambulance|evacuate|secure_perimeter), location, corridor_route, response_time_seconds, units_needed',
    agent=safety_agent,
)

communications_task = Task(
    description=(
        "Scenario: {scenario}\n\n"
        "Compose a bilingual public safety broadcast for the 80,000 fans at San Siro. "
        "Output valid JSON only."
    ),
    expected_output='JSON with fields: message_en, message_it, channel (app|screen|speaker), urgency (info|warning|alert|emergency), action_required',
    agent=communications_agent,
)

orchestrator_task = Task(
    description=(
        "Scenario: {scenario}\n\n"
        "Review all specialist reports and synthesize a final coordinated action plan for OlympusOS. "
        "Assign priorities, resolve conflicts between agent recommendations, and produce the definitive response. "
        "Output valid JSON only."
    ),
    expected_output='JSON with fields: priority (high|medium|low), summary, final_decisions (list of {agent, action, rationale}), estimated_resolution_minutes',
    agent=orchestrator_agent,
    context=[
        perception_task,
        forecast_task,
        mobility_task,
        transit_task,
        safety_task,
        communications_task,
    ],
)


# ------------------------------------------------------------------
# Crew
# ------------------------------------------------------------------

olympus_crew = Crew(
    agents=[
        perception_agent,
        forecast_agent,
        mobility_agent,
        transit_agent,
        safety_agent,
        communications_agent,
        orchestrator_agent,
    ],
    tasks=[
        perception_task,
        forecast_task,
        mobility_task,
        transit_task,
        safety_task,
        communications_task,
        orchestrator_task,
    ],
    process=Process.sequential,
    verbose=True,
)


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def run_demo_scenario() -> str:
    scenario = (
        "Metro M5 failed. 80,000 fans leaving San Siro. "
        "Crowd anomaly at Gate 4, severity 0.83."
    )
    result = olympus_crew.kickoff(inputs={"scenario": scenario})
    return str(result)
