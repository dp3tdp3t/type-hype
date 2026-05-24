"""
Curated Python snippets for the "Python (code)" typing source.

Hand-written, no external dependencies, no licensing concerns. Each
snippet is short enough to type in 30s-2m and demonstrates a common
Python pattern. All use 4-space indentation (PEP-8) and ASCII-only
characters so they render cleanly in the test screen.

To add more: append a dict with "title" and "code". Keep snippets
under ~500 chars for a good typing experience; very long snippets
discourage completion in shorter test durations.
"""

PYTHON_SNIPPETS = [
    {
        "title": "bubble sort",
        "code": (
            "def bubble_sort(items):\n"
            "    n = len(items)\n"
            "    for i in range(n):\n"
            "        for j in range(n - i - 1):\n"
            "            if items[j] > items[j + 1]:\n"
            "                items[j], items[j + 1] = items[j + 1], items[j]\n"
            "    return items"
        ),
    },
    {
        "title": "binary search",
        "code": (
            "def binary_search(arr, target):\n"
            "    lo, hi = 0, len(arr) - 1\n"
            "    while lo <= hi:\n"
            "        mid = (lo + hi) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        if arr[mid] < target:\n"
            "            lo = mid + 1\n"
            "        else:\n"
            "            hi = mid - 1\n"
            "    return -1"
        ),
    },
    {
        "title": "fibonacci (iterative)",
        "code": (
            "def fibonacci(n):\n"
            "    a, b = 0, 1\n"
            "    for _ in range(n):\n"
            "        a, b = b, a + b\n"
            "    return a"
        ),
    },
    {
        "title": "factorial (recursive)",
        "code": (
            "def factorial(n):\n"
            "    if n <= 1:\n"
            "        return 1\n"
            "    return n * factorial(n - 1)"
        ),
    },
    {
        "title": "fizzbuzz",
        "code": (
            "def fizzbuzz(n):\n"
            "    for i in range(1, n + 1):\n"
            "        if i % 15 == 0:\n"
            "            print('FizzBuzz')\n"
            "        elif i % 3 == 0:\n"
            "            print('Fizz')\n"
            "        elif i % 5 == 0:\n"
            "            print('Buzz')\n"
            "        else:\n"
            "            print(i)"
        ),
    },
    {
        "title": "is palindrome",
        "code": (
            "def is_palindrome(text):\n"
            "    cleaned = ''.join(c.lower() for c in text if c.isalnum())\n"
            "    return cleaned == cleaned[::-1]"
        ),
    },
    {
        "title": "reverse a string",
        "code": (
            "def reverse_string(text):\n"
            "    chars = list(text)\n"
            "    lo, hi = 0, len(chars) - 1\n"
            "    while lo < hi:\n"
            "        chars[lo], chars[hi] = chars[hi], chars[lo]\n"
            "        lo += 1\n"
            "        hi -= 1\n"
            "    return ''.join(chars)"
        ),
    },
    {
        "title": "linked list node",
        "code": (
            "class Node:\n"
            "    def __init__(self, value, next=None):\n"
            "        self.value = value\n"
            "        self.next = next\n"
            "\n"
            "    def __repr__(self):\n"
            "        return f'Node({self.value!r})'"
        ),
    },
    {
        "title": "stack",
        "code": (
            "class Stack:\n"
            "    def __init__(self):\n"
            "        self._items = []\n"
            "\n"
            "    def push(self, value):\n"
            "        self._items.append(value)\n"
            "\n"
            "    def pop(self):\n"
            "        return self._items.pop()\n"
            "\n"
            "    def peek(self):\n"
            "        return self._items[-1]\n"
            "\n"
            "    def __len__(self):\n"
            "        return len(self._items)"
        ),
    },
    {
        "title": "list comprehension",
        "code": (
            "numbers = range(1, 21)\n"
            "squares = [n * n for n in numbers if n % 2 == 0]\n"
            "pairs = [(x, y) for x in range(3) for y in range(3) if x != y]\n"
            "print(squares)\n"
            "print(pairs)"
        ),
    },
    {
        "title": "dict comprehension",
        "code": (
            "words = ['apple', 'banana', 'cherry', 'date']\n"
            "lengths = {w: len(w) for w in words}\n"
            "by_first = {w[0]: w for w in words}\n"
            "print(lengths)\n"
            "print(by_first)"
        ),
    },
    {
        "title": "generator",
        "code": (
            "def countdown(start):\n"
            "    while start > 0:\n"
            "        yield start\n"
            "        start -= 1\n"
            "\n"
            "for n in countdown(5):\n"
            "    print(n)"
        ),
    },
    {
        "title": "decorator",
        "code": (
            "def memoize(fn):\n"
            "    cache = {}\n"
            "    def wrapper(*args):\n"
            "        if args not in cache:\n"
            "            cache[args] = fn(*args)\n"
            "        return cache[args]\n"
            "    return wrapper\n"
            "\n"
            "@memoize\n"
            "def slow_square(n):\n"
            "    return n * n"
        ),
    },
    {
        "title": "context manager",
        "code": (
            "from contextlib import contextmanager\n"
            "\n"
            "@contextmanager\n"
            "def timed(label):\n"
            "    import time\n"
            "    start = time.time()\n"
            "    try:\n"
            "        yield\n"
            "    finally:\n"
            "        print(f'{label}: {time.time() - start:.3f}s')"
        ),
    },
    {
        "title": "read file lines",
        "code": (
            "def read_lines(path):\n"
            "    with open(path, 'r', encoding='utf-8') as f:\n"
            "        return [line.rstrip('\\n') for line in f]"
        ),
    },
    {
        "title": "counter from collections",
        "code": (
            "from collections import Counter\n"
            "\n"
            "def most_common_words(text, n=5):\n"
            "    words = text.lower().split()\n"
            "    return Counter(words).most_common(n)"
        ),
    },
    {
        "title": "defaultdict grouping",
        "code": (
            "from collections import defaultdict\n"
            "\n"
            "def group_by_first_letter(words):\n"
            "    groups = defaultdict(list)\n"
            "    for word in words:\n"
            "        groups[word[0]].append(word)\n"
            "    return dict(groups)"
        ),
    },
    {
        "title": "sorted with key",
        "code": (
            "people = [\n"
            "    {'name': 'Alice', 'age': 30},\n"
            "    {'name': 'Bob', 'age': 25},\n"
            "    {'name': 'Carol', 'age': 35},\n"
            "]\n"
            "by_age = sorted(people, key=lambda p: p['age'])\n"
            "by_name = sorted(people, key=lambda p: p['name'])"
        ),
    },
    {
        "title": "map and filter",
        "code": (
            "numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]\n"
            "evens = list(filter(lambda n: n % 2 == 0, numbers))\n"
            "squared = list(map(lambda n: n * n, evens))\n"
            "print(squared)"
        ),
    },
    {
        "title": "try and raise",
        "code": (
            "class ValidationError(Exception):\n"
            "    pass\n"
            "\n"
            "def divide(a, b):\n"
            "    if b == 0:\n"
            "        raise ValidationError('division by zero')\n"
            "    try:\n"
            "        return a / b\n"
            "    except TypeError as e:\n"
            "        raise ValidationError(str(e)) from e"
        ),
    },
    {
        "title": "dataclass-like repr",
        "code": (
            "class Point:\n"
            "    def __init__(self, x, y):\n"
            "        self.x = x\n"
            "        self.y = y\n"
            "\n"
            "    def __repr__(self):\n"
            "        return f'Point(x={self.x}, y={self.y})'\n"
            "\n"
            "    def __eq__(self, other):\n"
            "        return (self.x, self.y) == (other.x, other.y)"
        ),
    },
    {
        "title": "property",
        "code": (
            "class Circle:\n"
            "    def __init__(self, radius):\n"
            "        self._radius = radius\n"
            "\n"
            "    @property\n"
            "    def radius(self):\n"
            "        return self._radius\n"
            "\n"
            "    @radius.setter\n"
            "    def radius(self, value):\n"
            "        if value < 0:\n"
            "            raise ValueError('negative radius')\n"
            "        self._radius = value"
        ),
    },
    {
        "title": "static and class methods",
        "code": (
            "class Counter:\n"
            "    count = 0\n"
            "\n"
            "    @classmethod\n"
            "    def increment(cls):\n"
            "        cls.count += 1\n"
            "        return cls.count\n"
            "\n"
            "    @staticmethod\n"
            "    def reset():\n"
            "        Counter.count = 0"
        ),
    },
    {
        "title": "regex match",
        "code": (
            "import re\n"
            "\n"
            "EMAIL_RE = re.compile(r'^[\\w.+-]+@[\\w-]+\\.[\\w.-]+$')\n"
            "\n"
            "def is_valid_email(text):\n"
            "    return bool(EMAIL_RE.match(text))"
        ),
    },
    {
        "title": "walk directory",
        "code": (
            "import os\n"
            "\n"
            "def find_python_files(root):\n"
            "    found = []\n"
            "    for dirpath, _, filenames in os.walk(root):\n"
            "        for name in filenames:\n"
            "            if name.endswith('.py'):\n"
            "                found.append(os.path.join(dirpath, name))\n"
            "    return found"
        ),
    },
    {
        "title": "merge two sorted lists",
        "code": (
            "def merge(a, b):\n"
            "    result = []\n"
            "    i = j = 0\n"
            "    while i < len(a) and j < len(b):\n"
            "        if a[i] <= b[j]:\n"
            "            result.append(a[i])\n"
            "            i += 1\n"
            "        else:\n"
            "            result.append(b[j])\n"
            "            j += 1\n"
            "    result.extend(a[i:])\n"
            "    result.extend(b[j:])\n"
            "    return result"
        ),
    },
    {
        "title": "json round trip",
        "code": (
            "import json\n"
            "\n"
            "def save_config(path, data):\n"
            "    with open(path, 'w', encoding='utf-8') as f:\n"
            "        json.dump(data, f, indent=2)\n"
            "\n"
            "def load_config(path):\n"
            "    with open(path, 'r', encoding='utf-8') as f:\n"
            "        return json.load(f)"
        ),
    },
    {
        "title": "two-pointer pair sum",
        "code": (
            "def two_sum(nums, target):\n"
            "    seen = {}\n"
            "    for i, n in enumerate(nums):\n"
            "        complement = target - n\n"
            "        if complement in seen:\n"
            "            return (seen[complement], i)\n"
            "        seen[n] = i\n"
            "    return None"
        ),
    },
]
