class Expr:
    pass

class Variable(Expr):
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return f"?{self.name}"
    
    def __eq__(self, other):
        return isinstance(other, Variable) and self.name == other.name
    
    def __hash__(self):
        return hash(self.name)

class Constant(Expr):
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return self.name
    
    def __eq__(self, other):
        return isinstance(other, Constant) and self.name == other.name
    
    def __hash__(self):
        return hash(self.name)

class Predicate(Expr):
    def __init__(self, name, args):
        self.name = name
        self.args = args
    
    def __repr__(self):
        return f"{self.name}({', '.join(map(str, self.args))})"
    
    def __eq__(self, other):
        return (isinstance(other, Predicate) and 
                self.name == other.name and 
                len(self.args) == len(other.args) and 
                all(a == b for a, b in zip(self.args, other.args)))
    
    def __hash__(self):
        return hash(self.name) ^ hash(tuple(self.args))

class FOLKB:
    def __init__(self):
        self.clauses = [] # List of (head, body) where head is Predicate, body is list of Predicates
        # Facts are clauses with empty body

    def tell(self, sentence):
        # Sentence assumed to be Implication(body, head) or just Predicate (fact)
        # Simplified: We expect input as (Head, [Body...])
        # But to make it easier to use, let's accept objects
        if isinstance(sentence, Predicate):
            self.clauses.append((sentence, []))
        elif isinstance(sentence, tuple) and len(sentence) == 2:
            self.clauses.append(sentence)
        else:
            raise ValueError("Invalid sentence for FOL KB")

    def ask(self, query):
        # Returns a generator of substitutions
        return fol_bc_ask(self, query)

def unify(x, y, theta):
    if theta is None:
        return None
    elif x == y:
        return theta
    elif isinstance(x, Variable):
        return unify_var(x, y, theta)
    elif isinstance(y, Variable):
        return unify_var(y, x, theta)
    elif isinstance(x, Predicate) and isinstance(y, Predicate):
        return unify(x.args, y.args, unify(x.name, y.name, theta))
    elif isinstance(x, list) and isinstance(y, list):
        if len(x) != len(y): return None
        return unify(x[1:], y[1:], unify(x[0], y[0], theta))
    else:
        return None

def unify_var(var, x, theta):
    if var in theta:
        return unify(theta[var], x, theta)
    elif isinstance(x, Variable) and x in theta:
        return unify(var, theta[x], theta)
    # Occur check omitted for simplicity in this project
    else:
        new_theta = theta.copy()
        new_theta[var] = x
        return new_theta

def fol_bc_ask(kb, query):
    return fol_bc_or(kb, query, {})

def fol_bc_or(kb, goal, theta):
    for rule in kb.clauses:
        lhs, rhs = rule
        # Standardize variables to avoid name clashes (simplified: assume unique names or handle manually)
        # For this project, we'll assume the user manages variable names or we copy
        lhs, rhs = standardize_variables((lhs, rhs))
        
        unify_res = unify(lhs, goal, theta)
        if unify_res is not None:
            for res in fol_bc_and(kb, rhs, unify_res):
                yield res

def fol_bc_and(kb, goals, theta):
    if not goals:
        yield theta
    else:
        first, rest = goals[0], goals[1:]
        # Substitute variables in first with current theta
        subst_first = subst(theta, first)
        for theta_prime in fol_bc_or(kb, subst_first, theta):
            for theta_double_prime in fol_bc_and(kb, rest, theta_prime):
                yield theta_double_prime

def subst(theta, expr):
    if isinstance(expr, Variable):
        if expr in theta:
            return subst(theta, theta[expr])
        return expr
    elif isinstance(expr, Predicate):
        return Predicate(expr.name, [subst(theta, arg) for arg in expr.args])
    elif isinstance(expr, list):
        return [subst(theta, arg) for arg in expr]
    return expr

import itertools
_counter = itertools.count()
def standardize_variables(rule):
    # Rename variables in rule to be unique
    lhs, rhs = rule
    mapping = {}
    
    def replace(expr):
        if isinstance(expr, Variable):
            if expr.name not in mapping:
                mapping[expr.name] = Variable(f"{expr.name}_{next(_counter)}")
            return mapping[expr.name]
        elif isinstance(expr, Predicate):
            return Predicate(expr.name, [replace(arg) for arg in expr.args])
        return expr

    new_lhs = replace(lhs)
    new_rhs = [replace(p) for p in rhs]
    return new_lhs, new_rhs
