class InvoiceDetails:
    def __init__(
        self,
        amount: float = None,
        date: str = None,
        periodo: str = None,
    ):
        self.amount = amount
        self.date = date
        self.periodo = periodo
