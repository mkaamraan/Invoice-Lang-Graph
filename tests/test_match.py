from nodes.match import run_match

def test_match_exact():
    state = {
        "input_invoice":{"amount":100},
        "RETRIEVE":{"matched_pos":[{"amount":100}]}
    }
    out = run_match(state, {}, match_threshold=0.90)
    assert out["MATCH_TWO_WAY"]["match_result"] == "MATCHED"
