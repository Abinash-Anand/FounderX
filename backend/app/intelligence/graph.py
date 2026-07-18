from langgraph.graph import END, START, StateGraph

from app.intelligence.nodes import decide, map_sourcing, reduce_sourcing, run_diligence, screen
from app.intelligence.state import DealState


def build_decision_graph():
    """Compile the stateful sourcing-to-decision workflow."""
    workflow = StateGraph(DealState)
    workflow.add_node("map_sourcing", map_sourcing)
    workflow.add_node("reduce_sourcing", reduce_sourcing)
    workflow.add_node("screening", screen)
    workflow.add_node("diligence", run_diligence)
    workflow.add_node("decision", decide)

    workflow.add_edge(START, "map_sourcing")
    workflow.add_edge("map_sourcing", "reduce_sourcing")
    workflow.add_edge("reduce_sourcing", "screening")
    workflow.add_edge("screening", "diligence")
    workflow.add_edge("diligence", "decision")
    workflow.add_edge("decision", END)
    return workflow.compile()

