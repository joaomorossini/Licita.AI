from typing import Any, Type
from langchain_core.tools import BaseTool, ToolException
from langchain_core.pydantic_v1 import BaseModel, Field
from crewai.tools import tool


# class CalculatorSchema(BaseModel):
#     expression: str = Field(
#         description="Mathematical expression to evaluate. Example: '2 + 2 * 3'",
#         example="2 + 2 * 3"
#     )


# class Calculator(BaseTool):
#     name: str = "calculator"
#     description = "This tool evaluates mathematical expressions."
#     args_schema: Type[BaseModel] = CalculatorSchema

#     def _run(self, expression: str) -> Any:
#         try:
#             # Evaluate the mathematical expression
#             result = eval(expression)
#             return f"The result of the expression '{expression}' is: {result}"
#         except Exception as e:
#             print(f"Failed to evaluate expression: {str(e)}")
#             raise ToolException(
#                 f"Unable to execute tool action. \nError description: {str(e)}")


@tool("Calculator")
def calculator_tool(expression: str) -> str:
    """
    A tool to evaluate mathematical expressions.

    Args:
        expression (str): The mathematical expression to evaluate.

    Returns:
        str: The result of the evaluated expression.
    """
    try:
        result = eval(expression)
        return f"The result of the expression '{expression}' is: {result}"
    except Exception as e:
        raise ValueError(f"Failed to evaluate expression: {str(e)}")
