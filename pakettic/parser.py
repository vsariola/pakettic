from xml.dom.expatbuilder import DOCUMENT_NODE
from pakettic import ast
import pyparsing as pp
import functools

pp.ParserElement.enablePackrat()

LBRACK, RBRACK, LBRACE, RBRACE, LPAR, RPAR, EQ, COMMA, SEMI, COLON, PERIOD, VLINE = map(
    pp.Suppress, '[]{}()=,;:.|'
)
keywords = """\
    return break do end while if then elseif else for in function local repeat until nil false true and or not goto
    """.split()
keyword_pats = {
    k.upper(): pp.Regex(k + r"(?![a-zA-Z_])").suppress()
    for k in keywords
}
vars().update(keyword_pats)
any_keyword = pp.MatchFirst(keyword_pats.values()).setName("<keyword>")

# Name
Name = ~any_keyword + pp.Word(pp.alphas + "_", pp.alphanums + "_")

# LiteralString
short_literal_string = (pp.QuotedString(
    '"', escChar='\\') | pp.QuotedString('\'', escChar='\\')).setParseAction(lambda toks: ast.LiteralString(toks[0]))
long_literal_string = pp.Regex(r"\[(=*)\[(?P<str>[\s\S]*?)\]\1\]")
long_literal_string.setParseAction(lambda t: ast.LiteralString(
    t["str"][1:] if t["str"].startswith("\n") else t["str"]))
LiteralString = short_literal_string | long_literal_string

# Numeral
base10 = pp.Regex(r"(?P<whole>\d+)(?:\.(?P<frac>\d*))?(?:[eE](?P<exp>[+-]?\d+))?")
base10.set_parse_action(lambda t: ast.Numeral(int(t["whole"] or 0), int(
    t["frac"][::-1]) if t["frac"] else 0, int(t["exp"] or 0)))

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
block = pp.Group(stat[0, ...] + retstat[0, 1], aslist=True)
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
goto = (GOTO - Name).set_parse_action(lambda toks: ast.Goto(toks[0]))
doblock = DO - block - END
doblock.set_parse_action(lambda t: ast.Do(t[0]))
permblockstart = pp.Regex(r"--{[!]?")
permblockstart.set_parse_action(lambda t:
                                len(t[0]) < 4)
permblock = permblockstart + pp.Group(stat[0, ...], aslist=True) + pp.Literal('--}').suppress()
permblock.set_parse_action(lambda t: ast.Perm(t[1], allow_reorder=t[0]))
while_ = WHILE - exp - DO - block - END
while_.set_parse_action(lambda toks: ast.While(toks[0], toks[1]))
repeat = REPEAT - block - UNTIL - exp
repeat.set_parse_action(lambda toks: ast.Repeat(condition=toks[1], block=toks[0]))
for_range = FOR + Name + EQ - exp - COMMA - exp - (COMMA - exp)[0, 1] - DO - block - END
for_range.set_parse_action(lambda t: ast.ForRange(ast.Name(t[0]), t[1], t[2], None, t[3]) if len(
    t) < 5 else ast.ForRange(ast.Name(t[0]), t[1], t[2], t[3], t[4]))
if_ = IF - exp + THEN + block + \
    pp.Group(pp.ZeroOrMore(pp.Group(ELSEIF - exp + THEN + block))) + \
    pp.Optional(ELSE - block, default=None) + END
# The AST does not know anything about elseif; split them into else if
if_.set_parse_action(lambda toks: functools.reduce(lambda x, y: ast.If(x.test, body=x.body, orelse=ast.Block([ast.If(
    test=y[0], body=y[1], orelse=x.orelse)])), reversed(toks[2]), ast.If(test=toks[0], body=toks[1], orelse=toks[3])))
for_in = FOR + pp.Group(namelist, aslist=True) + IN - \
    explist - DO - block - END
for_in.set_parse_action(lambda toks: ast.ForIn(toks[0], toks[1], toks[2]))
local_var = LOCAL + pp.Group(namelist, aslist=True) - (EQ + explist)[0, 1]
local_var.set_parse_action(lambda toks: ast.Local(toks[0], None) if len(toks) < 2 else ast.Local(toks[0], toks[1]))
func_vanilla_def = FUNCTION + funcname + funcbody
func_vanilla_def.set_parse_action(lambda toks: ast.Assign([toks[0]], [toks[1]]))
# function t.a.b.c:f (params) body end is syntactic sugar for t.a.b.c.f = function (self, params) body end
func_member_def = FUNCTION + funcname + COLON - Name - funcbody
func_member_def.set_parse_action(lambda t: ast.Assign(
    [ast.Index(t[0], ast.LiteralString(t[1]))],
    [ast.Func(args=[ast.Name('self')] + t[2].args, body=t[2].body)]
))
func_def = func_vanilla_def | func_member_def
local_func_def = LOCAL + FUNCTION - Name - funcbody
local_func_def.set_parse_action(lambda toks: ast.Local([ast.Name(toks[0])], [toks[1]]))

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
retstat <<= RETURN - pp.Optional(explist, default=[]) - SEMI[0, 1]
retstat.set_parse_action(lambda toks: ast.Return(exps=toks[0]))

# label ::= ‘::’ Name ‘::’
label <<= pp.Literal('::').suppress() - Name - pp.Literal('::').suppress()
label.set_parse_action(lambda toks: ast.Label(toks[0]))

# funcname ::= Name {‘.’ Name} [‘:’ Name]
funcname <<= Name - (PERIOD - Name)[0, ...]
funcname.set_parse_action(lambda t: functools.reduce(lambda x, y: ast.Index(x, ast.LiteralString(y)), t[1:], ast.Name(t[0])))
# the [‘:’ Name] case is handled separately

# varlist ::= var {‘,’ var}
varlist <<= pp.Group(var - (COMMA - var)[0, ...], aslist=True)

# namelist ::= Name {‘,’ Name}
_Name = Name.copy().set_parse_action(lambda t: ast.Name(t[0]))
namelist <<= _Name - (COMMA + _Name)[0, ...]

# explist ::= exp {‘,’ exp}
explist <<= pp.Group(exp - (COMMA - exp)[0, ...], aslist=True)

# exp ::=  nil | false | true | Numeral | LiteralString | ‘...’ | functiondef | prefixexp | tableconstructor | exp binop exp | unop exp


left_assoc = lambda t: functools.reduce(lambda x, y: ast.BinOp(x, y[0], y[1]), zip(t[0][1::2], t[0][2::2]), t[0][0])
right_assoc = lambda t: functools.reduce(lambda x, y: ast.BinOp(y[1], y[0], x), zip(t[0][-2::-2], t[0][-3::-2]), t[0][-1])
alt = lambda t: ast.Alt(t.asList()) if len(t) > 1 else t[0]


def unaryAction(t):
    return functools.reduce(lambda x, y: ast.UnaryOp(op=y, operand=x), t[-2::-1], t[-1])


nil = pp.Keyword("nil").set_parse_action(lambda: ast.Nil())
false = pp.Keyword("false").set_parse_action(lambda: ast.Boolean(False))
true = pp.Keyword("true").set_parse_action(lambda: ast.Boolean(True))
ellipsis = pp.Literal("...").set_parse_action(lambda: ast.Ellipsis())
# The power operator is weird: it binds more strongly than unary to the
# thing on its left, but less strongly than unary to its right. So, we
# need to treat it separately
expliteral = nil | false | true | Numeral | LiteralString | ellipsis | functiondef | prefixexp | tableconstructor | LPAR + exp + RPAR
altexp = expliteral + (pp.Literal('--|').suppress() - expliteral)[0, ...]
altexp.set_parse_action(alt)
powerexp = pp.Forward()
unaryexp = pp.Regex(r"not(?![a-zA-Z_])|#|-(?!-)|~")[0, ...] + powerexp
unaryexp.set_parse_action(unaryAction)
powerexp <<= altexp + (pp.Literal('^').suppress() - unaryexp)[0, 1]
powerexp.set_parse_action(lambda t: ast.BinOp(left=t[0], op="^", right=t[1]) if len(t) > 1 else t[0])
exp <<= pp.infixNotation(
    unaryexp,
    [
        (pp.oneOf('* / // %'), 2, pp.OpAssoc.LEFT, left_assoc),
        (pp.Regex(r"[+]|-(?!-)"), 2, pp.OpAssoc.LEFT, left_assoc),
        ('..', 2, pp.OpAssoc.LEFT, left_assoc),
        (pp.oneOf('<< >>'), 2, pp.OpAssoc.LEFT, left_assoc),
        ('&', 2, pp.OpAssoc.LEFT, left_assoc),
        ('~', 2, pp.OpAssoc.LEFT, left_assoc),
        ('|', 2, pp.OpAssoc.LEFT, left_assoc),
        (pp.oneOf('< > <= >= ~= ==', left_assoc),
         2, pp.OpAssoc.LEFT, left_assoc),
        (pp.Regex(r"and(?![a-zA-Z_])"), 2, pp.OpAssoc.LEFT, left_assoc),  # can't use AND as it suppresses the token
        (pp.Regex(r"or(?![a-zA-Z_])"), 2, pp.OpAssoc.LEFT, left_assoc),  # can't use OR as it suppresses the token
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
parlist <<= pp.Group(namelist + (COMMA + ellipsis)[0, 1] | ellipsis, aslist=True)


# tableconstructor: := ‘{’ [fieldlist] ‘}’
tableconstructor <<= pp.Group(LBRACE - fieldlist[0, 1] - RBRACE, aslist=True)
tableconstructor.set_parse_action(lambda t: ast.Table(fields=t[0]))

# fieldlist: := field {fieldsep field}[fieldsep]
fieldlist <<= field + (fieldsep + field)[0, ...] + fieldsep[0, 1]

# field: := ‘[’ exp ‘]’ ‘=’ exp | Name ‘=’ exp | exp
field <<= (LBRACK + exp + RBRACK + EQ + exp).set_parse_action(lambda t: ast.Field(key=t[0], value=t[1])) | \
    (Name + EQ + exp).set_parse_action(lambda t: ast.Field(key=t[0], value=t[1])) | \
    (exp.copy()).set_parse_action(lambda t: ast.Field(value=t[0]))

# fieldsep ::= ‘,’ | ‘;’
fieldsep <<= COMMA | SEMI

# ignore comments, WARNING: has to be last, as it updates all the rules recursively
comment_intro = pp.Literal("--")
short_comment = pp.Regex(r"--(?![\|\{\}])") + pp.restOfLine
long_comment = pp.Regex(r"--\[(=*)\[(?P<str>[\s\S]*?)\]\1\]")
debug_comment = pp.Regex(r"--!(=*)\[[\s\S]*?--!\1\]")
lua_comment = debug_comment | long_comment | short_comment
block.ignore(lua_comment)


def parse_string(x):
    return chunk.parse_string(x, parse_all=True)[0]
