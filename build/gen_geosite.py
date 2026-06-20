#!/usr/bin/env python3
# Сборка geosite.dat (v2ray/Xray) из текстового списка доменов.
# Без внешних зависимостей — кодирует protobuf вручную.
#
# Использование:
#   python build/gen_geosite.py claude-ai/claude-ai.txt claude-ai/claude-ai.dat CLAUDE
#
# Префиксы в списке (как в Xray):
#   (без префикса) или domain:  -> subdomain-match  (Domain, type=2)
#   full:                       -> точное совпадение (Full, type=3)
#   regexp:                     -> регэксп          (Regex, type=1)
#   keyword:                    -> подстрока        (Plain, type=0)
import sys

def varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)

def tag(field, wire):
    return varint((field << 3) | wire)

def ld(field, data):  # length-delimited
    return tag(field, 2) + varint(len(data)) + data

def domain_msg(value, dtype):
    # Domain { type=1 varint; value=2 string }
    return tag(1, 0) + varint(dtype) + ld(2, value.encode())

PREFIX = {
    "full:": 3, "domain:": 2, "regexp:": 1, "keyword:": 0,
}

def parse_line(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    line = line.split("#", 1)[0].strip()  # inline-комментарий
    if not line:
        return None
    for p, t in PREFIX.items():
        if line.startswith(p):
            return (line[len(p):].strip(), t)
    return (line, 2)  # по умолчанию domain (subdomain-match)

def main():
    src, dst, code = sys.argv[1], sys.argv[2], sys.argv[3].upper()
    domains = bytearray()
    n = 0
    with open(src, encoding="utf-8") as f:
        for line in f:
            r = parse_line(line)
            if r:
                domains += ld(2, domain_msg(r[0], r[1]))  # GeoSite.domain (field 2)
                n += 1
    # GeoSite { country_code=1 string; domain=2 repeated }
    geosite = ld(1, code.encode()) + bytes(domains)
    # GeoSiteList { entry=1 repeated GeoSite }
    geosite_list = ld(1, geosite)
    with open(dst, "wb") as f:
        f.write(geosite_list)
    print(f"OK: {n} доменов -> {dst} (geosite:{code.lower()}), {len(geosite_list)} байт")

if __name__ == "__main__":
    main()
