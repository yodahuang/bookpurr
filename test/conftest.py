def pytest_assertrepr_compare(op, left, right):
    if op == "==":
        return ["Actual:", str(left), "Expected:", str(right)]
