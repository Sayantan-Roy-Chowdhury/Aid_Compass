from aidcompass.nodes.safety import capture_request, privacy_safety_gate


def test_normal_request_routes_to_continue():
    event = privacy_safety_gate(capture_request("I need tutoring in Scarborough."))
    assert event.actions.route == "CONTINUE"


def test_immediate_danger_routes_to_safety():
    event = privacy_safety_gate(
        capture_request("There is a medical emergency and we need help now.")
    )
    assert event.actions.route == "SAFETY"
