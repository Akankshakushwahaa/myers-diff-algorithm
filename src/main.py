import sys
from array import array


def read_lines(filename):
    try:
        with open(filename, "rb") as file:
            data = file.read()
    except OSError:
        print(f"Error: cannot read {filename}", file=sys.stderr)
        sys.exit(2)

    lines = data.split(b"\n")

    if lines and lines[-1] == b"":
        lines.pop()

    return lines


def myers_diff(a, b):
    n = len(a)
    m = len(b)

    # Nothing to compare.
    if n == 0:
        return [("insert", item) for item in b]

    if m == 0:
        return [("delete", item) for item in a]

    # If the two sequences share no elements, the minimal
    # edit script is all deletions followed by all insertions.
    if len(set(a).intersection(b)) == 0:
        operations = []

        for item in a:
            operations.append(("delete", item))

        for item in b:
            operations.append(("insert", item))

        return operations

    max_d = n + m
    offset = max_d

    # V[k] stores the furthest x-coordinate reached
    # on diagonal k.
    v = array("i", [0]) * (2 * max_d + 1)

    # Save only what backtracking needs: before round d, the values
    # of V on diagonals -(d-1), -(d-3), ..., d-1 (the ones of the
    # previous round), stored compactly as 4-byte integers.
    history = [None]

    for d in range(max_d + 1):
        if d > 0:
            history.append(
                v[offset - d + 1:offset + d:2]
            )

        for k in range(-d, d + 1, 2):

            index = k + offset

            if k == -d:
                x = v[index + 1]

            elif k == d:
                x = v[index - 1] + 1

            elif v[index - 1] < v[index + 1]:
                x = v[index + 1]

            else:
                x = v[index - 1] + 1

            y = x - k

            # Follow the matching sequence as far as possible.
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1

            v[index] = x

            if x >= n and y >= m:
                return build_script(history, a, b, d, offset)

    return []


def character_diff(old_text, new_text):
    old_chars = list(old_text)
    new_chars = list(new_text)

    return myers_diff(old_chars, new_chars)


def make_ranges(operations, side):
    ranges = []

    old_position = 0
    new_position = 0

    for operation, char in operations:

        if operation == "keep":
            old_position += 1
            new_position += 1

        elif operation == "delete":
            if side == "delete":
                start = old_position

                if ranges and ranges[-1][1] == start:
                    ranges[-1] = (ranges[-1][0], old_position + 1)
                else:
                    ranges.append((start, old_position + 1))

            old_position += 1

        elif operation == "insert":
            if side == "insert":
                start = new_position

                if ranges and ranges[-1][1] == start:
                    ranges[-1] = (ranges[-1][0], new_position + 1)
                else:
                    ranges.append((start, new_position + 1))

            new_position += 1

    if not ranges:
        return "."

    return ",".join(
        f"{start}-{end}" for start, end in ranges
    )


def build_script(history, a, b, d, offset):
    x = len(a)
    y = len(b)

    operations = []

    for current_d in range(d, 0, -1):

        snapshot = history[current_d]
        base = current_d - 1

        k = x - y

        # snapshot[(diagonal + base) // 2] is V[diagonal] before round d.
        if k == -current_d:
            previous_k = k + 1

        elif k == current_d:
            previous_k = k - 1

        elif (snapshot[(k - 1 + base) // 2]
              < snapshot[(k + 1 + base) // 2]):
            previous_k = k + 1

        else:
            previous_k = k - 1

        previous_x = snapshot[(previous_k + base) // 2]
        previous_y = previous_x - previous_k

        # Follow the matching sequence backwards.
        while x > previous_x and y > previous_y:
            operations.append(("keep", a[x - 1]))
            x -= 1
            y -= 1

        if previous_k == k + 1:
            # We came from an insertion.
            operations.append(("insert", b[y - 1]))
            y -= 1

        else:
            # We came from a deletion.
            operations.append(("delete", a[x - 1]))
            x -= 1

    # Remaining matching prefix.
    while x > 0 and y > 0:
        operations.append(("keep", a[x - 1]))
        x -= 1
        y -= 1

    while x > 0:
        operations.append(("delete", a[x - 1]))
        x -= 1

    while y > 0:
        operations.append(("insert", b[y - 1]))
        y -= 1

    operations.reverse()

    return operations


def print_diff(operations, highlight):
    write = sys.stdout.buffer.write
    i = 0

    while i < len(operations):

        # Normal unchanged line.
        if operations[i][0] == "keep":
            write(b" " + operations[i][1] + b"\n")
            i += 1
            continue

        # Collect one complete change block.
        deleted = []
        inserted = []

        while i < len(operations) and operations[i][0] != "keep":
            operation, line = operations[i]

            if operation == "delete":
                deleted.append(line)
            else:
                inserted.append(line)

            i += 1

        # Print all deleted lines first.
        for line in deleted:
            write(b"-" + line + b"\n")

        # Print inserted lines.
        pairs = min(len(deleted), len(inserted))

        for j, line in enumerate(inserted):
            write(b"+" + line + b"\n")

            # Part B: print character ranges for paired lines.
            if highlight and j < pairs:
                old_text = deleted[j].decode("utf-8")
                new_text = line.decode("utf-8")

                char_operations = character_diff(
                    old_text,
                    new_text
                )

                old_ranges = make_ranges(
                    char_operations,
                    "delete"
                )

                new_ranges = make_ranges(
                    char_operations,
                    "insert"
                )

                range_line = (
                    f"? {old_ranges} | {new_ranges}\n"
                )

                write(range_line.encode("utf-8"))


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: python main.py lines|highlight <fileA> <fileB>",
            file=sys.stderr
        )
        sys.exit(2)

    mode = sys.argv[1]

    if mode != "lines" and mode != "highlight":
        print(
            "Usage: python main.py lines|highlight <fileA> <fileB>",
            file=sys.stderr
        )
        sys.exit(2)

    file_a = read_lines(sys.argv[2])
    file_b = read_lines(sys.argv[3])

    operations = myers_diff(file_a, file_b)

    print_diff(
        operations,
        mode == "highlight"
    )


if __name__ == "__main__":
    main()