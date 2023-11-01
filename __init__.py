from collections.abc import Generator
import binaryninja
import builtins
import itertools
import pprint
import sys
import traceback
import time

original_displayhook = sys.__displayhook__
original_print = builtins.print
LAST_WIDTH_CHECK = 0
WIDTH_CACHE = None


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


def screen_width():
	global LAST_WIDTH_CHECK
	global WIDTH_CACHE
	if time.time() - LAST_WIDTH_CHECK > 0.5 or WIDTH_CACHE is None:
		LAST_WIDTH_CHECK = time.time()
		WIDTH_CACHE = binaryninja.Settings().get_integer("python.hexIntegers.prettyPrintWidth")
		if WIDTH_CACHE < 1:
			WIDTH_CACHE = 80
			try:
				import binaryninjaui
				import PySide6
				context: binaryninjaui.UIContext = binaryninjaui.UIContext.activeContext()
				window = context.mainWindow()
				consoles = window.findChildren(binaryninjaui.ScriptingConsole)

				for console in consoles:
					if console.getProviderName() == "Python":
						output = console.findChild(binaryninjaui.ScriptingConsoleOutput)
						visible_width = output.document().size().width() - (output.document().documentMargin() * 2)
						font = output.font()
						metrics = PySide6.QtGui.QFontMetricsF(font)
						WIDTH_CACHE = int(visible_width / metrics.horizontalAdvance("X"))
						break
			except:
				pass
	return WIDTH_CACHE


def do_print(value):
	if binaryninja.Settings().get_bool("python.hexIntegers.prettyPrint"):
		result = HexIntPPrint(width=screen_width(), top=True).pformat(value)
	else:
		result = convert_to_hexint(value, [], True)
	return result


def can_extract_generator(value):
	return (isinstance(value, (Generator,)) or hasattr(type(value), '__next__')) and binaryninja.Settings().get_bool("python.hexIntegers.generators")


def new_displayhook(value):
	# Python docs say:
	# Set '_' to None to avoid recursion
	builtins._ = None
	value_copy = value
	if can_extract_generator(value):
		# Save generator state so we don't consume _
		type_name = type(value).__name__
		value_copy, value = itertools.tee(value, 2)
		conts = []
		for v in value:
			if len(conts) >= binaryninja.Settings().get_integer("python.hexIntegers.generatorLength"):
				conts.append(Ellipsis)
				break
			conts.append(v)

		original_print(f'(generator {type_name}) ' + do_print(conts))
	else:
		result = do_print(value)
		if result is not None:
			original_print(result)
	builtins._ = value_copy


def print_override(*args, **kwargs):
	# To not break scripts, only hook this if we're in the script interpreter
	in_script_provider = False
	for frame in traceback.extract_stack():
		if frame.filename == binaryninja.scriptingprovider.__file__:
			in_script_provider = True
			break
	if not in_script_provider:
		original_print(*args, **kwargs)
		return

	# Generator extraction is only done for basic print calls
	if len(args) == 1 and len(kwargs) == 0 and can_extract_generator(args[0]):
		# Save generator state so we don't consume _
		conts = []
		type_name = type(args[0]).__name__
		for v in args[0]:
			if len(conts) >= binaryninja.Settings().get_integer("python.hexIntegers.generatorLength"):
				conts.append(Ellipsis)
				break
			conts.append(v)

		original_print(f'(generator {type_name}) ' + do_print(conts))
		return

	# Otherwise, convert all args to hexint and print
	def convert_arg(arg):
		if type(arg) is str:
			# Special for print(): strings are printed bare
			return arg
		else:
			return do_print(arg)

	args = [convert_arg(arg) for arg in args]
	return original_print(*args, **kwargs)


setattr(sys, 'displayhook', new_displayhook)
setattr(builtins, 'print', print_override)

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
		"description" : "If integers should print decimal, as well as hexadecimal values. Result is formatted like '123 / 0x7b'. Only applies to top-level integers.",
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
binaryninja.Settings().register_setting("python.hexIntegers.showTopNone", '''
	{
		"title" : "Show Top-Level 'None' Value",
		"description" : "If the expression typed returns 'None', should 'None' be printed?",
		"default" : false,
		"type" : "boolean"
	}
''')
binaryninja.Settings().register_setting("python.hexIntegers.prettyPrintWidth", '''
	{
		"title" : "Pretty Print Width",
		"description" : "Attempted maximum number of columns in the pretty printed output. 0: Calculate width from interpreter window. (Default: 0)",
		"default" : 0,
		"minValue" : 0,
		"maxValue" : 10000,
		"type" : "number"
	}
''')
