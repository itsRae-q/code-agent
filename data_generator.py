"""
股票数据生成器
用于生成符合筛选条件的测试数据
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

class StockDataGenerator:
    """股票数据生成器"""
    
    def __init__(self, num_stocks=200):
        self.num_stocks = num_stocks
        self.stock_codes = [f"{str(i).zfill(6)}" for i in range(1, num_stocks + 1)]
        
    def generate_basic_info(self) -> pd.DataFrame:
        """生成股票基础信息"""
        data = []
        
        # 行业列表
        industries = [
            "制造业", "信息技术", "医药生物", "电子", "化工", 
            "机械设备", "电气设备", "汽车", "食品饮料", "纺织服装",
            "建筑材料", "有色金属", "钢铁", "煤炭", "石油石化",
            "银行", "保险", "证券", "房地产", "商业贸易"  # 包含需要剔除的行业
        ]
        
        for i, code in enumerate(self.stock_codes):
            # 10%的股票是ST股票
            is_st = random.random() < 0.1
            name_prefix = "ST" if is_st else ""
            
            stock_name = f"{name_prefix}测试股票{i+1:03d}"
            industry = random.choice(industries)
            
            data.append({
                'code': code,
                'name': stock_name,
                'industry': industry
            })
        
        return pd.DataFrame(data)
    
    def generate_trading_data(self, stock_codes: list) -> dict:
        """生成交易数据"""
        trading_data = {}
        
        for code in stock_codes:
            # 生成随机的日均成交金额（万元）
            avg_amount = random.uniform(1000, 50000)  # 1千万到5亿
            latest_price = random.uniform(5, 100)  # 5-100元
            
            trading_data[code] = {
                'avg_trading_amount': avg_amount,
                'latest_price': latest_price
            }
        
        return trading_data
    
    def generate_financial_data(self, stock_codes: list) -> dict:
        """生成财务数据"""
        financial_data = {}
        
        for code in stock_codes:
            # 生成现金流数据（万元）
            operating_cash_flow = random.uniform(-10000, 50000)  # -1亿到5亿
            capex = random.uniform(1000, 20000)  # 1千万到2亿
            free_cash_flow = operating_cash_flow - capex
            
            # 生成其他财务指标
            revenue = random.uniform(50000, 500000)  # 5亿到50亿
            net_profit = random.uniform(-5000, 30000)  # -5千万到3亿
            
            # ROE相关数据（12个季度）
            roe_values = [random.uniform(-0.1, 0.3) for _ in range(12)]
            roe_std = np.std(roe_values)  # ROE标准差，用于稳定性评估
            
            # 模拟现金流量表数据结构
            cash_flow_df = pd.DataFrame({
                '报告期': ['2023-12-31'],
                '经营活动产生的现金流量净额': [operating_cash_flow],
                '购建固定资产、无形资产和其他长期资产支付的现金': [capex],
                '营业收入': [revenue],
                '净利润': [net_profit]
            })
            
            financial_data[code] = {
                'cash_flow': cash_flow_df,
                'code': code,
                'operating_cash_flow': operating_cash_flow,
                'free_cash_flow': free_cash_flow,
                'roe_stability': roe_std,
                'net_profit': net_profit
            }
        
        return financial_data
    
    def generate_all_data(self):
        """生成所有测试数据"""
        print("生成测试数据...")
        
        # 基础信息
        basic_info = self.generate_basic_info()
        
        # 交易数据
        trading_data = self.generate_trading_data(self.stock_codes)
        
        # 财务数据
        financial_data = self.generate_financial_data(self.stock_codes)
        
        return {
            'basic_info': basic_info,
            'trading_data': trading_data,
            'financial_data': financial_data
        }

def save_sample_data():
    """保存样本数据到文件"""
    generator = StockDataGenerator(200)
    data = generator.generate_all_data()
    
    # 保存基础信息
    data['basic_info'].to_csv('/workspace/sample_stock_basic.csv', index=False, encoding='utf-8-sig')
    
    # 保存交易数据
    trading_df = pd.DataFrame.from_dict(data['trading_data'], orient='index')
    trading_df.index.name = 'stock_code'
    trading_df.to_csv('/workspace/sample_trading_data.csv', encoding='utf-8-sig')
    
    # 保存财务数据摘要
    financial_summary = []
    for code, fin_data in data['financial_data'].items():
        financial_summary.append({
            'stock_code': code,
            'operating_cash_flow': fin_data['operating_cash_flow'],
            'free_cash_flow': fin_data['free_cash_flow'],
            'roe_stability': fin_data['roe_stability'],
            'net_profit': fin_data['net_profit']
        })
    
    financial_df = pd.DataFrame(financial_summary)
    financial_df.to_csv('/workspace/sample_financial_data.csv', index=False, encoding='utf-8-sig')
    
    print("样本数据已保存到CSV文件")
    return data

if __name__ == "__main__":
    save_sample_data()