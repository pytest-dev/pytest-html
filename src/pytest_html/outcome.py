class Outcome:
    def __init__(self, outcome, total=0, label=None, test_result=None, class_html=None):
        self.outcome = outcome
        self.label = label or outcome
        self.class_html = class_html or outcome
        self.total = total
        self.test_result = test_result or outcome
