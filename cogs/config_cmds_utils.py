import ast
import types
from typing import Any, Union


def convert_value(value: str, type_hint: Any) -> Any:
    # Handle Optional[T] -> T | None
    origin = getattr(type_hint, '__origin__', None)
    args = getattr(type_hint, '__args__', ())
    
    # Handle Union/Optional
    if origin is Union or isinstance(type_hint, types.UnionType):
        # If NoneType is in args, it's optional. find the other type.
        non_none_types = [t for t in args if t is not type(None)]
        if len(non_none_types) == 1:
            type_hint = non_none_types[0]
    
    # Handle simple types
    if type_hint is int:
        return int(value)
    elif type_hint is bool:
        return value.lower() in ('true', '1', 'yes', 'on')
    elif type_hint is str:
        return value
    elif type_hint is float:
        return float(value)
    elif type_hint is list[int]:
        return [int(a.strip()) for a in value.split(",")]
    elif type_hint is list[str]:
        return [a.strip() for a in value.split(",")]
    elif type_hint is list[float]:
        return [float(a.strip()) for a in value.split(",")]
    elif type_hint is dict:
        dict_compliant = value.startswith('{') and value.endswith('}')
        if not dict_compliant:
            value = f'{{{value}}}'
        return ast.literal_eval(value)
    
    raise ValueError(f"Unsupported type: {type_hint}")