from antlr4 import ParseTreeVisitor
from phpast import *

class UnHandledParseTreeCaseException(Exception): pass
DEBUG_MODE = False

class ErrorNode():
    def __init__(self, exception_object):
        self.exception_object = exception_object


class BaseVisitor(ParseTreeVisitor):

    def visit(self, node):
        node_type = type(node).__name__

        if node_type in ("TerminalNodeImpl", ):
            return node.getText()
        return super().visit(node)

    def visitChildren(self, node):
        node_children = node.children

        children = None
        if node.children is not None:
            children = [self.visit(child) for child in node.children]
        node.children = children
        returned_node = node

        node_type = type(returned_node).__name__
        node_type_processor = "process_"+node_type
        if hasattr(self, node_type_processor):
            node_type_processor_method = getattr(self, node_type_processor)
            if callable(node_type_processor_method):
                try:
                    return node_type_processor_method(returned_node)
                except Exception as e:
                    print("Error Occurred")
                    return ErrorNode(e)
        return returned_node


class Visitor(BaseVisitor):

    def process_PhpBlockContext(self, node):
        return Block(node.children)

    """
    ============================================
                    INLINE HTML
    ============================================
    """
    def process_HtmlElementContext(self, node):
        return node.children[0]

    def process_HtmlElementsContext(self, node):
        return "".join(node.children)

    def process_InlineHtmlContext(self, node):
        return node.children[0]

    def process_InlineHtmlStatementContext(self, node):
        return InlineHTML(node.children[0])
    """
    ============================================
                BASIC EXPRESSIONS
    ============================================
    """

    def process_StringContext(self, node):
        # TODO: Other variants in the grammar
        # TODO: single quoted string contains the quotes in the string
        # Slice [1:-1] -> String broken at interpolated parts
        string_list_quotes_removed = list(filter(lambda x: x!='"', node.children))
        return "".join(string_list_quotes_removed)

    def process_InterpolatedStringPartContext(self, node):
        # One bit of the String broken at interpolated parts
        return node.children[0]

    def process_ScalarExpressionContext(self, node):
        # Constants, Strings, etc.
        return node.children[0]

    def process_NumericConstantContext(self, node):
        # Numbers
        # TODO: Check for Octals, Hex and Binary
        return int(node.children[0])

    def process_LiteralConstantContext(self, node):
        # Numbers, Reals, Boolean and 
        # String constants (without quotation marks, e.g. false)
        # TODO: Reals with exponents
        # TODO: Alternative for Handling Booleans

        value = node.children[0]
        if isinstance(value, str): # Booleans and String Constatns
            if value in ("false", "False"): # False Boolean
                return False
            elif value in ("True", "true"): # True Boolean
                return True
            try:
                return float(value) # Float number
            except ValueError:
                return Constant(value) # Just a String Constant

        elif isinstance(value, int):
            return value
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            return node


    def process_ConstantContext(self, node):
        # Nulls, Literal Constants, Class Constants, Magic Constants, Namespace Names
        return node.children[0]

    def process_StringConstantContext(self, node):
        return node.children[0]

    def process_ParenthesesContext(self, node):
        return node.children[1]

    """
    ================================================
                Generic Statement Nodes
    ================================================
    """

    def process_TopStatementContext(self, node):
        # Wrapper for different kind of Statement Nodes
        return node.children[0]


    def process_StatementContext(self, node):
        # All statements other than namespace Declarations, 
        # function declarations, class declarations and 
        # global constant declarations
        return node.children[0]

    def process_EmptyStatementContext(self, node):
        # Semicolon statments
        # #TODO: Ignore it from the block
        return node.children[0]

    def process_ExpressionStatementContext(self, node):
        # Top Level Expression Node for more than 40 
        # different Expression types
        return node.children[0]


    # Block Related Nodes, Used in functions
    def process_BlockStatementContext(self, node):
        return Block(node.children[1])

    def process_InnerStatementListContext(self, node):
        return node.children

    def process_InnerStatementContext(self, node):
        return node.children[0]

    def process_StatementContext(self, node):
        return node.children[0]

    """
    ================================================
                Chain Expression Nodes
    ================================================
    """

    def process_ChainExpressionContext(self, node):
        # Wrapper for chainContext
        return node.children[0]


    def process_ChainContext(self, node):
        # Simple Variables or variables with accessors
        if len(node.children) == 1:
           return node.children[0]
        else:
            return self._process_ChainList(node.children)


    def _process_ChainList(self, children):
        # Recursive Helper function for resolving ChainContexts
        if len(children) == 1:
            return children[0]
        else:
            last_node = children.pop()
            if isinstance(last_node, MethodCall):
                return MethodCall(self._process_ChainList(children), last_node.name, last_node.params)
            elif isinstance(last_node, ObjectProperty):
                return ObjectProperty(self._process_ChainList(children), last_node.name)


    def process_ChainBaseContext(self, node):
        # TODO: Case with QualifiedStaticTypeRef::KeyedVar
        # TODO: Case with KeyedVar::KeyedVar
        if len(node.children) == 1:
            return node.children[0]
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            return node


    def process_MemberAccessContext(self, node):
        # Member access with index 0 as the arrow

        if len(node.children) == 3: 
            # The third child is the ArgumentList
            return MethodCall(None, node.children[1], node.children[2])
        elif len(node.children) == 2:
            # Just the arrow and a property
            return ObjectProperty(None, node.children[1])
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            return node


    def process_ChainOriginContext(self, node):
        # The starting part of a Chain
        # TODO: Handle the case when chainOrigin is functioncall or newExpr
        # Only the case of a simple chainBase is handled
        if len(node.children) >  1:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            return node
        return node.children[0]


    def process_ExpressionListContext(self, node):
        # List of expression nodes, separated by ","
        return [node.children[i] for i in range(len(node.children)) if not i%2]


    """
    ================================================
              Variable Name Related Nodes
    ================================================
    """

    def process_SquareCurlyExpressionContext(self, node):
        # Replace SquareCurly Blocks with simplified placeholder
        # nodes to help in processing the parent node

        if node.children[0] == "{":
            node_type = "curly"
        elif node.children[0] == "[":
            node_type = "square"
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            return node
        return SquareCurly(node_type, node.children[1])

    def process_IdentifierContext(self, node):
        # Wrapper around user-defined names
        return node.children[0]

    def process_KeyedVariableContext(self, node):
        # Variables may contain other variables and/or
        # indexes using curly or square brackets

        if isinstance(node.children[-1], SquareCurly):
            index_node = node.children.pop()
            if index_node.type == "square":
                return ArrayOffset(self.process_KeyedVariableContext(node), index_node.expr)
            else: #curly
                return StringOffset(self.process_KeyedVariableContext(node), index_node.expr)
        else:
            name = self._find_variable_name(node.children)
            return Variable(name)

    def _find_variable_name(self, var_children):
        # Recursive Helper function to get the name 
        # of the variable from the children of the node
        if var_children[0] == "$":
            sub_name = self._find_variable_name(var_children[1:])
            name = Variable(sub_name)
        elif var_children[0].startswith("$"):
            name = var_children[0]
        elif var_children[0] == "{":
            name = var_children[1]
        return name

    def process_TypeRefContext(self, node):
        # Wrapper around Type (Class) Names used when instantiating 
        # and object
        return node.children[0]


    """
    ==================================================
                Field Name Nodes
    ==================================================
    """

    # TODO: MORE COMPLEX VARIATIONS FROM GRAMMAR
    #
    def process_KeyedSimpleFieldNameContext(self, node):
        return node.children[0]

    def process_KeyedFieldNameContext(self, node):
        return node.children[0]



    """
    ==================================================
                Other Simple Expressions
    ==================================================
    """

    def process_ArithmeticExpressionContext(self, node):
        # Arithmetic Expressions: expression op expression
        if len(node.children) == 3:
            return BinaryOp(node.children[1], node.children[0], node.children[2])
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            return node

    def process_ParenthesisExpressionContext(self, node):
        return node.children[0]

    def process_ComparisonExpressionContext(self, node):
        # Comparison Operators: expression op expression
        return BinaryOp(node.children[1], node.children[0], node.children[2])

    def process_LogicalExpressionContext(self, node):
        # Logical Expressions Like and, or, etc
        return BinaryOp(node.children[1], node.children[0], node.children[2])

    def process_BitwiseExpressionContext(self, node):
        # Bitwise Expressions: ^, &, ||, |, &

        return BinaryOp(node.children[1], node.children[0], node.children[2])


    def process_UnaryOperatorExpressionContext(self, node):
        # Unary Operators: @, ~, ~, -, +
        return UnaryOp(node.children[0], node.children[1])

    def process_PostfixIncDecExpressionContext(self, node):
        # Postfix Unary Operators: ++ and --
        return PostIncDecOp(node.children[1], node.children[0])

    def process_PrefixIncDecExpressionContext(self, node):
        # Prefix Unary Operators: ++ and --
        return PreIncDecOp(node.children[0], node.children[1])

    def process_NewExpressionContext(self, node):
        # Wrapper for NewExprContext
        return node.children[0]

    def process_NewExprContext(self, node):
        # New Expression: new ClassName(parameter*)
        if len(node.children) == 3:
            arguments = [node.children[2][i] for i in range(len(node.children[2])) if not i%2]
        else:
            arguments = []
        return New(node.children[1], arguments)

    def process_CloneExpressionContext(self, node):
        if len(node.children) == 2:
            return Clone(node.children[1])
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            else: return node

    def process_CastOperationContext(self, node):
        return node.children[0]

    def process_CastExpressionContext(self, node):
        # Casting Operation: (castType) expression
        return Cast(node.children[1], node.children[3])

    # Assignment Lists
    def process_AssignmentListContext(self, node):
        # List of elements used for list assignment in SpecialWordExpression
        # Odd indexes occupy commas
        return [node.children[i] for i in range(len(node.children)) if not i%2]

    def process_AssignmentListElementContext(self, node):
        # Wrapper around a single element of the list
        return node.children[0]


    """
    ==================================================
                Assignment Related Nodes
    ==================================================
    """

    def process_AssignableContext(self, node):
        # Wrapper
        return node.children[0]

    def process_AssignmentOperatorContext(self, node):
        # Wrapper 
        return node.children[0]

    def process_AssignmentExpressionContext(self, node):
        # Assignment expressions for simple and augmented
        # assignments
        if node.children[1] == "=": # Simple
            return Assignment(node.children[0], node.children[2], False)
        else: #Augmented
            return AssignOp(node.children[1], node.children[0], node.children[2])


    """
    ==================================================
                Other Statements
    ==================================================
    """

    def process_EchoStatementContext(self, node):
        return Echo(node.children[1])

    def process_ReturnStatementContext(self, node):
        return Return(node.children[1])

    """
    ==================================================
                  Function Related Nodes
    ==================================================
    """
    # Calls Related

    def process_ActualArgumentContext(self, node):
        # Wrapper around the passed argument
        return node.children[0]

    def process_ArgumentsContext(self, node):
        # Arguments List node.
        # index 0 and -1 occupy Parentheses
        arguments = node.children[1:-1]
        return arguments

    def process_ActualArgumentsContext(self, node):
        # Arguments List node.
        # Odd indexes occupy commas
        args = node.children[0]
        return [args[i] for i in range(len(args)) if not i%2]

    def process_FunctionCallNameContext(self, node):
        # Wrapper
        return node.children[0]

    def process_FunctionCallContext(self, node):
        # Actual Call
        # 0 -> Function Name, 1-> Arguments passed
        returned_node= FunctionCall(node.children[0], node.children[1])
        if isinstance(returned_node.name, str):
            function_call_processor = "process_FunctionCall_"+returned_node.name
            if hasattr(self, function_call_processor):
                fc_processor_func = getattr(self, function_call_processor)
                if callable(fc_processor_func): return fc_processor_func(returned_node)

        elif isinstance(returned_node.name, ClassConstantAccess):
            return StaticMethodCall(returned_node.name.class_, returned_node.name.name, returned_node.params)

        elif len(node.children) == 2:
            return returned_node
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            else: return node

        return returned_node

    # Declaration Related

    def process_FunctionDeclarationContext(self, node):
        # TODO : Is ref currently set to False
        return Function(node.children[2], node.children[4], node.children[6], False)

    def process_FormalParameterListContext(self, node):
        # Parameter List
        # Odd indexes occupy commas
        if node is None:
            return []
        else:
            return not node.children or [node.children[i] for i in range(len(node.children)) if not i%2]

    def process_FormalParameterContext(self, node):
        # Single Parameter
        # TODO: Handle Type and is_ref
        param = FormalParameter(node.children[1][0], None, False, None)
        if len(node.children[1]) == 3:
            param.default = node.children[1][2]
        return param

    def process_VariableInitializerContext(self, node):
        # Variable node for each parameter
        return node.children

    def process_ConstantInititalizerContext(self, node):
        # Default Constant value of a parameter. 
        # TODO: Fix the name of this one in the grammar. We have two of these for now
        return node.children[0]

    def process_ConstantInitializerContext(self, node):
        return node.children[0]

    """
    ==================================================
              Anonymous Function Related Nodes
    ==================================================
    """

    def process_LambdaFunctionExpressionContext(self, node):
        # Wrapper around the LambdaFunctionExprContext
        return node.children[0]

    def process_LambdaFunctionExprContext(self, node):
        # The Lambda Function definition node
        # May or may not have a static which can change indexes
        # May or may not have a LambdaUse node
        # TODO: is_ref
        returned_node = Closure([], [], [], False, False)
        returned_node.static = node.children[0] == "static"
        par_open_index = node.children.index("(")
        returned_node.params = node.children[par_open_index+1]
        returned_node.nodes = node.children[-1]
        if isinstance(node.children[-2], LambdaUse):
            returned_node.vars = node.children[-2].nodes
        return returned_node

    def process_LambdaFunctionUseVarsContext(self, node):
        # Use node for Lambda Function Definitions
        # Contains string of variable names resolved
        # from LambdaFunctionUseVarContext nodes
        # 0=> 'use'     1=> "("
        par_open_index = node.children.index("(")
        par_close_index = node.children.index(")")
        vars_with_commas = node.children[par_open_index+1:par_close_index]
        vars_without_commas = [vars_with_commas[i] for i in range(len(vars_with_commas)) if not i%2]
        return LambdaUse(vars_without_commas)

    def process_LambdaFunctionUseVarContext(self, node):
        if len(node.children) == 1:
            return LexicalVariable(node.children[0], False)
        elif len(node.children) == 2 and node.children[0] =="&":
            return LexicalVariable(node.children[1], True)
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            else: return node

    """
    ==================================================
                  Conditionals Related
    ==================================================
    """

    def process_IfStatementContext(self, node):
        created_node = If(node.children[1], node.children[2], [], None)
        if len(node.children) > 2:
            created_node.else_ = node.children[-1]

        if len(node.children) > 3:
            created_node.elseifs.extend(node.children[3:-1])

        return created_node

    def process_ElseIfStatementContext(self, node):
        return ElseIf(node.children[1], node.children[2])

    def process_ElseStatementContext(self, node):
        return Else(node.children[1])

    def process_ConditionalExpressionContext(self, node):
        if len(node.children) == 5:
            return TernaryOp(node.children[0], node.children[2], node.children[4])
        elif len(node.children) == 4:
            return TernaryOp(node.children[0], None, node.children[3] )
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            else: return node

    """
    ==================================================
                  Loops Related
    ==================================================
    """

    def process_WhileStatementContext(self, node):
        return While(node.children[1], node.children[2])

    def process_ForInitContext(self, node):
        return node.children[0][0]

    def process_ForUpdateContext(self, node):
        return node.children[0][0]


    def process_ForStatementContext(self, node):
        return For(node.children[2], node.children[4][0], node.children[6], node.children[8])


    def process_DoWhile(self, node):
        return DoWhile(node.children[1], node.children[3])

    def process_DoWhileStatementContext(self, node):
        return DoWhile(node.children[1], node.children[3])

    def process_ContinueStatementContext(self, node):
        return Continue(None)

    def process_ForeachStatementContext(self, node):
        # TODO: is_ref not handled
        # TODO: Only typical case is handled for now
        if len(node.children) == 7:
            key_var = ForeachVariable(node.children[4], False)
            return Foreach(node.children[2], key_var, None, node.children[6])
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            else: return node

    """
    ==================================================
              Exception Handling Related
    ==================================================
    """

    def process_TryCatchFinallyContext(self, node):
        # Exception handling code with one try block, one or more
        # catch blocks and one or none finally block

        returned_node = Try(node.children[1], [], None)
        if isinstance(node.children[-1], Finally):
            finally_block = node.children.pop()
            returned_node.finally_ = finally_block
        returned_node.catches = node.children[2:]
        return returned_node

    def process_CatchClauseContext(self, node):
        return Catch(node.children[2], node.children[3], node.children[5])

    def process_FinallyStatementContext(self, node):
        return Finally(node.children[1])

    def process_ThrowStatementContext(self, node):
        return Throw(node.children[1])



    """
    ==================================================
              Class Declaration Node
    ==================================================
    """

    def process_ClassDeclarationContext(self, node):
        # Node for classes and interfaces
        # Class Declaration. Type can be "abstract" or None
        # Can extends one or no classes
        # Can implement zero or more interfaces
        # TODO: private and partial?
        # TODO: Improve the approach used

        if isinstance(node.children[1], list):
            class_type = node.children[1][0]
            class_name = node.children[3]
        else:
            class_type = None
            class_name = node.children[2]

        if len(node.children[0]) >0:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            return node

        if "class" in node.children:
            returned_node = Class(class_name, class_type, None, [], [], [])
        elif "interface" in node.children:
            returned_node = Interface(class_name, None, [])

        elif "trait" in node.children:
            # TODO: traits property not handled
            returned_node = Trait(class_name, [], [])

        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            else: return node

        br_open_index = node.children.index("{") # Body Starts here
        returned_node.nodes = node.children[br_open_index+1:-1]

        extends_index = None
        implements_index = None
        if "extends" in node.children:
            extends_index = node.children.index("extends")
            returned_node.extends = node.children[extends_index+1]

        if "implements" in node.children:
            implements_index = node.children.index("implements")
            returned_node.implements = node.children[implements_index+1]
        return returned_node

    def process_ClassEntryTypeContext(self, node):
        # Wrapper around the class keyword
        return node.children[0]


    def process_ModifierContext(self, node):
        # Modifier List. For the class it can be ["abstract"] or 
        # not present at all
        return node.children if node.children else []

    def process_AttributesContext(self, node):
        # Wrapper around list of attrbutes. None if no attributes
        return node.children if node.children else []

    def process_InterfaceListContext(self, node):
        # List of implemented interfaces
        # Odd indexes occupy commas
        return [node.children[i] for i in range(len(node.children)) if not i%2]


    def process_QualifiedStaticTypeRefContext(self, node):
        # Class Name for extends
        # TODO: Look into other cases
        return node.children[0]


    """
    ==================================================
                Namespace Related Nodes
    ==================================================
    """

    def process_QualifiedNamespaceNameContext(self, node):
        # Node for Namespaced names and plain namespace declarations
        # e.g. 'namespace ABC\DEF' or 'NS1\NS2\SampleException'
        #
        if len(node.children) == 1:  # Just a name
            return node.children[0]
        elif len(node.children) == 2 and node.children[0] == "\\":
            # Chain with a leading backslash
            return node.children[1]
        elif len(node.children) == 2 and node.children[0] == "namespace":
            # Namespace Declaration (at the top of file)
            return Namespace(node.children[1], [])
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            else: return node

    def process_NamespaceDeclarationContext(self, node):
        # Namespace Declaration with body inside braces
        # May or may not have a name which may affect index
        if node.children[1] == "{": # No name
            return Namespace(None, node.children[2:-1])
        elif node.children[2] == "{":
            return Namespace(node.children[1], node.children[3:-1])
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            else: return node

    def process_NamespaceNameListContext(self, node):
        # List of the namespace heirarchy
        # Odd indexes occupy "\\" 
        # In case of "\\" at 0, we remove it
        if len(node.children) == 1:
            return node.children[0]
        children_without_slashes = [node.children[i] for i in range(len(node.children)) if not i%2]
        return NamespaceChain(children_without_slashes)

    def process_NamespaceStatementContext(self, node):
        return node.children[0]

    def process_NamespaceNameTailContext(self, node):
        # Used in use declarations. Can be aliased
        # Can have multiple names in a single node
        if node.children[0] == "{":
            namespace_names_list = node.children[1:-1]
            name_list_without_commas = [i for i in namespace_names_list if isinstance(i, NamespaceNameTail)]
            returned_node = NamespaceNameTailList(name_list_without_commas)
        else:
            returned_node = NamespaceNameTail(node.children[0], None)
            if len(node.children) == 3:
                returned_node.alias = node.children[2]

        return returned_node

    """
    ==================================================
                  Class Members Nodes
    ==================================================
    """

    def process_ClassStatementContext(self, node):
        # Statement Inside a class (Method/Attribute)
        # TODO: Look into other members (use declarations) that can
        # be directly inside a class
        # TODO: is_ref

        # Use Declaration
        if node.children[0] == "use":
            return node

        # Method Declaration
        if "function" in node.children:
            if node.children[1] == "function": # No Modifiers
                return Method(node.children[2], [], node.children[4], node.children[6], False)

            elif node.children[2] == "function": # With Modifiers
                return Method(node.children[3], node.children[1], node.children[5], node.children[7], False)

            else:
                if DEBUG_MODE: raise UnHandledParseTreeCaseException()
                return node

        # Attribute Assignment
        if len(node.children[2]) == 3 and "=" in node.children[2]:
            prop_declaration_data = node.children[2]
            prop_declaration = ClassVariable(prop_declaration_data[0], prop_declaration_data[2])
            mods = node.children[1]
            return ClassVariables(mods, prop_declaration)

        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            else: return node

    def process_MethodBodyContext(self, node):
        # Wrapper around Block node of the Method
        return node.children

    def process_MemberModifierContext(self, node):
        return node.children[0]

    def process_MemberModifiersContext(self, node):
        return node.children

    def process_PropertyModifiersContext(self, node):
        return node.children[0]

    def process_ClassConstantContext(self, node):
        # Class Constants: class_name::member_name
        # TODO: Handle other variants
        if len(node.children) == 3 and node.children[1] == "::":
            return ClassConstantAccess(node.children[0], node.children[2])
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            else: return node
    """
    ==================================================
                  Array Related Nodes
    ==================================================
    """

    # Array Related Stuff
    #
    def process_ArrayItemContext(self, node):
        # Single Array Element
        # TODO : Refs
        if len(node.children) == 1:
            return ArrayElement(None, node.children[0], False)
        elif len(node.children) == 3:
            return ArrayElement(node.children[0], node.children[2], False)
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            return node

    def process_ArrayItemListContext(self, node):
        # Array Elements
        # Odd indexes occupy commas
        return [node.children[i] for i in range(len(node.children)) if not i%2]

    def process_ArrayCreationContext(self, node):
        # New Array Creation node
        if node.children[0] == "array":
            return Array(node.children[2])
        else:
            return Array(node.children[1])

    def process_ArrayCreationExpressionContext(self, node):
        # Wrapper
        return node.children[0]


    """
    ==================================================
                  Switch Related Nodes
    ==================================================
    """
    def process_BreakStatementContext(self, node):
        return Break(None)

    def process_SwitchBlockContext(self, node):
        # Case blocks present inside switch statements
        # Due to the way the grammars are designed, if we
        # have a default block, it gets embedded inside the case
        # block. Therefore we process this and return a list of the 
        # case and default node and then unpack them in the 
        # SwitchStatementContext

        case_expr = node.children[1]
        case_block = node.children[3]

        if "default" in case_block: # If there is a default embedded
            default_index = case_block.index("default")
            case_part = case_block[:default_index]
            default_part = case_block[default_index+1:]
            return [Case(case_expr, case_part), Default(default_part)]
        else:
            return [Case(case_expr, case_block)] # List to be unpacked

    def process_SwitchStatementContext(self, node):
        # Switch Statement
        # Blocks are the SwitchBlocks. Need to be unpacked

        switch_expr = node.children[1]
        brace_index = node.children.index("{")
        blocks = node.children[brace_index+1:-1]
        case_default_nodes = [item for sublist in blocks for item in sublist]
        return Switch(switch_expr, case_default_nodes)


    """
    ==================================================
                Special Word Expressions
    ==================================================
    """
    def process_SpecialWordExpressionContext(self, node):

        # Include and Include Once
        if node.children[0] in ("include", "include_once"):
            returned_node = Include(node.children[1], False, None)
            returned_node.once = node.children[0] == "include_once"

        # Require and Require Once
        elif node.children[0] in ("require", "require_once"):
            returned_node = Require(node.children[1], False, None)
            returned_node.once = node.children[0] == "require_once"

        elif node.children[0] == "list":
            returned_node = ListAssignment(node.children[2], node.children[5])
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            else: return node

        return returned_node

    def process_FunctionCall_include(self, fc):
        # Include and Include Once Function Call Forms
        return Include(fc.params[0], False, None)

    def process_FunctionCall_include_once(self, fc):
        return Include(fc.params[0], True, None)

    def process_FunctionCall_require(self, fc):
        # Require and Require Once Function Call Forms
        return Require(fc.params[0], False, None)

    def process_FunctionCall_require_once(self, fc):
        return Require(fc.params[0], True, None)

    def process_FunctionCall_eval(self, fc):
        # eval(expression)
        return Eval(fc.params[0])

    def process_FunctionCall_exit(self, fc):
        # exit(expression)
        # TODO: 'type' property of the Function Call

        if len(fc.params)>0:
            return Exit(fc.params[0], None)
        else: return Exit(None, None)

    def process_FunctionCall_isset(self, fc):
        # issset(expression)
        return IsSet(fc.params)

    def process_FunctionCall_unset(self, fc):
        # unset(expressions)
        return Unset(fc.params)

    def process_FunctionCall_empty(self, fc):
        # empty(expression)
        return Empty(fc.params[0])

    def process_GotoStatementContext(self, node):
        return GoTo(node.children[1])

    def process_YieldExpressionContext(self, node):
        # TODO: Improve on the approach used
        #
        if len(node.children) == 2:
            return Yield(node.children[1])
        elif len(node.children) == 3 and node.children[1] == "from":
            return YieldFrom(node.children[2])
        elif len(node.children) == 4 and node.children[2] == "=>":
            return Yield(node.children[2:])
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            else: return node


    """
    ==================================================
                        Globals
    ==================================================
    """
    def process_GlobalVarContext(self, node):
        if len(node.children) == 1:
            return node.children[0]
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            else: return node

    def process_GlobalStatementContext(self, node):
        declared_vars = node.children[1:]
        vars_without_commas = [declared_vars[i] for i in range(len(declared_vars)) if not i%2]
        return Global(vars_without_commas)

    def process_IdentifierInititalizerContext(self, node):
        # TODO: Fix Name
        if len(node.children) == 3:
            return ConstantDeclaration(node.children[0], node.children[2])
        else:
            if DEBUG_MODE: raise UnHandledParseTreeCaseException()
            else: return node

    def process_GlobalConstantDeclarationContext(self, node):
        const_nodes = [i for i in node.children if isinstance(i, ConstantDeclaration)]
        return ConstantDeclarations(const_nodes)


    """
    ==================================================
                   Use Declaration Nodes
    ==================================================
    """
    def process_UseDeclarationContentContext(self, node):
        # Wrapper
        ns_chain = node.children[0]
        if isinstance(ns_chain.nodes[-1], NamespaceNameTailList):
            return [NamespaceChain(ns_chain.nodes[:-1]+[i]) for i in ns_chain.nodes[-1].nodes]
        else:
            return [node.children[0]]

    def process_UseDeclarationContentListContext(self, node):
        ns_chains = [item for sublist in node.children for item in sublist if isinstance(sublist, list)]
        return ns_chains

    def process_UseDeclarationContext(self, node):
        if node.children[1] == "function":
            return UseDeclarations("function", node.children[2])
        elif node.children[1] == "const":
            return UseDeclarations("const", node.children[2])
        else:
            return UseDeclarations(None, node.children[1])

