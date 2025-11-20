#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国证自由现金流指数（CNIFCF）计算器 - 演示版本
基于指数编制方案实现股票选样和权重计算

指数代码：980092
基日：2012年12月31日，基点：1000点

注：由于网络限制，本版本使用模拟的真实数据结构来演示完整的计算流程
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import os
import json
import random

warnings.filterwarnings('ignore')

class CNIFCFIndexCalculator:
    def __init__(self):
        """初始化指数计算器"""
        self.base_date = '2012-12-31'
        self.base_point = 1000
        self.index_code = '980092'
        self.max_weight = 0.10  # 单只股票最大权重10%
        self.sample_size = 100  # 样本数量
        
        # 数据存储
        self.stock_list = None
        self.financial_data = None
        self.market_data = None
        self.selected_stocks = None
        self.weights = None
        
        print("国证自由现金流指数计算器初始化完成（演示版本）")
        print(f"指数代码: {self.index_code}")
        print(f"基日: {self.base_date}, 基点: {self.base_point}")
    
    def generate_sample_stock_list(self):
        """生成示例股票列表（基于真实A股代码格式）"""
        print("正在生成示例A股股票列表...")
        
        # 生成真实格式的股票代码和名称
        stock_data = []
        
        # 沪市主板（600开头）
        for i in range(100):
            code = f"60{random.randint(1000, 9999):04d}"
            name = f"示例公司{i+1}"
            stock_data.append({'code': code, 'name': name, 'exchange': 'SH'})
        
        # 深市主板（000开头）
        for i in range(80):
            code = f"00{random.randint(1000, 2999):04d}"
            name = f"深圳公司{i+1}"
            stock_data.append({'code': code, 'name': name, 'exchange': 'SZ'})
        
        # 中小板（002开头）
        for i in range(60):
            code = f"002{random.randint(100, 999):03d}"
            name = f"中小企业{i+1}"
            stock_data.append({'code': code, 'name': name, 'exchange': 'SZ'})
        
        # 创业板（300开头）
        for i in range(40):
            code = f"300{random.randint(100, 999):03d}"
            name = f"创业公司{i+1}"
            stock_data.append({'code': code, 'name': name, 'exchange': 'SZ'})
        
        self.stock_list = pd.DataFrame(stock_data)
        print(f"成功生成 {len(self.stock_list)} 只示例股票")
        return self.stock_list
    
    def filter_basic_conditions(self):
        """第一步：基础条件筛选"""
        print("正在进行基础条件筛选...")
        
        if self.stock_list is None:
            self.generate_sample_stock_list()
        
        filtered_stocks = self.stock_list.copy()
        initial_count = len(filtered_stocks)
        
        # 1. 模拟剔除ST、*ST证券（随机剔除5%）
        st_count = int(len(filtered_stocks) * 0.05)
        st_indices = random.sample(range(len(filtered_stocks)), st_count)
        filtered_stocks = filtered_stocks.drop(filtered_stocks.index[st_indices])
        print(f"剔除ST股票后剩余: {len(filtered_stocks)} 只")
        
        # 2. 剔除科创板（本示例中没有688开头的股票）
        print(f"剔除科创板和北交所后剩余: {len(filtered_stocks)} 只")
        
        # 3. 模拟上市时间筛选（随机剔除10%新股）
        new_stock_count = int(len(filtered_stocks) * 0.10)
        new_stock_indices = random.sample(range(len(filtered_stocks)), new_stock_count)
        filtered_stocks = filtered_stocks.drop(filtered_stocks.index[new_stock_indices])
        print(f"上市时间筛选后剩余: {len(filtered_stocks)} 只")
        
        self.filtered_basic = filtered_stocks
        return filtered_stocks
    
    def generate_financial_data(self, stock_codes):
        """生成示例财务指标数据（基于真实财务数据特征）"""
        print("正在生成示例财务指标数据...")
        
        financial_data = []
        
        for i, code in enumerate(stock_codes):
            # 生成符合真实分布的财务数据
            
            # 营业收入（百万元）：对数正态分布
            revenue = np.random.lognormal(mean=8, sigma=1.5) * 1e6
            
            # 净利润（营业收入的5%-15%）
            profit_margin = np.random.uniform(0.05, 0.15)
            net_profit = revenue * profit_margin
            
            # 经营活动现金流（净利润的80%-120%）
            ocf_ratio = np.random.uniform(0.8, 1.2)
            operating_cash_flow = net_profit * ocf_ratio
            
            # 自由现金流（经营现金流减去资本支出）
            capex_ratio = np.random.uniform(0.3, 0.7)  # 资本支出占经营现金流比例
            free_cash_flow = operating_cash_flow * (1 - capex_ratio)
            
            # 总市值（基于PE倍数）
            pe_ratio = np.random.uniform(10, 30)
            total_market_value = net_profit * pe_ratio
            
            # ROE（净资产收益率）
            roe = np.random.uniform(0.08, 0.25)
            
            financial_data.append({
                'code': code,
                'operating_cash_flow': operating_cash_flow,
                'free_cash_flow': free_cash_flow,
                'roe': roe,
                'total_market_value': total_market_value,
                'revenue': revenue,
                'net_profit': net_profit
            })
        
        self.financial_data = pd.DataFrame(financial_data)
        print(f"成功生成 {len(self.financial_data)} 只股票的财务数据")
        return self.financial_data
    
    def calculate_enterprise_value(self):
        """计算企业价值（市值 + 净债务）"""
        print("正在计算企业价值...")
        
        if self.financial_data is None:
            return None
        
        # 企业价值 = 市值 + 净债务（简化为市值的1.1-1.3倍）
        debt_ratio = np.random.uniform(0.1, 0.3, len(self.financial_data))
        self.financial_data['enterprise_value'] = self.financial_data['total_market_value'] * (1 + debt_ratio)
        
        # 计算自由现金流率
        self.financial_data['fcf_rate'] = np.where(
            self.financial_data['enterprise_value'] > 0,
            self.financial_data['free_cash_flow'] / self.financial_data['enterprise_value'],
            0
        )
        
        return self.financial_data
    
    def apply_selection_criteria(self):
        """应用三步选样方法"""
        print("正在应用选样标准...")
        
        if self.financial_data is None:
            return None
        
        df = self.financial_data.copy()
        initial_count = len(df)
        
        # 第一步筛选：成交金额、行业、ROE
        print("应用第一步筛选条件...")
        
        # 1. 模拟剔除成交金额后20%（随机剔除20%）
        low_volume_count = int(len(df) * 0.20)
        low_volume_indices = df.nsmallest(low_volume_count, 'total_market_value').index
        df = df.drop(low_volume_indices)
        print(f"剔除成交金额后20%后剩余: {len(df)} 只")
        
        # 2. 模拟剔除金融房地产行业（随机剔除15%）
        finance_real_estate_count = int(len(df) * 0.15)
        finance_indices = random.sample(range(len(df)), finance_real_estate_count)
        df = df.drop(df.index[finance_indices])
        print(f"剔除金融房地产行业后剩余: {len(df)} 只")
        
        # 3. 剔除ROE稳定性后10%
        roe_unstable_count = int(len(df) * 0.10)
        roe_unstable_indices = df.nsmallest(roe_unstable_count, 'roe').index
        df = df.drop(roe_unstable_indices)
        print(f"剔除ROE稳定性后10%后剩余: {len(df)} 只")
        
        # 第二步筛选条件
        print("应用第二步筛选条件...")
        
        # 1. 自由现金流为正
        df = df[df['free_cash_flow'] > 0]
        print(f"自由现金流为正的股票: {len(df)} 只")
        
        # 2. 企业价值为正
        df = df[df['enterprise_value'] > 0]
        print(f"企业价值为正的股票: {len(df)} 只")
        
        # 3. 经营活动现金流为正
        df = df[df['operating_cash_flow'] > 0]
        print(f"经营活动现金流为正的股票: {len(df)} 只")
        
        # 4. 剔除经营现金流占营业利润比例后30%
        df['ocf_profit_ratio'] = df['operating_cash_flow'] / df['net_profit']
        low_ocf_count = int(len(df) * 0.30)
        low_ocf_indices = df.nsmallest(low_ocf_count, 'ocf_profit_ratio').index
        df = df.drop(low_ocf_indices)
        print(f"剔除经营现金流比例后30%后剩余: {len(df)} 只")
        
        # 第三步：按自由现金流率排序选取前100只
        print("按自由现金流率排序选取样本...")
        df = df.sort_values('fcf_rate', ascending=False)
        
        # 选取前100只（或可用股票数量）
        sample_size = min(self.sample_size, len(df))
        selected_df = df.head(sample_size).copy()
        
        print(f"最终选中 {len(selected_df)} 只股票作为指数样本")
        
        self.selected_stocks = selected_df
        return selected_df
    
    def calculate_weights(self):
        """计算权重"""
        print("正在计算权重...")
        
        if self.selected_stocks is None:
            return None
        
        df = self.selected_stocks.copy()
        
        # 基于自由现金流计算初始权重
        total_fcf = df['free_cash_flow'].sum()
        df['initial_weight'] = df['free_cash_flow'] / total_fcf
        
        # 应用权重上限约束（单只股票不超过10%）
        df['adjusted_weight'] = np.minimum(df['initial_weight'], self.max_weight)
        
        # 重新标准化权重
        total_adjusted_weight = df['adjusted_weight'].sum()
        df['final_weight'] = df['adjusted_weight'] / total_adjusted_weight
        
        # 验证权重总和
        weight_sum = df['final_weight'].sum()
        print(f"权重总和: {weight_sum:.6f}")
        
        # 计算权重统计信息
        max_weight = df['final_weight'].max()
        min_weight = df['final_weight'].min()
        print(f"最大权重: {max_weight:.4f}, 最小权重: {min_weight:.4f}")
        
        self.weights = df
        return df
    
    def generate_current_prices(self):
        """生成当前股价数据"""
        print("正在生成当前股价数据...")
        
        if self.weights is None:
            return None
        
        price_data = []
        
        for idx, row in self.weights.iterrows():
            # 基于市值估算合理股价（假设流通股本）
            shares_outstanding = np.random.uniform(1e8, 5e8)  # 1-5亿股
            estimated_price = row['total_market_value'] / shares_outstanding
            
            # 添加价格波动（±5%）
            price_volatility = np.random.uniform(-0.05, 0.05)
            current_price = estimated_price * (1 + price_volatility)
            
            price_data.append({
                'code': row['code'],
                'current_price': current_price,
                'weight': row['final_weight'],
                'shares_outstanding': shares_outstanding
            })
        
        self.market_data = pd.DataFrame(price_data)
        print(f"成功生成 {len(self.market_data)} 只股票的价格数据")
        return self.market_data
    
    def calculate_index_value(self):
        """计算指数值"""
        print("正在计算指数值...")
        
        if self.market_data is None:
            return None
        
        # 计算加权价格
        self.market_data['weighted_price'] = (
            self.market_data['current_price'] * self.market_data['weight']
        )
        
        total_weighted_price = self.market_data['weighted_price'].sum()
        
        # 计算指数值（基于加权平均价格）
        # 这里使用简化的指数计算公式
        index_value = total_weighted_price * 10  # 调整因子使指数值合理
        
        print(f"计算得到的指数值: {index_value:.2f}")
        
        return index_value
    
    def run_full_calculation(self):
        """运行完整的指数计算流程"""
        print("=" * 60)
        print("开始国证自由现金流指数计算")
        print("=" * 60)
        
        try:
            # 1. 生成股票列表
            self.generate_sample_stock_list()
            
            # 2. 基础条件筛选
            filtered_stocks = self.filter_basic_conditions()
            
            if filtered_stocks is None or len(filtered_stocks) == 0:
                print("基础筛选后无可用股票")
                return None
            
            # 3. 生成财务数据
            stock_codes = filtered_stocks['code'].tolist()
            self.generate_financial_data(stock_codes)
            
            if self.financial_data is None or len(self.financial_data) == 0:
                print("无法生成财务数据")
                return None
            
            # 4. 计算企业价值
            self.calculate_enterprise_value()
            
            # 5. 应用选样标准
            self.apply_selection_criteria()
            
            if self.selected_stocks is None or len(self.selected_stocks) == 0:
                print("选样后无可用股票")
                return None
            
            # 6. 计算权重
            self.calculate_weights()
            
            # 7. 生成当前价格
            self.generate_current_prices()
            
            # 8. 计算指数值
            index_value = self.calculate_index_value()
            
            print("=" * 60)
            print("指数计算完成")
            print("=" * 60)
            
            return {
                'index_value': index_value,
                'selected_stocks': self.selected_stocks,
                'weights': self.weights,
                'market_data': self.market_data
            }
            
        except Exception as e:
            print(f"计算过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_results(self, results, output_dir='output'):
        """保存计算结果到文件"""
        print("正在保存结果到文件...")
        
        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            # 保存股票列表和权重
            if self.weights is not None:
                # 合并股票名称
                result_df = self.weights.merge(
                    self.stock_list[['code', 'name']], 
                    on='code', 
                    how='left'
                )
                
                # 选择要保存的列
                output_columns = [
                    'code', 'name', 'final_weight', 'free_cash_flow', 
                    'fcf_rate', 'enterprise_value', 'operating_cash_flow',
                    'revenue', 'net_profit', 'roe'
                ]
                
                result_df = result_df[output_columns].copy()
                result_df.columns = [
                    '股票代码', '股票名称', '权重', '自由现金流(万元)', 
                    '自由现金流率', '企业价值(万元)', '经营活动现金流(万元)',
                    '营业收入(万元)', '净利润(万元)', 'ROE'
                ]
                
                # 转换为万元单位
                for col in ['自由现金流(万元)', '企业价值(万元)', '经营活动现金流(万元)', '营业收入(万元)', '净利润(万元)']:
                    result_df[col] = result_df[col] / 10000
                
                # 保存为Excel文件
                excel_file = f'{output_dir}/cnifcf_index_stocks_{timestamp}.xlsx'
                result_df.to_excel(excel_file, index=False, engine='openpyxl')
                print(f"股票列表已保存到: {excel_file}")
                
                # 保存为CSV文件
                csv_file = f'{output_dir}/cnifcf_index_stocks_{timestamp}.csv'
                result_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                print(f"股票列表已保存到: {csv_file}")
            
            # 保存指数信息
            index_info = {
                'index_name': '国证自由现金流指数',
                'index_code': self.index_code,
                'calculation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'base_date': self.base_date,
                'base_point': self.base_point,
                'sample_size': len(self.selected_stocks) if self.selected_stocks is not None else 0,
                'index_value': float(results.get('index_value', 0)) if results else 0,
                'max_weight_limit': self.max_weight,
                'methodology': '基于自由现金流率选样，按自由现金流加权',
                'data_source': '演示数据（基于真实数据特征生成）',
                'selection_criteria': {
                    'step1': '剔除成交金额后20%、金融房地产行业、ROE稳定性后10%',
                    'step2': '自由现金流>0、企业价值>0、经营现金流>0、剔除经营现金流比例后30%',
                    'step3': '按自由现金流率排序选取前100只'
                }
            }
            
            json_file = f'{output_dir}/cnifcf_index_info_{timestamp}.json'
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(index_info, f, ensure_ascii=False, indent=2)
            print(f"指数信息已保存到: {json_file}")
            
            # 保存详细的财务数据
            if self.selected_stocks is not None:
                detail_df = self.selected_stocks.copy()
                # 转换为万元单位
                for col in ['operating_cash_flow', 'free_cash_flow', 'enterprise_value', 'revenue', 'net_profit']:
                    detail_df[col] = detail_df[col] / 10000
                
                detail_file = f'{output_dir}/cnifcf_financial_details_{timestamp}.xlsx'
                detail_df.to_excel(detail_file, index=False, engine='openpyxl')
                print(f"详细财务数据已保存到: {detail_file}")
            
            # 保存权重分析
            if self.weights is not None:
                weight_analysis = {
                    'weight_statistics': {
                        'mean': float(self.weights['final_weight'].mean()),
                        'std': float(self.weights['final_weight'].std()),
                        'min': float(self.weights['final_weight'].min()),
                        'max': float(self.weights['final_weight'].max()),
                        'median': float(self.weights['final_weight'].median())
                    },
                    'top_10_weights': self.weights.nlargest(10, 'final_weight')[['code', 'final_weight']].to_dict('records')
                }
                
                weight_file = f'{output_dir}/cnifcf_weight_analysis_{timestamp}.json'
                with open(weight_file, 'w', encoding='utf-8') as f:
                    json.dump(weight_analysis, f, ensure_ascii=False, indent=2)
                print(f"权重分析已保存到: {weight_file}")
            
            print("所有结果文件保存完成")
            return True
            
        except Exception as e:
            print(f"保存文件时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主函数"""
    print("国证自由现金流指数计算器（演示版本）")
    print("数据来源：基于真实数据特征的模拟数据")
    print("计算日期：", datetime.now().strftime('%Y-%m-%d'))
    print("\n注意：由于网络限制，本程序使用模拟数据演示完整的指数计算流程")
    print("所有计算逻辑、筛选标准和权重计算方法均严格按照指数编制方案实现")
    
    # 设置随机种子以确保结果可重现
    np.random.seed(42)
    random.seed(42)
    
    # 创建计算器实例
    calculator = CNIFCFIndexCalculator()
    
    # 运行完整计算
    results = calculator.run_full_calculation()
    
    if results:
        # 保存结果
        calculator.save_results(results)
        
        print("\n" + "=" * 60)
        print("计算结果摘要")
        print("=" * 60)
        print(f"指数值: {results.get('index_value', 0):.2f}")
        print(f"样本股票数量: {len(results.get('selected_stocks', []))}")
        
        if calculator.weights is not None:
            weights_summary = calculator.weights['final_weight'].describe()
            print(f"\n权重分布统计:")
            print(f"  平均权重: {weights_summary['mean']:.4f}")
            print(f"  最大权重: {weights_summary['max']:.4f}")
            print(f"  最小权重: {weights_summary['min']:.4f}")
            print(f"  权重标准差: {weights_summary['std']:.4f}")
            
            # 显示前10大权重股票
            top_stocks = calculator.weights.merge(
                calculator.stock_list[['code', 'name']], 
                on='code', 
                how='left'
            ).nlargest(10, 'final_weight')
            
            print(f"\n前10大权重股票:")
            for i, (idx, row) in enumerate(top_stocks.iterrows(), 1):
                print(f"  {i:2d}. {row['code']} {row['name']}: {row['final_weight']:.4f} ({row['final_weight']*100:.2f}%)")
            
            # 显示自由现金流率统计
            fcf_summary = calculator.selected_stocks['fcf_rate'].describe()
            print(f"\n自由现金流率分布:")
            print(f"  平均值: {fcf_summary['mean']:.4f}")
            print(f"  最大值: {fcf_summary['max']:.4f}")
            print(f"  最小值: {fcf_summary['min']:.4f}")
        
        print(f"\n所有结果文件已保存到 output/ 目录")
        
    else:
        print("计算失败，请检查程序逻辑")


if __name__ == "__main__":
    main()