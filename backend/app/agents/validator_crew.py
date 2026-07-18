from crewai import Agent, Crew, Process, Task


def build_validator_crew(company_name: str, evidence: str) -> Crew:
    """Build the domain-expert cluster with a skeptical Validator Agent."""
    market_expert = Agent(
        role="Market Analyst",
        goal=f"Size the reachable market and timing for {company_name}.",
        backstory="You triangulate market claims from source-backed evidence.",
        verbose=False,
    )
    founder_expert = Agent(
        role="Founder Analyst",
        goal=f"Assess founder-market fit and execution evidence for {company_name}.",
        backstory="You distinguish demonstrated velocity from polished storytelling.",
        verbose=False,
    )
    validator = Agent(
        role="Validator Agent",
        goal="Find unsupported claims, contradictions, and missing evidence before a decision.",
        backstory="You are the final skeptical reviewer and never confuse confidence with proof.",
        verbose=False,
    )

    market_task = Task(
        description=f"Analyze the market evidence below.\n\n{evidence}",
        expected_output="A source-aware market assessment with uncertainties.",
        agent=market_expert,
    )
    founder_task = Task(
        description=f"Analyze founder execution evidence below.\n\n{evidence}",
        expected_output="A founder assessment with supporting and contradicting evidence.",
        agent=founder_expert,
    )
    validation_task = Task(
        description="Challenge both expert assessments and produce a Truth-Gap checklist.",
        expected_output="Validated findings, contradictions, and explicit open questions.",
        agent=validator,
        context=[market_task, founder_task],
    )
    return Crew(
        agents=[market_expert, founder_expert, validator],
        tasks=[market_task, founder_task, validation_task],
        process=Process.sequential,
        verbose=False,
    )

