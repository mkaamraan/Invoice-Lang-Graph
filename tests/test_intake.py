from nodes.intake import run_intake

def test_intake_minimal():
    state = {"input_invoice": {"invoice_id":"X1","vendor_name":"ABC","amount":100}}
    out = run_intake(state, {})
    assert out["INTAKE"]["validated"] is True
