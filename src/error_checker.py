"""纠错 Agent v5.0 — 数据验证 + AI 输出质量检查"""
import re
from datetime import datetime


def check_data_quality(data: dict, data_name: str) -> dict:
    """检查数据质量"""
    issues = []
    warnings = []

    if data is None:
        issues.append(f"{data_name}: 数据为 None")
        return {"valid": False, "issues": issues, "warnings": warnings}

    if isinstance(data, dict):
        if not data:
            issues.append(f"{data_name}: 数据字典为空")
        # 检查是否有 error 字段
        for key, val in data.items():
            if isinstance(val, dict) and "error" in val:
                warnings.append(f"{data_name}.{key}: {val['error']}")
    elif isinstance(data, list):
        if not data:
            issues.append(f"{data_name}: 数据列表为空")
        # 检查列表项是否有 error
        error_count = sum(1 for item in data if isinstance(item, dict) and "error" in item)
        if error_count > 0:
            warnings.append(f"{data_name}: {error_count}/{len(data)} 项有错误")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
    }


def check_price_anomalies(market_data: dict) -> list[str]:
    """检查价格异常"""
    anomalies = []

    if not market_data:
        return ["市场数据为空，无法检查异常"]

    # 检查指数涨跌幅是否异常
    for idx in market_data.get("indices", []):
        pct = idx.get("week_change_pct", 0)
        if abs(pct) > 15:
            anomalies.append(f"指数 {idx.get('display_name')} 周涨跌幅 {pct:.2f}% 异常大，请核实")
        elif abs(pct) > 10:
            anomalies.append(f"指数 {idx.get('display_name')} 周涨跌幅 {pct:.2f}% 较大，注意核实")

    # 检查板块涨跌幅
    for sector in market_data.get("sectors", []):
        pct = sector.get("week_change_pct", 0)
        if abs(pct) > 20:
            anomalies.append(f"板块 {sector.get('display_name')} 涨跌幅 {pct:.2f}% 异常大")

    return anomalies


def check_technical_consistency(technicals: dict) -> list[str]:
    """检查技术指标一致性"""
    issues = []

    if not technicals:
        return ["技术数据为空"]

    for name, tech in technicals.items():
        if isinstance(tech, dict) and "error" not in tech:
            rsi = tech.get("rsi")
            macd = tech.get("macd", {})
            trend = tech.get("trend", "")

            # RSI 与 MACD 一致性
            if rsi and rsi > 70 and macd.get("bullish"):
                issues.append(f"{name}: RSI超买({rsi})但MACD看涨，信号矛盾需核实")
            elif rsi and rsi < 30 and not macd.get("bullish"):
                issues.append(f"{name}: RSI超卖({rsi})且MACD看跌，极端悲观信号")

            # 价格与均线一致性
            price = tech.get("price")
            sma50 = tech.get("sma50")
            if price and sma50 and sma50 != "N/A":
                if price > sma50 * 1.1:
                    issues.append(f"{name}: 价格高于50日均线10%以上，短期过热风险")
                elif price < sma50 * 0.9:
                    issues.append(f"{name}: 价格低于50日均线10%以上，超卖可能")

    return issues


def validate_ai_report(report: str) -> dict:
    """验证 AI 生成报告的质量"""
    issues = []
    warnings = []

    if not report:
        return {"valid": False, "issues": ["报告为空"], "warnings": []}

    # 基本长度检查
    char_count = len(report)
    if char_count < 500:
        issues.append(f"报告过短 ({char_count}字)，可能不完整")
    elif char_count < 1000:
        warnings.append(f"报告较短 ({char_count}字)")

    # 检查是否有关键章节
    required_sections = ["Executive Summary", "市场全景", "技术面", "前瞻"]
    for section in required_sections:
        if section not in report:
            warnings.append(f"缺少章节: {section}")

    # 检查置信度标注
    confidence_count = report.count("置信度")
    if confidence_count < 3:
        warnings.append(f"置信度标注较少 ({confidence_count}处)")

    # 检查是否有多空观点
    has_bull = "多头" in report or "看涨" in report or "Bull" in report
    has_bear = "空头" in report or "看空" in report or "Bear" in report
    if not has_bull or not has_bear:
        warnings.append("报告可能缺少多空平衡观点")

    # 检查是否有风险提示
    if "风险" not in report and "止损" not in report:
        warnings.append("缺少风险提示")

    # 检查是否有具体数字
    numbers = re.findall(r'\d+\.?\d*%|\$\d+', report)
    if len(numbers) < 5:
        warnings.append(f"具体数据较少 ({len(numbers)}处)")

    return {
        "valid": len(issues) == 0,
        "char_count": char_count,
        "issues": issues,
        "warnings": warnings,
        "confidence_count": confidence_count,
        "has_bull_bear": has_bull and has_bear,
        "number_count": len(numbers),
    }


def check_report_consistency(report: str, market_data: dict) -> list[str]:
    """检查报告内容与数据一致性"""
    issues = []

    if not report or not market_data:
        return []

    # 检查指数名称是否在报告中出现
    for idx in market_data.get("indices", []):
        name = idx.get("display_name", "")
        price = idx.get("price", 0)
        if name and price:
            # 检查价格是否大致在报告中提及
            price_str = str(int(price))
            if price_str not in report:
                issues.append(f"报告中未提及 {name} 的价格 ({price})")

    return issues


def run_full_check(market_data: dict, technicals: dict, sentiment: dict,
                   news_data: dict, report: str) -> dict:
    """全面纠错检查 — 主入口"""
    print("\n[纠错Agent] 开始全面数据质量检查...")

    results = {
        "timestamp": datetime.now().isoformat(),
        "data_quality": {},
        "price_anomalies": [],
        "technical_issues": [],
        "report_validation": {},
        "consistency_issues": [],
        "overall_status": "PASS",
        "critical_issues": [],
        "warnings": [],
    }

    # 1. 数据质量检查
    datasets = {
        "市场数据": market_data,
        "技术数据": technicals,
        "情绪数据": sentiment,
        "新闻数据": news_data,
    }
    for name, data in datasets.items():
        check = check_data_quality(data, name)
        results["data_quality"][name] = check
        if not check["valid"]:
            results["critical_issues"].extend(check["issues"])
        results["warnings"].extend(check["warnings"])

    # 2. 价格异常检查
    results["price_anomalies"] = check_price_anomalies(market_data)
    results["warnings"].extend(results["price_anomalies"])

    # 3. 技术指标一致性
    results["technical_issues"] = check_technical_consistency(technicals)
    results["warnings"].extend(results["technical_issues"])

    # 4. 报告质量验证
    if report:
        results["report_validation"] = validate_ai_report(report)
        if not results["report_validation"]["valid"]:
            results["critical_issues"].extend(results["report_validation"]["issues"])
        results["warnings"].extend(results["report_validation"].get("warnings", []))

        # 5. 数据一致性
        results["consistency_issues"] = check_report_consistency(report, market_data)
        results["warnings"].extend(results["consistency_issues"])

    # 总体状态
    if results["critical_issues"]:
        results["overall_status"] = "FAIL"
    elif len(results["warnings"]) > 5:
        results["overall_status"] = "WARN"

    # 输出摘要
    print(f"[纠错Agent] 状态: {results['overall_status']}")
    print(f"  关键问题: {len(results['critical_issues'])}")
    print(f"  警告: {len(results['warnings'])}")
    if results["critical_issues"]:
        for issue in results["critical_issues"]:
            print(f"  [CRITICAL] {issue}")
    if results["warnings"][:5]:
        for w in results["warnings"][:5]:
            print(f"  [WARN] {w}")

    return results


def format_error_check_for_prompt(check_result: dict) -> str:
    """格式化纠错结果为 prompt 文本"""
    if not check_result:
        return ""

    lines = ["### 数据质量与纠错报告\n"]
    lines.append(f"总体状态: **{check_result['overall_status']}**")

    if check_result["critical_issues"]:
        lines.append("\n**关键问题:**")
        for issue in check_result["critical_issues"]:
            lines.append(f"  - {issue}")

    if check_result["warnings"]:
        lines.append(f"\n**警告 ({len(check_result['warnings'])}项):**")
        for w in check_result["warnings"][:8]:
            lines.append(f"  - {w}")

    report_val = check_result.get("report_validation", {})
    if report_val:
        lines.append(f"\n**报告质量:** 字数 {report_val.get('char_count', 'N/A')} | 置信度标注 {report_val.get('confidence_count', 0)} 处 | 数据引用 {report_val.get('number_count', 0)} 处")
        lines.append(f"多空平衡: {'是' if report_val.get('has_bull_bear') else '否'}")

    return "\n".join(lines)
