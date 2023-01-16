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
		if top and not binaryninja.Settings().get_bool("python.hexIntegers.showTopNone"):
			return
		else:
			return 'None'
	elif isinstance(value, (int,)):
		# Could be an enum or something else with a custom repr()
		if value.__repr__.__qualname__ != 'int.__repr__':
			if top and binaryninja.Settings().get_bool("python.hexIntegers.alsoDecimal"):
				# Enums already include the decimal in repr()
				if f"{value}" in repr(value):
					return f"{repr(value)} / 0x{value:x}"
				else:
					return f"{repr(value)} / {value} / 0x{value:x}"
			else:
				return repr(value)
		else:
			if top and binaryninja.Settings().get_bool("python.hexIntegers.alsoDecimal"):
				return f"{value} / 0x{value:x}"
			else:
				return f"0x{value:x}"
	elif isinstance(value, (float,)) and (value % 1) < 0.0001:
		value = int(value)
		if top and binaryninja.Settings().get_bool("python.hexIntegers.alsoDecimal"):
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
		return '{' + ', '.join(convert_to_hexint(k, seen) + ': ' + convert_to_hexint(v, seen) for k, v in value.items()) + '}'
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
	if (isinstance(value, (Generator,)) or hasattr(type(value), '__next__')) and binaryninja.Settings().get_bool("python.hexIntegers.generators"):
		# Save generator state so we don't consume _
		value_copy, value = itertools.tee(value, 2)
		conts = []
		for v in value:
			if len(conts) >= binaryninja.Settings().get_integer("python.hexIntegers.generatorLength"):
				conts.append(Ellipsis)
				break
			conts.append(v)

		print('(generator) ' + convert_to_hexint(conts, [], True))
	else:
		result = convert_to_hexint(value, [], True)
		if result is not None:
			print(result)
	builtins._ = value_copy


setattr(sys, 'displayhook', new_displayhook)

binaryninja.Settings().register_setting("python.hexIntegers.generatorLength", '''
	{
		"title" : "Generator Preview Length",
		"description" : "How many items to preview when displaying generators.",
		"default" : 100,
		"minValue" : 0,
		"maxValue" : 1000,
		"type" : "number"
	}
''')
binaryninja.Settings().register_setting("python.hexIntegers.generators", '''
	{
		"title" : "Generator Previews",
		"description" : "If generators should be loaded and previewed when displayed.",
		"default" : true,
		"type" : "boolean"
	}
''')
binaryninja.Settings().register_setting("python.hexIntegers.alsoDecimal", '''
	{
		"title" : "Show Decimal",
		"description" : "If integers should decimal, as well as hexadecimal values.",
		"default" : true,
		"type" : "boolean"
	}
''')
binaryninja.Settings().register_setting("python.hexIntegers.showTopNone", '''
	{
		"title" : "Show Top-Level 'None' Value",
		"description" : "If the expression typed returns 'None', should 'None' be printed?",
		"default" : false,
		"type" : "boolean"
	}
''')
