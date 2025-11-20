#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票持仓及权重计算程序
基于国证自由现金流指数编制方案
"""

import json
import random
from typing import List, Dict
from datetime import datetime


class Stock:
    """股票数据类"""
    def __init__(self, code: str, name: str, price: float, shares: float, 
                 free_cash_flow: float, roe_stability: float, 
                 trading_amount: float, industry: str):
        self.code = code
        self.name = name
        self.price = price  # 收盘价
        self.shares = shares  # 流通股本（万股）
        self.free_cash_flow = free_cash_flow  # 近一年自由现金流（万元）
        self.roe_stability = roe_stability  # ROE稳定性排名（越小越好）
        self.trading_amount = trading_amount  # 最近半年日均成交金额（万元）
        self.industry = industry  # 行业


def generate_mock_stocks() -> List[Stock]:
    """生成mock股票数据（不超过20个）"""
    stocks = []
    industries = ['科技', '制造', '消费', '医药', '能源']
    
    for i in range(1, 16):  # 生成15只股票
        code = f"00000{i:02d}"
        name = f"股票{i}"
        price = round(random.uniform(10, 100), 2)
        shares = round(random.uniform(10000, 100000), 0)  # 万股
        free_cash_flow = round(random.uniform(5000, 50000), 0)  # 万元
        roe_stability = random.uniform(0, 100)  # ROE稳定性排名
        trading_amount = round(random.uniform(1000, 10000), 0)  # 万元
        industry = random.choice(industries)
        
        stock = Stock(code, name, price, shares, free_cash_flow, 
                     roe_stability, trading_amount, industry)
        stocks.append(stock)
    
    return stocks


def filter_stocks(stocks: List[Stock]) -> List[Stock]:
    """选样方法：根据规则筛选股票"""
    # 1. 剔除最近半年日均成交金额排名后20%的证券
    sorted_by_trading = sorted(stocks, key=lambda x: x.trading_amount, reverse=True)
    cutoff = int(len(sorted_by_trading) * 0.8)
    filtered = sorted_by_trading[:cutoff]
    
    # 2. 剔除金融或房地产行业的证券
    filtered = [s for s in filtered if s.industry not in ['金融', '房地产']]
    
    # 3. 剔除近12个季度ROE稳定性排名后10%的证券
    sorted_by_roe = sorted(filtered, key=lambda x: x.roe_stability)
    cutoff = int(len(sorted_by_roe) * 0.9)
    filtered = sorted_by_roe[:cutoff]
    
    # 4. 选取近一年自由现金流为正的证券（mock数据已保证为正）
    filtered = [s for s in filtered if s.free_cash_flow > 0]
    
    # 5. 对剩余证券按照近一年自由现金流率从高到低排序，选取前100只
    # 这里简化处理，直接按自由现金流排序
    sorted_by_fcf = sorted(filtered, key=lambda x: x.free_cash_flow, reverse=True)
    
    return sorted_by_fcf


def calculate_weights(stocks: List[Stock]) -> List[Dict]:
    """计算股票权重"""
    # 计算初始权重（基于自由现金流）
    total_fcf = sum(s.free_cash_flow for s in stocks)
    
    holdings = []
    for stock in stocks:
        # 初始权重 = 该股票自由现金流 / 总自由现金流
        initial_weight = stock.free_cash_flow / total_fcf if total_fcf > 0 else 0
        
        # 权重调整：单只样本权重不超过10%
        weight = min(initial_weight, 0.10)
        
        # 计算市值
        market_value = stock.price * stock.shares
        
        holdings.append({
            'code': stock.code,
            'name': stock.name,
            'price': stock.price,
            'shares': stock.shares,
            'market_value': round(market_value, 2),
            'free_cash_flow': stock.free_cash_flow,
            'initial_weight': round(initial_weight * 100, 4),
            'weight': round(weight * 100, 4),  # 转换为百分比
            'industry': stock.industry
        })
    
    # 重新归一化权重（确保总和为100%）
    total_weight = sum(h['weight'] for h in holdings)
    if total_weight > 0:
        for h in holdings:
            h['weight'] = round(h['weight'] * 100 / total_weight, 4)
    
    return holdings


def save_weights_to_file(holdings: List[Dict], filename: str = 'stock_weights.json'):
    """保存权重数据到文件"""
    output_data = {
        'calculation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_stocks': len(holdings),
        'total_weight': round(sum(h['weight'] for h in holdings), 4),
        'holdings': holdings
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"权重数据已保存到文件: {filename}")


def main():
    """主函数"""
    print("=" * 50)
    print("股票持仓及权重计算程序")
    print("=" * 50)
    
    # 1. 生成mock数据
    print("\n1. 生成mock股票数据...")
    stocks = generate_mock_stocks()
    print(f"   生成了 {len(stocks)} 只股票")
    
    # 2. 选样
    print("\n2. 执行选样筛选...")
    selected_stocks = filter_stocks(stocks)
    print(f"   筛选后剩余 {len(selected_stocks)} 只股票")
    
    # 3. 计算权重
    print("\n3. 计算股票权重...")
    holdings = calculate_weights(selected_stocks)
    
    # 显示前5只股票的权重信息
    print("\n   前5只股票权重预览:")
    for i, h in enumerate(holdings[:5], 1):
        print(f"   {i}. {h['name']}({h['code']}): {h['weight']}%")
    
    # 4. 保存到文件
    print("\n4. 保存权重数据...")
    save_weights_to_file(holdings)
    
    print("\n" + "=" * 50)
    print("计算完成！")
    print("=" * 50)


if __name__ == '__main__':
    main()
