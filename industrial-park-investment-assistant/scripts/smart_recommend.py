#!/usr/bin/env python3
"""
智能房源推荐脚本 v3.0
根据客户需求智能匹配最合适的房源
使用知识库抽象层（支持多项目、多数据源）
"""

import os
import sys
import json
import re
from datetime import datetime
import argparse

# 导入知识库抽象层
from knowledge_base import KnowledgeBase, parse_record_fields


def load_sheet_data(sheet_name, project_id=None):
    """
    从知识库加载指定 sheet 的数据
    使用 KnowledgeBase 抽象层（支持多种数据源）
    sheet_name: "房源销控表" / "租金报价表" / "配套资源表"
    """
    # 创建知识库实例
    kb = KnowledgeBase(project_id=project_id)
    
    # 加载数据
    data, error = kb.load(sheet_name)
    
    if error:
        return None, error
    
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


def calculate_match_score(room_fields, requirements):
    """
    计算房源匹配得分
    room_fields: 解析后的房源字段字典
    requirements: {"需求面积": 400, "意向楼层": "低区", "预算上限": 2.5}
    """
    score = 0
    details = []

    # 1. 面积匹配度 (40%)
    req_area = requirements.get("需求面积", 0)
    room_area = room_fields.get("面积(㎡)", room_fields.get("面积", 0))
    try:
        room_area = float(room_area) if room_area else 0
    except (ValueError, TypeError):
        room_area = 0

    if req_area > 0 and room_area > 0:
        area_diff = abs(room_area - req_area) / req_area
        if area_diff <= 0.1:
            area_score = 100
            details.append(f"面积完全匹配（{room_area}㎡ vs {req_area}㎡）")
        elif area_diff <= 0.2:
            area_score = 80
            details.append(f"面积接近（{room_area}㎡ vs {req_area}㎡）")
        else:
            area_score = 50
            details.append(f"面积有差距（{room_area}㎡ vs {req_area}㎡）")
    else:
        area_score = 60
        details.append("未指定面积需求或房源面积未知")

    score += area_score * 0.4

    # 2. 租金匹配度 (30%)
    req_budget = requirements.get("预算上限", 0)
    # 尝试从多个字段获取租金
    room_rent = room_fields.get("底价(元/㎡/天)", room_fields.get("参考均价", 0))
    try:
        room_rent = float(room_rent) if room_rent else 0
    except (ValueError, TypeError):
        room_rent = 0

    if req_budget > 0 and room_rent > 0:
        rent_diff = (room_rent - req_budget) / req_budget
        if rent_diff <= -0.1:
            rent_score = 100
            details.append(f"租金低于预算（{room_rent}元 vs {req_budget}元）")
        elif rent_diff <= 0:
            rent_score = 90
            details.append(f"租金在预算内（{room_rent}元 vs {req_budget}元）")
        elif rent_diff <= 0.15:
            rent_score = 70
            details.append(f"租金略超预算（{room_rent}元 vs {req_budget}元）")
        else:
            rent_score = 40
            details.append(f"租金超预算（{room_rent}元 vs {req_budget}元）")
    else:
        rent_score = 60
        details.append("未指定预算或房源租金未知")

    score += rent_score * 0.3

    # 3. 楼层/区域匹配度 (20%)
    # 从楼层字段推断区域
    floor_str = room_fields.get("楼层", room_fields.get("楼层区间", ""))
    room_zone = ""
    if floor_str:
        # 提取数字部分（处理 "7F", "7", "7楼" 等格式）
        import re
        match = re.search(r'\d+', str(floor_str))
        if match:
            try:
                floor_num = int(match.group())
                if floor_num <= 5:
                    room_zone = "低区"
                elif floor_num <= 10:
                    room_zone = "中区"
                else:
                    room_zone = "高区"
            except ValueError:
                room_zone = ""
    
    req_zone = requirements.get("意向区域", "")
    if req_zone and room_zone:
        if req_zone in room_zone or room_zone in req_zone:
            floor_score = 100
            details.append(f"区域匹配（{room_zone}）")
        else:
            floor_score = 60
            details.append(f"区域不匹配（需求{req_zone} vs 当前{room_zone}）")
    elif req_zone:
        floor_score = 60
        details.append(f"无法判断房源区域（楼层：{floor_str}）")
    else:
        floor_score = 75
        details.append(f"未指定区域偏好（当前{room_zone or '未知'}）")

    score += floor_score * 0.2

    # 4. 备注/状态加分 (10%)
    remark = room_fields.get("备注", "")
    if remark and ("性价比" in remark or "优选" in remark or "优先" in remark):
        bonus_score = 100
        details.append(f"备注加分：{remark}")
    elif remark and ("已租满" in remark or "无房源" in remark):
        bonus_score = 0  # 已租满的房源不应推荐
        details.append(f"⚠️ 备注提示：{remark}")
    else:
        bonus_score = 75
        details.append("无特殊备注")

    score += bonus_score * 0.1

    return round(score, 1), details


def recommend_rooms(requirements, top_n=5, project_id=None):
    """
    推荐房源
    1. 加载房源销控表数据
    2. 过滤有效房源（排除已租满）
    3. 计算匹配得分
    4. 返回 Top N
    """
    # 加载数据
    data_result, err = load_sheet_data("房源销控表", project_id=project_id)
    if err:
        return None, err
    
    records = data_result["records"]
    filtered_count = data_result["filtered_count"]
    
    # 解析每条记录
    rooms = []
    for rec in records:
        fields = parse_record_fields(rec)
        # 过滤已租满的房源
        remark = fields.get("备注", "")
        if "已租满" in remark:
            continue
        rooms.append(fields)
    
    if not rooms:
        return None, "⚠️ 暂无有效可租房源，请检查腾讯文档数据。"
    
    # 计算匹配得分
    scored_rooms = []
    for room in rooms:
        score, details = calculate_match_score(room, requirements)
        scored_rooms.append({
            "room": room,
            "score": score,
            "details": details
        })

    # 按得分排序
    scored_rooms.sort(key=lambda x: x["score"], reverse=True)

    return {
        "recommendations": scored_rooms[:top_n],
        "total_rooms": len(rooms),
        "filtered_count": filtered_count
    }, None


def format_recommendation(result, requirements):
    """格式化推荐结果"""
    recommendations = result["recommendations"]
    total_rooms = result["total_rooms"]
    filtered_count = result["filtered_count"]

    output = "# 🏢 智能推荐房源（Top {}）\n\n".format(len(recommendations))

    output += "## 客户需求\n"
    output += f"- **需求面积**：{requirements.get('需求面积', '未指定')}㎡\n"
    output += f"- **意向区域**：{requirements.get('意向区域', '未指定')}\n"
    output += f"- **预算上限**：{requirements.get('预算上限', '未指定')} 元/㎡/天\n\n"

    output += "## 推荐房源\n\n"
    output += f"*（数据来源：腾讯文档，共 {total_rooms} 条有效房源"
    if filtered_count > 0:
        output += f"，已过滤 {filtered_count} 条空记录"
    output += "）*\n\n"

    for i, rec in enumerate(recommendations, 1):
        room = rec["room"]
        score = rec["score"]
        details = rec["details"]

        floor = room.get("楼层", room.get("楼层区间", "未知"))
        area = room.get("面积(㎡)", room.get("面积", "未知"))
        rent = room.get("底价(元/㎡/天)", room.get("参考均价", "未知"))
        remark = room.get("备注", "")

        output += f"### 【推荐{i}】{floor}层 | {area}㎡ | 底价 {rent} 元/㎡/天\n"
        output += f"- **匹配得分**：**{score}分**\n"
        output += f"- **匹配详情**：{'; '.join(details)}\n"
        if remark:
            output += f"- **备注**：{remark}\n"
        output += f"- **看房预约**：回复「预约看房 {floor}层」\n\n"

    output += "---\n"
    output += "**匹配算法**：面积40% + 租金30% + 区域20% + 备注10%\n"
    output += "**数据时效**：实时从腾讯文档读取\n"

    return output


def save_to_file(content, project_id=None, output_dir=None):
    """保存推荐结果到项目目录"""
    if output_dir is None:
        project_dir = get_project_dir(project_id)
        output_dir = os.path.join(project_dir, "output")
    
    os.makedirs(output_dir, exist_ok=True)
    
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"推荐房源_{date_str}.md")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
        f.write(f"\n\n---\n*本推荐由招商助手自动生成 @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    return output_file


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='智能房源推荐')
    parser.add_argument('--project', type=str, default=None, help='项目ID（如：meilan-center）')
    parser.add_argument('--requirements', type=str, required=True, help='需求JSON字符串')
    
    args = parser.parse_args()
    
    # 解析需求 JSON
    try:
        requirements = json.loads(args.requirements)
    except json.JSONDecodeError:
        print("❌ 需求参数必须是合法 JSON")
        sys.exit(1)
    
    print("🏢 开始智能推荐房源...")
    print(f"📋 客户需求: {requirements}")
    print(f"📁 当前项目: {args.project or '默认项目'}")

    # 推荐房源
    result, err = recommend_rooms(requirements, top_n=5, project_id=args.project)
    if err:
        print(err)
        sys.exit(1)

    # 格式化输出
    content = format_recommendation(result, requirements)
    print("\n" + content)

    # 保存到文件
    output_file = save_to_file(content, project_id=args.project)
    print(f"\n✅ 推荐报告已保存: {output_file}")

    return output_file


if __name__ == "__main__":
    main()
