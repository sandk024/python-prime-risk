from dsl import *

unit("u0", "Python from Zero", "Never written code? Start here. One idea per 10-minute lesson, in plain English: print, numbers, variables, errors, text, decisions, lists, loops, dictionaries and your own functions.")

# ---------------------------------------------------------------- 1
beginner("u0l1", "What a program is (and how to run one here)",
"What a program is, and how to run Python code in this app.",
[chunk(r'''
A **program** is a list of instructions for a computer. **Python** is a language for writing those instructions, a bit like a recipe written in very precise English.

The computer **runs** a program by doing the instructions one line at a time, from top to bottom.

Below is a real Python program. Tap **▶ Run** under it. The grey box that appears underneath is the **output**: whatever the program shows you.
''', r'''
print("Hello!")
print("This is my first program.")
'''),
chunk(r'''
`print(...)` is an instruction that shows something in the output box. Each `print` shows one line.

Lines run in order. Try it: in the box below, move the last line to the top (or change the words between the quotes), then tap **▶ Run** again.

You can't break anything here. The **↺** button puts the original code back.
''', r'''
print("1. Lace up")
print("2. Warm up")
print("3. Run")
'''),
chunk(r'''
A line that starts with `#` is a **comment**: a note for humans. Python skips it completely. Programmers use comments to explain their code, and to switch a line off without deleting it.
''', r'''
# This line is a comment, so nothing happens
print("This line runs")
# print("This line is switched off")
'''),
chunk(r'''
**How exercises work**

Each exercise has its own code box. Type your code, then tap **✓ Check**. The app runs your code and checks the result:

- ✅ means that part is right.
- ❌ explains what it expected and what it got instead.

Starter code often has comments showing the shape of the line to write, like `# total = ___`. The `___` is the blank you fill in. Type your own line without the `#` (a line starting with `#` is skipped).

Stuck? Tap **Hint**. After two tries you can open the **solution**, which explains every line. Exercises you miss come back later in your daily **Review**.
''')],
q("What does this program show?", ["one, two, three (on three lines)", "one, three (on two lines)", "three, one (on two lines)", "Nothing"], 1,
  "The middle line starts with #, so it's a comment and Python skips it. The other two lines run top to bottom.",
  code=r'''
print("one")
# print("two")
print("three")
'''),
[
ex("Say hello", r'''
Make the program show exactly this line:

`Hello, Python!`

Type this into the box, then tap **✓ Check**:

`print("Hello, Python!")`
''', r'''
# Type your line below this comment
''', r'''
print("Hello, Python!")   # print shows the text between the quotes
''', [("The output is: Hello, Python!", r'''
assert _out, "Nothing was shown. Your line needs print( ) around the text, and the text needs quotes: print(\"Hello, Python!\")"
assert _out == ["Hello, Python!"], f"Expected the output to be exactly: Hello, Python!\nYours was: {_out[0] if len(_out) == 1 else _out}\nCheck capital letters, the comma and the exclamation mark."
''')], hints=["Copy the line from the instructions exactly, including the quotes.", "Capital H, capital P, a comma after Hello and a ! at the end."],
wrong=r'''
print("hello python")
'''),
ex("Ready, set, go", r'''
Show these three lines, in this order, using three `print` lines:

```
Ready
Set
Go!
```
''', r'''
# Write three print lines below
''', r'''
print("Ready")   # line 1 runs first
print("Set")     # then line 2
print("Go!")     # then line 3
''', [("Three lines in the right order", r'''
assert len(_out) == 3, f"Expected 3 lines of output, but there were {len(_out)}. Use one print per line."
assert sorted(_out) != sorted(["Ready", "Set", "Go!"]) or _out == ["Ready", "Set", "Go!"], f"Right words, wrong order: {_out}. Python runs lines top to bottom, so put the print lines in the order you want them shown."
assert _out == ["Ready", "Set", "Go!"], f"Expected Ready / Set / Go!  but got {_out}. Check spelling and capitals."
''')], hints=["Each line looks like print(\"Ready\")", "The order of your print lines is the order of the output."],
wrong=r'''
print("Set")
print("Ready")
print("Go!")
'''),
ex("Switch a line off", r'''
This shopping list prints three items. Turn the spaceship line **off** by putting `#` at the start of it. Don't delete the line.

The output should be just:
```
Buy milk
Buy bread
```
''', r'''
print("Buy milk")
print("Buy a spaceship")
print("Buy bread")
''', r'''
print("Buy milk")             # still runs
# print("Buy a spaceship")   # the # makes this line a comment, so it's skipped
print("Buy bread")            # still runs
''', [("The spaceship line is switched off", r'''
assert "Buy a spaceship" not in _out, "The spaceship line is still running. Put a # at the very start of that line."
assert _out == ["Buy milk", "Buy bread"], f"Expected Buy milk / Buy bread but got {_out}."
'''), ("The line is still there (as a comment)", r'''
assert "spaceship" in _source, "Don't delete the spaceship line: keep it, with a # in front, so it becomes a comment."
''')], hints=["A comment starts with #.", "Type # right before print on line 2."],
wrong=r'''
print("Buy milk")
print("Buy bread")
'''),
],
"A program is instructions run top to bottom; print() shows output, # starts a comment, ▶ Run tries code and ✓ Check grades it.")

# ---------------------------------------------------------------- 2
beginner("u0l2", "print() and text in quotes",
"How to show text with print(), and why text always goes inside quotes.",
[chunk(r'''
Text in Python is called a **string** (think: a string of letters). A string goes inside quotes: `"like this"` or `'like this'`. Both kinds work. Just start and end with the same kind.
''', r'''
print("Double quotes work")
print('Single quotes work too')
'''),
chunk(r'''
Numbers don't need quotes. But `"42"` *with* quotes is text that happens to look like a number. Python treats the two differently (lesson 7 explains why that matters).

Without quotes, Python thinks a word is the **name** of something, and complains if it doesn't know that name. So: **text always goes in quotes.**
''', r'''
print(42)      # a number
print("42")    # text that looks like a number (same output, different thing)
print("Run 5 miles")
'''),
chunk(r'''
`print` can show several things at once. Separate them with commas, and `print` puts a single space between them.

Need an apostrophe inside your text? Wrap the text in double quotes, so the `'` inside doesn't end it.
''', r'''
print("Price:", 20, "dollars")
print("It's sunny")
print()            # an empty print shows a blank line
print("Done")
''')],
q("What does this show?", ["Hi there", "Hithere", "Hi, there", "\"Hi\" \"there\""], 0,
  "Commas separate the things to print; print puts one space between them and doesn't show the quotes.",
  code=r'''print("Hi", "there")'''),
[
ex("Your first sentence", r'''
Show exactly:

`I am learning Python`
''', r'''
# One print line
''', r'''
print("I am learning Python")   # the text goes inside quotes, inside print( )
''', [("The output is: I am learning Python", r'''
assert _out, "Nothing was shown. Use print(\"...\") with your text inside the quotes."
assert _out == ["I am learning Python"], f"Expected: I am learning Python\nYours:    {' / '.join(_out)}\nCheck capitals (capital I and P) and spaces."
''')], hints=["print(\"I am learning Python\")"],
wrong=r'''
print("I am learning python")
'''),
ex("Text and a number", r'''
Use **one** `print` with three items separated by commas:
1. the text `"Miles run:"`
2. the number `12` (no quotes)
3. the text `"today"`

The output should be `Miles run: 12 today`
''', r'''
# One print with three items, separated by commas
''', r'''
print("Miles run:", 12, "today")   # three items; print adds a space between each
''', [("The output is: Miles run: 12 today", r'''
assert _out == ["Miles run: 12 today"], f"Expected: Miles run: 12 today\nYours:    {' / '.join(_out) or '(nothing)'}" + ("\nLooks like a space is missing: give print three separate items with commas, and it adds the spaces for you." if _out and _out[0].replace(' ', '') == "Milesrun:12today" else "")
'''), ("12 is given as a number, with commas between the items", r'''
assert _source.count("print(") == 1, "Use just one print line."
import re
assert re.search(r",\s*12\s*,", _source), "Give 12 as its own item: no quotes around it, with a comma before and after it."
''')], hints=["Three items: \"Miles run:\", 12, \"today\"", "print(\"Miles run:\", 12, \"today\")"],
wrong=r'''
print("Miles run:12 today")
'''),
ex("An apostrophe inside", r'''
Show exactly:

`It's race day!`
''', r'''
# Careful with the apostrophe in It's
''', r'''
print("It's race day!")   # double quotes outside, so the ' inside is just a character
''', [("The output is: It's race day!", r'''
assert _out == ["It's race day!"], f"Expected: It's race day!\nYours:    {' / '.join(_out) or '(nothing)'}\nWrap the text in double quotes \" \" so the apostrophe can sit inside."
''')], hints=["Use double quotes around the whole text: \"It's race day!\""],
wrong=r'''
print("Its race day!")
'''),
],
"Text (a string) goes in quotes; print shows it; commas let one print show several items with spaces between.")

# ---------------------------------------------------------------- 3
beginner("u0l3", "Numbers and arithmetic",
"How Python does math with + - * / ** // % and in what order.",
[chunk(r'''
Python is a calculator. Put math inside `print( )` to see the answer.

`*` means multiply and `/` means divide. Notice that `7 / 2` gives `3.5`: dividing always gives a **decimal number**. Python calls decimal numbers **floats** and whole numbers **ints** (short for integers).
''', r'''
print(2 + 3)
print(10 - 4)
print(6 * 7)
print(7 / 2)
'''),
chunk(r'''
Three more operators:

- `**` is "to the power of": `2 ** 3` is 2 × 2 × 2 = 8
- `//` divides and drops the remainder (whole-number division)
- `%` gives just the remainder

Example: 17 cookies shared by 5 friends. Each gets `17 // 5` = 3 cookies, and `17 % 5` = 2 are left over.
''', r'''
print(2 ** 3)
print(17 // 5)
print(17 % 5)
'''),
chunk(r'''
**Order of operations** works like school math: `**` first, then `*  /  //  %`, then `+  -`. Use parentheses `( )` to choose the order yourself.

`round(number, 2)` rounds to 2 decimal places. Like `print`, `round` is a **function**: a built-in instruction you use by writing its name followed by parentheses.
''', r'''
print(2 + 3 * 4)      # multiply first: 2 + 12
print((2 + 3) * 4)    # parentheses first: 5 * 4
print(round(10 / 3, 2))
''')],
q("What does this show?", ["24", "4", "12", "8"], 1, "Multiplication happens before subtraction: 2 * 3 = 6, then 10 − 6 = 4.",
  code=r'''print(10 - 2 * 3)'''),
[
ex("Hours in a year", r'''
Print how many hours are in a year (365 days × 24 hours). Let Python do the math: write the multiplication, not the answer.
''', r'''
# print(___) with a multiplication inside
''', r'''
print(365 * 24)   # * multiplies; print shows the result, 8760
''', [("The answer is 8760", r'''
assert _out, "Nothing was shown. Put the math inside print( )."
assert _out == ["8760"], f"You printed {_out[0]}; expected 8760." + (" Use * to multiply, not +." if _out[0] == "389" else "")
'''), ("Python did the math", r'''
assert "*" in _source, "Write the multiplication (365 * 24) inside print, rather than typing the answer."
''')], hints=["* means multiply.", "print(365 * 24)"],
wrong=r'''
print(365 + 24)
'''),
ex("Share the pizza", r'''
29 slices are shared by 4 people. Use two `print` lines:
1. how many **whole** slices each person gets (use `//`)
2. how many slices are **left over** (use `%`)
''', r'''
# Line 1: whole slices each (use //)
# Line 2: slices left over (use %)
''', r'''
print(29 // 4)   # // whole-number division: 7 slices each
print(29 % 4)    # % remainder: 1 slice left over
''', [("Whole slices each: 7", r'''
assert len(_out) >= 1, "Nothing was shown. Use two print lines."
assert _out[0] == "7", f"Line 1 shows {_out[0]}; expected 7." + (" / gives a decimal; use // to drop the remainder." if _out[0] == "7.25" else "")
'''), ("Left over: 1", r'''
assert len(_out) == 2, f"Expected 2 lines of output; got {len(_out)}."
assert _out[1] == "1", f"Line 2 shows {_out[1]}; expected 1 (29 = 4 × 7 + 1). Use %."
''')], hints=["29 // 4 for the whole slices", "29 % 4 for the remainder"],
wrong=r'''
print(29 / 4)
print(29 % 4)
'''),
ex("Average of three runs", r'''
Your last three runs were 80, 90 and 70 minutes. Print the average: add them up, then divide by 3.

Watch the order of operations!
''', r'''
# print the average of 80, 90 and 70
''', r'''
print((80 + 90 + 70) / 3)   # parentheses make the adding happen before the dividing
''', [("The average is 80.0", r'''
assert _out, "Nothing was shown."
assert _out == ["80.0"], f"You printed {_out[0]}; expected 80.0." + (" Without parentheses only the 70 gets divided by 3. Wrap the sum in ( )." if _out[0].startswith("193.3") else "")
''')], hints=["Division happens before addition unless you use parentheses.", "(80 + 90 + 70) / 3"],
wrong=r'''
print(80 + 90 + 70 / 3)
'''),
],
"+ - * / do the usual math, ** is power, // drops the remainder, % gives the remainder, and parentheses set the order.")

# ---------------------------------------------------------------- 4
beginner("u0l4", "Variables: a named box",
"How to store a value under a name (a variable) and change it later.",
[chunk(r'''
A **variable** is a name that holds a value, like a labelled box.

`=` means "put the value on the right into the box on the left". It's not "equals" in the math sense; read it as "becomes".

`print(miles)` has no quotes, because we want the **value in the box**, not the word "miles".
''', r'''
miles = 5
print(miles)
print(miles * 2)
print("miles")     # with quotes: just the word
'''),
chunk(r'''
**Naming rules:** letters, digits and underscores `_` only; no spaces; can't start with a digit. Capitals matter: `Price` and `price` are different boxes.

Pick names that say what's inside, like `price` or `total_cost`.
''', r'''
price = 20
quantity = 3
total_cost = price * quantity
print(total_cost)
'''),
chunk(r'''
**Reassignment** means putting a new value in a box. The old value is gone.

You can use the old value to work out the new one. `score = score + 5` means: take what's in `score`, add 5, put the result back in `score`.

The shortcut `score += 5` does the same thing (`-=` and `*=` work too).
''', r'''
score = 10
print(score)
score = score + 5
print(score)
score += 5
print(score)
''')],
q("What does this show?", ["7", "8", "4", "3"], 0, "x starts at 4, becomes 4 × 2 = 8, then 8 − 1 = 7. Each line replaces the value in the box.",
  code=r'''
x = 4
x = x * 2
x = x - 1
print(x)
'''),
[
ex("Fill two boxes", r'''
Create two variables:
- `city` holding the text `"Denver"`
- `year` holding the number `2027` (a number, so no quotes)
''', r'''
# city = ___
# year = ___
''', r'''
city = "Denver"   # text goes in quotes
year = 2027       # a number: no quotes
''', [("city is \"Denver\"", r'''
assert city == "Denver", f"city is {_kind(city)}; expected \"Denver\" (capital D, in quotes)."
'''), ("year is the number 2027", r'''
assert not isinstance(year, str), f"year is {_kind(year)}. For a number, leave the quotes off: year = 2027"
assert year == 2027, f"year is {_kind(year)}; expected 2027."
''')], hints=["A text value needs quotes; a number doesn't.", "city = \"Denver\" on one line, year = 2027 on the next."],
wrong=r'''
city = "Denver"
year = "2027"
'''),
ex("Shopping total", r'''
`price` and `quantity` are given. Create a variable `total` that is **price times quantity**, using the two variables (don't type 24 yourself).
''', r'''
price = 4
quantity = 6
# total = ___
''', r'''
price = 4
quantity = 6
total = price * quantity   # use the boxes' values: 4 * 6 = 24
print(total)
''', [("total is 24", r'''
assert total == 24, f"total is {_kind(total)}; expected 24." + (" That's price + quantity. Use * to multiply." if total == 10 else "")
'''), ("total uses the variables", r'''
line = [l for l in _source.splitlines() if l.replace(" ", "").startswith("total=")]
assert line and "price" in line[-1] and "quantity" in line[-1], "Build total from the variables (total = price * quantity), so it stays right if the price changes."
''')], hints=["total = price * quantity"],
wrong=r'''
price = 4
quantity = 6
total = price + quantity
'''),
ex("Update the box", r'''
You walked 3000 steps this morning. Update the **same** variable `steps`:
1. add 2500 steps from lunch
2. then add 1500 steps from the evening

Don't type the final answer: let the reassignment lines do the adding.
''', r'''
steps = 3000
# add 2500 to steps
# then add 1500 to steps
print(steps)
''', r'''
steps = 3000
steps = steps + 2500   # take the old value (3000), add 2500, store 5500
steps += 1500          # shortcut for steps = steps + 1500, so steps is 7000
print(steps)
''', [("steps ends at 7000", r'''
assert steps == 7000, f"steps is {_kind(steps)}; expected 7000." + (" It looks like you replaced the value instead of adding to it. Use steps = steps + 2500." if steps in (2500, 1500, 4000) else "")
'''), ("You added instead of typing the answer", r'''
assert "7000" not in "\n".join(l.split("#")[0] for l in _source.splitlines()), "Let Python add it up: use steps = steps + ... (or steps += ...) instead of typing 7000."
''')], hints=["steps = steps + 2500", "Then steps += 1500"],
wrong=r'''
steps = 3000
steps = 2500
steps = steps + 1500
'''),
],
"A variable is a named box; = puts a value in it, and x = x + 1 (or x += 1) updates it using the old value.")

# ---------------------------------------------------------------- 5
beginner("u0l5", "Reading error messages",
"How to read Python's error messages and fix the three most common ones.",
[chunk(r'''
Errors are normal: programmers see them all day. When Python can't run a line, it stops and shows an **error message**. Read it in three parts:

1. **which line**: `Line 2`
2. **the kind of error**: `NameError`
3. **what went wrong**: `name 'totl' is not defined`

Run this broken example and read the message:
''', r'''
total = 10
print(totl)
''', error=True),
chunk(r'''
**NameError** means you used a name Python doesn't know. It's usually a typo, or a variable used before it was created. Fix the example above by changing `totl` to `total`, then run it again.

**SyntaxError** means the code breaks Python's grammar rules (its **syntax**). Usually a bracket, quote or colon is missing. The line number points at the problem or just after it.
''', r'''
print("hello"
''', error=True),
chunk(r'''
**TypeError** means you mixed kinds of values (**types**) that don't go together. Here, `+` can't join text and a number.

One fix: `str(age)` turns the number 30 into the text `"30"`, and text can be joined to text. Lesson 7 covers this properly.
''', r'''
age = 30
print("I am " + age)
''', error=True)],
q("`price = 5` is on line 1. What happens when line 2 is `print(Price)`?", ["NameError", "SyntaxError", "TypeError", "It shows 5"], 0,
  "Capital letters matter: Price and price are different names, and Python has never seen Price, so it's a NameError."),
[
ex("Fix the NameError", r'''
This program should show `Half marathon: 13.1`, but it stops with a NameError. Run it, read the message, and fix the typo.
''', r'''
distance = 13.1
print("Half marathon:", distanse)
''', r'''
distance = 13.1                      # the variable is called distance
print("Half marathon:", distance)    # spell it the same way when you use it
''', [("The output is: Half marathon: 13.1", r'''
assert _out == ["Half marathon: 13.1"], f"Expected: Half marathon: 13.1\nYours:    {' / '.join(_out) or '(nothing)'}" + ("\nYou printed the word distance. Remove the quotes to show the value inside the variable." if _out == ["Half marathon: distance"] else "")
''')], hints=["Compare the spelling on line 2 with line 1.", "distanse should be distance"],
wrong=r'''
distance = 13.1
print("Half marathon:", "distance")
'''),
ex("Fix the SyntaxError", r'''
This program should show two lines, `Start line` then `Finish line`. Run it, read the message, and fix it.
''', r'''
print("Start line)
print("Finish line")
''', r'''
print("Start line")    # the text needed its closing quote before the )
print("Finish line")
''', [("Two lines: Start line, Finish line", r'''
assert _out == ["Start line", "Finish line"], f"Expected Start line / Finish line, but got {_out}."
''')], hints=["Every opening quote needs a closing quote.", "Line 1 is missing a \" after Start line"],
wrong=r'''
print("Start line")
print("Finish line"
'''),
ex("Fix the TypeError", r'''
`message` should be the text `Laps done: 4`. Line 2 fails with a TypeError because it joins text and a number. Fix it with `str(laps)`.
''', r'''
laps = 4
message = "Laps done: " + laps
print(message)
''', r'''
laps = 4                              # a number
message = "Laps done: " + str(laps)   # str() turns 4 into the text "4", so + can join it
print(message)                        # Laps done: 4
''', [("message is \"Laps done: 4\"", r'''
assert message == "Laps done: 4", f"message is {_kind(message)}; expected \"Laps done: 4\"." + (" You joined the word laps. Use str(laps), without quotes, to get the value." if message == "Laps done: laps" else "")
''')], hints=["str(laps) gives \"4\"", "message = \"Laps done: \" + str(laps)"],
wrong=r'''
laps = 4
message = "Laps done: " + "laps"
'''),
],
"An error message tells you the line, the kind (NameError = unknown name, SyntaxError = broken grammar, TypeError = mixed types) and what went wrong.")

# ---------------------------------------------------------------- 6
beginner("u0l6", "Working with text",
"How to join text, build sentences with f-strings, and measure or change text.",
[chunk(r'''
`+` joins two strings into one. Python doesn't add spaces for you, so put them in yourself.
''', r'''
first = "Ada"
last = "Lovelace"
full = first + " " + last
print(full)
'''),
chunk(r'''
An **f-string** is an easier way to build a sentence. Put the letter `f` right before the opening quote. Anything inside curly braces `{ }` is replaced by its value. You can even do math inside the braces.

`{price:.2f}` means "show price with 2 decimal places". The `.2f` part is a **format code**.
''', r'''
name = "Ada"
miles = 5
price = 3.5
print(f"{name} ran {miles} miles")
print(f"Double that is {miles * 2}")
print(f"Gel: ${price:.2f}")
'''),
chunk(r'''
`len(text)` counts the characters in a string, including spaces.

A **method** is a function attached to a value, written after a dot:

- `text.upper()` gives the text in CAPITALS
- `text.lower()` gives it in small letters
- `text.strip()` removes spaces from both ends

None of these change the original string. Each one gives you a new string.
''', r'''
word = "trail"
print(len(word))
print(word.upper())
padded = "   hello   "
print(padded.strip() + "!")
''')],
q("What does this show?", ["Hi Sam! 3", "Hi {name}! 3", "Hi Sam! 5", "Hi name! 3"], 0,
  "The f before the quote fills {name} with \"Sam\", and len(\"Sam\") is 3.",
  code=r'''
name = "Sam"
print(f"Hi {name}!", len(name))
'''),
[
ex("Full name", r'''
Create `full_name` = first name, a space, then last name, joining the given variables with `+`. It should be `"Grace Hopper"`.
''', r'''
first = "Grace"
last = "Hopper"
# full_name = ___
''', r'''
first = "Grace"                  # given
last = "Hopper"                  # given
full_name = first + " " + last   # join: "Grace" + " " + "Hopper"
print(full_name)                 # Grace Hopper
''', [("full_name is \"Grace Hopper\"", r'''
assert full_name == "Grace Hopper", f"full_name is {_kind(full_name)}; expected \"Grace Hopper\"." + (" The space is missing: join first + \" \" + last." if full_name == "GraceHopper" else "")
''')], hints=["Put a space string \" \" in the middle.", "full_name = first + \" \" + last"],
wrong=r'''
first = "Grace"
last = "Hopper"
full_name = first + last
'''),
ex("A sentence with an f-string", r'''
Use an **f-string** with the given variables to create `sentence` = `"I packed 6 gels"`.
''', r'''
item = "gels"
count = 6
# sentence = f"___"
''', r'''
item = "gels"
count = 6
sentence = f"I packed {count} {item}"   # f fills each {name} with its value
print(sentence)
''', [("sentence is \"I packed 6 gels\"", r'''
assert sentence == "I packed 6 gels", f"sentence is {_kind(sentence)}; expected \"I packed 6 gels\"." + (" The braces weren't filled in: put f right before the opening quote." if "{" in str(sentence) else "")
'''), ("You used an f-string", r'''
assert 'f"' in _source or "f'" in _source, "Build it with an f-string: f\"I packed {count} {item}\""
''')], hints=["f\"I packed {count} {item}\""],
wrong=r'''
item = "gels"
count = 6
sentence = "I packed {count} {item}"
'''),
ex("Shout it", r'''
Create:
- `shout`: the word in capitals with an exclamation mark at the end, `"FINISH!"`
- `size`: the number of letters in `word`, using `len`
''', r'''
word = "finish"
# shout = ___
# size = ___
''', r'''
word = "finish"
shout = word.upper() + "!"   # "FINISH", then join "!"
size = len(word)             # len counts characters: 6
''', [("shout is \"FINISH!\"", r'''
assert shout == "FINISH!", f"shout is {_kind(shout)}; expected \"FINISH!\"." + (" Add the exclamation mark: word.upper() + \"!\"" if shout == "FINISH" else "")
'''), ("size is 6", r'''
assert size == 6, f"size is {_kind(size)}; expected 6. Use len(word)."
''')], hints=["word.upper() gives \"FINISH\"", "Then + \"!\""],
wrong=r'''
word = "finish"
shout = word.upper()
size = len(word)
'''),
ex("Price tag", r'''
Create `tag` = `"$4.50"` from `price` using an f-string with `:.2f` (two decimal places). Put a `$` before the braces.
''', r'''
price = 4.5
# tag = f"___"
''', r'''
price = 4.5
tag = f"${price:.2f}"   # $ is plain text; {price:.2f} shows 4.50
print(tag)
''', [("tag is \"$4.50\"", r'''
assert tag == "$4.50", f"tag is {_kind(tag)}; expected \"$4.50\"." + (" Add :.2f inside the braces to always show 2 decimals." if tag == "$4.5" else "")
''')], hints=["Inside the braces: {price:.2f}", "tag = f\"${price:.2f}\""],
wrong=r'''
price = 4.5
tag = f"${price}"
'''),
],
"+ joins strings, f\"...{x}...\" fills in values, len() counts characters, and .upper() .lower() .strip() give changed copies.")

# ---------------------------------------------------------------- 7
beginner("u0l7", "Text vs numbers: int(), float(), str()",
"Why \"5\" and 5 are different, and how to convert between text and numbers.",
[chunk(r'''
Every value has a **type**, meaning what kind of thing it is:

- `str`: text
- `int`: a whole number
- `float`: a decimal number

`type(x)` tells you the type. Output like `<class 'str'>` just means "this is a str".
''', r'''
print(type("5"))
print(type(5))
print(type(5.0))
'''),
chunk(r'''
Why care? `"5" + "5"` joins text and gives `"55"`, but `5 + 5` gives `10`.

Values that come from a person typing, or from a file, always arrive as **text**. Python's `input()` function asks the person at the keyboard to type something, and it always gives you text. Programs in this app can't pause for typing, so we'll pretend:

`answer = "42"   # as if the user typed 42`
''', r'''
print("5" + "5")
print(5 + 5)
'''),
chunk(r'''
Convert with:

- `int("42")` gives the number 42
- `float("3.5")` gives 3.5
- `str(42)` gives the text `"42"`

`int(3.9)` gives 3: it chops the decimals off, it doesn't round. `int("hello")` fails with a **ValueError**, because that text isn't a number.
''', r'''
typed = "42"          # pretend the user typed this
number = int(typed)
print(number + 1)
print("Total: " + str(number))
''')],
q("What does this show?", ["333 9", "9 9", "333 333", "An error"], 0,
  "\"3\" * 3 repeats the text three times (\"333\"); int(\"3\") is the number 3, and 3 * 3 = 9.",
  code=r'''print("3" * 3, int("3") * 3)'''),
[
ex("Text to number", r'''
`typed_age` is text, as if someone typed it. Create:
- `age`: the same value as a whole number (use `int`)
- `next_year`: `age` plus 1
''', r'''
typed_age = "34"   # pretend the user typed this
# age = ___
# next_year = ___
''', r'''
typed_age = "34"         # text, like everything a user types
age = int(typed_age)     # convert the text "34" to the number 34
next_year = age + 1      # now math works: 35
''', [("age is the number 34", r'''
assert not isinstance(age, str), f"age is {_kind(age)}: still text. Wrap it in int( ) to make it a number."
assert age == 34, f"age is {_kind(age)}; expected 34."
'''), ("next_year is 35", r'''
assert next_year == 35, f"next_year is {_kind(next_year)}; expected 35."
''')], hints=["age = int(typed_age)", "next_year = age + 1"],
wrong=r'''
typed_age = "34"
age = typed_age
next_year = 35
'''),
ex("Add two typed prices", r'''
Two prices arrived as text. Create `total`, their sum as a decimal number (`3.75`).
''', r'''
a = "2.50"
b = "1.25"
# total = ___
''', r'''
a = "2.50"
b = "1.25"
total = float(a) + float(b)   # convert each to a decimal number, then add
print(total)
''', [("total is 3.75", r'''
assert not isinstance(total, str), f"total is {_kind(total)}. + joined the text instead of adding. Convert each with float( ) first."
assert _close(total, 3.75), f"total is {_kind(total)}; expected 3.75."
''')], hints=["float(a) turns \"2.50\" into 2.5", "total = float(a) + float(b)"],
wrong=r'''
a = "2.50"
b = "1.25"
total = a + b
'''),
ex("Number into a sentence", r'''
Create `msg` = `"Laps: 12"` by joining the text `"Laps: "` and `laps` with `+`. (You'll need `str`.)
''', r'''
laps = 12
# msg = ___
''', r'''
laps = 12
msg = "Laps: " + str(laps)   # str(12) is "12", so + can join text with text
print(msg)
''', [("msg is \"Laps: 12\"", r'''
assert msg == "Laps: 12", f"msg is {_kind(msg)}; expected \"Laps: 12\"." + (" That joined the word laps. Use str(laps), without quotes." if msg == "Laps: laps" else "")
'''), ("You used str() and +", r'''
assert "str(" in _source and "+" in _source, "Practice the conversion: \"Laps: \" + str(laps)"
''')], hints=["str(laps) is \"12\""],
wrong=r'''
laps = 12
msg = "Laps: " + "laps"
'''),
],
"str is text, int a whole number, float a decimal; typed input is always text, so convert with int(), float() or str() before mixing.")

# ---------------------------------------------------------------- 8
beginner("u0l8", "True/False and comparisons",
"Using True and False, and comparing values with == != < > <= >= and/or/not.",
[chunk(r'''
A **boolean** (`bool`) is either `True` or `False`. Write them with a capital letter and no quotes. A comparison asks a yes/no question and answers with a boolean.

`==` asks "are these equal?". A single `=` puts a value in a variable; a double `==` compares two values. Mixing them up is a very common slip.
''', r'''
print(5 > 3)
print(5 < 3)
print(10 == 10)
print(10 != 10)   # != means "not equal"
'''),
chunk(r'''
`>=` means "at least" and `<=` means "at most". You can compare text too, but capitals matter: `"apple" == "Apple"` is False.

You can store a comparison's answer in a variable, like any other value.
''', r'''
speed = 7
print(speed >= 7)
print("apple" == "Apple")
is_fast = speed > 6
print(is_fast)
'''),
chunk(r'''
Combine questions with:

- `and`: True only if **both** sides are True
- `or`: True if **at least one** side is True
- `not`: flips True to False and False to True
''', r'''
sunny = True
warm = False
print(sunny and warm)
print(sunny or warm)
print(not warm)
''')],
q("What does this show?", ["False", "True", "5", "An error"], 0,
  "x > 2 is True but x < 4 is False, and `and` needs both sides True.",
  code=r'''
x = 5
print(x > 2 and x < 4)
'''),
[
ex("Can I afford it?", r'''
Create `can_afford`: `True` if `savings` is **at least** `price`. Use a comparison (don't just type True), so it stays right if the numbers change.
''', r'''
savings = 120
price = 95
# can_afford = ___
''', r'''
savings = 120                   # given
price = 95                      # given
can_afford = savings >= price   # "at least" means >=; 120 >= 95 is True
''', [("can_afford is True here", r'''
assert can_afford is True, f"can_afford is {_kind(can_afford)}; with savings 120 and price 95 it should be True." + (" You compared the other way round: savings >= price." if can_afford is False else "")
'''), ("It works for other numbers too", r'''
ns = _rerun(savings=50)
assert ns["can_afford"] is False, "With savings = 50 it should be False. Use a comparison (savings >= price) instead of typing True."
ns = _rerun(savings=95)
assert ns["can_afford"] is True, "With savings exactly equal to price (95) it should be True: 'at least' means >=, not >."
''')], hints=["\"At least\" is >=", "can_afford = savings >= price"],
wrong=r'''
savings = 120
price = 95
can_afford = savings > price
'''),
ex("Same or different?", r'''
Create:
- `same`: compare `answer` and `guess` exactly with `==` (it will be False, because capitals differ)
- `same_ignoring_case`: compare `answer.lower()` with `guess.lower()` (it will be True)
''', r'''
answer = "Blue"
guess = "blue"
# same = ___
# same_ignoring_case = ___
''', r'''
answer = "Blue"
guess = "blue"
same = answer == guess                              # "Blue" vs "blue": False
same_ignoring_case = answer.lower() == guess.lower()  # "blue" vs "blue": True
''', [("same is False", r'''
assert same is False, f"same is {_kind(same)}; expected False (\"Blue\" and \"blue\" differ in capitals). Use ==, not =."
'''), ("same_ignoring_case is True", r'''
assert same_ignoring_case is True, f"same_ignoring_case is {_kind(same_ignoring_case)}; expected True. Compare answer.lower() == guess.lower()."
''')], hints=["same = answer == guess", ".lower() makes both \"blue\""],
wrong=r'''
answer = "Blue"
guess = "blue"
same = answer == guess
same_ignoring_case = answer == guess
'''),
ex("Good day for a run?", r'''
Create `good_day`: True when `temp` is between 10 and 25 (including 10 and 25) **and** it is **not** raining.
''', r'''
temp = 18
raining = False
# good_day = ___
''', r'''
temp = 18
raining = False
good_day = temp >= 10 and temp <= 25 and not raining   # all three must be True
''', [("True on a dry 18° day", r'''
assert good_day is True, f"good_day is {_kind(good_day)}; with temp 18 and no rain it should be True."
'''), ("False when it rains", r'''
assert _rerun(raining=True)["good_day"] is False, "When raining = True, good_day should be False. Add: and not raining"
'''), ("Checks both temperature limits", r'''
assert _rerun(temp=30)["good_day"] is False, "With temp = 30 it should be False (above 25)."
assert _rerun(temp=5)["good_day"] is False, "With temp = 5 it should be False (below 10)."
assert _rerun(temp=25)["good_day"] is True and _rerun(temp=10)["good_day"] is True, "10 and 25 themselves count as good: use >= and <=."
''')], hints=["temp >= 10 and temp <= 25", "... and not raining"],
wrong=r'''
temp = 18
raining = False
good_day = temp >= 10 and temp <= 25
'''),
],
"Comparisons (== != < > <= >=) give True or False; and needs both, or needs one, not flips it; = stores, == compares.")

# ---------------------------------------------------------------- 9
beginner("u0l9", "Making decisions: if, elif, else",
"How to make your program choose what to do with if, elif and else.",
[chunk(r'''
`if` runs some lines only when a condition is True. The pattern is: `if`, the condition, a colon `:`, then the lines to run, **indented** by 4 spaces (the ⇥ key on the toolbar does this).

Those indented lines are called a **block**. The first line that isn't indented runs every time.
''', r'''
temp = 30
if temp > 25:
    print("Hot! Bring extra water.")
    print("And a hat.")
print("Done checking.")
'''),
chunk(r'''
`else:` says what to do when the condition is False. It has no condition of its own.

Change `temp` to 15 and run it again.
''', r'''
temp = 30
if temp > 25:
    print("Hot run")
else:
    print("Comfortable run")
'''),
chunk(r'''
`elif` (short for "else if") checks another condition, but only if the ones above it were False. Python goes from top to bottom and runs **only the first branch that's True**, then skips the rest.

So the order of the checks matters: put the strictest one first.
''', r'''
score = 72
if score >= 90:
    grade = "A"
elif score >= 70:
    grade = "B"
else:
    grade = "C"
print(grade)
''')],
q("What does this show?", ["medium", "big", "small", "medium and small"], 0,
  "15 > 20 is False, so Python checks the elif: 15 > 10 is True, so it shows medium and skips the else.",
  code=r'''
x = 15
if x > 20:
    print("big")
elif x > 10:
    print("medium")
else:
    print("small")
'''),
[
ex("Hot or not", r'''
Create `advice`:
- `"Bring water"` if `temp` is **above** 25
- otherwise `"Enjoy the run"`
''', r'''
temp = 31
# if ___:
#     advice = ___
# else:
#     advice = ___
''', r'''
temp = 31
if temp > 25:                 # condition, then a colon
    advice = "Bring water"    # indented: runs only when temp > 25
else:
    advice = "Enjoy the run"  # runs otherwise
print(advice)
''', [("31° gives \"Bring water\"", r'''
assert advice == "Bring water", f"advice is {_kind(advice)}; with temp 31 expected \"Bring water\"."
'''), ("Cooler days give \"Enjoy the run\"", r'''
r = _rerun(temp=10)["advice"]
assert r == "Enjoy the run", f"With temp = 10, advice is {_kind(r)}; expected \"Enjoy the run\"."
r = _rerun(temp=25)["advice"]
assert r == "Enjoy the run", f"With temp = 25, advice is {_kind(r)}; 25 is not ABOVE 25, so use > rather than >=."
''')], hints=["if temp > 25:", "Indent the advice = ... lines by 4 spaces."],
wrong=r'''
temp = 31
if temp >= 25:
    advice = "Bring water"
else:
    advice = "Enjoy the run"
'''),
ex("Pace label", r'''
Create `label` from `minutes_per_mile`:
- under 7 gives `"fast"`
- 7 up to (but not including) 10 gives `"steady"`
- 10 or more gives `"easy"`
''', r'''
minutes_per_mile = 9
# label = ___
''', r'''
minutes_per_mile = 9
if minutes_per_mile < 7:        # first check: under 7
    label = "fast"
elif minutes_per_mile < 10:     # only reached if it wasn't under 7
    label = "steady"
else:                           # 10 or more
    label = "easy"
print(label)
''', [("9 gives \"steady\"", r'''
assert label == "steady", f"label is {_kind(label)}; with 9 expected \"steady\"."
'''), ("Edges: 6.5, 7, 10, 12", r'''
for v, exp in [(6.5, "fast"), (7, "steady"), (10, "easy"), (12, "easy")]:
    got = _rerun(minutes_per_mile=v)["label"]
    assert got == exp, f"With minutes_per_mile = {v}, label is {_kind(got)}; expected \"{exp}\"." + (" 7 is not UNDER 7: use < 7." if v == 7 else "")
''')], hints=["Start with if minutes_per_mile < 7:", "Then elif minutes_per_mile < 10:, then else:"],
wrong=r'''
minutes_per_mile = 9
if minutes_per_mile <= 7:
    label = "fast"
elif minutes_per_mile < 10:
    label = "steady"
else:
    label = "easy"
'''),
ex("Order size", r'''
A trade has a `quantity` (how many units). Create `size`:
- `"large"` if quantity is 1000 or more
- `"medium"` if it's 100 or more
- otherwise `"small"`
''', r'''
quantity = 250
# size = ___
''', r'''
quantity = 250
if quantity >= 1000:      # check the biggest case first
    size = "large"        # 1000 or more
elif quantity >= 100:     # only reached if it's under 1000
    size = "medium"       # 100 to 999
else:                     # everything else
    size = "small"        # under 100
print(size)
''', [("250 is \"medium\"", r'''
assert size == "medium", f"size is {_kind(size)}; with 250 expected \"medium\"."
'''), ("1500, 1000, 99 and 5", r'''
for v, exp in [(1500, "large"), (1000, "large"), (100, "medium"), (99, "small"), (5, "small")]:
    got = _rerun(quantity=v)["size"]
    assert got == exp, f"With quantity = {v}, size is {_kind(got)}; expected \"{exp}\"." + (" Python runs only the FIRST true branch: check >= 1000 before >= 100." if v >= 1000 and got == "medium" else "")
''')], hints=["Put the >= 1000 check first.", "elif quantity >= 100:"],
wrong=r'''
quantity = 250
if quantity >= 100:
    size = "medium"
elif quantity >= 1000:
    size = "large"
else:
    size = "small"
'''),
],
"if runs an indented block when its condition is True; elif adds more checks; else catches the rest; only the first True branch runs.")

# ---------------------------------------------------------------- 10
beginner("u0l10", "Lists",
"How to keep many values in one list, get items by position, and add to it.",
[chunk(r'''
A **list** holds several values in order. Write it with square brackets `[ ]` and commas between the items. `len(list)` tells you how many items it has.
''', r'''
runs = [5, 8, 3, 10]
print(runs)
print(len(runs))
'''),
chunk(r'''
Get one item by its position, called its **index**: `runs[0]`.

**Counting starts at 0**, so the first item is `runs[0]` and the second is `runs[1]`. Negative indexes count from the end: `runs[-1]` is the last item.

Asking for a position that doesn't exist, like `runs[10]`, gives an **IndexError**.
''', r'''
runs = [5, 8, 3, 10]
print(runs[0])
print(runs[1])
print(runs[-1])
'''),
chunk(r'''
**Changing a list:**

- `runs[0] = 6` replaces the first item
- `runs.append(7)` adds 7 to the end (`append` is a method of lists)

`sum()`, `min()` and `max()` work on a list of numbers.
''', r'''
runs = [5, 8, 3, 10]
runs[0] = 6
runs.append(7)
print(runs)
print(sum(runs), min(runs), max(runs))
''')],
q("What does this show?", ["green 4", "red 4", "green 3", "blue 4"], 0,
  "Index 1 is the SECOND item (counting starts at 0), and append made the list 4 items long.",
  code=r'''
colors = ["red", "green", "blue"]
colors.append("pink")
print(colors[1], len(colors))
'''),
[
ex("Make a list", r'''
Create a list `snacks` with the text items `"gel"`, `"banana"`, `"chews"`, in that order. Then create `first_snack` by taking the first item **using an index**.
''', r'''
# snacks = [___]
# first_snack = ___
''', r'''
snacks = ["gel", "banana", "chews"]   # square brackets, commas between items
first_snack = snacks[0]               # index 0 is the first item
''', [("snacks has the 3 items in order", r'''
assert snacks == ["gel", "banana", "chews"], f"snacks is {snacks!r}; expected [\"gel\", \"banana\", \"chews\"]."
'''), ("first_snack is \"gel\", taken by index", r'''
assert first_snack == "gel", f"first_snack is {_kind(first_snack)}; expected \"gel\"." + (" Counting starts at 0, so the first item is snacks[0]." if first_snack == "banana" else "")
assert "snacks[0]" in _source.replace(" ", ""), "Take it from the list with snacks[0] rather than typing \"gel\"."
''')], hints=["snacks = [\"gel\", \"banana\", \"chews\"]", "The first item is at index 0."],
wrong=r'''
snacks = ["gel", "banana", "chews"]
first_snack = snacks[1]
'''),
ex("Last, count, biggest", r'''
From `prices`, create:
- `last_price`: the last item, using a **negative index**
- `count`: how many prices there are (use `len`)
- `biggest`: the largest price (use `max`)
''', r'''
prices = [12, 7, 30, 18, 5]
# last_price = ___
# count = ___
# biggest = ___
''', r'''
prices = [12, 7, 30, 18, 5]
last_price = prices[-1]   # -1 counts from the end: 5
count = len(prices)       # 5 items
biggest = max(prices)     # 30
''', [("last_price is 5", r'''
assert last_price == 5, f"last_price is {_kind(last_price)}; expected 5 (the last item)." + (" prices[-2] is second-to-last; use prices[-1]." if last_price == 18 else "")
assert "[-1]" in _source.replace(" ", ""), "Use a negative index: prices[-1]"
'''), ("count is 5", r'''
assert count == 5, f"count is {_kind(count)}; expected 5. Use len(prices)."
'''), ("biggest is 30", r'''
assert biggest == 30, f"biggest is {_kind(biggest)}; expected 30. Use max(prices)."
''')], hints=["prices[-1] is the last item", "len(prices), max(prices)"],
wrong=r'''
prices = [12, 7, 30, 18, 5]
last_price = prices[-2]
count = 4
biggest = max(prices)
'''),
ex("Change and grow a list", r'''
Starting from `miles`:
1. add `10` to the end with `append`
2. change the **first** item to `6`
3. create `total_miles` as the sum of the list

`miles` should end as `[6, 8, 3, 10]` and `total_miles` should be `27`.
''', r'''
miles = [5, 8, 3]
# 1. append 10
# 2. change the first item to 6
# 3. total_miles = ___
''', r'''
miles = [5, 8, 3]
miles.append(10)          # [5, 8, 3, 10]
miles[0] = 6              # replace index 0: [6, 8, 3, 10]
total_miles = sum(miles)  # 6 + 8 + 3 + 10 = 27
''', [("miles is [6, 8, 3, 10]", r'''
assert miles == [6, 8, 3, 10], f"miles is {miles}; expected [6, 8, 3, 10]." + (" The first item is still 5: use miles[0] = 6." if miles and miles[0] == 5 else "")
'''), ("total_miles is 27", r'''
assert total_miles == 27, f"total_miles is {_kind(total_miles)}; expected 27. Work it out after changing the list: sum(miles)."
''')], hints=["miles.append(10)", "miles[0] = 6, then total_miles = sum(miles)"],
wrong=r'''
miles = [5, 8, 3]
miles.append(10)
total_miles = sum(miles)
'''),
],
"A list [a, b, c] keeps items in order; list[0] is the first and list[-1] the last; .append() adds; len, sum, min, max summarize.")

# ---------------------------------------------------------------- 11
beginner("u0l11", "for loops",
"How to repeat code once for every item in a list with a for loop.",
[chunk(r'''
A **loop** repeats code. `for run in runs:` runs the indented block once for each item in the list. Each time round, the variable `run` holds the next item.

The name after `for` is up to you. Pick something that describes one item.
''', r'''
runs = [5, 8, 3]
for run in runs:
    print("Ran", run, "miles")
print("Week done")   # not indented: runs once, after the loop
'''),
chunk(r'''
A very common pattern is the **running total**:

1. before the loop, start a variable at 0
2. inside the loop, add each item to it
3. after the loop, it holds the total

Trace it: `total` goes 0 → 5 → 13 → 16.
''', r'''
miles = [5, 8, 3]
total = 0
for m in miles:
    total = total + m
print(total)
'''),
chunk(r'''
`range(3)` gives the numbers 0, 1, 2, so `for i in range(3):` repeats something 3 times.

Put an `if` inside a loop to count or pick out only some items.
''', r'''
for i in range(3):
    print("Lap", i + 1)

long_runs = 0
for m in [5, 12, 3, 15]:
    if m >= 10:
        long_runs = long_runs + 1
print("Long runs:", long_runs)
''')],
q("What does this show?", ["6", "1 then 3 then 6", "3", "0"], 0,
  "The print isn't indented, so it runs once after the loop, when total has reached 1 + 2 + 3 = 6.",
  code=r'''
total = 0
for n in [1, 2, 3]:
    total = total + n
print(total)
'''),
[
ex("Say hi to everyone", r'''
Use a `for` loop over `names` to show one line per person:
```
Hi Ann
Hi Ben
Hi Cy
```
''', r'''
names = ["Ann", "Ben", "Cy"]
# for ___ in names:
#     print(___)
''', r'''
names = ["Ann", "Ben", "Cy"]
for name in names:        # name is "Ann", then "Ben", then "Cy"
    print("Hi", name)     # indented: runs once per name
''', [("One greeting per name", r'''
assert _out == ["Hi Ann", "Hi Ben", "Hi Cy"], f"Expected Hi Ann / Hi Ben / Hi Cy but got {_out}." + (" You printed the whole list at once; loop over it and print one name each time." if any("[" in l for l in _out) else "")
'''), ("You used a for loop", r'''
assert "for " in _source, "Use a for loop: for name in names:"
''')], hints=["for name in names:", "Inside (indented): print(\"Hi\", name)"],
wrong=r'''
names = ["Ann", "Ben", "Cy"]
print("Hi", names)
'''),
ex("Total with a loop", r'''
Add up `prices` with a `for` loop and a running total in `total`. Don't use `sum` this time: the point is to practise the pattern.
''', r'''
prices = [3, 12, 5, 20]
total = 0
# loop over prices and add each one to total
print(total)
''', r'''
prices = [3, 12, 5, 20]
total = 0                  # start the running total at 0
for p in prices:           # p is each price in turn
    total = total + p      # add it to the total
print(total)               # after the loop: 40
''', [("total is 40", r'''
assert total == 40, f"total is {_kind(total)}; expected 40." + (" That's just the last price: you replaced total each time. Use total = total + p." if total == 20 else "")
'''), ("Done with a for loop, not sum", r'''
assert "for " in _source and "sum(" not in _source, "Use a for loop with total = total + p (no sum)."
''')], hints=["for p in prices:", "Inside: total = total + p"],
wrong=r'''
prices = [3, 12, 5, 20]
total = 0
for p in prices:
    total = p
'''),
ex("Count the big orders", r'''
Create `big_count`: how many numbers in `quantities` are **100 or more**. Use a loop and an `if`.
''', r'''
quantities = [50, 200, 100, 10, 500]
big_count = 0
# loop, and add 1 to big_count when the quantity is 100 or more
print(big_count)
''', r'''
quantities = [50, 200, 100, 10, 500]
big_count = 0
for q in quantities:          # look at each quantity
    if q >= 100:              # "100 or more" means >=
        big_count += 1        # count it
print(big_count)              # 200, 100 and 500, so 3
''', [("big_count is 3", r'''
assert big_count == 3, f"big_count is {_kind(big_count)}; expected 3 (200, 100 and 500)." + (" 100 itself counts: use >= 100." if big_count == 2 else "")
'''), ("Works on another list", r'''
got = _rerun(quantities=[100, 99, 1000])["big_count"]
assert got == 2, f"With quantities = [100, 99, 1000], big_count is {got}; expected 2."
''')], hints=["for q in quantities:", "if q >= 100: big_count += 1"],
wrong=r'''
quantities = [50, 200, 100, 10, 500]
big_count = 0
for q in quantities:
    if q > 100:
        big_count += 1
'''),
],
"for item in list: runs the indented block once per item; start a total at 0 before the loop and add inside it; range(n) repeats n times.")

# ---------------------------------------------------------------- 12
beginner("u0l12", "while loops",
"How to repeat while a condition stays True, and how to avoid a loop that never ends.",
[chunk(r'''
`while condition:` repeats its block **as long as** the condition is True. Use it when you don't know in advance how many times you'll need to repeat.
''', r'''
savings = 0
weeks = 0
while savings < 100:
    savings += 30
    weeks += 1
print(weeks, "weeks, saved", savings)
'''),
chunk(r'''
**Careful:** if the condition never becomes False, the loop runs forever. That's called an **infinite loop**. Always change something inside the loop that eventually makes the condition False. If it happens here, tap **⏹ Stop**.

Which loop to use:

- `for`: once per item in a list
- `while`: until something becomes true
''', r'''
count = 3
while count > 0:
    print(count)
    count -= 1      # without this line, count stays 3 forever
print("Liftoff!")
''')],
q("What does this show?", ["32", "16", "20", "64"], 0,
  "n doubles 1 → 2 → 4 → 8 → 16 → 32. At 32 the condition n < 20 is False, so the loop stops.",
  code=r'''
n = 1
while n < 20:
    n = n * 2
print(n)
'''),
[
ex("Countdown", r'''
Use a `while` loop to show `3`, `2`, `1`, then `Go!` (one per line).
''', r'''
count = 3
# while ___:
#     print(count)
#     ___
print("Go!")
''', r'''
count = 3
while count > 0:      # keep going while count is above 0
    print(count)      # show 3, then 2, then 1
    count -= 1        # count goes down by 1, so the loop ends after 1
print("Go!")          # after the loop
''', [("Shows 3, 2, 1, Go!", r'''
assert _out == ["3", "2", "1", "Go!"], f"Expected 3 / 2 / 1 / Go! but got {_out}." + (" 0 was shown too: loop while count > 0, not >= 0." if "0" in _out else "")
'''), ("You used a while loop", r'''
assert "while " in _source, "Use a while loop for this one."
''')], hints=["while count > 0:", "Inside: print(count), then count -= 1"],
wrong=r'''
count = 3
while count >= 0:
    print(count)
    count -= 1
print("Go!")
'''),
ex("Weeks to reach a goal", r'''
You save `weekly` dollars each week, starting from 0. Create `weeks`: how many weeks until `savings` reaches **at least** `goal`. Use a `while` loop.
''', r'''
savings = 0
weekly = 45
goal = 200
weeks = 0
# while ___:
print(weeks)
''', r'''
savings = 0
weekly = 45
goal = 200
weeks = 0
while savings < goal:      # not there yet?
    savings += weekly      # save another week
    weeks += 1             # count that week
print(weeks)               # 45, 90, 135, 180, 225: 5 weeks
''', [("5 weeks at $45", r'''
assert weeks == 5, f"weeks is {_kind(weeks)}; expected 5 (45, 90, 135, 180, 225)."
'''), ("Stops as soon as the goal is reached", r'''
got = _rerun(weekly=50)["weeks"]
assert got == 4, f"With weekly = 50, weeks is {got}; expected 4 (50, 100, 150, 200 reaches the goal). Loop while savings < goal."
''')], hints=["while savings < goal:", "Inside: savings += weekly, weeks += 1"],
wrong=r'''
savings = 0
weekly = 45
goal = 200
weeks = 0
while savings <= goal:
    savings += weekly
    weeks += 1
'''),
],
"while condition: repeats until the condition is False, so make sure something inside the loop changes it (⏹ Stop rescues you).")

# ---------------------------------------------------------------- 13
beginner("u0l13", "Dictionaries: look things up by name",
"How to store and look up values by name with a dictionary (key → value).",
[chunk(r'''
A **dictionary** (`dict`) stores pairs: a **key** and its **value**. It works like a contacts list: look up a name (the key) to get the number (the value).

Write it with curly braces `{ }`, as `key: value` pairs separated by commas. Look a value up with square brackets and the key.
''', r'''
ages = {"Ann": 31, "Ben": 28}
print(ages["Ann"])
print(len(ages))     # number of pairs
'''),
chunk(r'''
- **Add or change:** `d[key] = value`
- **Check a key exists:** `key in d` gives True or False
- **Missing key:** `d[key]` with a key that isn't there gives a **KeyError**. `d.get(key, default)` gives the default instead.
''', r'''
stock = {"gel": 10, "chews": 4}
stock["banana"] = 6        # add a new pair
stock["gel"] = 8           # change an existing value
print(stock)
print("tea" in stock)
print(stock.get("tea", 0))
'''),
chunk(r'''
To loop over every pair, use `.items()`. `for name, qty in stock.items():` gives you two variables each time round: the key and its value.
''', r'''
stock = {"gel": 8, "chews": 4, "banana": 6}
for name, qty in stock.items():
    print(name, "->", qty)
''')],
q("What does this show?", ["4 2", "3 2", "4 1", "5 2"], 0,
  "apples changes from 3 to 4, and pears is added, so there are 2 pairs.",
  code=r'''
stock = {"apples": 3}
stock["pears"] = 5
stock["apples"] = stock["apples"] + 1
print(stock["apples"], len(stock))
'''),
[
ex("Look it up, add one", r'''
1. Create `chews_price` by looking up `"chews"` in `prices`.
2. Add a new pair to `prices`: `"water"` with the value `1.0`.
''', r'''
prices = {"gel": 2.5, "banana": 0.5, "chews": 3.0}
# chews_price = ___
# add "water"
''', r'''
prices = {"gel": 2.5, "banana": 0.5, "chews": 3.0}
chews_price = prices["chews"]   # look up the value for the key "chews"
prices["water"] = 1.0           # a new key gets added
''', [("chews_price is 3.0, looked up", r'''
assert chews_price == 3.0, f"chews_price is {_kind(chews_price)}; expected 3.0 (the value for \"chews\")."
assert 'prices["chews"]' in _source or "prices['chews']" in _source or ".get(" in _source, "Look it up from the dict: prices[\"chews\"]"
'''), ("prices now has water: 1.0", r'''
assert prices.get("water") == 1.0, f"prices is {prices}; add the pair with prices[\"water\"] = 1.0"
''')], hints=["prices[\"chews\"]", "prices[\"water\"] = 1.0"],
wrong=r'''
prices = {"gel": 2.5, "banana": 0.5, "chews": 3.0}
chews_price = prices["gel"]
'''),
ex("A safe lookup", r'''
`"tea"` isn't in `prices`. Create `tea_price` using `.get` so that it's `0` when the key is missing (no KeyError).
''', r'''
prices = {"gel": 2.5, "banana": 0.5, "chews": 3.0}
# tea_price = ___
''', r'''
prices = {"gel": 2.5, "banana": 0.5, "chews": 3.0}
tea_price = prices.get("tea", 0)   # "tea" is missing, so we get the default 0
''', [("tea_price is 0", r'''
assert tea_price == 0 and tea_price is not None, f"tea_price is {_kind(tea_price)}; expected 0. Give .get a default: prices.get(\"tea\", 0)"
'''), ("Uses .get", r'''
assert ".get(" in _source, "Use prices.get(\"tea\", 0)"
''')], hints=["prices.get(\"tea\", 0)"],
wrong=r'''
prices = {"gel": 2.5, "banana": 0.5, "chews": 3.0}
tea_price = prices.get("tea")
'''),
ex("Count the words", r'''
Build a dict `counts` saying how many times each word appears in `words`, e.g. `{"buy": 3, ...}`. Loop over the words; for each word do:

`counts[w] = counts.get(w, 0) + 1`
''', r'''
words = ["buy", "sell", "buy", "buy", "sell", "hold"]
counts = {}
# loop over words
print(counts)
''', r'''
words = ["buy", "sell", "buy", "buy", "sell", "hold"]
counts = {}                              # start with an empty dict
for w in words:                          # each word in turn
    counts[w] = counts.get(w, 0) + 1     # old count (0 if new) plus 1
print(counts)                            # {'buy': 3, 'sell': 2, 'hold': 1}
''', [("buy 3, sell 2, hold 1", r'''
assert counts == {"buy": 3, "sell": 2, "hold": 1}, f"counts is {counts}; expected {{'buy': 3, 'sell': 2, 'hold': 1}}." + (" Every count is 1: add to the old count with counts.get(w, 0) + 1." if counts and set(counts.values()) == {1} else "")
''')], hints=["for w in words:", "counts[w] = counts.get(w, 0) + 1"],
wrong=r'''
words = ["buy", "sell", "buy", "buy", "sell", "hold"]
counts = {}
for w in words:
    counts[w] = 1
'''),
],
"A dict {key: value} looks values up by key: d[key] reads, d[key] = v adds or changes, d.get(key, default) avoids KeyError, .items() loops pairs.")

# ---------------------------------------------------------------- 14
beginner("u0l14", "Writing your own functions",
"How to write your own function with def, give it inputs (parameters) and send back an answer with return.",
[chunk(r'''
You've already used functions: `print()`, `len()`, `round()`. A **function** is a named, reusable recipe. Make your own with `def`: the name, parentheses, a colon, then an indented body.

**Defining** a function doesn't run it. **Calling** it (its name followed by parentheses) does, as many times as you like.
''', r'''
def cheer():
    print("You've got this!")

cheer()
cheer()
'''),
chunk(r'''
**Parameters** are the function's inputs: variable names inside the parentheses. They get their values when you call the function. The value you pass in (like `"Ann"`) is called an **argument**.
''', r'''
def greet(name):
    print(f"Hello, {name}!")

greet("Ann")
greet("Ben")
'''),
chunk(r'''
`return` sends an answer back to the place where the function was called, so you can store it or use it in more math. `print` only shows a value on screen.

As soon as `return` runs, the function stops. A function without `return` gives back `None`, Python's word for "nothing".
''', r'''
def total_cost(price, quantity):
    return price * quantity

bill = total_cost(4, 6)
print(bill)
print(total_cost(2, 3) + 1)
''')],
q("What does this show?", ["8", "6", "62", "None"], 0,
  "double(3) returns 6 and double(1) returns 2; 6 + 2 = 8.",
  code=r'''
def double(n):
    return n * 2

print(double(3) + double(1))
'''),
[
ex("square(n)", r'''
Write a function `square(n)` that **returns** `n` times `n`. For example, `square(3)` should give `9`.
''', r'''
# def square(n):
#     return ___
''', r'''
def square(n):        # n is the input
    return n * n      # send the answer back

print(square(3))      # 9
''', [("square(3) is 9", r'''
r = square(3)
assert r is not None, "square(3) gave back None. Use return n * n, not print."
assert r == 9, f"square(3) returned {_kind(r)}; expected 9."
'''), ("square(10) is 100", r'''
assert square(10) == 100, f"square(10) returned {_kind(square(10))}; expected 100. Use the parameter n, not a fixed number."
''')], hints=["def square(n):", "Indented: return n * n"],
wrong=r'''
def square(n):
    print(n * n)
'''),
ex("full_name(first, last)", r'''
Write `full_name(first, last)` that returns the first name, a space, then the last name. `full_name("Ada", "Lovelace")` should return `"Ada Lovelace"`.
''', r'''
# def full_name(first, last):
''', r'''
def full_name(first, last):      # two parameters
    return first + " " + last    # join with a space between

print(full_name("Ada", "Lovelace"))
''', [("full_name(\"Ada\", \"Lovelace\")", r'''
r = full_name("Ada", "Lovelace")
assert r == "Ada Lovelace", f"Returned {_kind(r)}; expected \"Ada Lovelace\"." + (" Missing the space in the middle." if r == "AdaLovelace" else "")
'''), ("Works for other names", r'''
assert full_name("Grace", "Hopper") == "Grace Hopper", "Use the parameters first and last rather than fixed names."
''')], hints=["return first + \" \" + last"],
wrong=r'''
def full_name(first, last):
    return first + last
'''),
ex("pace(minutes, miles)", r'''
Write `pace(minutes, miles)` that returns minutes per mile, rounded to 2 decimal places. `pace(45, 5)` gives `9.0` and `pace(50, 6)` gives `8.33`.
''', r'''
# def pace(minutes, miles):
''', r'''
def pace(minutes, miles):              # two inputs
    return round(minutes / miles, 2)   # minutes divided by miles, rounded to 2 places

print(pace(50, 6))                     # 8.33
''', [("pace(45, 5) is 9.0", r'''
r = pace(45, 5)
assert r is not None, "pace gave back None: add a return."
assert _close(r, 9.0), f"pace(45, 5) returned {_kind(r)}; expected 9.0." + (" Looks upside down: divide minutes by miles." if _close(r, 0.11) else "")
'''), ("pace(50, 6) is 8.33", r'''
r = pace(50, 6)
assert r == 8.33, f"pace(50, 6) returned {_kind(r)}; expected 8.33. Use round(..., 2)."
''')], hints=["minutes / miles", "return round(minutes / miles, 2)"],
wrong=r'''
def pace(minutes, miles):
    return round(miles / minutes, 2)
'''),
ex("order_side(quantity)", r'''
On a trading desk a positive quantity means buying and a negative one means selling. Write `order_side(quantity)` that returns:
- `"BUY"` if quantity is above 0
- `"SELL"` if it's below 0
- `"NONE"` if it's exactly 0
''', r'''
# def order_side(quantity):
''', r'''
def order_side(quantity):   # one input: the quantity
    if quantity > 0:        # positive: buying
        return "BUY"        # return ends the function here
    elif quantity < 0:      # negative: selling
        return "SELL"
    else:                   # exactly zero
        return "NONE"

print(order_side(-5))
''', [("BUY and SELL", r'''
assert order_side(10) == "BUY", f"order_side(10) returned {_kind(order_side(10))}; expected \"BUY\"."
assert order_side(-5) == "SELL", f"order_side(-5) returned {_kind(order_side(-5))}; expected \"SELL\"."
'''), ("Zero gives NONE", r'''
r = order_side(0)
assert r == "NONE", f"order_side(0) returned {_kind(r)}; expected \"NONE\". Add a branch for exactly 0."
''')], hints=["if quantity > 0: return \"BUY\"", "elif quantity < 0: ..., else: return \"NONE\""],
wrong=r'''
def order_side(quantity):
    if quantity > 0:
        return "BUY"
    else:
        return "SELL"
'''),
],
"def name(parameters): defines a reusable recipe; calling it runs it; return sends the answer back (print only shows it).")

# ---------------------------------------------------------------- 15
beginner("u0l15", "Putting it together: a mini-project",
"How to combine variables, lists, dicts, loops, if and functions into one small program.",
[chunk(r'''
Real programs are just the pieces you've learned, combined. The plan for any small program:

1. **Data:** what do I have? (a list, a dict…)
2. **Steps:** what do I do to each item? (a loop, an if)
3. **Answer:** what do I give back? (return a number, text or dict)

A dict is a handy way to return several answers at once.
''', r'''
def week_stats(miles):
    total = 0
    for m in miles:
        total = total + m
    return {"total": total, "runs": len(miles)}

stats = week_stats([5, 8, 3])
print(stats)
print(stats["total"])
'''),
chunk(r'''
A list can hold dicts. That's a common way to store records, such as trades: each trade is a dict, and the list holds all of them.

- `trades[0]` is the first trade (a dict)
- `trades[0]["qty"]` is that trade's quantity

Here **qty** is short for quantity, and **side** says whether it's a buy or a sell.
''', r'''
trades = [
    {"side": "BUY", "qty": 10},
    {"side": "SELL", "qty": 4},
]
print(trades[0])
print(trades[0]["qty"])
for t in trades:
    print(t["side"], t["qty"])
''')],
q("What does this show?", ["4", "BUY", "10", "SELL"], 0,
  "trades[1] is the SECOND dict (index 1), and its \"qty\" value is 4.",
  code=r'''
trades = [{"side": "BUY", "qty": 10}, {"side": "SELL", "qty": 4}]
print(trades[1]["qty"])
'''),
[
ex("summarize(miles)", r'''
Write `summarize(miles)` that takes a list of numbers and **returns a dict** with three keys:
- `"total"`: the sum
- `"longest"`: the biggest number
- `"average"`: total divided by how many numbers there are, rounded to 1 decimal place

`summarize([5, 8, 3, 10])` should return `{"total": 26, "longest": 10, "average": 6.5}`.
''', r'''
def summarize(miles):
    # work out total, longest and average
    # return {"total": ___, "longest": ___, "average": ___}
    pass   # "pass" means "do nothing yet": replace it with your code
''', r'''
def summarize(miles):
    total = sum(miles)                         # add them all up
    longest = max(miles)                       # biggest value
    average = round(total / len(miles), 1)     # total ÷ how many, 1 decimal place
    return {"total": total, "longest": longest, "average": average}   # three answers in one dict

print(summarize([5, 8, 3, 10]))
''', [("summarize([5, 8, 3, 10])", r'''
r = summarize([5, 8, 3, 10])
assert isinstance(r, dict), f"summarize returned {_kind(r)}; expected a dict like {{\"total\": 26, ...}}. Remember to return it."
assert r.get("total") == 26, f"\"total\" is {r.get('total')}; expected 26."
assert r.get("longest") == 10, f"\"longest\" is {r.get('longest')}; expected 10."
assert r.get("average") == 6.5, f"\"average\" is {r.get('average')}; expected 6.5 (26 ÷ 4)."
'''), ("Rounds the average to 1 decimal", r'''
r = summarize([5, 5, 6])
assert r.get("average") == 5.3, f"For [5, 5, 6] the average is {r.get('average')}; expected 5.3 (16 ÷ 3 = 5.333…, rounded to 1 place)."
''')], hints=["sum(miles), max(miles), len(miles)", "round(total / len(miles), 1)"],
wrong=r'''
def summarize(miles):
    total = sum(miles)
    return {"total": total, "longest": max(miles), "average": total / len(miles)}
'''),
ex("net_quantity(trades)", r'''
Write `net_quantity(trades)`. For each trade, a `"BUY"` **adds** its `"qty"` and a `"SELL"` **subtracts** it. Return the result.

For the trades below the answer is 10 − 4 + 6 − 2 = **10**.
''', r'''
trades = [
    {"side": "BUY", "qty": 10},
    {"side": "SELL", "qty": 4},
    {"side": "BUY", "qty": 6},
    {"side": "SELL", "qty": 2},
]

def net_quantity(trades):
    net = 0
    # loop over the trades: add for BUY, subtract for SELL
    return net

print(net_quantity(trades))
''', r'''
trades = [
    {"side": "BUY", "qty": 10},
    {"side": "SELL", "qty": 4},
    {"side": "BUY", "qty": 6},
    {"side": "SELL", "qty": 2},
]

def net_quantity(trades):
    net = 0                          # running total
    for t in trades:                 # t is one trade (a dict)
        if t["side"] == "BUY":       # buying adds
            net = net + t["qty"]
        else:                        # selling subtracts
            net = net - t["qty"]
    return net                       # after the loop: 10

print(net_quantity(trades))
''', [("The example gives 10", r'''
r = net_quantity(trades)
assert r == 10, f"net_quantity returned {_kind(r)}; expected 10." + (" That's every qty added up: subtract the SELLs." if r == 22 else "")
'''), ("Works on other trades", r'''
r = net_quantity([{"side": "SELL", "qty": 5}, {"side": "BUY", "qty": 1}])
assert r == -4, f"For SELL 5 then BUY 1 it returned {r}; expected -4."
assert net_quantity([]) == 0, "With no trades the answer should be 0."
''')], hints=["for t in trades:", "if t[\"side\"] == \"BUY\": net = net + t[\"qty\"]  else: subtract"],
wrong=r'''
trades = []
def net_quantity(trades):
    net = 0
    for t in trades:
        net = net + t["qty"]
    return net
'''),
ex("report(trades)", r'''
Write `report(trades)` that returns a one-line summary like:

`4 trades, net quantity 10`

Use `len` for the number of trades, and call your `net_quantity` (it's provided below) for the net.
''', r'''
def net_quantity(trades):
    net = 0
    for t in trades:
        if t["side"] == "BUY":
            net = net + t["qty"]
        else:
            net = net - t["qty"]
    return net

def report(trades):
    # return an f-string using len(trades) and net_quantity(trades)
    pass   # replace this line

trades = [{"side": "BUY", "qty": 10}, {"side": "SELL", "qty": 4}, {"side": "BUY", "qty": 6}, {"side": "SELL", "qty": 2}]
print(report(trades))
''', r'''
# net_quantity was given (it's your function from the last exercise)
def net_quantity(trades):
    net = 0                        # running total
    for t in trades:               # each trade dict
        if t["side"] == "BUY":     # buys add
            net = net + t["qty"]
        else:                      # sells subtract
            net = net - t["qty"]
    return net                     # the net quantity

def report(trades):                     # your new function
    count = len(trades)                 # how many trades (4)
    net = net_quantity(trades)          # one function can call another (10)
    return f"{count} trades, net quantity {net}"   # build and return the line

trades = [{"side": "BUY", "qty": 10}, {"side": "SELL", "qty": 4}, {"side": "BUY", "qty": 6}, {"side": "SELL", "qty": 2}]
print(report(trades))                   # 4 trades, net quantity 10
''', [("The example line", r'''
r = report(trades)
assert r is not None, "report gave back None. Return the text (don't print it)."
assert r == "4 trades, net quantity 10", f"report returned {_kind(r)}; expected \"4 trades, net quantity 10\"."
'''), ("Works on other trades", r'''
r = report([{"side": "SELL", "qty": 3}])
assert r == "1 trades, net quantity -3", f"For one SELL of 3 it returned {_kind(r)}; expected \"1 trades, net quantity -3\". Use len(trades) and net_quantity(trades), not fixed numbers."
''')], hints=["return f\"{len(trades)} trades, net quantity {net_quantity(trades)}\""],
wrong=r'''
def report(trades):
    print(f"{len(trades)} trades, net quantity 10")
'''),
],
"A program is data + steps + an answer: loop over a list (of numbers or dicts), decide with if, and return the result from a function.", minutes=15)
