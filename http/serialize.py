class BaseSerializer:
    def __init__(self, check, data):
        self.errs = []
        self.check = check
        self.data = data
        self.methods = {
            "rq": self.is_required,
            "int": self.is_int,
            "float": self.is_float,
        }
        self._run()

    def is_required(self, name, value):
        if not value:
            self.errs.append(f"Field '{name}' is required")

    def is_int(self, name, value):
        try:
            int(value)
        except ValueError:
            self.errs.append(f"Field '{name}' must be a number")

    def is_float(self, name, value):
        try:
            float(value)
        except ValueError:
            self.errs.append(f"Field '{name}' must be a float number")

    def _run(self):
        for name, values in self.check.items():
            for val in values.split(":"):
                fn = self.methods[val]
                try:
                    fn(name, self.data[name])
                except KeyError:
                    self.errs.append(f"Field '{name}' value not provided")
                    break

    @property
    def errors(self):
        return self.errs

