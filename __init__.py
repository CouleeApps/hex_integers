from collections.abc import Iterable, Mapping
import sys

original_displayhook = sys.__displayhook__

def convert_to_hexint(value):
	if isinstance(value, (int,)):
		return f"{value} / 0x{value:x}"
	elif isinstance(value, (float,)) and (value % 1) < 0.0001:
		return f"~{value} / ~0x{value:x}"
	elif isinstance(value, (str,)):
		return repr(value)
	elif isinstance(value, (tuple,)):
		return '(' + ', '.join(convert_to_hexint(v) for v in value) + ')'
	elif isinstance(value, (list,)):
		return '[' + ', '.join(convert_to_hexint(v) for v in value) + ']'
	elif isinstance(value, (dict,)):
		return '{' + ', '.join(convert_to_hexint(k) + ': ' + convert_to_hexint(v) for k,v in value.items()) + '}'
	elif isinstance(value, (set,)):
		return '{' + ', '.join(convert_to_hexint(v) for v in value) + '}'
	#elif isinstance(value, (Iterable,)):
	#	return '(' + ', '.join(convert_to_hexint(v) for v in value) + ')'
	#elif isinstance(value, (Mapping,)):
	#	return '{' + ', '.join(convert_to_hexint(k) + ': ' + convert_to_hexint(value[k]) for k in value) + '}'
	else:
		return repr(value)


def new_displayhook(value):
	print(convert_to_hexint(value))


setattr(sys, 'displayhook', new_displayhook)
