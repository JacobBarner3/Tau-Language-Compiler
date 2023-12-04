from tau.asts import *
from tau.tokens import *
from scanner import *
from tau.error import *

class Parser:
    def __init__(self, scanner):
        self.scanner = scanner

    def error(self, msg: str):
        raise Exception(msg + " at " + str(self.scanner.peek()))
        

    def match(self, kind: str):
        if self.current() == kind:
            return self.scanner.consume()
        else:
            self.error(f"expected {kind}")

    def current(self):
        return self.scanner.peek().kind

    def parse(self):
        v = self._program()
        self.match("EOF")
        return v
    
    def start_coord(self):
        return self.scanner.peek().span.start
    
    def end_coord(self):
        return self.scanner.peek().span.end
    # program -> { function_dec }
    def _program(self):
        start = self.start_coord()
        end = self.end_coord()
        func_decs = []
        while self.current() in {'func'}:
            function_dec = self._function_dec()
            func_decs.append(function_dec)
            end = function_dec.span.end
        span = Span(start, end)
        program = Program(func_decs, span)
        return program
    # function_dec -> "func" ID "(" [ params ] ")" ":" type nest
    def _function_dec(self):
        start = self.start_coord()
        self.match('func')
        inner = self.match('ID')
        assert(inner is not None)
        id = Id(inner)
        self.match('(')
        params = []
        if self.current() in {'ID'}:
            params = self._params()
        self.match(')')
        self.match(':')
        type = self._type()
        assert(type is not None)
        comp_stmt = self._nest()
        assert(comp_stmt is not None)
        span = Span(start, comp_stmt.span.end)
        function_dec = FuncDecl(id, params, type, comp_stmt, span)
        return function_dec
    # params -> paramater { "," paramater }
    def _params(self):
        params = []
        paramater = self._paramater()
        params.append(paramater)
        while self.current() in {','}:
            self.match(',')
            paramater = self._paramater()
            params.append(paramater)
        return params
    # paramater -> ID ":" type
    def _paramater(self):
        inner = self.match('ID')
        assert(inner is not None)
        id = Id(inner)
        self.match(':')
        type = self._type()
        span = Span(id.span.start, type.span.end)
        param = ParamDecl(id, type, span)
        return param
    # declaration -> "var" ID ":" type
    def _declaration(self):
        start = self.start_coord()
        self.match('var')
        inner = self.match('ID')
        assert(inner is not None)
        id = Id(inner)
        self.match(':')
        type = self._type()
        span = Span(start, type.span.end)
        declaration = VarDecl(id, type, span) # default?
        return declaration
    # statement -> call | print | if | while | equation
    def _statement(self):
        if self.current() in {'call'}:
            statement = self._call()
        elif self.current() in {'print'}:
            statement = self._print()
        elif self.current() in {'if'}:
            statement = self._if()
        elif self.current() in {'while'}:
            statement = self._while()
        elif self.current() in {'ID'}:
            statement = self._equation()
        else:
            self.error('syntax error')
            assert False
        return statement
    # func_call -> ID "(" [ expression_or { "," expression_or } ] ")"
    def _func_call(self):
        inner = self.match('ID')
        assert(inner is not None)
        name = Id(inner)
        id = IdExpr(name, name.span)
        self.match('(')
        params = []
        if self.current() in {'(', '-', 'false', 'not', 'true', 'ID', 'INT'}:
            params.append(self._expression_or())
            while self.current() in {','}:
                self.match(',')
                params.append(self._expression_or())
        end = self.end_coord()
        self.match(')')
        span = Span(id.span.start, end)
        func_call = CallExpr(id, params, span) # default?
        return func_call
    # passed -> "(" [ expression_or { "," expression_or } ] ")"
    def _passed(self, name):
        id = IdExpr(name, name.span)
        self.match('(')
        params = []
        if self.current() in {'(', '-', 'false', 'not', 'true', 'ID', 'INT'}:
            params.append(self._expression_or())
            while self.current() in {','}:
                self.match(',')
                params.append(self._expression_or())
        end = self.end_coord()
        self.match(')')
        span = Span(id.span.start, end)
        passed = CallExpr(id, params, span) # default?
        return passed
    # nest -> "{" { declaration } { statement | nest } [ return ] "}"
    def _nest(self):
        start = self.start_coord()
        self.match('{')
        decls = []
        stmts = []
        while self.current() in {'var'}:
            decls.append(self._declaration())
        while self.current() in {'call', 'if', 'print', 'while', '{', 'ID'}:
            if self.current() in {'call', 'if', 'print', 'while', 'ID'}:
                stmts.append(self._statement())
            elif self.current() in {'{'}:
                compound = self._nest()
                stmts.append(compound)
            else:
                self.error('syntax error')
                assert False
        if self.current() in {'return'}:
            stmts.append(self._return())
        end = self.end_coord()
        self.match('}')
        span = Span(start, end)
        compound_stmt = CompoundStmt(decls, stmts, span) # default?
        return compound_stmt
    # if -> "if" expression_or nest [ else ]
    def _if(self):
        start = self.start_coord()
        self.match('if')
        expression = self._expression_or()
        assert(expression is not None)
        comp_stmt = self._nest()
        assert(comp_stmt is not None)
        end = comp_stmt.span.end
        else_expression = None
        if self.current() in {'else'}:
            else_expression = self._else()
            assert(else_expression is not None)
            end = else_expression.span.end
        span = Span(start, end)
        if_stmt = IfStmt(expression, comp_stmt, else_expression, span)
        return if_stmt
    # else -> "else" nest
    def _else(self):
        self.match('else')
        else_stmt = self._nest()
        return else_stmt
    # while -> "while" (expression_or) nest
    def _while(self):
        start = self.start_coord()
        self.match('while')
        expression = self._expression_or()
        assert(expression is not None)
        comp_stmt = self._nest()
        span = Span(start, comp_stmt.span.end)
        while_stmt = WhileStmt(expression, comp_stmt, span) # default?
        return while_stmt
    # call -> "call" func_call
    def _call(self):
        start = self.start_coord()
        self.match('call')
        call = self._func_call()
        span = Span(start, call.span.end)
        call_stmt =  CallStmt(call, span) # default?
        return call_stmt
    # print -> "print" expression_or
    def _print(self):
        start = self.start_coord()
        self.match('print')
        expression = self._expression_or()
        assert(expression is not None)
        span = Span(start, expression.span.end)
        print_stmt = PrintStmt(expression, span) # default?
        return print_stmt
    # return -> "return" [ expression_or ]
    def _return(self):
        start = self.start_coord()
        end = self.end_coord()
        self.match('return')
        expression = None
        if self.current() in {'(', '-', 'false', 'not', 'true', 'ID', 'INT'}:
            expression = self._expression_or()
            assert(expression is not None)
            end = expression.span.end
        span = Span(start, end)
        return_stmt = ReturnStmt(expression, span) # default?
        return return_stmt
    # equation -> (ID | array) "=" expression_or
    def _equation(self):
        start = self.start_coord()
        inner = self.match('ID')
        assert(inner is not None)
        id = Id(inner)
        lhs = IdExpr(id, id.span)
        if self.current() in {'['}:
            lhs = self._array(id)
        self.match('=')
        expression = self._expression_or()
        assert(expression is not None)
        span = Span(start, expression.span.end)
        equation = AssignStmt(lhs, expression, span) # default?
        return equation
    # expression_or -> expression_and { "or" expression_and }
    def _expression_or(self):
        bin_op = self._expression_and()
        assert(bin_op is not None)
        start = bin_op.span.start
        while self.current() in {'or'}:
            op = self.match('or')
            assert(op is not None)
            expression = self._expression_and()
            assert(expression is not None)
            span = Span(start, expression.span.end)
            bin_op = BinaryOp(op, bin_op, expression, span)
        return bin_op
    # expression_and -> expression_comp { "and" expression_comp }
    def _expression_and(self):
        bin_op = self._expression_comp()
        assert(bin_op is not None)
        start = bin_op.span.start
        while self.current() in {'and'}:
            op = self.match('and')
            assert(op is not None)
            expression = self._expression_comp()
            assert(expression is not None)
            span = Span(start, expression.span.end)
            bin_op = BinaryOp(op, bin_op, expression, span)
        return bin_op
    # expression_comp -> expression_as { ("<" | ">" | "<=" | ">=" | "==" | "!=") expression_as }
    def _expression_comp(self):
        bin_op = self._expression_as()
        assert(bin_op is not None)
        start = bin_op.span.start
        while self.current() in {'!=', '<', '<=', '==', '>', '>='}:
            if self.current() in {'<'}:
                op = self.match('<')
                assert(op is not None)
            elif self.current() in {'>'}:
                op = self.match('>')
                assert(op is not None)
            elif self.current() in {'<='}:
                op = self.match('<=')
                assert(op is not None)
            elif self.current() in {'>='}:
                op = self.match('>=')
                assert(op is not None)
            elif self.current() in {'=='}:
                op = self.match('==')
                assert(op is not None)
            elif self.current() in {'!='}:
                op = self.match('!=')
                assert(op is not None)
            else:
                self.error('syntax error')
                assert False
            expression = self._expression_as()
            assert(expression is not None)
            span = Span(start, expression.span.end)
            bin_op = BinaryOp(op, bin_op, expression, span)
        return bin_op
    # expression_as -> expression_md { ("+" | "-") expression_md }
    def _expression_as(self):
        bin_op = self._expression_md()
        assert(bin_op is not None)
        start = bin_op.span.start
        while self.current() in {'+', '-'}:
            if self.current() in {'+'}:
                op = self.match('+')
                assert(op is not None)
            elif self.current() in {'-'}:
                op = self.match('-')
                assert(op is not None)
            else:
                self.error('syntax error')
                assert False
            expression = self._expression_md()
            assert(expression is not None)
            span = Span(start, expression.span.end)
            bin_op = BinaryOp(op, bin_op, expression, span)
        return bin_op
    # expression_md -> expression_biop { ("*" | "/") expression_biop }
    def _expression_md(self):
        bin_op = self._expression_biop()
        assert(bin_op is not None)
        start = bin_op.span.start
        while self.current() in {'*', '/'}:
            if self.current() in {'*'}:
                op = self.match('*')
                assert(op is not None)
            elif self.current() in {'/'}:
                op = self.match('/')
                assert(op is not None)
            else:
                self.error('syntax error')
                assert False
            expression = self._expression_biop()
            assert(expression is not None)
            span = Span(start, expression.span.end)
            bin_op = BinaryOp(op, bin_op, expression, span)
        return bin_op
    # expression_biop -> { "-" | "not" } (INT | "true" | "false" | "(" expression_or ")" | term)
    def _expression_biop(self):
        un_op = None
        while self.current() in {'-', 'not'}:
            if self.current() in {'-'}:
                un_op = self.match('-')
                assert(un_op is not None)
                expression = self._expression_biop()
                assert(expression is not None)
                span = Span(un_op.span.start, expression.span.end)
                unary_Op = UnaryOp(un_op, expression, span)
                return(unary_Op)
            elif self.current() in {'not'}:
                un_op = self.match('not')
                assert(un_op is not None)
            else:
                self.error('syntax error')
                assert False
        if self.current() in {'INT'}:
            token = self.match('INT')
            assert(token is not None)
            expression = IntLiteral(token, token.span)
        elif self.current() in {'true'}:
            token = self.match('true')
            assert(token is not None)
            expression = BoolLiteral(token, True, token.span)
        elif self.current() in {'false'}:
            token = self.match('false')
            assert(token is not None)
            expression = BoolLiteral(token, False, token.span)
        elif self.current() in {'('}:
            self.match('(')
            expression = self._expression_or()
            assert(expression is not None)
            self.match(')')
        elif self.current() in {'ID'}:
            expression = self._term()
            assert(expression is not None)
        else:
            self.error('syntax error')
            assert False
        if(un_op != None):
            span = Span(un_op.span.start, expression.span.end)
            unary_Op = UnaryOp(un_op, expression, span)
            return(unary_Op)
        return expression
    
    # term -> ID [ (passed | type_array) ]
    def _term(self):
        inner = self.match('ID')
        assert(inner is not None)
        id = Id(inner)
        term = IdExpr(id, id.span)
        if self.current() in {'(', '['}:
            if self.current() in {'('}:
                term = self._passed(id)
                assert(term is not None)
            elif self.current() in {'['}:
                term = self._array(id)
                assert(term is not None)
            else:
                self.error('syntax error')
                assert False
        return(term)
    
    # array -> ID "[" expression_or "]"
    def _array(self, name):
        id = IdExpr(name, name.span)
        self.match('[')
        expression = self._expression_or()
        assert(expression is not None)
        end = self.end_coord()
        assert(end is not None)
        self.match(']')
        span = Span(id.span.start, end)
        array = ArrayCell(id, expression, span) # default?
        return array
    # type_array -> "[" expression_or "]"
    def _type_array(self):
        start = self.start_coord()
        self.match('[')
        expression = None
        if self.current() in {'(', '-', 'false', 'not', 'true', 'ID', 'INT'}:
            expression = self._expression_or()
            assert(expression is not None)
        self.match(']')
        type = self._type()
        span = Span(start, type.span.end)
        type_array = ArrayType(expression, type, span)
        return type_array
    # binary_lit -> "true" | "false"
    def _binary_lit(self):
        if self.current() in {'true'}:
            binary_lit = self.match('true')
            assert(binary_lit is not None)
            boolean = BoolLiteral(binary_lit, True, binary_lit.span)
        elif self.current() in {'false'}:
            binary_lit = self.match('false')
            assert(binary_lit is not None)
            boolean = BoolLiteral(binary_lit, False, binary_lit.span)
        else:
            self.error('syntax error')
            assert False
        return boolean
    # type -> "int" | "bool" | "void" | type_array
    def _type(self):
        if self.current() in {'int'}:
            token = self.match('int')
            assert(token is not None)
            type = IntType(token)
        elif self.current() in {'bool'}:
            token = self.match('bool')
            assert(token is not None)
            type = BoolType(token)
        elif self.current() in {'void'}:
            token = self.match('void')
            assert(token is not None)
            type = VoidType(token)
        elif self.current() in {'['}:
            type = self._type_array()
        else:
            self.error('syntax error')
            assert False
        return type