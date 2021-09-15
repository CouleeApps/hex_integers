from collections.abc import Iterable, Mapping
import sys

original_displayhook = sys.__displayhook__

def convert_to_hexint(value, seen):
	if value in seen:
		return "<recursion>"
	seen = seen + [value]

	if isinstance(value, (int,)):
		return f"{value} / 0x{value:x}"
	elif isinstance(value, (float,)) and (value % 1) < 0.0001:
		value = int(value)
		return f"~{value} / ~0x{value:x}"
	elif isinstance(value, (str,)):
		return repr(value)
	elif isinstance(value, (tuple,)):
		return '(' + ', '.join(convert_to_hexint(v, seen) for v in value) + ')'
	elif isinstance(value, (list,)):
		return '[' + ', '.join(convert_to_hexint(v, seen) for v in value) + ']'
	elif isinstance(value, (dict,)):
		return '{' + ', '.join(convert_to_hexint(k, seen) + ': ' + convert_to_hexint(v, seen) for k,v in value.items()) + '}'
	elif isinstance(value, (set,)):
		return '{' + ', '.join(convert_to_hexint(v, seen) for v in value) + '}'
	#elif isinstance(value, (Iterable,)):
	#	return '(' + ', '.join(convert_to_hexint(v, seen) for v in value) + ')'
	#elif isinstance(value, (Mapping,)):
	#	return '{' + ', '.join(convert_to_hexint(k, seen) + ': ' + convert_to_hexint(value[k], seen) for k in value) + '}'
	else:
		return repr(value)


def new_displayhook(value):
	seen = []
	print(convert_to_hexint(value, seen))



setattr(sys, 'displayhook', new_displayhook)
