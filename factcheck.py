import re
import sys
import time

from place import search_place

DEFAULT_FILE = "1.txt"
HEADER_NAMES = {"가게이름", "가게", "상호", "상호명", "이름", "장소", "장소명"}


def _norm(text):
    """비교용: 공백·기호를 빼고 소문자로."""
    return re.sub(r"[\s\-_·.,()]", "", text).lower()


def same_name(given, found):
    """이름이 같은 곳인지: 같거나, 한쪽이 다른 쪽에 들어 있으면(지점·업종이 붙은 이름) 같은 이름으로 본다."""
    a, b = _norm(given), _norm(found)
    return len(a) >= 2 and (a == b or a in b or b in a)


def parse_line(line):
    """'1. 이름 | 주소', '| 이름 | 주소 |' 같은 줄에서 (이름, 주소)를 꺼낸다. 읽을 수 없으면 None."""
    line = line.strip()
    if not line or re.fullmatch(r"[|\s:\-]+", line):  # 빈 줄, | --- | --- | 줄
        return None
    line = re.sub(r"^\d+\s*[.)]\s*", "", line)  # 줄 앞 번호 1. 2)
    cells = [c.strip() for c in line.strip("|").split("|")]
    if len(cells) >= 3 and cells[0].isdigit():  # | 1 | 이름 | 주소 | 표의 번호 칸
        cells = cells[1:]
    if len(cells) < 2 or not cells[0] or not cells[1]:
        return None
    name, address = cells[0], cells[1]
    if _norm(name) in HEADER_NAMES:  # 표 머리글 줄
        return None
    return name, address


ADDRESS_LINE = re.compile(r"^[\s•·\-*]*(?:도로명\s*|지번\s*)?주소\s*[:：]\s*(.+)$")


def parse_lines(lines):
    """한 줄 형식('이름 | 주소')과 두 줄 형식('1. 이름' 다음 줄 '• 도로명 주소: …')을 모두 읽는다."""
    items = []
    pending = None  # 주소 줄을 기다리는 가게 이름
    for line in lines:
        m = ADDRESS_LINE.match(line)
        if m and pending:
            items.append((pending, m.group(1).strip()))
            pending = None
            continue
        item = parse_line(line)
        if item:
            items.append(item)
            pending = None
            continue
        text = re.sub(r"^\d+\s*[.)]\s*", "", line.strip())  # 줄 앞 번호 1. 2)
        pending = text if text and "|" not in text and not m else None
    return items


def address_tokens(address):
    """주소를 단어로 나누고 첫 단어(서울특별시/서울 같은 시·도)는 뺀다."""
    return address.split()[1:]


def neighborhood(address):
    """검색에 붙일 동네: 주소에서 시·도를 뺀 앞 두 단어 (예: '성동구 성수동')."""
    return " ".join(address_tokens(address)[:2])


def address_matches(given, place):
    """주소의 구와 동(길)이 둘 다 맞으면 True. 도로명·지번 주소 중 어느 쪽에든 있으면 된다."""
    want = address_tokens(given)[:2]
    if len(want) < 2:
        return False
    have = set(address_tokens(place["주소"])) | set(address_tokens(place["지번주소"]))
    return all(w in have for w in want)


def judge(name, address):
    """'✅' / '🟡' / '❌' 와 이유를 돌려준다. 실패하면 RuntimeError('⛔ ...')."""
    hood = neighborhood(address)
    candidates = search_place(f"{hood} {name}".strip(), size=15)
    same = [p for p in candidates if same_name(name, p["이름"])]
    if not same:
        # 동네가 틀렸을 수 있으니 가게 이름만으로 한 번 더 찾아, 다른 곳에 있으면 🟡
        time.sleep(0.1)
        same = [p for p in search_place(name, size=15) if same_name(name, p["이름"])]
        if not same:
            return "❌", "못 찾았어요"
        return "🟡", f"카카오: {same[0]['이름']} | {same[0]['주소']}"
    for p in same:
        if address_matches(address, p):
            return "✅", f"{p['이름']} | {p['주소']}"
    return "🟡", f"카카오: {same[0]['이름']} | {same[0]['주소']}"


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FILE
    try:
        with open(path, encoding="utf-8-sig") as f:
            lines = f.read().splitlines()
    except OSError:
        sys.exit(f"{path} 을(를) 열지 못했어요")

    items = parse_lines(lines)
    if not items:
        sys.exit(f"{path} 에 읽을 줄이 없어요 (형식: 가게이름 | 주소)")

    counts = {"✅": 0, "🟡": 0, "❌": 0}
    for i, (name, address) in enumerate(items, 1):
        try:
            mark, note = judge(name, address)
        except RuntimeError as e:
            sys.exit(str(e))  # ⛔ 키·설정·연결 에러는 바로 멈춘다
        counts[mark] += 1
        print(f"{i}. {mark} {name} | {address}  →  {note}")
        time.sleep(0.1)

    total = len(items)
    wrong = counts["🟡"] + counts["❌"]
    print()
    print(f"전체 {total}곳: ✅ {counts['✅']} / 🟡 {counts['🟡']} / ❌ {counts['❌']}")
    print(f"AI 실수율(🟡+❌): {wrong}/{total} = {wrong / total * 100:.0f}%")
    print("판정 기준: 검색어 '동네 이름'으로 15곳까지 찾아, 이름이 같거나 한쪽이 다른 쪽에 포함되는 곳 중 "
          "주소의 구·동(길) 두 단어가 모두 같은 곳이 있으면 ✅ / 이름만 맞으면 🟡 / 이름이 맞는 곳이 없으면 ❌ "
          "(동네 검색에서 못 찾으면 가게 이름만으로 한 번 더 찾아, 다른 곳에 있으면 🟡)")
    print("\n출처: 카카오 로컬 API (키워드로 장소 검색)")
