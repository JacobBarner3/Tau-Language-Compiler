# Description: Template for writing a visitor for the ASTs
# Copy and use as necessary
#
# The "ctx" parameter is used to pass information down the AST walk.
# It is not used in this template, but some compiler passes will use it.

from tau import asts
from tau.symbols import *
from tau.error import *
from tau.tokens import Span, Coord
# process is the entry point for the visitor
# It may need to be renamed to match the name of the pass
def process(ast: asts.Program):
    program(ast)


def bind(ast: asts.Program):
    program_ast = program(ast)
    return program_ast


def id(ast: asts.Id, ctx: Scope):
    assert(False)

def idexpr(ast: asts.IdExpr, ctx: Scope):
    sym = ctx.lookup(ast.id.token.value)
    assert sym is not None
    ast.id.symbol = sym


def callexpr(ast: asts.CallExpr, ctx: Scope):
    expr(ast.fn, ctx)
    for arg in ast.args:
        expr(arg, ctx)


def arraycell(ast: asts.ArrayCell, ctx: Scope):
    expr(ast.arr, ctx)
    expr(ast.idx, ctx)


def intliteral(ast: asts.IntLiteral, ctx: Scope):
    pass


def boolliteral(ast: asts.BoolLiteral, ctx: Scope):
    pass


def binaryop(ast: asts.BinaryOp, ctx: Scope):
    expr(ast.left, ctx)
    expr(ast.right, ctx)


def unaryop(ast: asts.UnaryOp, ctx: Scope):
    expr(ast.expr, ctx)


def expr(ast: asts.Expr, ctx: Scope):
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
            error("no type", Span(Coord(0,0), Coord(0,0)))
            raise NotImplementedError(
                f"expr() not implemented for {type(ast)}"
            )


def inttype(ast: asts.IntType, ctx: Scope):
    pass


def booltype(ast: asts.BoolType, ctx: Scope):
    pass


def arraytype(ast: asts.ArrayType, ctx: Scope):
    if ast.size is not None:
        expr(ast.size, ctx)
    typ(ast.element_type_ast, ctx)


def voidtype(ast: asts.VoidType, ctx: Scope):
    pass


def typ(ast: asts.TypeAST, ctx: Scope):
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
            error("no type", Span(Coord(0,0), Coord(0,0)))
            raise NotImplementedError(f"typ() not implemented for {type(ast)}")


def paramdecl(ast: asts.ParamDecl, ctx: Scope):
    id_symbol = IdSymbol(ast.id.token.value, ctx)
    ast.id.symbol = id_symbol
    ctx.symtab[ast.id.token.value] = ast.id.symbol
    typ(ast.type_ast, ctx)


def vardecl(ast: asts.VarDecl, ctx: Scope):
    id_symbol = IdSymbol(ast.id.token.value, ctx)
    ast.id.symbol = id_symbol
    ctx.symtab[ast.id.token.value] = ast.id.symbol
    typ(ast.type_ast, ctx)


def compoundstmt(ast: asts.CompoundStmt, ctx: Scope):
    local_scope = LocalScope(ctx, ast.span)
    ast.local_scope = local_scope
    for decl in ast.decls:
        vardecl(decl, local_scope)
    for s in ast.stmts:
        stmt(s, local_scope)


def assignstmt(ast: asts.AssignStmt, ctx: Scope):
    expr(ast.lhs, ctx)
    expr(ast.rhs, ctx)


def ifstmt(ast: asts.IfStmt, ctx: Scope):
    expr(ast.expr, ctx)
    stmt(ast.thenStmt, ctx)
    if ast.elseStmt is not None:
        stmt(ast.elseStmt, ctx)


def whilestmt(ast: asts.WhileStmt, ctx: Scope):
    expr(ast.expr, ctx)
    stmt(ast.stmt, ctx)


def returnstmt(ast: asts.ReturnStmt, ctx: Scope):
    if ast.expr is not None:
        expr(ast.expr, ctx)


def callstmt(ast: asts.CallStmt, ctx: Scope):
    callexpr(ast.call, ctx)


def printstmt(ast: asts.PrintStmt, ctx: Scope):
    expr(ast.expr, ctx)


def stmt(ast: asts.Stmt, ctx: Scope):
    match ast:
        case asts.CompoundStmt():
            compoundstmt(ast, ctx)
        case asts.AssignStmt():
            assignstmt(ast, ctx)
        case asts.IfStmt():
            ifstmt(ast, ctx)
        case asts.WhileStmt():
            whilestmt(ast, ctx)
        case asts.ReturnStmt():
            returnstmt(ast, ctx)
        case asts.CallStmt():
            callstmt(ast, ctx)
        case asts.PrintStmt():
            printstmt(ast, ctx)
        case _:
            error("no type", Span(Coord(0,0), Coord(0,0)))
            raise NotImplementedError(
                f"stmt() not implemented for {type(ast)}"
            )


def funcdecl(ast: asts.FuncDecl, ctx: Scope):
    id_symbol = IdSymbol(ast.id.token.value, ctx)
    ast.id.symbol = id_symbol
    ctx.symtab[ast.id.token.value] = id_symbol
    func_scope = FuncScope(ctx, ast.span)
    ast.func_scope = func_scope
    for param in ast.params:
        paramdecl(param, func_scope)
    if(ast.ret_type_ast is None):
        error("no return type", Span(Coord(0,0), Coord(0,0)))
    typ(ast.ret_type_ast, func_scope)
    compoundstmt(ast.body, func_scope)


def program(ast: asts.Program):
    global_scope = GlobalScope(ast.span)
    for decl in ast.decls:
        funcdecl(decl, global_scope)