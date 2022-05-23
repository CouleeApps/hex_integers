from collections.abc import Generator, Iterable, Mapping
import binaryninja
import builtins
import itertools
import sys
import pprint

original_displayhook = sys.__displayhook__


class HexIntPPrint(pprint.PrettyPrinter):
	def __init__(self, indent=1, width=80, depth=None, stream=None, *, compact=False, sort_dicts=True, underscore_numbers=False, top=False):
		self._top = top
		super().__init__(indent, width, depth, stream, compact=compact, sort_dicts=sort_dicts, underscore_numbers=underscore_numbers)

	def _safe_repr(self, object, context, maxlevels, level):
		# Return triple (repr_string, isreadable, isrecursive).
		typ = type(object)
		r = getattr(typ, "__repr__", None)

		if object is Ellipsis:
			return '...', True, False

		if issubclass(typ, int) and r is int.__repr__:
			if object.__repr__.__qualname__ != 'int.__repr__':
				if self._top and binaryninja.Settings().get_bool("python.hexIntegers.alsoDecimal"):
					# Enums already include the decimal in repr()
					if f"{object}" in repr(object):
						return f"{repr(object)} / 0x{object:x}", True, False
					else:
						return f"{repr(object)} / {object} / 0x{object:x}", True, False
			else:
				if self._top and binaryninja.Settings().get_bool("python.hexIntegers.alsoDecimal"):
					return f"{object} / 0x{object:x}", True, False
				else:
					return f"0x{object:x}", True, False
		elif isinstance(object, (float,)) and (object % 1) < 0.0001:
			object = int(object)
			if self._top and binaryninja.Settings().get_bool("python.hexIntegers.alsoDecimal"):
				return f"~{object} / ~0x{object:x}", True, False
			else:
				return f"~0x{object:x}", True, False

		self._top = False
		return super()._safe_repr(object, context, maxlevels, level)

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
	if (isinstance(value, (Generator,)) or hasattr(type(value), '__next__')) and binaryninja.Settings().get_bool("python.hexIntegers.generators"):
		# Save generator state so we don't consume _
		value_copy, value = itertools.tee(value, 2)
		conts = []
		for v in value:
			if len(conts) >= binaryninja.Settings().get_integer("python.hexIntegers.generatorLength"):
				conts.append(Ellipsis)
				break
			conts.append(v)

		if binaryninja.Settings().get_bool("python.hexIntegers.prettyPrint"):
			width = binaryninja.Settings().get_integer("python.hexIntegers.prettyPrintWidth")
			if width < 1:
				width = 80
			print('(generator) ' + HexIntPPrint(width=width, top=True).pformat(conts))
		else:
			print('(generator) ' + convert_to_hexint(conts, [], True))
	else:
		if binaryninja.Settings().get_bool("python.hexIntegers.prettyPrint"):
			width = binaryninja.Settings().get_integer("python.hexIntegers.prettyPrintWidth")
			if width < 1:
				width = 80
			result = HexIntPPrint(width=width, top=True).pformat(value)
		else:
			result = convert_to_hexint(value, [], True)
		if result:
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
binaryninja.Settings().register_setting("python.hexIntegers.prettyPrint", '''
	{
		"title" : "Pretty Print",
		"description" : "Output should be pretty-printed using pprint.",
		"default" : false,
		"type" : "boolean"
	}
''')
binaryninja.Settings().register_setting("python.hexIntegers.prettyPrintWidth", '''
	{
		"title" : "Pretty Print Width",
		"description" : "Attempted maximum number of columns in the pretty printed output. (Default: 80)",
		"default" : 80,
		"minValue" : 1,
		"maxValue" : 10000,
		"type" : "number"
	}
''')
