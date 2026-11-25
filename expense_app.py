"""Member B - Web UI enhancements: Date/Today/Month filter, Category/Keyword search, and CSV export.

Run:  python expense_app.py   then open http://127.0.0.1:8000
"""
import csv
import datetime
import html
import io
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import expense_chart
import expense_trend
from expense_input import delete_expense, load_expenses, parse_amount, parse_date, save_expense

PORT = 8000


def fmt_amount(value):
    v = float(value)
    return f"{v:,.0f}" if v == int(v) else f"{v:,.1f}"


def month_of(expense):
    """'2026-11-14' -> '2026-11'."""
    return expense["date"][:7]


def list_months(expenses):
    return sorted({month_of(e) for e in expenses}, reverse=True)


def list_categories(expenses):
    return sorted({e["category"] for e in expenses if e.get("category")})


def apply_filters(expenses, date="", month="", category="", keyword=""):
    """Filter expenses by exact date or month, category, and keyword (in category or notes)."""
    result = expenses
    if date:
        result = [e for e in result if e["date"] == date]
    elif month:
        result = [e for e in result if month_of(e) == month]

    if category:
        result = [e for e in result if e.get("category") == category]

    kw = keyword.strip().lower()
    if kw:
        result = [
            e for e in result
            if kw in e.get("category", "").lower() or kw in (e.get("notes") or "").lower()
        ]
    return result


CSS = """
:root{--bg:#f4f3ef;--card:#fff;--ink:#0b0b0b;--ink2:#52514e;--line:#e4e3dd;--blue:#2a78d6;--red:#e34948}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.5 -apple-system,"Segoe UI","Noto Sans TC","PingFang TC",sans-serif}
header{padding:28px 32px 8px}h1{margin:0;font-size:26px}header p{margin:2px 0 0;color:var(--ink2)}
main{max-width:1100px;margin:0 auto;padding:12px 24px 40px;display:grid;gap:18px;grid-template-columns:340px 1fr}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px}
.stats{grid-column:1/-1;display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.stat small{color:var(--ink2);text-transform:uppercase;letter-spacing:.06em;font-size:12px}
.stat b{display:block;font-size:28px;margin-top:4px}
h2{margin:0 0 14px;font-size:17px}label{display:block;font-size:13px;color:var(--ink2);margin:12px 0 4px}
input{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:9px;font:inherit}
input:focus{outline:2px solid var(--blue);border-color:transparent}
button{margin-top:18px;width:100%;padding:11px;border:0;border-radius:9px;background:var(--blue);
color:#fff;font:inherit;font-weight:600;cursor:pointer}button:hover{filter:brightness(1.08)}
.err{background:#fdecec;color:#a02424;border-radius:9px;padding:9px 12px;margin-bottom:6px;font-size:14px}
.tabs{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}.tabs a{padding:6px 14px;border-radius:99px;text-decoration:none;
color:var(--ink2);border:1px solid var(--line);font-size:14px}.tabs a.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.chart img{width:100%;height:auto;display:block}.empty{color:var(--ink2);padding:40px 0;text-align:center}
.wide{grid-column:1/-1}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:9px 8px;
border-bottom:1px solid var(--line)}th{font-size:12px;color:var(--ink2);text-transform:uppercase;letter-spacing:.05em}
.filter{margin-bottom:12px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;color:var(--ink2);font-size:14px}
.filter select,.filter input{width:auto;padding:6px 10px;border:1px solid var(--line);border-radius:9px;font:inherit;background:#fff}
.pill-btn{padding:6px 12px;border-radius:9px;text-decoration:none;border:1px solid var(--line);color:var(--ink);background:#fff;font-size:13px;font-weight:500;cursor:pointer;display:inline-block}
.pill-btn.on{background:var(--blue);color:#fff;border-color:var(--blue)}
.pill-btn:hover{filter:brightness(0.96)}
.table-bar{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:12px}
.table-bar h2{margin:0}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
button.del{margin:0;width:auto;padding:4px 12px;background:#fff;color:var(--red);border:1px solid var(--line);font-weight:500}
button.del:hover{background:#fdecec;filter:none}td.act{text-align:right;width:1%}
@media(max-width:820px){main{grid-template-columns:1fr}.stats{grid-template-columns:1fr}}
"""


def render_page(error="", chart="pie", date="", month="", category="", keyword=""):
    all_expenses = load_expenses()
    months = list_months(all_expenses)
    categories = list_categories(all_expenses)
    today_str = datetime.date.today().isoformat()

    # Validate date format if provided; date filter takes precedence over month
    if date:
        try:
            date = parse_date(date)
            month = ""
        except ValueError:
            date = ""
    elif month not in months:
        month = ""

    if category not in categories:
        category = ""

    indexed_filtered = [
        (i, e) for i, e in enumerate(all_expenses)
        if e in apply_filters([e], date=date, month=month, category=category, keyword=keyword)
    ]
    expenses = [e for _, e in indexed_filtered]

    totals = expense_chart.totals_by_category(expenses) if expenses else {}
    total = sum(totals.values())
    top = next(iter(totals), "-")

    if indexed_filtered:
        rows = "".join(
            f"<tr><td>{html.escape(e['date'])}</td><td>{html.escape(e['category'])}</td>"
            f"<td class='n'>{fmt_amount(e['amount'])}</td><td>{html.escape(e.get('notes') or '')}</td>"
            f"<td class='act'><form method='post' action='/delete' onsubmit=\"return confirm('Delete this expense?')\">"
            f"<input type='hidden' name='index' value='{i}'>"
            f"<input type='hidden' name='chart' value='{html.escape(chart)}'>"
            f"<input type='hidden' name='date' value='{html.escape(date)}'>"
            f"<input type='hidden' name='month' value='{html.escape(month)}'>"
            f"<input type='hidden' name='category' value='{html.escape(category)}'>"
            f"<input type='hidden' name='keyword' value='{html.escape(keyword)}'>"
            f"<button class='del'>Delete</button></form></td></tr>"
            for i, e in reversed(indexed_filtered[-30:])
        )
    else:
        empty_msg = f"No expenses recorded on {date}." if date else "No matching expenses found."
        rows = f"<tr><td colspan='5' style='text-align:center;color:var(--ink2);padding:24px'>{empty_msg}</td></tr>"

    err = f"<div class='err'>{html.escape(error)}</div>" if error else ""

    def qs(**overrides):
        params = {
            "chart": chart,
            "date": date,
            "month": month,
            "category": category,
            "keyword": keyword,
        }
        params.update(overrides)
        return urlencode({k: v for k, v in params.items() if v})

    if all_expenses:
        tabs = "".join(
            f"<a href='/?{qs(chart=k)}' class='{'on' if chart == k else ''}'>{n}</a>"
            for k, n in (("pie", "Donut chart"), ("bar", "Bar chart"), ("trend", "Monthly trend"))
        )
        options = "<option value=''>All months</option>" + "".join(
            f"<option value='{m}'{' selected' if m == month else ''}>{m}</option>" for m in months
        )
        all_url = f"/?{qs(date='', month='')}"
        today_url = f"/?{qs(date=today_str, month='')}"
        mode_btns = (
            f"<a href='{all_url}' class='pill-btn {'on' if not date and not month else ''}'>All</a>"
            f"<a href='{today_url}' class='pill-btn {'on' if date == today_str else ''}'>Today</a>"
        )
        picker = (
            f"<div class='filter'>{mode_btns}"
            f"<form method='get' action='/' style='display:inline-flex;align-items:center;gap:6px;margin:0'>"
            f"<input type='hidden' name='chart' value='{html.escape(chart)}'>"
            f"<input type='hidden' name='category' value='{html.escape(category)}'>"
            f"<input type='hidden' name='keyword' value='{html.escape(keyword)}'>"
            f"<span>Date</span> <input type='date' name='date' value='{html.escape(date)}' onchange='this.form.submit()'>"
            f"</form>"
            f"<form method='get' action='/' style='display:inline-flex;align-items:center;gap:6px;margin:0'>"
            f"<input type='hidden' name='chart' value='{html.escape(chart)}'>"
            f"<input type='hidden' name='category' value='{html.escape(category)}'>"
            f"<input type='hidden' name='keyword' value='{html.escape(keyword)}'>"
            f"<span>Month</span> <select name='month' onchange='this.form.submit()'>{options}</select>"
            f"</form></div>"
        )
        if chart == "trend":
            picker = ""

        if expenses or chart == "trend":
            img_qs = urlencode({
                "kind": chart,
                "date": date,
                "month": month,
                "category": category,
                "keyword": keyword,
                "n": len(all_expenses),
            })
            img = f"<img src='/chart.png?{img_qs}' alt='chart'>"
        else:
            img = f"<div class='empty'>{f'No expenses recorded on {date}.' if date else 'No data for current filter.'}</div>"

        chart_html = f"{picker}<div class='tabs'>{tabs}</div>{img}"
    else:
        chart_html = "<div class='empty'>No data yet. Add your first expense on the left.</div>"

    cat_options = "<option value=''>All categories</option>" + "".join(
        f"<option value='{html.escape(c)}'{' selected' if c == category else ''}>{html.escape(c)}</option>"
        for c in categories
    )
    export_url = f"/export.csv?{qs()}"
    reset_url = f"/?{qs(category='', keyword='', date='', month='')}"

    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Expense Tracker</title><style>{CSS}</style>
<header><h1>Expense Tracker</h1><p>Add expenses and see where your money goes.</p></header>
<main>
<section class="stats">
<div class="card stat"><small>Total spent</small><b>{fmt_amount(total)}</b></div>
<div class="card stat"><small>Records</small><b>{len(expenses)}</b></div>
<div class="card stat"><small>Top category</small><b>{html.escape(top)}</b></div></section>
<section class="card"><h2>Add expense</h2>{err}
<form method="post" action="/add">
<label>Date</label><input type="date" name="date" required>
<label>Amount</label><input type="number" name="amount" step="0.1" min="0.1" placeholder="e.g. 120 or 45.5" required>
<label>Category</label><input name="category" list="cats" placeholder="Food, Transport..." required>
<datalist id="cats"><option>Food<option>Transport<option>Shopping<option>Entertainment<option>Education</datalist>
<label>Notes (optional)</label><input name="notes" placeholder="Lunch with friends">
<button>Add expense</button></form>
<script>document.querySelector('form[action="/add"] input[type=date]').valueAsDate=new Date()</script></section>
<section class="card chart"><h2>Spending by category</h2>{chart_html}</section>
<section class="card wide">
<div class="table-bar">
<h2>Recent expenses</h2>
<form class="filter" method="get" action="/" style="margin:0">
<input type="hidden" name="chart" value="{html.escape(chart)}">
<input type="hidden" name="date" value="{html.escape(date)}">
<input type="hidden" name="month" value="{html.escape(month)}">
<select name="category" onchange="this.form.submit()">{cat_options}</select>
<input type="text" name="keyword" value="{html.escape(keyword)}" placeholder="Search notes or category..." style="width:190px">
<button type="submit" class="pill-btn on" style="margin:0;width:auto">Search</button>
<a href="{reset_url}" class="pill-btn">Reset</a>
<a href="{export_url}" class="pill-btn">Export CSV</a>
</form>
</div>
<table><tr><th>Date</th><th>Category</th><th class="n">Amount</th><th>Notes</th><th></th></tr>{rows}</table></section>
</main></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, body, ctype="text/html; charset=utf-8", status=200, extra_headers=None):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        q = parse_qs(url.query)
        chart = q.get("chart", ["pie"])[0]
        date = q.get("date", [""])[0]
        month = q.get("month", [""])[0]
        category = q.get("category", [""])[0]
        keyword = q.get("keyword", [""])[0]

        if url.path == "/chart.png":
            kind = q.get("kind", ["pie"])[0]
            all_expenses = load_expenses()
            if kind == "trend":
                expenses = all_expenses
            else:
                expenses = apply_filters(
                    all_expenses,
                    date=date,
                    month=month,
                    category=category,
                    keyword=keyword,
                )
            if not expenses:
                return self._send("no data", "text/plain", 404)
            buf = io.BytesIO()
            if kind == "trend":
                expense_trend.make_trend(expense_trend.monthly_totals(expenses), buf)
            else:
                totals = expense_chart.totals_by_category(expenses)
                fn = expense_chart.make_bar if kind == "bar" else expense_chart.make_pie
                fn(totals, buf)
            return self._send(buf.getvalue(), "image/png")

        if url.path == "/export.csv":
            filtered = apply_filters(
                load_expenses(),
                date=date,
                month=month,
                category=category,
                keyword=keyword,
            )
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["date", "amount", "category", "notes"])
            for e in filtered:
                writer.writerow([e["date"], e["amount"], e["category"], e.get("notes", "")])
            csv_bytes = ("\ufeff" + buf.getvalue()).encode("utf-8")
            filename = f"expenses_{date}.csv" if date else "expenses_filtered.csv"
            return self._send(
                csv_bytes,
                "text/csv; charset=utf-8",
                extra_headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

        if url.path == "/":
            return self._send(
                render_page(
                    chart=chart,
                    date=date,
                    month=month,
                    category=category,
                    keyword=keyword,
                )
            )
        self._send("not found", "text/plain", 404)

    def do_POST(self):
        if self.path not in ("/add", "/delete"):
            return self._send("not found", "text/plain", 404)
        form = parse_qs(self.rfile.read(int(self.headers.get("Content-Length", 0))).decode())

        def get(k):
            return form.get(k, [""])[0].strip()

        if self.path == "/delete":
            try:
                delete_expense(int(get("index")))
            except (ValueError, IndexError):
                pass
            params = {
                "chart": get("chart") or "pie",
                "date": get("date"),
                "month": get("month"),
                "category": get("category"),
                "keyword": get("keyword"),
            }
            back = urlencode({k: v for k, v in params.items() if v})
            self.send_response(303)
            self.send_header("Location", f"/?{back}" if back else "/")
            self.end_headers()
            return
        try:
            save_expense({
                "date": parse_date(get("date")),
                "amount": parse_amount(get("amount")),
                "category": get("category") or "Other",
                "notes": get("notes"),
            })
        except ValueError as e:
            return self._send(render_page(error=f"Invalid input: {e}"), status=400)
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def log_message(self, *args):
        pass


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}"
    print(f"Expense Tracker running at {url}  (Ctrl+C to stop)")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBye!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
