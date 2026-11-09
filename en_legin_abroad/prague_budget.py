import json
from pathlib import Path

from django.shortcuts import render

with Path(__file__).with_suffix(".json").open(encoding="utf-8") as data_file:
    BUDGET = json.load(data_file)


def prague_cost_of_living(request):
    """A browser-only budget planner with server-rendered examples."""
    scenarios = BUDGET["scenarios"]
    default = scenarios[BUDGET["default_scenario"]]
    expense_fields = BUDGET["expense_fields"]
    totals = {
        key: sum(scenario[field["key"]] for field in expense_fields)
        for key, scenario in scenarios.items()
    }
    balances = {key: scenario["income"] - totals[key] for key, scenario in scenarios.items()}
    initial_total = totals[BUDGET["default_scenario"]]
    initial_balance = balances[BUDGET["default_scenario"]]
    rows = [
        ("Take-home income", [f"{scenario['income']:,}" for scenario in scenarios.values()]),
        *[
            (field["label"], [f"{scenario[field['key']]:,}" for scenario in scenarios.values()])
            for field in expense_fields
        ],
    ]
    context = {
        "budget": BUDGET,
        "default_income": default["income"],
        "expenses": [{**field, "value": default[field["key"]]} for field in expense_fields],
        "example_rows": rows,
        "total_row": [f"{value:,}" for value in totals.values()],
        "balance_row": [f"{value:,}" for value in balances.values()],
        "initial": {
            "total": f"{initial_total:,}",
            "balance": f"{abs(initial_balance):,}",
            "annual": f"{initial_balance * 12:,}",
            "annual_shortfall": f"{abs(initial_balance * 12):,}",
            "per_person": f"{initial_total / default['people']:,.0f}",
            "is_shortfall": initial_balance < 0,
            "has_income": default["income"] > 0,
            "rate": f"{abs(initial_balance) / default['income']:.1%}" if default["income"] else "",
        },
    }
    return render(request, "en_legin_abroad/prague_cost_of_living.html", context)
