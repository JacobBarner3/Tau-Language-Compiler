# Description: Template for writing a visitor for the ASTs
# Copy and use as necessary
#
# The "ctx" parameter is used to pass information down the AST walk.
# It is not used in this template, but some compiler passes will use it.

from tau import asts
from tau.symbols import *
from tau.error import *
from tau.tokens import *
# process is the entry point for the visitor
# It may need to be renamed to match the name of the pass
def process(ast: asts.Program):
    program(ast)


def id(ast: asts.Id):
    assert False


def idexpr(ast: asts.IdExpr):
    ast.id.semantic_type = ast.id.symbol.get_type()
    ast.semantic_type = ast.id.semantic_type


def callexpr(ast: asts.CallExpr, ctx: asts.TypeAST):
    expr(ast.fn, ctx)
    assert isinstance(ast.fn.semantic_type, FuncType)
    ast.semantic_type = ast.fn.semantic_type.ret
    for arg in ast.args:
        expr(arg, ctx)


def arraycell(ast: asts.ArrayCell, ctx: asts.TypeAST):
    expr(ast.arr, ctx)
    expr(ast.idx, ctx)
    assert isinstance(ast.arr.semantic_type, ArrayType)
    ast.semantic_type = ast.arr.semantic_type.element_type


def intliteral(ast: asts.IntLiteral):
    ast.semantic_type = IntType()


def boolliteral(ast: asts.BoolLiteral):
    ast.semantic_type = BoolType()


def binaryop(ast: asts.BinaryOp, ctx: asts.TypeAST):
    expr(ast.left, ctx)
    expr(ast.right, ctx)
    if ast.op.value in {"+", "-", "*", "/"}:
        ast.semantic_type = IntType()
    elif ast.op.value in {"or", "and", ">", "<", ">=", "<=", "==", "!="}:
        ast.semantic_type = BoolType()


def unaryop(ast: asts.UnaryOp, ctx: asts.TypeAST):
    expr(ast.expr, ctx)
    if ast.op.value in {"-"}:
        ast.semantic_type = IntType()
    elif ast.op.value in {"not"}:
        ast.semantic_type = BoolType()


def expr(ast: asts.Expr, ctx: asts.TypeAST):
    match ast:
        case asts.IdExpr():
            idexpr(ast)
        case asts.CallExpr():
            callexpr(ast, ctx)
        case asts.ArrayCell():
            arraycell(ast, ctx)
        case asts.IntLiteral():
            intliteral(ast)
        case asts.BoolLiteral():
            boolliteral(ast)
        case asts.BinaryOp():
            binaryop(ast, ctx)
        case asts.UnaryOp():
            unaryop(ast, ctx)
        case _:
            raise NotImplementedError(
                f"expr() not implemented for {type(ast)}"
            )


def inttype(ast: asts.IntType):
    ast.semantic_type = IntType()


def booltype(ast: asts.BoolType):
    ast.semantic_type = BoolType()


def arraytype(ast: asts.ArrayType, ctx: asts.TypeAST):
    if ast.size is not None:
        expr(ast.size, ctx)
    typ(ast.element_type_ast, ctx)
    ast.semantic_type = ArrayType(ast.element_type_ast.semantic_type)


def voidtype(ast: asts.VoidType):
    ast.semantic_type = VoidType()


def typ(ast: asts.TypeAST, ctx: asts.TypeAST):
    match ast:
        case asts.IntType():
            inttype(ast)
        case asts.BoolType():
            booltype(ast)
        case asts.ArrayType():
            arraytype(ast, ctx)
        case asts.VoidType():
            voidtype(ast)
        case _:
            raise NotImplementedError(f"typ() not implemented for {type(ast)}")


def paramdecl(ast: asts.ParamDecl, ctx: asts.TypeAST):
    typ(ast.type_ast, ctx)
    ast.semantic_type = ast.type_ast.semantic_type
    ast.id.semantic_type = ast.type_ast.semantic_type
    ast.id.symbol.set_type(ast.type_ast.semantic_type)


def vardecl(ast: asts.VarDecl, ctx: asts.TypeAST):
    typ(ast.type_ast, ctx)
    ast.semantic_type = ast.type_ast.semantic_type
    ast.id.symbol.set_type(ast.type_ast.semantic_type)
    ast.id.semantic_type = ast.type_ast.semantic_type


def compoundstmt(ast: asts.CompoundStmt, ctx: asts.TypeAST):
    for decl in ast.decls:
        vardecl(decl, ctx)
    for s in ast.stmts:
        stmt(s, ctx)


def assignstmt(ast: asts.AssignStmt, ctx: asts.TypeAST):
    expr(ast.lhs, ctx)
    expr(ast.rhs, ctx)
    if(ast.lhs.semantic_type != ast.rhs.semantic_type):
        error("Mis-matched types", Span(ast.lhs.span.start, ast.rhs.span.end))


def ifstmt(ast: asts.IfStmt, ctx: asts.TypeAST):
    expr(ast.expr, ctx)
    stmt(ast.thenStmt, ctx)
    if ast.elseStmt is not None:
        stmt(ast.elseStmt, ctx)


def whilestmt(ast: asts.WhileStmt, ctx: asts.TypeAST):
    expr(ast.expr, ctx)
    stmt(ast.stmt, ctx)


def returnstmt(ast: asts.ReturnStmt, ctx: asts.TypeAST):
    if ast.expr is not None:
        expr(ast.expr, ctx)
        if(ast.expr.semantic_type != ctx.semantic_type):
            error("Wrong return type", ast.span)


def callstmt(ast: asts.CallStmt, ctx: asts.TypeAST):
    callexpr(ast.call, ctx)


def printstmt(ast: asts.PrintStmt, ctx: asts.TypeAST):
    expr(ast.expr, ctx)


def stmt(ast: asts.Stmt, ctx: asts.TypeAST):
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


def funcdecl(ast: asts.FuncDecl, ctx: asts.TypeAST):
    typ(ast.ret_type_ast, ctx)
    for param in ast.params:
        paramdecl(param, ctx)
    params = [param.semantic_type for param in ast.params]
    func_type = FuncType(params, ast.ret_type_ast.semantic_type)
    ast.id.symbol.set_type(func_type)
    ast.id.semantic_type = func_type
    compoundstmt(ast.body, ast.ret_type_ast)


def program(ast: asts.Program):
    for decl in ast.decls:
        funcdecl(decl, asts.TypeAST())