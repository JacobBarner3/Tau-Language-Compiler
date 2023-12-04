# Description: Template for writing a visitor for the ASTs
# Copy and use as necessary
#
# The "ctx" parameter is used to pass information down the AST walk.
# It is not used in this template, but some compiler passes will use it.

from tau import asts
from tau.symbols import *

# process is the entry point for the visitor
# It may need to be renamed to match the name of the pass
def process(ast: asts.Program):
    program(ast)

def id(ast: asts.Id, ctx: int):
    assert(False)

def idexpr(ast: asts.IdExpr, ctx: int):
    pass

def callexpr(ast: asts.CallExpr, ctx: int):
    expr(ast.fn, ctx)
    for arg in ast.args:
        expr(arg, ctx)

def arraycell(ast: asts.ArrayCell, ctx: int):
    expr(ast.arr, ctx)
    expr(ast.idx, ctx)

def intliteral(ast: asts.IntLiteral, ctx: int):
    pass

def boolliteral(ast: asts.BoolLiteral, ctx: int):
    pass

def binaryop(ast: asts.BinaryOp, ctx: int):
    expr(ast.left, ctx)
    expr(ast.right, ctx)

def unaryop(ast: asts.UnaryOp, ctx: int):
    expr(ast.expr, ctx)

def expr(ast: asts.Expr, ctx: int):
    match ast:
        case asts.IdExpr():
            idexpr(ast, ctx)
        case asts.CallExpr():
            callexpr(ast, ctx)
        case asts.ArrayCell():
            arraycell(ast, ctx)
        case asts.IntLiteral():
            intliteral(ast, ctx)
        case asts.BoolLiteral():
            boolliteral(ast, ctx)
        case asts.BinaryOp():
            binaryop(ast, ctx)
        case asts.UnaryOp():
            unaryop(ast, ctx)
        case _:
            raise NotImplementedError(
                f"expr() not implemented for {type(ast)}"
            )

def inttype(ast: asts.IntType, ctx: int):
    pass

def booltype(ast: asts.BoolType, ctx: int):
    pass

def arraytype(ast: asts.ArrayType, ctx: int):
    if ast.size is not None:
        expr(ast.size, ctx)
    typ(ast.element_type_ast, ctx)

def voidtype(ast: asts.VoidType, ctx: int):
    pass

def typ(ast: asts.TypeAST, ctx: int):
    match ast:
        case asts.IntType():
            inttype(ast, ctx)
        case asts.BoolType():
            booltype(ast, ctx)
        case asts.ArrayType():
            arraytype(ast, ctx)
        case asts.VoidType():
            voidtype(ast, ctx)
        case _:
            raise NotImplementedError(f"typ() not implemented for {type(ast)}")

def paramdecl(ast: asts.ParamDecl, ctx: int):
    ast.id.symbol.offset = ctx
    typ(ast.type_ast, ctx)

def vardecl(ast: asts.VarDecl, ctx: int):
    ast.id.symbol.offset = ctx
    typ(ast.type_ast, ctx)

def compoundstmt(ast: asts.CompoundStmt, ctx: int):
    total = 0
    for decl in ast.decls:
        vardecl(decl, ctx)
        ctx += 1
    total = ctx
    for s in ast.stmts:
        total += stmt(s, ctx)
    return(total)

def assignstmt(ast: asts.AssignStmt, ctx: int):
    expr(ast.lhs, ctx)
    expr(ast.rhs, ctx)
    return(0)

def ifstmt(ast: asts.IfStmt, ctx: int):
    expr(ast.expr, ctx)
    total = stmt(ast.thenStmt, ctx)
    if ast.elseStmt is not None:
        total += stmt(ast.elseStmt, ctx)
    return(total)


def whilestmt(ast: asts.WhileStmt, ctx: int):
    expr(ast.expr, ctx)
    total = stmt(ast.stmt, ctx)
    return(total)

def returnstmt(ast: asts.ReturnStmt, ctx: int):
    if ast.expr is not None:
        expr(ast.expr, ctx)
    return(0)


def callstmt(ast: asts.CallStmt, ctx: int):
    callexpr(ast.call, ctx)
    return(0)


def printstmt(ast: asts.PrintStmt, ctx: int):
    expr(ast.expr, ctx)
    return(0)


def stmt(ast: asts.Stmt, ctx: int):
    total = 0
    match ast:
        case asts.CompoundStmt():
            total += compoundstmt(ast, ctx)
        case asts.AssignStmt():
            total += assignstmt(ast, ctx)
        case asts.IfStmt():
            total += ifstmt(ast, ctx)
        case asts.WhileStmt():
            total += whilestmt(ast, ctx)
        case asts.ReturnStmt():
            total += returnstmt(ast, ctx)
        case asts.CallStmt():
            total += callstmt(ast, ctx)
        case asts.PrintStmt():
            total += printstmt(ast, ctx)
        case _:
            raise NotImplementedError(
                f"stmt() not implemented for {type(ast)}"
            )
    return(total)

def funcdecl(ast: asts.FuncDecl, ctx: int):
    ast.id.symbol.offset = 0
    ctx = -2
    for param in ast.params:
        paramdecl(param, ctx)
        ctx -= 1
    typ(ast.ret_type_ast, ctx)
    ctx = 3
    ctx += compoundstmt(ast.body, ctx)
    ast.size = ctx

def program(ast: asts.Program):
    for decl in ast.decls:
        funcdecl(decl, 0)