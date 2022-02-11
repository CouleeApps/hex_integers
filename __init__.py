from collections.abc import Generator, Iterable, Mapping
import binaryninja
import builtins
import itertools
import sys

original_displayhook = sys.__displayhook__


def convert_to_hexint(value, seen, top=False):
	if value in seen:
		return "<recursion>"
	seen = seen + [value]
	if isinstance(value, (bool,)):
		return repr(value)
	elif value is None:
		return
	elif isinstance(value, (int,)):
		# Could be an enum or something else with a custom repr()
		if value.__repr__.__qualname__ != 'int.__repr__':
			if top:
				# Enums already include the decimal in repr()
				if f"{value}" in repr(value):
					return f"{repr(value)} / 0x{value:x}"
				else:
					return f"{repr(value)} / {value} / 0x{value:x}"
			else:
				return repr(value)
		else:
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
	else:
		return repr(value)


def new_displayhook(value):
	# Python docs say:
	# Set '_' to None to avoid recursion
	builtins._ = None
	value_copy = value
	if isinstance(value, (Generator,)) or hasattr(value, '__next__'):
		# Save generator state so we don't consume _
		value_copy, value = itertools.tee(value, 2)
		conts = []
		for v in value:
			conts.append(v)
			if len(conts) > 100:
				conts.append(Ellipsis)
				break

		print('(generator) ' + convert_to_hexint(conts, [], True))
	else:
		result = convert_to_hexint(value, [], True)
		if result:
			print(result)
	builtins._ = value_copy


setattr(sys, 'displayhook', new_displayhook)
