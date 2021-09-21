from collections.abc import Generator, Iterable, Mapping
import binaryninja
import sys

original_displayhook = sys.__displayhook__


def convert_to_hexint(value, seen, top=False):
	if value in seen:
		return "<recursion>"
	seen = seen + [value]

	if isinstance(value, (int,)):
		if top:
			return f"{value} / 0x{value:x}"
		else:
			return f"0x{value:x}"
	elif isinstance(value, (float,)) and (value % 1) < 0.0001:
		value = int(value)
		if top:
			return f"~{value} / ~0x{value:x}"
		else:
			return f"~0x{value:x}"
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
	elif value is Ellipsis:
		return '...'
	#elif isinstance(value, (Iterable,)):
	#	return '(' + ', '.join(convert_to_hexint(v, seen) for v in value) + ')'
	#elif isinstance(value, (Mapping,)):
	#	return '{' + ', '.join(convert_to_hexint(k, seen) + ': ' + convert_to_hexint(value[k], seen) for k in value) + '}'
	else:
		return repr(value)


def new_displayhook(value):
	if isinstance(value, (Generator,)) or hasattr(value, '__next__'):
		conts = []
		for v in value:
			conts.append(v)
			if len(conts) > 100:
				conts.append(Ellipsis)
				break
		value = conts
	print(convert_to_hexint(value, [], True))


setattr(sys, 'displayhook', new_displayhook)
