from typing import List

from tau.error import *
from tau import asts, symbols
from tau.vm.vm import (
    Equal,
    Insn,
    NotEqual,
    RestoreEvalStack,
    SaveEvalStack,
    Store,
    Print,
    Label,
    Jump,
    Add,
    Mul,
    Sub,
    Div,
    LessThan,
    LessThanEqual,
    GreaterThan,
    GreaterThanEqual,
    JumpIfNotZero,
    JumpIfZero,
    Load,
    PushFP,
    PushImmediate,
    PushSP,
    PushLabel,
    Negate,
    Not,
    Pop,
    PopFP,
    PopSP,
    JumpIndirect,
    Call,
    Halt,
    Noop,
    Swap,
)


# This is the entry point for the visitor.
def generate(ast: asts.Program) -> List[Insn]:
    return _Program(ast)


def _Program(ast: asts.Program) -> List[Insn]:
    f = []
    f.append(PushLabel("main")) #intro for main func
    f.append(Call())
    f.append(Halt())
    for decl in ast.decls:
        f += _FuncDecl(decl)
    #instruction_dump(f)
    return(f)


def _Stmt(ast: asts.Stmt) -> List[Insn]:
    stack = []
    if isinstance(ast, asts.AssignStmt):
        stack += _AssignStmt(ast)
    elif isinstance(ast, asts.IfStmt):
        stack += _IfStmt(ast)
    elif isinstance(ast, asts.WhileStmt):
        stack += _WhileStmt(ast)
    elif isinstance(ast, asts.CallStmt):
        stack += _CallStmt(ast)
    elif isinstance(ast, asts.CompoundStmt):
        stack += _CompoundStmt(ast)
    elif isinstance(ast, asts.PrintStmt):
        stack += _PrintStmt(ast)
    elif isinstance(ast, asts.ReturnStmt):
        stack += _ReturnStmt(ast)
    else:
        assert False, f"_Stmt() not implemented for {type(ast)}"
    return(stack)


def rval_CallExpr(ast: asts.CallExpr) -> List[Insn]:
    stack = []
    # do pre-call stuff
    stack.append(PushSP(1 + len(ast.args)))
    stack.append(PopSP())
    # do something with ast.fn
    for i, arg in enumerate(ast.args):
        # do something with arg
        stack.append(PushSP(-(i)-2))
        stack += rval(arg)
        stack.append(Store()) 
    stack += (lval(ast.fn))
    stack.append(Call())
    # do post-call stuff
    stack.append(PushSP(-1))
    stack.append(Load())
    stack.append(PushSP(-1-len(ast.args)))
    stack.append(PopSP())
    return(stack)


def _AssignStmt(ast: asts.AssignStmt) -> List[Insn]:
    stack = []
    # do something with ast.lhs
    stack += lval(ast.lhs)
    # do something with ast.rhs
    stack += rval(ast.rhs)
    stack.append(Store())
    return(stack)


def _PrintStmt(ast: asts.PrintStmt) -> List[Insn]:
    stack = []
    # do something with ast.expr
    stack += rval(ast.expr)
    if(rval(ast.expr) == []):
        error("not defined", ast.expr.span)
    stack.append(Print())
    return(stack)


def _IfStmt(ast: asts.IfStmt) -> List[Insn]:
    stack = []
    label_else = str(id(ast)) + "else"
    label_exit = str(id(ast)) + "exit"
    # do something with ast.expr
    stack += control(ast.expr, label_else, False)
    # do something with ast.thenStmt
    stack += _Stmt(ast.thenStmt)
    stack.append(Jump(label_exit))
    # do something with ast.elseStmt
    stack.append(Label(label_else))
    if(ast.elseStmt is not None):
        stack += _Stmt(ast.elseStmt)
    stack.append(Label(label_exit))
    return(stack)


def _WhileStmt(ast: asts.WhileStmt) -> List[Insn]:
    stack = []
    label_top = str(id(ast)) + "top"
    label_exit = str(id(ast)) + "exit"
    stack.append(Label(label_top))
    # do something with ast.expr
    stack += control(ast.expr, label_exit, False)
    # do something with ast.stmt
    stack += _Stmt(ast.stmt)
    stack.append(Jump(label_top))
    stack.append(Label(label_exit))
    return(stack)


# Generate the code such that control is transferred to the label
# if the expression evaluated to the "sense" value.
def control(e: asts.Expr, label: str, sense: bool) -> List[Insn]:
    stack = []
    match e:
        case asts.BinaryOp():
            stack += control_BinaryOp(e, label, sense)
        case asts.UnaryOp():
            stack += control_UnaryOp(e, label, sense)
        case asts.BoolLiteral():
            stack += control_BoolLiteral(e, label, sense)
        case _:
            # TODO: handle other cases
            stack += rval(e)
            if(sense):
                stack.append(JumpIfNotZero(label))
            else:
                stack.append(JumpIfZero(label))
    return(stack)


def control_BoolLiteral(
    e: asts.BoolLiteral, label: str, sense: bool
) -> List[Insn]:
    # TODO: implement
    stack = []
    if(e.value == sense):
        stack.append(Jump(label))
    return(stack)


def control_BinaryOp(e: asts.BinaryOp, label: str, sense: bool) -> List[Insn]:
    stack = []
    exit = str(id(e)) + "exit"
    match e.op.kind:
        case "and":
            # TODO: implement
            if(sense):
                stack += control(e.left, exit, False)
                stack += control(e.right, label, True)
                stack.append(Label(exit))
            else:
                stack += control(e.left, label, False)
                stack += control(e.right, label, False)
        case "or":
            # TODO: implement
            if(sense):
                stack += control(e.left, label, True)
                stack += control(e.right, label, True)
            else:
                stack += control(e.left, exit, True)
                stack += control(e.right, label, False)
                stack.append(Label(exit))
        case _:
            # TODO: handle other cases
            stack += rval(e)
            if(sense):
                stack.append(JumpIfNotZero(label))
            else:
                stack.append(JumpIfZero(label))
    return(stack)


def control_UnaryOp(e: asts.UnaryOp, label: str, sense: bool) -> List[Insn]:
    stack = []
    match e.op.kind:
        case "not":
            # TODO: implement
            if(e.op.kind == "not"):
                stack += control(e.expr, label, not(sense))
        case _:
            assert False, f"control_UnaryOp() not implemented for {e.op.kind}"
    return(stack)


def _CallStmt(ast: asts.CallStmt) -> List[Insn]:
    # do something with ast.call
    stack = []
    stack += rval(ast.call)
    stack.append(Pop())
    return(stack)


def _CompoundStmt(ast: asts.CompoundStmt) -> List[Insn]:
    stack = []
    for stmt in ast.stmts:
        stack += _Stmt(stmt)
    return(stack)


def _FuncDecl(ast: asts.FuncDecl) -> List[Insn]:
    # do something for prologue
    stack = []
    stack.append(Label(ast.id.token.value)) #label for func dec
    stack.append(PushSP(0))
    stack.append(Swap())
    stack.append(Store()) #store the return address at the old SP (this is new fp at offset 0)
    stack.append(PushSP(1))
    stack.append(PushFP(0))
    stack.append(Store()) #this is storing the old fp at offset 1
    stack.append(PushSP(2))
    stack.append(PushSP(0))
    stack.append(Store()) #this is storing the old sp at the new fp with offset 2
    stack.append(PushSP(0))
    stack.append(PopFP())
    stack.append(PushSP(ast.size)) #setting new fp to the old sp and setting the new sp based on the frame size.
    stack.append(PopSP())

    stack += _CompoundStmt(ast.body)
    
    # do something for epilogue
    stack.append(PushFP(0))
    stack.append(Load()) #getting return address
    stack.append(PushFP(2))
    stack.append(Load())
    stack.append(PopSP()) #setting the callie to the callers return address
    stack.append(PushFP(1))
    stack.append(Load())
    stack.append(PopFP()) #setting the callie fp value to the callers fp value
    stack.append(JumpIndirect()) #returns you to the callers frame pointer.
    return(stack)


def _ReturnStmt(ast: asts.ReturnStmt) -> List[Insn]:
    # do something with ast.expr, if present
    stack = []
    if(ast.expr is not None):
        stack.append(PushFP(-1))
        stack += rval(ast.expr)
        assert(rval != [])
        stack.append(Store())
    stack.append(PushFP(0))
    stack.append(Load()) #getting return address
    stack.append(PushFP(2))
    stack.append(Load())
    stack.append(PopSP()) #setting the callie to the callers return address
    stack.append(PushFP(1))
    stack.append(Load())
    stack.append(PopFP()) #setting the callie fp value to the callers fp value
    stack.append(JumpIndirect()) #returns you to the callers frame pointer.
    return(stack)


def lval(e: asts.Expr) -> List[Insn]:
    match e:
        case asts.IdExpr():
            return lval_IdExpr(e)
        case _:
            assert False, f"lval() not implemented for {type(e)}"


def lval_IdExpr(e: asts.IdExpr) -> List[Insn]:
    assert isinstance(e.id.symbol, symbols.IdSymbol)
    stack = []
    match type(e.id.symbol.scope):
        case symbols.GlobalScope:
            # TODO: implement
            stack.append(PushLabel(e.id.token.value))
        case symbols.LocalScope:
            # TODO: implement
            local_offset = e.id.symbol.offset
            stack.append(PushFP(local_offset))

        case symbols.FuncScope:
            # TODO: implement
            func_offset = e.id.symbol.offset
            stack.append(PushFP(func_offset))
        case _:
            assert (
                False
            ), f"lval_id() not implemented for {type(e.id.symbol.scope)}"
    return(stack)


def rval(e: asts.Expr) -> List[Insn]:
    stack = []
    match e:
        case asts.BinaryOp():
            stack += rval_BinaryOp(e)
        case asts.UnaryOp():
            stack += rval_UnaryOp(e)
        case asts.CallExpr():
            stack += rval_CallExpr(e)
        case asts.IdExpr():
            stack += rval_IdExpr(e)
        case asts.IntLiteral():
            stack += rval_IntLiteral(e)
        case asts.BoolLiteral():
            stack += rval_BoolLiteral(e)
        case _:
            assert False, f"rval() not implemented for {type(e)}"
    return(stack)


def rval_BoolLiteral(e: asts.BoolLiteral) -> List[Insn]:
    # TODO: implement
    stack = []
    if(e.value == True):
        stack.append(PushImmediate(1))
        return(stack)
    stack.append(PushImmediate(0))
    return(stack)


def rval_IntLiteral(e: asts.IntLiteral) -> List[Insn]:
    # TODO: implement
    stack = []
    stack.append(PushImmediate(int(e.token.value)))
    return(stack)


def rval_IdExpr(e: asts.IdExpr) -> List[Insn]:
    # TODO: implement
    stack = []
    stack.append(PushFP(e.id.symbol.offset))
    stack.append(Load())
    return(stack)


def rval_BinaryOp(e: asts.BinaryOp) -> List[Insn]:
    stack = []
    match e.op.kind:
        case "+":
            # TODO: implement
            stack += rval(e.left)
            stack += rval(e.right)
            stack.append(Add())
        case "-":
            # TODO: implement
            stack += rval(e.left)
            stack += rval(e.right)
            stack.append(Sub())
        case "*":
            # TODO: implement
            stack += rval(e.left)
            stack += rval(e.right)
            stack.append(Mul())
        case "/":
            # TODO: implement
            stack += rval(e.left)
            stack += rval(e.right)
            stack.append(Div())
        case "<":
            # TODO: implement
            stack += rval(e.left)
            stack += rval(e.right)
            stack.append(LessThan())
        case "<=":
            # TODO: implement
            stack += rval(e.left)
            stack += rval(e.right)
            stack.append(LessThanEqual())
        case ">":
            # TODO: implement
            stack += rval(e.left)
            stack += rval(e.right)
            stack.append(GreaterThan())
        case ">=":
            # TODO: implement
            stack += rval(e.left)
            stack += rval(e.right)
            stack.append(GreaterThanEqual())
        case "==":
            # TODO: implement
            stack += rval(e.left)
            stack += rval(e.right)
            stack.append(Equal())
        case "!=":
            # TODO: implement
            stack += rval(e.left)
            stack += rval(e.right)
            stack.append(NotEqual())
        case "and":
            # TODO: implement
            first_false = str(id(e)) + "false"
            exit = str(id(e)) + "exit"
            stack += control(e, first_false, False)
            stack.append(PushImmediate(1))
            stack.append(Jump(exit))
            stack.append(Label(first_false))
            stack.append(PushImmediate(0))
            stack.append(Label(exit))
        case "or":
            # TODO: implement
            false = str(id(e)) + "false"
            exit = str(id(e)) + "exit"
            stack += control(e, false, True)
            stack.append(PushImmediate(0))
            stack.append(Jump(exit))
            stack.append(Label(false))
            stack.append(PushImmediate(1))
            stack.append(Label(exit))
        case _:
            assert False, f"rval_BinaryOp() not implemented for {e.op}"
    return(stack)


def rval_UnaryOp(e: asts.UnaryOp) -> List[Insn]:
    stack = []
    stack += rval(e.expr)
    match e.op.kind:
        case "-":
            # TODO: implement
            stack.append(Negate())
        case "not":
            # TODO: implement
            stack.append(Not())
        case _:
            assert False, f"rval_UnaryOp() not implemented for {e.op}"
    return(stack)

# def instruction_dump(insns: List[Insn]):
#     with open("./insns_list", 'w') as file:
#         for insn in insns:
#             file.write(f"{insn}\n")