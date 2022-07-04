from typing import Optional

from py.xml import html


class Outcome:
    def __init__(
        self,
        outcome: str,
        total: int = 0,
        label: Optional[str] = None,
        test_result: Optional[str] = None,
        class_html: Optional[str] = None,
    ) -> None:
        self.outcome = outcome
        self.label = label or outcome
        self.class_html = class_html or outcome
        self.total = total
        self.test_result = test_result or outcome

        self.generate_checkbox()
        self.generate_summary_item()

    def generate_checkbox(self) -> None:
        checkbox_kwargs = {"data-test-result": self.test_result.lower()}
        if self.total == 0:
            checkbox_kwargs["disabled"] = "true"

        self.checkbox = html.input(
            type="checkbox",
            checked="true",
            onChange="filterTable(this)",
            name="filter_checkbox",
            class_="filter",
            hidden="true",
            **checkbox_kwargs,
        )

    def generate_summary_item(self) -> None:
        self.summary_item = html.span(
            f"{self.total} {self.label}", class_=self.class_html
        )
