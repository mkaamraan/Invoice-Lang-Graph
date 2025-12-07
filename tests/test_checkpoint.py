from nodes.checkpoint_hitl import run_checkpoint

def test_checkpoint_created():
    state = {
        "input_invoice":{"invoice_id":"X1"},
        "MATCH_TWO_WAY":{"match_result":"FAILED"}
    }
    out = run_checkpoint(state, {})
    assert out["paused"] is True
