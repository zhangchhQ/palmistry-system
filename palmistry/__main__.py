import argparse
import json
import sys

from .engine import analyze, knowledge, lookup
from .iching import all_hexagrams, cast, compose, element_relation, palm_analogy
from .render import render
from .forms import get_form


def main(argv=None):
    parser = argparse.ArgumentParser(description="观掌：观察、规则组合与易学基础；默认不存资料")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("analyze", help="从stdin或明确给定JSON读取观察；不直接识别像素")
    p.add_argument("input", nargs="?", default="-")
    p.add_argument("--format", choices=["json", "text"], default="text")
    p.add_argument("--audit", action="store_true")
    p = sub.add_parser("lookup")
    p.add_argument("term")
    p.add_argument("--context")
    p = sub.add_parser("form", help="查整书图例的中性形态定义")
    p.add_argument("identifier")
    p = sub.add_parser("hexagram")
    p.add_argument("--lower", required=True)
    p.add_argument("--upper", required=True)
    p = sub.add_parser("cast")
    p.add_argument("values", nargs=6, type=int)
    p = sub.add_parser("analogy")
    p.add_argument("line", choices=["life", "head", "heart", "fate", "sun"])
    p.add_argument("--variant", choices=["观", "晋"])
    p = sub.add_parser("elements")
    p.add_argument("a")
    p.add_argument("b")
    sub.add_parser("catalog")
    sub.add_parser("hexagrams")
    args = parser.parse_args(argv)
    try:
        if args.command == "analyze":
            if args.input == "-":
                payload = json.load(sys.stdin)
            else:
                with open(args.input, encoding="utf-8") as handle:
                    payload = json.load(handle)
            result = analyze(payload)
            print(render(result, args.audit) if args.format == "text" else json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command == "lookup":
            result = lookup(args.term, args.context)
        elif args.command == "form":
            result = get_form(args.identifier)
        elif args.command == "hexagram":
            result = compose(args.lower, args.upper)
        elif args.command == "cast":
            result = cast(args.values)
        elif args.command == "analogy":
            result = palm_analogy(args.line, args.variant)
        elif args.command == "elements":
            result = {"from": args.a, "to": args.b, "relation": element_relation(args.a, args.b)}
        elif args.command == "catalog":
            result = knowledge()
        else:
            result = all_hexagrams()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, TypeError, OSError) as error:
        print(f"输入未通过：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
