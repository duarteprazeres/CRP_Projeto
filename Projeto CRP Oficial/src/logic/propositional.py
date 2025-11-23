class Expr:
    def __invert__(self):
        return Not(self)

    def __and__(self, other):
        return And(self, other)

    def __or__(self, other):
        return Or(self, other)

    def __rshift__(self, other):
        return Implication(self, other)

    def __eq__(self, other):
        return isinstance(other, Expr) and str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

class Symbol(Expr):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def evaluate(self, model):
        return model.get(self, False)

class Not(Expr):
    def __init__(self, operand):
        self.operand = operand

    def __repr__(self):
        return f"~{self.operand}"

    def evaluate(self, model):
        return not self.operand.evaluate(model)

class And(Expr):
    def __init__(self, *operands):
        self.operands = operands

    def __repr__(self):
        return f"({' & '.join(map(str, self.operands))})"

    def evaluate(self, model):
        return all(op.evaluate(model) for op in self.operands)

class Or(Expr):
    def __init__(self, *operands):
        self.operands = operands

    def __repr__(self):
        return f"({' | '.join(map(str, self.operands))})"

    def evaluate(self, model):
        return any(op.evaluate(model) for op in self.operands)

class Implication(Expr):
    def __init__(self, antecedent, consequent):
        self.antecedent = antecedent
        self.consequent = consequent

    def __repr__(self):
        return f"({self.antecedent} >> {self.consequent})"

    def evaluate(self, model):
        return (not self.antecedent.evaluate(model)) or self.consequent.evaluate(model)

class PropositionalKB:
    def __init__(self):
        self.clauses = []

    def tell(self, sentence):
        self.clauses.append(sentence)

    def ask(self, query):
        return tt_entails(And(*self.clauses), query)

    def retract_all(self):
        self.clauses = []

def tt_entails(kb, alpha):
    symbols = list(get_symbols(kb) | get_symbols(alpha))
    return tt_check_all(kb, alpha, symbols, {})

def tt_check_all(kb, alpha, symbols, model):
    if not symbols:
        if pl_true(kb, model):
            return pl_true(alpha, model)
        else:
            return True
    
    P = symbols[0]
    rest = symbols[1:]
    
    return (tt_check_all(kb, alpha, rest, extend(model, P, True)) and
            tt_check_all(kb, alpha, rest, extend(model, P, False)))

def pl_true(exp, model):
    return exp.evaluate(model)

def get_symbols(exp):
    if isinstance(exp, Symbol):
        return {exp}
    elif isinstance(exp, Not):
        return get_symbols(exp.operand)
    elif isinstance(exp, (And, Or)):
        s = set()
        for op in exp.operands:
            s.update(get_symbols(op))
        return s
    elif isinstance(exp, Implication):
        return get_symbols(exp.antecedent) | get_symbols(exp.consequent)
    return set()

def extend(model, var, val):
    new_model = model.copy()
    new_model[var] = val
    return new_model
