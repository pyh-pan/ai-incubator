from dataclasses import dataclass


@dataclass
class ThinkingStateSignals:
    turn_count: int = 0
    node_count: int = 0
    answered_node_count: int = 0
    open_question_count: int = 0
    decision_count: int = 0
    assumption_count: int = 0
    risk_count: int = 0
    last_3_turns_repeated: bool = False
    user_requested_action_plan: bool = False
    user_expressed_confusion: bool = False
    map_density: str = "low"
    focused_node_depth: int = 0


@dataclass
class ThinkingModeRecommendation:
    mode: str
    reason: str


def recommend_thinking_mode(signals: ThinkingStateSignals) -> ThinkingModeRecommendation:
    if signals.user_requested_action_plan:
        return ThinkingModeRecommendation("converge", "The user requested an action plan, so converge into a minimum next step.")

    if signals.last_3_turns_repeated:
        return ThinkingModeRecommendation("challenge", "Recent turns are repeating, so challenge the frame or introduce a new angle.")

    if signals.user_expressed_confusion:
        return ThinkingModeRecommendation("clarify", "The user expressed confusion, so clarify the current problem before adding branches.")

    if signals.turn_count <= 3 or signals.node_count <= 3:
        return ThinkingModeRecommendation("diverge", "The project is early and sparse, so explore breadth before narrowing.")

    if signals.open_question_count >= 5 and signals.map_density == "high":
        return ThinkingModeRecommendation("converge", "There are many open questions in a dense map, so summarize before adding more branches.")

    if signals.assumption_count >= 3 and signals.decision_count == 0:
        return ThinkingModeRecommendation("validate", "Several assumptions exist without decisions, so validate the most important uncertainty.")

    return ThinkingModeRecommendation("clarify", "The next best step is to clarify the most important unresolved point.")
