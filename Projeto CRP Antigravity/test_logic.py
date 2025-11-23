import unittest
from src.logic.propositional import PropositionalKB, Symbol, And, Or, Not, Implication, tt_entails
from src.logic.first_order import FOLKB, Predicate, Variable, Constant, unify, fol_bc_ask

class TestPropositional(unittest.TestCase):
    def test_symbols(self):
        kb = PropositionalKB()
        kb.tell(Symbol("A"))
        self.assertTrue(kb.ask(Symbol("A")))
        self.assertFalse(kb.ask(Symbol("B")))

    def test_implication(self):
        kb = PropositionalKB()
        # A -> B
        kb.tell(Implication(Symbol("A"), Symbol("B")))
        kb.tell(Symbol("A"))
        self.assertTrue(kb.ask(Symbol("B")))

    def test_complex(self):
        kb = PropositionalKB()
        # (A & B) -> C
        kb.tell(Implication(And(Symbol("A"), Symbol("B")), Symbol("C")))
        kb.tell(Symbol("A"))
        kb.tell(Symbol("B"))
        self.assertTrue(kb.ask(Symbol("C")))

class TestFOL(unittest.TestCase):
    def test_unify(self):
        x = Variable("x")
        y = Variable("y")
        a = Constant("A")
        b = Constant("B")
        
        # Unify(x, A) -> {x: A}
        theta = unify(x, a, {})
        self.assertEqual(theta[x], a)
        
        # Unify(P(x), P(A)) -> {x: A}
        p1 = Predicate("P", [x])
        p2 = Predicate("P", [a])
        theta = unify(p1, p2, {})
        self.assertEqual(theta[x], a)

    def test_bc(self):
        kb = FOLKB()     
        v_x = Variable("x")
        c_tom = Constant("Tom")
        
        kb.tell(Predicate("Cat", [c_tom]))
        kb.tell((Predicate("Animal", [v_x]), [Predicate("Cat", [v_x])]))
        
        results = list(kb.ask(Predicate("Animal", [c_tom])))
        self.assertTrue(len(results) > 0)

if __name__ == '__main__':
    unittest.main()
