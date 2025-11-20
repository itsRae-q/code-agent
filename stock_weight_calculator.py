#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票持仓及权重计算器
基于国证自由现金流指数编制方案
"""

import json
import random
from typing import List, Dict


def generate_mock_data(n: int = 20) -> List[Dict]:
    """生成mock股票数据"""
    industries = ['科技', '制造', '消费', '医药', '能源', '化工', '电子', '汽车']
    stocks = []
    
    for i in range(1, n + 1):
        stock = {
            'code': f'{600000 + i:06d}',
            'name': f'股票{i}',
            'industry': random.choice(industries),
            'is_st': False,
            'is_finance_real_estate': False,
            'daily_turnover_rank': random.uniform(0, 1),  # 0-1之间，越小排名越靠后
            'roe_stability_rank': random.uniform(0, 1),  # 0-1之间，越小排名越靠后
            'free_cash_flow': random.uniform(100000000, 10000000000),  # 近一年自由现金流（元）
            'enterprise_value': random.uniform(1000000000, 50000000000),  # 企业价值（元）
            'operating_cash_flow': random.uniform(50000000, 5000000000),  # 近三年经营活动现金流（元）
            'operating_profit': random.uniform(50000000, 5000000000),  # 营业利润（元）
        }
        stocks.append(stock)
    
    # 确保部分股票满足筛选条件
    # 设置部分股票为金融或房地产（用于测试剔除）
    stocks[5]['is_finance_real_estate'] = True
    stocks[12]['is_finance_real_estate'] = True
    
    # 设置部分股票为ST（用于测试剔除）
    stocks[3]['is_st'] = True
    
    # 确保部分股票自由现金流、企业价值、经营活动现金流为正
    for stock in stocks:
        if stock['free_cash_flow'] < 0:
            stock['free_cash_flow'] = abs(stock['free_cash_flow'])
        if stock['enterprise_value'] < 0:
            stock['enterprise_value'] = abs(stock['enterprise_value'])
        if stock['operating_cash_flow'] < 0:
            stock['operating_cash_flow'] = abs(stock['operating_cash_flow'])
    
    return stocks


def filter_stocks(stocks: List[Dict]) -> List[Dict]:
    """根据选样规则筛选股票"""
    filtered = []
    
    for stock in stocks:
        # 1. 剔除ST、*ST证券
        if stock['is_st']:
            continue
        
        # 2. 剔除金融或房地产行业
        if stock['is_finance_real_estate']:
            continue
        
        # 3. 剔除最近半年日均成交金额排名后20%
        if stock['daily_turnover_rank'] < 0.2:
            continue
        
        # 4. 剔除近12个季度ROE稳定性排名后10%
        if stock['roe_stability_rank'] < 0.1:
            continue
        
        # 5. 选取近一年自由现金流、企业价值和近三年经营活动现金流均为正的证券
        if stock['free_cash_flow'] <= 0 or stock['enterprise_value'] <= 0 or stock['operating_cash_flow'] <= 0:
            continue
        
        # 6. 计算经营活动现金流占营业利润比例
        if stock['operating_profit'] > 0:
            cash_flow_ratio = stock['operating_cash_flow'] / stock['operating_profit']
            stock['cash_flow_ratio'] = cash_flow_ratio
        else:
            continue
        
        filtered.append(stock)
    
    # 7. 剔除近一年经营活动现金流占营业利润比例排名后30%
    if filtered:
        filtered.sort(key=lambda x: x['cash_flow_ratio'], reverse=True)
        cutoff_index = int(len(filtered) * 0.7)
        filtered = filtered[:cutoff_index]
    
    return filtered


def calculate_weights(stocks: List[Dict]) -> List[Dict]:
    """计算股票权重"""
    # 计算自由现金流率（自由现金流/企业价值）
    for stock in stocks:
        stock['free_cash_flow_rate'] = stock['free_cash_flow'] / stock['enterprise_value']
    
    # 按自由现金流率从高到低排序
    stocks.sort(key=lambda x: x['free_cash_flow_rate'], reverse=True)
    
    # 选取前100只（由于只有20个mock数据，这里选取全部）
    selected_stocks = stocks[:100]
    
    # 计算初始权重（基于自由现金流）
    total_free_cash_flow = sum(s['free_cash_flow'] for s in selected_stocks)
    
    # 先计算原始权重
    raw_weights = []
    for stock in selected_stocks:
        raw_weight = stock['free_cash_flow'] / total_free_cash_flow
        raw_weights.append(raw_weight)
    
    # 应用10%上限限制
    capped_weights = [min(w, 0.1) for w in raw_weights]
    
    # 迭代分配剩余权重，直到所有股票都达到上限或权重总和为1
    max_iterations = 100
    for _ in range(max_iterations):
        current_total = sum(capped_weights)
        remaining = 1.0 - current_total
        
        if abs(remaining) < 0.0001:  # 权重总和已接近1
            break
        
        # 找出未达到上限的股票
        eligible_indices = [i for i, w in enumerate(capped_weights) if w < 0.1]
        
        if not eligible_indices:  # 所有股票都达到上限
            break
        
        # 按原始权重比例分配剩余权重
        eligible_raw_total = sum(raw_weights[i] for i in eligible_indices)
        if eligible_raw_total > 0:
            for i in eligible_indices:
                additional = remaining * (raw_weights[i] / eligible_raw_total)
                new_weight = capped_weights[i] + additional
                capped_weights[i] = min(new_weight, 0.1)
    
    # 分配权重到股票
    for i, stock in enumerate(selected_stocks):
        stock['weight'] = capped_weights[i]
    
    return selected_stocks


def save_weights_to_file(stocks: List[Dict], filename: str = 'stock_weights.json'):
    """保存权重数据到文件"""
    output_data = []
    
    for stock in stocks:
        output_data.append({
            'code': stock['code'],
            'name': stock['name'],
            'industry': stock['industry'],
            'free_cash_flow': stock['free_cash_flow'],
            'enterprise_value': stock['enterprise_value'],
            'free_cash_flow_rate': round(stock['free_cash_flow_rate'], 6),
            'weight': round(stock['weight'], 6)
        })
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"权重数据已保存到 {filename}")
    print(f"共 {len(output_data)} 只股票")


def main():
    """主函数"""
    print("开始生成mock数据...")
    stocks = generate_mock_data(20)
    print(f"生成了 {len(stocks)} 只股票的mock数据")
    
    print("\n开始筛选股票...")
    filtered_stocks = filter_stocks(stocks)
    print(f"筛选后剩余 {len(filtered_stocks)} 只股票")
    
    print("\n开始计算权重...")
    weighted_stocks = calculate_weights(filtered_stocks)
    print(f"最终入选 {len(weighted_stocks)} 只股票")
    
    # 显示权重信息
    print("\n权重分布：")
    total_weight = 0
    for stock in weighted_stocks:
        print(f"{stock['name']} ({stock['code']}): {stock['weight']:.4%}")
        total_weight += stock['weight']
    print(f"\n总权重: {total_weight:.4%}")
    
    print("\n保存权重数据...")
    save_weights_to_file(weighted_stocks, 'stock_weights.json')


if __name__ == '__main__':
    main()
