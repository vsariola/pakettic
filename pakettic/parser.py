from sys import prefix
from xml.dom.expatbuilder import DOCUMENT_NODE
from pakettic import ast
import pyparsing as pp
import functools

pp.ParserElement.enablePackrat()

LBRACK, RBRACK, LBRACE, RBRACE, LPAR, RPAR, EQ, COMMA, SEMI, COLON, PERIOD, VLINE = map(
    pp.Suppress, '[]{}()=,;:.|'
)
keywords = {
    k.upper(): pp.Combine(pp.Literal(k) + ~pp.Char(pp.alphanums + "_")) .suppress()
    for k in """\
    return break do end while if then elseif else for in function local repeat until nil false true and or not goto
    """.split()
}
vars().update(keywords)
any_keyword = pp.MatchFirst(keywords.values()).setName("<keyword>")

# Name
Name = ~any_keyword + pp.Word(pp.alphas, pp.alphanums + "_")

# LiteralString
short_literal_string = (pp.QuotedString(
    '"', escChar='\\') | pp.QuotedString('\'', escChar='\\')).setParseAction(lambda toks: ast.LiteralString(toks[0]))
long_literal_string = pp.QuotedString(
    quote_char="[[", end_quote_char="]]", multiline=True, convert_whitespace_escapes=False)
for i in range(3):
    long_literal_string |= pp.QuotedString(
        quote_char="[=" + "=" * i + "[", end_quote_char="]=" + "=" * i + "]", multiline=True, convert_whitespace_escapes=False)
long_literal_string.setParseAction(lambda toks: ast.LiteralString(
    toks[0][1:] if toks[0].startswith("\n") else toks[0]))
LiteralString = short_literal_string | long_literal_string

# Numeral
base10 = pp.Regex(r"(?P<whole>\d+)(?:\.(?P<frac>\d*))?(?:[eE](?P<exp>[+-]?\d+))?")
base10.set_parse_action(lambda t: ast.Numeral(int(t["whole"] or 0), int(
    t["frac"][::-1]) if t["frac"] is not None else 0, int(t["exp"] or 0)))

frac10 = pp.Regex(r"\.(?P<frac>\d+)(?:[eE](?P<exp>[+-]?\d+))?")
frac10.set_parse_action(lambda t: ast.Numeral(0, int(t["frac"][::-1] or 0), int(t["exp"] or 0)))

base16 = pp.Regex(r"0[xX](?P<whole>[0-9a-fA-F]+)(?:\.(?P<frac>[0-9a-fA-F]*))?(?:[pP](?P<exp>[+-]?\d+))?")
base16.set_parse_action(lambda t: ast.Numeral(int(t["whole"], 16) if t["whole"]
                        else 0, int(t["frac"][::-1], 16) if t["frac"] else 0, int(t["exp"] or 0), hex=True))

frac16 = pp.Regex(r"0[xX]\.(?P<frac>[0-9a-fA-F]*)(?:[pP](?P<exp>[+-]?\d+))?")
frac16.set_parse_action(lambda t: ast.Numeral(0, int(t["frac"][::-1], 16) if t["frac"] else 0, int(t["exp"] or 0), hex=True))

# warning: order is important. base16 have to come before base10 as 0x would be matched as 0
Numeral = base16 | frac16 | base10 | frac10

# The actual grammar
stat = pp.Forward()
retstat = pp.Forward()
varlist = pp.Forward()
explist = pp.Forward()
functioncall = pp.Forward()
label = pp.Forward()
exp = pp.Forward()
namelist = pp.Forward()
funcname = pp.Forward()
funcbody = pp.Forward()
var = pp.Forward()
functiondef = pp.Forward()
prefixexp = pp.Forward()
tableconstructor = pp.Forward()
args = pp.Forward()
parlist = pp.Forward()
fieldlist = pp.Forward()
fieldsep = pp.Forward()
field = pp.Forward()

# block ::= {stat} [retstat]
block = pp.Group(stat[0, ...], aslist=True) + retstat[0, 1]
block.set_parse_action(lambda t: ast.Block(t[0]))
chunk = block

# stat ::=  ‘;’ |
#        varlist ‘=’ explist |
#        functioncall |
#        label |
#        break |
#        goto Name |
#        do block end |
#        while exp do block end |
#        repeat block until exp |
#        if exp then block {elseif exp then block} [else block] end |
#        for Name ‘=’ exp ‘,’ exp [‘,’ exp] do block end |
#        for namelist in explist do block end |
#        function funcname funcbody |
#        local function Name funcbody |
#        local namelist [‘=’ explist]
assign = varlist + EQ + explist
assign.set_parse_action(lambda toks: ast.Assign(toks[0], toks[1]))
break_ = BREAK.set_parse_action(lambda toks: ast.Break())
goto = (GOTO + Name).set_parse_action(lambda toks: ast.Goto(toks[0]))
doblock = DO + block + END
doblock.set_parse_action(lambda t: ast.Do(t[0]))
permblockstart = pp.Combine(pp.Literal('--{') + pp.Optional('!'))
permblockstart.set_parse_action(lambda t:
                                len(t[0]) < 4)
permblock = permblockstart + pp.Group(stat[0, ...], aslist=True) + pp.Literal('--}').suppress()
permblock.set_parse_action(lambda t: ast.Perm(t[1], allow_reorder=t[0]))
while_ = WHILE + exp + DO + block + END
while_.set_parse_action(lambda toks: ast.While(toks[0], toks[1]))
repeat = REPEAT + block + UNTIL + exp
repeat.set_parse_action(lambda toks: ast.Repeat(condition=toks[1], block=toks[0]))
for_range = FOR + Name + EQ + exp + COMMA + exp + (COMMA + exp)[0, 1] + DO + block + END
for_range.set_parse_action(lambda t: ast.ForRange(ast.Name(t[0]), t[1], t[2], None, t[3]) if len(
    t) < 5 else ast.ForRange(ast.Name(t[0]), t[1], t[2], t[3], t[4]))
if_ = IF + exp + THEN + block + \
    pp.Group(pp.ZeroOrMore(pp.Group(ELSEIF + exp + THEN + block))) + \
    pp.Optional(ELSE + block, default=None) + END
# The AST does not know anything about elseif; split them into else if
if_.set_parse_action(lambda toks: functools.reduce(lambda x, y: ast.If(x.test, body=x.body, orelse=[ast.If(
    test=y[0], body=y[1], orelse=x.orelse)]), reversed(toks[2]), ast.If(test=toks[0], body=toks[1], orelse=toks[3])))
for_in = FOR + namelist + IN + \
    explist + DO + block + END
for_in.set_parse_action(lambda toks: ast.ForIn(toks[0], toks[1], toks[2]))
local_var = LOCAL + namelist + EQ + explist
local_var.set_parse_action(lambda toks: ast.Local(toks[0], toks[1]))
func_def = FUNCTION + funcname + funcbody
func_def.set_parse_action(lambda toks: ast.Assign([toks[0]], [toks[1]]))
local_func_def = LOCAL + FUNCTION + Name + funcbody
local_func_def.set_parse_action(lambda toks: ast.Local([toks[0]], [toks[1]]))

stat <<= SEMI | \
    label | \
    break_ | \
    goto | \
    doblock | \
    permblock | \
    while_ | \
    repeat | \
    for_range | \
    if_ | \
    for_in | \
    local_var | \
    func_def | \
    assign | \
    local_func_def | \
    functioncall

# retstat ::= return [explist] [‘;’]
retstat <<= RETURN + pp.Optional(explist, default=[]) + SEMI[0, 1]
retstat.set_parse_action(lambda toks: ast.Return(exps=toks[0]))

# label ::= ‘::’ Name ‘::’
label <<= pp.Literal('::').suppress() + Name + pp.Literal('::').suppress()
label.set_parse_action(lambda toks: ast.Label(toks[0]))

# funcname ::= Name {‘.’ Name} [‘:’ Name]
funcname <<= Name + (PERIOD + Name)[0, ...] + (COLON + Name)[0, 1]
funcname.set_parse_action(lambda t: functools.reduce(lambda x, y: ast.Index(x, ast.LiteralString(y)), t[1:], ast.Name(t[0])))
# TODO: is there a special meaning for that last COLON Name

# varlist ::= var {‘,’ var}
varlist <<= pp.Group(var + (COMMA + var)[0, ...], aslist=True)

# namelist ::= Name {‘,’ Name}
_Name = Name.copy().set_parse_action(lambda t: ast.Name(t[0]))
namelist <<= pp.Group(_Name + (COMMA + _Name)[0, ...], aslist=True)

# explist ::= exp {‘,’ exp}
explist <<= pp.Group(exp + (COMMA + exp)[0, ...], aslist=True)

# exp ::=  nil | false | true | Numeral | LiteralString | ‘...’ | functiondef | prefixexp | tableconstructor | exp binop exp | unop exp


left_assoc = lambda t: functools.reduce(lambda x, y: ast.BinOp(x, y[0], y[1]), zip(t[0][1::2], t[0][2::2]), t[0][0])
right_assoc = lambda t: functools.reduce(lambda x, y: ast.BinOp(y[1], y[0], x), zip(t[0][-2::-2], t[0][-3::-2]), t[0][-1])
alt = lambda t: ast.Alt(t[0].asList())


def unaryAction(t):
    return functools.reduce(lambda x, y: ast.UnaryOp(op=y, operand=x), t[0][-2::-1], t[0][-1])


nil = pp.Keyword("nil").set_parse_action(lambda: ast.Nil)
false = pp.Keyword("false").set_parse_action(lambda: ast.Boolean(False))
true = pp.Keyword("true").set_parse_action(lambda: ast.Boolean(True))
ellipsis = pp.Literal("...").set_parse_action(lambda: ast.Ellipsis())
exp <<= pp.infixNotation(
    nil | false | true | Numeral | LiteralString | ellipsis | functiondef | prefixexp | tableconstructor,
    [
        (pp.Literal('--|').suppress(), 2, pp.opAssoc.LEFT, alt),
        (pp.oneOf('not # - ~'), 1, pp.OpAssoc.RIGHT, unaryAction),
        ('^', 2, pp.opAssoc.RIGHT, right_assoc),
        (pp.oneOf('* / // %'), 2, pp.OpAssoc.LEFT, left_assoc),
        (pp.oneOf('+ -'), 2, pp.OpAssoc.LEFT, left_assoc),
        ('..', 2, pp.OpAssoc.LEFT, left_assoc),
        (pp.oneOf('<< >>'), 2, pp.OpAssoc.LEFT, left_assoc),
        ('&', 2, pp.OpAssoc.LEFT, left_assoc),
        ('~', 2, pp.OpAssoc.LEFT, left_assoc),
        ('|', 2, pp.OpAssoc.LEFT, left_assoc),
        (pp.oneOf('< > <= >= ~= ==', left_assoc),
         2, pp.OpAssoc.LEFT, left_assoc),
        ('and', 2, pp.OpAssoc.LEFT, left_assoc),
        ('or', 2, pp.OpAssoc.LEFT, left_assoc),
    ]
)

# args: := ‘(’ [explist] ‘)’ | tableconstructor | LiteralString
args <<= LPAR + pp.Optional(explist, default=[]) + RPAR | (tableconstructor | LiteralString).set_parse_action(lambda t: [[t[0]]])


# prefixexp: := var | functioncall | ‘(’ exp ‘)’
# prefixexp has a nasty left recursive grammar. we need to implement the grammar slightly differently to avoid it
postfix = args.copy().set_parse_action(lambda t: ast.Call(None, t[0])) | \
    (COLON + Name + args).set_parse_action(lambda t: ast.MethodCall(None, t[0], t[1])) | \
    (LBRACK + exp + RBRACK).set_parse_action(lambda t: ast.Index(None, t[0])) | \
    (PERIOD + Name).set_parse_action(lambda t: ast.Index(None, ast.LiteralString(t[0])))
prefixexp <<= (
    Name.copy().set_parse_action(lambda toks: ast.Name(id=toks[0])) |
    LPAR + exp + RPAR) + pp.ZeroOrMore(postfix)
prefixexp.set_parse_action(lambda t: functools.reduce(
    lambda x, y: ast.Call(x, y.args) if type(y) is ast.Call else
    ast.MethodCall(x, y.method, y.args) if type(y) is ast.MethodCall else
    ast.Index(x, y.item) if type(y) is ast.Index else
    None, t[1:], t[0])
)

# var ::=  Name | prefixexp ‘[’ exp ‘]’ | prefixexp ‘.’ Name
# var <<= Name.copy().set_parse_action(lambda t: ast.Name(t[0])) | \
#   (prefixexp + LBRACK + exp + RBRACK).set_parse_action(lambda t: ast.Index(t[0], t[1])) | \
#    (prefixexp + PERIOD + Name).set_parse_action(lambda t: ast.Index(t[0], ast.LiteralString(t[1])))


def checkVar(t):
    if not isinstance(t[0], (ast.Index, ast.Name)):
        raise pp.ParseException(f"Expected ast.Index or ast.Name call, got {type(t[0])}")


var <<= prefixexp.copy().add_parse_action(checkVar)

# functioncall: := prefixexp args | prefixexp ‘:’ Name args


def checkFunctionCall(t):
    if not isinstance(t[0], (ast.Call, ast.MethodCall)):
        raise pp.ParseException(f"Expected call or method call, got {type(t[0])}")


functioncall <<= prefixexp.copy().add_parse_action(checkFunctionCall)

# functiondef: := function funcbody
functiondef <<= FUNCTION + funcbody

# funcbody: := ‘(’ [parlist] ‘)’ block end
funcbody <<= LPAR + pp.Optional(parlist, default=[]) + RPAR + block + END
funcbody.set_parse_action(lambda toks: ast.Func(args=toks[0], body=toks[1]))

# parlist: := namelist[‘,’ ‘...’] | ‘...’
parlist <<= namelist + (COMMA + ellipsis)[0, 1] | ellipsis

# tableconstructor: := ‘{’ [fieldlist] ‘}’
tableconstructor <<= pp.Group(LBRACE + fieldlist[0, 1] + RBRACE, aslist=True)
tableconstructor.set_parse_action(lambda t: ast.Table(fields=t[0]))

# fieldlist: := field {fieldsep field}[fieldsep]
fieldlist <<= field + (fieldsep + field)[0, ...] + fieldsep[0, 1]

# field: := ‘[’ exp ‘]’ ‘=’ exp | Name ‘=’ exp | exp
field <<= (LBRACK + exp + RBRACK + EQ + exp).set_parse_action(lambda t: ast.Field(key=t[0], value=t[1])) | \
    (Name + EQ + exp).set_parse_action(lambda t: ast.Field(key=ast.LiteralString(t[0]), value=t[1])) | \
    (exp.copy()).set_parse_action(lambda t: ast.Field(value=t[0]))

# fieldsep ::= ‘,’ | ‘;’
fieldsep <<= COMMA | SEMI

# ignore comments, WARNING: has to be last, as it updates all the rules recursively
block.ignore(('--' + ~pp.FollowedBy(VLINE | LBRACE | RBRACE)) + pp.restOfLine)


def parse_string(x):
    return chunk.parse_string(x, parseAll=True)[0]
