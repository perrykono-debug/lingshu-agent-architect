#!/usr/bin/env python3
"""
招商方案生成脚本
自动生成完整的招商方案（Markdown格式）
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# 模拟数据（实际应从腾讯文档读取）
PARK_INFO = {
    "name": "中集金地[园区名称]",
    "location": "上海市宝山区湄浦路",
    "area": "8.4万㎡",
    "buildings": "T1/T2栋",
    "features": ["地铁5号线", "人才公寓", "园区餐厅", "共享会议中心"],
}

SAMPLE_ROOMS = [
    {"楼栋": "T1", "楼层": 8, "房号": "801", "面积": 256, "租金": 2.1, "装修": "精装", "层高": 4.5},
    {"楼栋": "T1", "楼层": 12, "房号": "1201", "面积": 228, "租金": 2.3, "装修": "毛坯", "层高": 4.5},
    {"楼栋": "T2", "楼层": 5, "房号": "502", "面积": 318, "租金": 1.9, "装修": "精装", "层高": 4.2},
]

POLICIES = [
    {"名称": "人才补贴", "内容": "本科1万/硕士3万/博士5万", "条件": "园区企业员工"},
    {"名称": "税收返还", "内容": "增值税地方留存部分返还50%", "条件": "年纳税额>100万"},
    {"名称": "研发补贴", "内容": "研发投入补贴最高100万/年", "条件": "高新技术企业"},
]

def generate_proposal(company_name, area, budget):
    """生成招商方案"""
    # 匹配房源
    recommended_rooms = match_rooms(area, budget)
    
    # 计算TCO
    tco_analysis = calculate_tco(recommended_rooms[0] if recommended_rooms else None)
    
    # 匹配政策
    matched_policies = match_policies()
    
    # 生成方案内容
    content = format_proposal(company_name, recommended_rooms, tco_analysis, matched_policies)
    
    return content

def match_rooms(area, budget):
    """匹配房源"""
    # 简单匹配逻辑：面积±20%，租金±10%
    matched = []
    
    for room in SAMPLE_ROOMS:
        area_diff = abs(room["面积"] - area) / area if area > 0 else 1
        rent_diff = abs(room["租金"] - budget) / budget if budget > 0 else 1
        
        if area_diff <= 0.2 and (budget == 0 or rent_diff <= 0.1):
            matched.append(room)
    
    # 按面积匹配度排序
    matched.sort(key=lambda x: abs(x["面积"] - area))
    
    return matched[:3]  # 返回Top 3

def calculate_tco(room):
    """计算TCO（总拥有成本）"""
    if not room:
        return None
    
    area = room["面积"]
    rent = room["租金"]
    
    # 月成本
    monthly_rent = area * rent * 30  # 租金
    monthly_property_fee = area * 0.8  # 物业费
    monthly_parking = 300 * 2  # 停车费（假设2个车位）
    
    monthly_total = monthly_rent + monthly_property_fee + monthly_parking
    
    # 年成本
    yearly_total = monthly_total * 12
    
    # 3年总成本
    three_year_total = yearly_total * 3
    
    # 政策收益（模拟）
    policy_income = 500000  # 假设3年可获得50万政策补贴
    
    # 净成本
    net_cost = three_year_total - policy_income
    
    return {
        "area": area,
        "monthly_total": monthly_total,
        "yearly_total": yearly_total,
        "three_year_total": three_year_total,
        "policy_income": policy_income,
        "net_cost": net_cost,
    }

def match_policies():
    """匹配政策（简化版：返回所有政策）"""
    return POLICIES

def format_proposal(company_name, rooms, tco, policies):
    """格式化招商方案"""
    content = f"# 🏢 招商方案 - {company_name}\n\n"
    
    content += f"## 📋 项目概述\n\n"
    content += f"**园区名称**：{PARK_INFO['name']}\n\n"
    content += f"**地理位置**：{PARK_INFO['location']}\n\n"
    content += f"**园区规模**：总建筑面积{PARK_INFO['area']}，由{PARK_INFO['buildings']}组成\n\n"
    content += f"**核心优势**：\n"
    for feature in PARK_INFO['features']:
        content += f"- {feature}\n"
    content += f"\n"
    
    content += f"## 🏗️ 房源推荐（Top 3）\n\n"
    
    if not rooms:
        content += f"⚠️ 未找到完全匹配的房源，以下为相近推荐：\n\n"
        # 使用默认推荐
        rooms = SAMPLE_ROOMS[:3]
    
    for i, room in enumerate(rooms, 1):
        content += f"### 【推荐{i}】{room['楼栋']}栋 {room['楼层']}楼 {room['房号']}室\n\n"
        content += f"- **面积**：{room['面积']}㎡\n"
        content += f"- **租金**：{room['租金']}元/㎡/天\n"
        content += f"- **装修**：{room['装修']}\n"
        content += f"- **层高**：{room['层高']}米\n"
        content += f"- **匹配理由**：面积{'完全' if abs(room['面积'] - rooms[0]['面积']) < 20 else '接近'}匹配，租金{'在预算内' if room['租金'] <= (rooms[0]['租金'] if rooms else 2.2) else '略超预算'}\n\n"
    
    content += f"## 💰 TCO成本分析（3年）\n\n"
    
    if tco:
        content += f"**基于推荐1计算：**\n\n"
        content += f"- **月总成本**：¥{tco['monthly_total']:,.0f}元（租金+物业费+停车费）\n"
        content += f"- **年总成本**：¥{tco['yearly_total']:,.0f}元\n"
        content += f"- **3年总成本**：¥{tco['three_year_total']:,.0f}元\n"
        content += f"- **可获政策补贴**：¥{tco['policy_income']:,.0f}元\n"
        content += f"- **净成本**：¥{tco['net_cost']:,.0f}元（扣除政策补贴后）\n\n"
    else:
        content += f"⚠️ 无法计算TCO，请先确认推荐房源\n\n"
    
    content += f"## 📜 政策匹配\n\n"
    
    for policy in policies:
        content += f"### {policy['名称']}\n"
        content += f"- **内容**：{policy['内容']}\n"
        content += f"- **申请条件**：{policy['条件']}\n\n"
    
    content += f"## 🛎️ 入驻服务\n\n"
    content += f"- **一站式服务**：工商注册、税务登记、银行开户等手续代办\n"
    content += f"- **产业生态**：园区已入驻企业{50}+家，形成完整产业链\n"
    content += f"- **人才服务**：人才公寓、子女教育、医疗保障等配套\n"
    content += f"- **技术支持**：共享实验室、测试平台、技术转移中心\n\n"
    
    content += f"## 📎 附件\n\n"
    content += f"- 房源平面图（T1栋8楼801室）\n"
    content += f"- 政策申报指南（人才补贴/税收返还/研发补贴）\n"
    content += f"- 成功案例（同行业企业入驻案例）\n"
    content += f"- 园区宣传册（电子版）\n\n"
    
    content += f"---\n\n"
    content += f"**联系人**：[招商经理姓名]\n"
    content += f"**联系电话**：[电话号码]\n"
    content += f"**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return content

def save_to_file(content, company_name, output_dir=None):
    """保存招商方案到文件"""
    if output_dir is None:
        output_dir = os.path.expanduser("~/.qclaw/workspace-investment-assistant")
    
    os.makedirs(output_dir, exist_ok=True)
    
    date_str = datetime.now().strftime("%Y%m%d")
    output_file = os.path.join(output_dir, f"招商方案_{company_name}_{date_str}.md")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    return output_file

def main():
    """主函数"""
    if len(sys.argv) < 4:
        print("用法: python3 generate_proposal.py <企业名> <面积> <预算>")
        print("示例: python3 generate_proposal.py \"测试科技公司\" 300 2.2")
        sys.exit(1)
    
    company_name = sys.argv[1]
    area = float(sys.argv[2])
    budget = float(sys.argv[3])
    
    print(f"🏢 开始生成招商方案...")
    print(f"📋 企业名称: {company_name}")
    print(f"📐 需求面积: {area}㎡")
    print(f"💰 预算范围: {budget}元/㎡/天")
    
    # 生成方案
    content = generate_proposal(company_name, area, budget)
    
    # 保存文件
    output_file = save_to_file(content, company_name)
    
    print(f"\n✅ 招商方案已生成: {output_file}")
    print(f"\n📄 内容预览:")
    print(content[:800] + "..." if len(content) > 800 else content)
    
    return output_file

if __name__ == "__main__":
    main()
