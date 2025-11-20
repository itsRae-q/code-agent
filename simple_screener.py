"""
简化版股票筛选器
使用本地生成的测试数据进行筛选
"""

import pandas as pd
import numpy as np
from data_generator import StockDataGenerator
from typing import Dict, List, Tuple

class SimpleStockScreener:
    """简化版股票筛选器"""
    
    def __init__(self):
        self.generator = StockDataGenerator(200)
        self.data = None
        
    def load_data(self):
        """加载测试数据"""
        print("加载测试数据...")
        self.data = self.generator.generate_all_data()
        print(f"加载完成：{len(self.data['basic_info'])} 只股票")
    
    def filter_basic_conditions(self) -> pd.DataFrame:
        """基础条件筛选：剔除ST股票"""
        print("\n1. 执行基础条件筛选（剔除ST股票）...")
        
        basic_info = self.data['basic_info']
        # 剔除ST股票
        filtered = basic_info[~basic_info['name'].str.contains('ST', na=False)]
        
        print(f"   原始股票数: {len(basic_info)}")
        print(f"   剔除ST后: {len(filtered)}")
        
        return filtered
    
    def filter_liquidity(self, stock_codes: List[str]) -> List[str]:
        """流动性筛选：剔除成交金额排名后20%"""
        print("\n2. 执行流动性筛选（剔除成交金额排名后20%）...")
        
        trading_data = self.data['trading_data']
        
        # 计算成交金额排名
        amounts = [(code, trading_data[code]['avg_trading_amount']) 
                  for code in stock_codes if code in trading_data]
        amounts.sort(key=lambda x: x[1], reverse=True)
        
        # 保留前80%
        keep_count = int(len(amounts) * 0.8)
        filtered_codes = [code for code, _ in amounts[:keep_count]]
        
        print(f"   筛选前: {len(stock_codes)}")
        print(f"   筛选后: {len(filtered_codes)}")
        
        return filtered_codes
    
    def filter_industry(self, stock_codes: List[str]) -> List[str]:
        """行业筛选：剔除金融和房地产行业"""
        print("\n3. 执行行业筛选（剔除金融和房地产）...")
        
        basic_info = self.data['basic_info']
        industry_map = dict(zip(basic_info['code'], basic_info['industry']))
        
        filtered_codes = []
        financial_industries = ['银行', '保险', '证券', '房地产']
        
        for code in stock_codes:
            industry = industry_map.get(code, '')
            if not any(fin_industry in industry for fin_industry in financial_industries):
                filtered_codes.append(code)
        
        print(f"   筛选前: {len(stock_codes)}")
        print(f"   筛选后: {len(filtered_codes)}")
        
        return filtered_codes
    
    def filter_roe_stability(self, stock_codes: List[str]) -> List[str]:
        """ROE稳定性筛选：剔除ROE稳定性排名后10%"""
        print("\n4. 执行ROE稳定性筛选（剔除稳定性排名后10%）...")
        
        financial_data = self.data['financial_data']
        
        # 计算ROE稳定性排名（标准差越小越稳定）
        roe_stability = [(code, financial_data[code]['roe_stability']) 
                        for code in stock_codes if code in financial_data]
        roe_stability.sort(key=lambda x: x[1])  # 升序，标准差小的在前
        
        # 保留前90%（剔除后10%）
        keep_count = int(len(roe_stability) * 0.9)
        filtered_codes = [code for code, _ in roe_stability[:keep_count]]
        
        print(f"   筛选前: {len(stock_codes)}")
        print(f"   筛选后: {len(filtered_codes)}")
        
        return filtered_codes
    
    def filter_cash_flow_conditions(self, stock_codes: List[str]) -> List[str]:
        """现金流条件筛选"""
        print("\n5. 执行现金流条件筛选...")
        
        financial_data = self.data['financial_data']
        filtered_codes = []
        
        for code in stock_codes:
            if code not in financial_data:
                continue
                
            data = financial_data[code]
            
            # 检查现金流条件
            operating_cf_positive = data['operating_cash_flow'] > 0
            free_cf_positive = data['free_cash_flow'] > 0
            
            if operating_cf_positive and free_cf_positive:
                filtered_codes.append(code)
        
        print(f"   筛选前: {len(stock_codes)}")
        print(f"   筛选后: {len(filtered_codes)}")
        
        return filtered_codes
    
    def filter_operating_quality(self, stock_codes: List[str]) -> List[str]:
        """经营质量筛选：剔除经营现金流/净利润比例排名后30%"""
        print("\n6. 执行经营质量筛选（剔除现金流质量排名后30%）...")
        
        financial_data = self.data['financial_data']
        quality_ratios = []
        
        for code in stock_codes:
            if code not in financial_data:
                continue
                
            data = financial_data[code]
            operating_cf = data['operating_cash_flow']
            net_profit = data['net_profit']
            
            # 计算经营现金流/净利润比例
            if net_profit > 0:
                ratio = operating_cf / net_profit
            else:
                ratio = 0  # 亏损企业比例设为0
            
            quality_ratios.append((code, ratio))
        
        # 按比例降序排序
        quality_ratios.sort(key=lambda x: x[1], reverse=True)
        
        # 保留前70%（剔除后30%）
        keep_count = int(len(quality_ratios) * 0.7)
        filtered_codes = [code for code, _ in quality_ratios[:keep_count]]
        
        print(f"   筛选前: {len(stock_codes)}")
        print(f"   筛选后: {len(filtered_codes)}")
        
        return filtered_codes
    
    def calculate_fcf_yield_and_select_top100(self, stock_codes: List[str]) -> List[Tuple[str, float]]:
        """计算自由现金流率并选取前100只"""
        print("\n7. 计算自由现金流率并选取前100只...")
        
        financial_data = self.data['financial_data']
        trading_data = self.data['trading_data']
        
        fcf_yields = []
        
        for code in stock_codes:
            if code not in financial_data or code not in trading_data:
                continue
                
            fin_data = financial_data[code]
            trading = trading_data[code]
            
            free_cash_flow = fin_data['free_cash_flow']
            # 简化：用市值代替企业价值（股价 * 假设流通股本1亿股）
            market_cap = trading['latest_price'] * 100000000  # 1亿股
            
            if market_cap > 0 and free_cash_flow > 0:
                fcf_yield = free_cash_flow / market_cap
                fcf_yields.append((code, fcf_yield))
        
        # 按自由现金流率降序排序
        fcf_yields.sort(key=lambda x: x[1], reverse=True)
        
        # 选取前100只
        top_100 = fcf_yields[:100]
        
        print(f"   计算出FCF收益率的股票数: {len(fcf_yields)}")
        print(f"   选取前100只股票")
        
        return top_100
    
    def calculate_weights(self, selected_stocks: List[Tuple[str, float]]) -> Dict[str, float]:
        """计算股票权重"""
        print("\n8. 计算股票权重...")
        
        financial_data = self.data['financial_data']
        
        # 收集所有股票的自由现金流
        fcf_values = []
        for code, _ in selected_stocks:
            fcf = financial_data[code]['free_cash_flow']
            fcf_values.append(max(fcf, 0))  # 确保非负
        
        total_fcf = sum(fcf_values)
        weights = {}
        
        if total_fcf > 0:
            # 按自由现金流计算初始权重
            for i, (code, _) in enumerate(selected_stocks):
                initial_weight = fcf_values[i] / total_fcf
                # 限制单只股票权重不超过10%
                capped_weight = min(initial_weight, 0.10)
                weights[code] = capped_weight
            
            # 重新标准化权重
            total_weight = sum(weights.values())
            if total_weight > 0:
                for code in weights:
                    weights[code] = weights[code] / total_weight
        else:
            # 等权重
            equal_weight = 1.0 / len(selected_stocks)
            for code, _ in selected_stocks:
                weights[code] = equal_weight
        
        # 统计权重信息
        max_weight = max(weights.values())
        min_weight = min(weights.values())
        
        print(f"   权重计算完成")
        print(f"   最大权重: {max_weight:.4f} ({max_weight*100:.2f}%)")
        print(f"   最小权重: {min_weight:.4f} ({min_weight*100:.2f}%)")
        
        return weights
    
    def run_screening(self) -> Tuple[List[str], Dict[str, float]]:
        """执行完整筛选流程"""
        print("=" * 60)
        print("开始执行国证自由现金流指数股票筛选")
        print("=" * 60)
        
        # 加载数据
        self.load_data()
        
        # 1. 基础条件筛选
        filtered_basic = self.filter_basic_conditions()
        stock_codes = filtered_basic['code'].tolist()
        
        # 2. 流动性筛选
        stock_codes = self.filter_liquidity(stock_codes)
        
        # 3. 行业筛选
        stock_codes = self.filter_industry(stock_codes)
        
        # 4. ROE稳定性筛选
        stock_codes = self.filter_roe_stability(stock_codes)
        
        # 5. 现金流条件筛选
        stock_codes = self.filter_cash_flow_conditions(stock_codes)
        
        # 6. 经营质量筛选
        stock_codes = self.filter_operating_quality(stock_codes)
        
        # 7. 计算FCF收益率并选取前100只
        selected_stocks = self.calculate_fcf_yield_and_select_top100(stock_codes)
        
        # 8. 计算权重
        final_codes = [code for code, _ in selected_stocks]
        weights = self.calculate_weights(selected_stocks)
        
        return final_codes, weights, selected_stocks

def main():
    """主函数"""
    # 创建筛选器
    screener = SimpleStockScreener()
    
    # 执行筛选
    selected_codes, weights, selected_stocks = screener.run_screening()
    
    # 输出结果
    print("\n" + "=" * 60)
    print("筛选结果汇总")
    print("=" * 60)
    
    if selected_codes and weights:
        # 获取股票基本信息
        basic_info = screener.data['basic_info']
        financial_data = screener.data['financial_data']
        trading_data = screener.data['trading_data']
        
        name_map = dict(zip(basic_info['code'], basic_info['name']))
        industry_map = dict(zip(basic_info['code'], basic_info['industry']))
        
        # 创建结果表格
        results = []
        for i, (code, fcf_yield) in enumerate(selected_stocks):
            weight = weights.get(code, 0)
            
            results.append({
                '排名': i + 1,
                '股票代码': code,
                '股票名称': name_map.get(code, '未知'),
                '所属行业': industry_map.get(code, '未知'),
                '自由现金流率': f"{fcf_yield:.6f}",
                '权重': f"{weight:.4f}",
                '权重百分比': f"{weight*100:.2f}%",
                '自由现金流(万元)': f"{financial_data[code]['free_cash_flow']:,.0f}",
                '经营现金流(万元)': f"{financial_data[code]['operating_cash_flow']:,.0f}",
                '最新股价(元)': f"{trading_data[code]['latest_price']:.2f}"
            })
        
        results_df = pd.DataFrame(results)
        
        # 显示前20名
        print("\n前20名股票详情:")
        print("-" * 120)
        print(results_df.head(20).to_string(index=False))
        
        # 保存完整结果
        results_df.to_csv('/workspace/fcf_index_results.csv', index=False, encoding='utf-8-sig')
        print(f"\n完整结果已保存到: fcf_index_results.csv")
        
        # 权重分布统计
        print(f"\n权重分布统计:")
        print(f"- 入选股票总数: {len(selected_codes)}")
        print(f"- 权重总和: {sum(weights.values()):.6f}")
        print(f"- 最大权重: {max(weights.values()):.4f} ({max(weights.values())*100:.2f}%)")
        print(f"- 最小权重: {min(weights.values()):.4f} ({min(weights.values())*100:.2f}%)")
        print(f"- 平均权重: {np.mean(list(weights.values())):.4f} ({np.mean(list(weights.values()))*100:.2f}%)")
        
        # 行业分布统计
        industry_count = {}
        for code in selected_codes:
            industry = industry_map.get(code, '未知')
            industry_count[industry] = industry_count.get(industry, 0) + 1
        
        print(f"\n行业分布:")
        for industry, count in sorted(industry_count.items(), key=lambda x: x[1], reverse=True):
            print(f"- {industry}: {count}只")
        
        # 现金流统计
        fcf_values = [financial_data[code]['free_cash_flow'] for code in selected_codes]
        print(f"\n自由现金流统计(万元):")
        print(f"- 总计: {sum(fcf_values):,.0f}")
        print(f"- 平均: {np.mean(fcf_values):,.0f}")
        print(f"- 最大: {max(fcf_values):,.0f}")
        print(f"- 最小: {min(fcf_values):,.0f}")
        
    else:
        print("未筛选出符合条件的股票")
    
    print("\n" + "=" * 60)
    print("筛选程序执行完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()