from analyzer.engine import analyze_company
from analyzer.reporting import generate_report

result = analyze_company("https://www.coderabbit.ai")

report = generate_report(result)

print(report)