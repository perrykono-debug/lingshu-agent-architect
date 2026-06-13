#!/usr/bin/env python3
"""
园区数据查询脚本 v3.0
从知识库加载数据（支持多项目、多数据源）
使用知识库抽象层（KnowledgeBase）
"""

import os
import sys
import json
from datetime import datetime
import argparse

# 导入知识库抽象层
from knowledge_base import KnowledgeBase, parse_record_fields


def get_project_dir(project_id=None):
    """获取项目目录"""
    if project_id is None:
        # 读取默认项目
        config_file = os.path.join(WORKSPACE_DIR, "config.json")
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                project_id = config.get("default_project", DEFAULT_PROJECT)
        else:
            project_id = DEFAULT_PROJECT
    
    return os.path.join(WORKSPACE_DIR, "projects", project_id)


def load_sheet_data(sheet_name, project_id=None):
    """
    从知识库加载指定 sheet 的数据
    使用 KnowledgeBase 抽象层（支持多种数据源）
    sheet_name: "房源" / "租金" / "配套" / "客户"
    """
    # 创建知识库实例
    kb = KnowledgeBase(project_id=project_id)
    
    # Sheet名称映射
    sheet_map = {
        "房源": "房源销控表",
        "租金": "租金报价表",
        "配套": "配套资源表",
        "客户": "客户跟进记录",
        "政策": "产业政策库"
    }
    
    actual_sheet = sheet_map.get(sheet_name, sheet_name)
    
    # 加载数据
    data, error = kb.load(actual_sheet)
    
    if error:
        return None, error
    
    # 添加 sheet_name 到返回数据
    data["sheet_name"] = actual_sheet
    
    return data, None


def parse_record_fields(record):
    """
    解析记录中的字段值
    支持两种数据格式：
    1. MCP原始格式：{"field_values": [{"field": "楼层", "text_value": {...}}]}
    2. 紧凑格式：{"楼层": "7F", "面积(㎡)": 143.92}
    返回 {字段名: 值} 的字典
    """
    # 检测数据格式
    if "field_values" in record:
        # MCP原始格式
        fields = {}
        for fv in record.get("field_values", []):
            field_name = fv.get("field", "")
            # 尝试提取各种类型的值
            if "text_value" in fv:
                items = fv["text_value"].get("items", [])
                fields[field_name] = items[0]["text"] if items else ""
            elif "number_value" in fv:
                fields[field_name] = fv["number_value"]
            elif "option_value" in fv:
                items = fv["option_value"].get("items", [])
                fields[field_name] = items[0]["text"] if items else ""
            else:
                fields[field_name] = ""
        return fields
    else:
        # 紧凑格式：直接返回记录（排除 record_id）
        fields = {k: v for k, v in record.items() if k != "record_id"}
        return fields


def query_data(data_type, filter_key=None, filter_value=None, project_id=None):
    """
    查询园区数据（从本地 JSON 文件）
    data_type: "房源" / "租金" / "配套" / "客户"
    project_id: 项目ID（如：meilan-center）
    """
    # 加载数据
    data_result, err = load_sheet_data(data_type, project_id=project_id)
    if err:
        return None, err
    
    records = data_result["records"]
    sheet_name = data_result["sheet_name"]
    filtered_count = data_result["filtered_count"]
    
    # 解析所有记录
    items = []
    for rec in records:
        fields = parse_record_fields(rec)
        items.append(fields)
    
    # 过滤
    if filter_key and filter_value:
        filtered = []
        for item in items:
            if item.get(filter_key) == filter_value:
                filtered.append(item)
        items = filtered
    
    return {
        "data_type": data_type,
        "sheet_name": sheet_name,
        "total": len(items),
        "filtered_count": filtered_count,
        "data": items
    }, None


def format_output(result):
    """格式化输出查询结果"""
    data = result["data"]
    data_type = result["data_type"]
    filtered_count = result["filtered_count"]

    if not data:
        return f"⚠️ 未找到匹配数据（已过滤 {filtered_count} 条空记录）"

    output = f"# 📊 {data_type}查询结果（共{len(data)}条）\n\n"
    output += f"*（已过滤 {filtered_count} 条空记录）*\n\n"

    if data_type == "房源":
        output += "| 楼层 | 面积(㎡) | 底价(元/㎡/天) | 月租金(元) | 备注 |\n"
        output += "|------|----------|----------------|------------|------|\n"
        for item in data:
            floor = item.get("楼层", item.get("楼层区间", "-"))
            area = item.get("面积(㎡)", "-")
            rent = item.get("底价(元/㎡/天)", item.get("参考均价", "-"))
            monthly = item.get("估算月租金(元)", "-")
            remark = item.get("备注", "-")
            output += f"| {floor} | {area} | {rent} | {monthly} | {remark} |\n"

    elif data_type == "租金":
        output += "| 区域 | 楼层区间 | 底价区间 | 参考均价 | TCO折算 | 议价空间 | 备注 |\n"
        output += "|------|---------|---------|---------|--------|---------|------|\n"
        for item in data:
            region = item.get("区域", "-")
            floor = item.get("楼层区间", "-")
            base = item.get("底价区间", "-")
            avg = item.get("参考均价", "-")
            tco = item.get("TCO折算", "-")
            negotiable = item.get("议价空间", "-")
            remark = item.get("备注", "-")
            output += f"| {region} | {floor} | {base} | {avg} | {tco} | {negotiable} | {remark} |\n"

    elif data_type == "配套":
        output += "| 名称 | 类别 | 详情 | 状态 |\n"
        output += "|------|------|------|------|\n"
        for item in data:
            name = item.get("配套名称", "-")
            category = item.get("配套类别", "-")
            detail = item.get("详情", "-")
            status = item.get("备注/状态", "-")
            output += f"| {name} | {category} | {detail} | {status} |\n"

    elif data_type == "客户":
        output += "| 企业名称 | 联系人 | 需求面积(㎡) | 意向等级 | 客户状态 | 招商顾问 |\n"
        output += "|---------|--------|-------------|---------|---------|--------|\n"
        for item in data:
            name = item.get("企业名称", "-")
            contact = item.get("联系人", "-")
            area = item.get("需求面积(㎡)", "-")
            level = item.get("意向等级", "-")
            status = item.get("客户状态", "-")
            advisor = item.get("招商顾问", "-")
            output += f"| {name} | {contact} | {area} | {level} | {status} | {advisor} |\n"

    return output


def save_to_file(result, project_id=None, output_dir=None):
    """保存查询结果到项目目录"""
    if output_dir is None:
        # 使用 KnowledgeBase 获取项目目录
        kb = KnowledgeBase(project_id=project_id)
        output_dir = os.path.join(kb.project_dir, "output")
    
    os.makedirs(output_dir, exist_ok=True)
    
    formatted = format_output(result)
    
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"查询结果_{date_str}.md")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# 📊 园区数据查询结果\n\n")
        f.write(f"**查询时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**数据类型：** {result['data_type']}\n\n")
        f.write(formatted)
        f.write(f"\n\n---\n*本报告由招商助手自动生成*")
    
    return output_file


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='园区数据查询')
    parser.add_argument('--project', type=str, default=None, help='项目ID（如：meilan-center）')
    parser.add_argument('--type', type=str, required=True, choices=['房源', '租金', '配套', '客户'], help='数据类型')
    parser.add_argument('--filter-key', type=str, default=None, help='过滤键')
    parser.add_argument('--filter-value', type=str, default=None, help='过滤值')
    
    args = parser.parse_args()
    
    print(f"🔍 开始查询 {args.type} 数据...")
    print(f"📁 当前项目: {args.project or '默认项目'}")
    
    # 查询数据
    result, err = query_data(args.type, args.filter_key, args.filter_value, project_id=args.project)
    if err:
        print(err)
        sys.exit(1)
    
    # 格式化输出
    formatted = format_output(result)
    print("\n" + formatted)
    
    # 保存到文件
    output_file = save_to_file(result, project_id=args.project)
    print(f"\n✅ 查询结果已保存: {output_file}")
    
    return output_file


if __name__ == "__main__":
    main()
