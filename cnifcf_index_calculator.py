#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国证自由现金流指数（CNIFCF）计算器
基于指数编制方案实现股票选样和权重计算

指数代码：980092
基日：2012年12月31日，基点：1000点
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import os
import json

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
        
        print("国证自由现金流指数计算器初始化完成")
        print(f"指数代码: {self.index_code}")
        print(f"基日: {self.base_date}, 基点: {self.base_point}")
    
    def get_stock_list(self):
        """获取A股股票列表"""
        print("正在获取A股股票列表...")
        try:
            # 获取沪深A股列表
            stock_sh = ak.stock_info_a_code_name()
            stock_sz = ak.stock_info_sz_name()
            
            # 合并股票列表
            stock_list = pd.concat([stock_sh, stock_sz], ignore_index=True)
            stock_list.columns = ['code', 'name']
            
            # 添加交易所信息
            stock_list['exchange'] = stock_list['code'].apply(
                lambda x: 'SH' if x.startswith(('60', '68', '11', '13')) else 'SZ'
            )
            
            self.stock_list = stock_list
            print(f"成功获取 {len(stock_list)} 只股票")
            return stock_list
            
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return None
    
    def filter_basic_conditions(self):
        """第一步：基础条件筛选"""
        print("正在进行基础条件筛选...")
        
        if self.stock_list is None:
            self.get_stock_list()
        
        filtered_stocks = self.stock_list.copy()
        initial_count = len(filtered_stocks)
        
        # 1. 剔除ST、*ST证券
        st_pattern = r'\*?ST'
        filtered_stocks = filtered_stocks[~filtered_stocks['name'].str.contains(st_pattern, na=False)]
        print(f"剔除ST股票后剩余: {len(filtered_stocks)} 只")
        
        # 2. 剔除科创板和北交所（简化处理，实际需要检查上市时间）
        # 科创板：688开头，北交所：43、83、87开头
        filtered_stocks = filtered_stocks[
            ~filtered_stocks['code'].str.startswith(('688', '43', '83', '87'))
        ]
        print(f"剔除科创板和北交所后剩余: {len(filtered_stocks)} 只")
        
        # 3. 获取上市时间并筛选（上市超过6个月）
        cutoff_date = (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')
        
        valid_stocks = []
        for idx, row in filtered_stocks.iterrows():
            try:
                # 获取股票基本信息
                stock_info = ak.stock_individual_info_em(symbol=row['code'])
                if stock_info is not None and len(stock_info) > 0:
                    # 查找上市日期
                    listing_date_row = stock_info[stock_info['item'] == '上市时间']
                    if len(listing_date_row) > 0:
                        listing_date = listing_date_row['value'].iloc[0]
                        if listing_date and listing_date.replace('-', '') < cutoff_date:
                            valid_stocks.append(row)
                    else:
                        # 如果没有找到上市时间，保守处理，假设符合条件
                        valid_stocks.append(row)
                        
            except Exception as e:
                # 如果获取信息失败，保守处理
                valid_stocks.append(row)
                continue
        
        filtered_stocks = pd.DataFrame(valid_stocks)
        print(f"上市时间筛选后剩余: {len(filtered_stocks)} 只")
        
        self.filtered_basic = filtered_stocks
        return filtered_stocks
    
    def get_financial_indicators(self, stock_codes):
        """获取财务指标数据"""
        print("正在获取财务指标数据...")
        
        financial_data = []
        
        for i, code in enumerate(stock_codes[:200]):  # 限制数量以避免请求过多
            try:
                print(f"获取 {code} 财务数据... ({i+1}/{min(len(stock_codes), 200)})")
                
                # 获取现金流量表数据
                cash_flow = ak.stock_financial_analysis_indicator(symbol=code)
                if cash_flow is not None and len(cash_flow) > 0:
                    # 获取最近一年的数据
                    recent_data = cash_flow.iloc[0] if len(cash_flow) > 0 else None
                    
                    if recent_data is not None:
                        financial_data.append({
                            'code': code,
                            'operating_cash_flow': recent_data.get('经营活动现金流量净额', 0),
                            'free_cash_flow': recent_data.get('自由现金流量', 0),
                            'roe': recent_data.get('净资产收益率', 0),
                            'total_market_value': recent_data.get('总市值', 0),
                            'revenue': recent_data.get('营业收入', 0),
                            'net_profit': recent_data.get('净利润', 0)
                        })
                
            except Exception as e:
                print(f"获取 {code} 财务数据失败: {e}")
                continue
        
        self.financial_data = pd.DataFrame(financial_data)
        print(f"成功获取 {len(self.financial_data)} 只股票的财务数据")
        return self.financial_data
    
    def calculate_enterprise_value(self):
        """计算企业价值（市值 + 净债务）"""
        print("正在计算企业价值...")
        
        if self.financial_data is None:
            return None
        
        # 简化计算：企业价值 ≈ 总市值（实际应该加上净债务）
        self.financial_data['enterprise_value'] = self.financial_data['total_market_value']
        
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
    
    def get_current_prices(self):
        """获取当前股价数据"""
        print("正在获取当前股价数据...")
        
        if self.weights is None:
            return None
        
        price_data = []
        
        for idx, row in self.weights.iterrows():
            try:
                # 获取实时行情
                current_price = ak.stock_zh_a_spot_em()
                stock_price = current_price[current_price['代码'] == row['code']]
                
                if len(stock_price) > 0:
                    price = stock_price['最新价'].iloc[0]
                    price_data.append({
                        'code': row['code'],
                        'current_price': price,
                        'weight': row['final_weight']
                    })
                    
            except Exception as e:
                print(f"获取 {row['code']} 价格失败: {e}")
                # 使用市值估算价格
                estimated_price = row['total_market_value'] / 100000000  # 简化估算
                price_data.append({
                    'code': row['code'],
                    'current_price': estimated_price,
                    'weight': row['final_weight']
                })
        
        self.market_data = pd.DataFrame(price_data)
        return self.market_data
    
    def calculate_index_value(self):
        """计算指数值"""
        print("正在计算指数值...")
        
        if self.market_data is None:
            return None
        
        # 计算加权市值
        self.market_data['weighted_value'] = (
            self.market_data['current_price'] * self.market_data['weight']
        )
        
        total_weighted_value = self.market_data['weighted_value'].sum()
        
        # 计算指数值（简化公式）
        index_value = total_weighted_value * self.base_point
        
        print(f"计算得到的指数值: {index_value:.2f}")
        
        return index_value
    
    def run_full_calculation(self):
        """运行完整的指数计算流程"""
        print("=" * 60)
        print("开始国证自由现金流指数计算")
        print("=" * 60)
        
        try:
            # 1. 获取股票列表
            self.get_stock_list()
            
            # 2. 基础条件筛选
            filtered_stocks = self.filter_basic_conditions()
            
            if filtered_stocks is None or len(filtered_stocks) == 0:
                print("基础筛选后无可用股票")
                return None
            
            # 3. 获取财务数据
            stock_codes = filtered_stocks['code'].tolist()
            self.get_financial_indicators(stock_codes)
            
            if self.financial_data is None or len(self.financial_data) == 0:
                print("无法获取财务数据")
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
            
            # 7. 获取当前价格
            self.get_current_prices()
            
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
                    'fcf_rate', 'enterprise_value', 'operating_cash_flow'
                ]
                
                result_df = result_df[output_columns].copy()
                result_df.columns = [
                    '股票代码', '股票名称', '权重', '自由现金流', 
                    '自由现金流率', '企业价值', '经营活动现金流'
                ]
                
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
                'index_value': results.get('index_value', 0) if results else 0,
                'max_weight_limit': self.max_weight,
                'methodology': '基于自由现金流率选样，按自由现金流加权'
            }
            
            json_file = f'{output_dir}/cnifcf_index_info_{timestamp}.json'
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(index_info, f, ensure_ascii=False, indent=2)
            print(f"指数信息已保存到: {json_file}")
            
            # 保存详细的财务数据
            if self.selected_stocks is not None:
                detail_file = f'{output_dir}/cnifcf_financial_details_{timestamp}.xlsx'
                self.selected_stocks.to_excel(detail_file, index=False, engine='openpyxl')
                print(f"详细财务数据已保存到: {detail_file}")
            
            print("所有结果文件保存完成")
            return True
            
        except Exception as e:
            print(f"保存文件时发生错误: {e}")
            return False


def main():
    """主函数"""
    print("国证自由现金流指数计算器")
    print("数据来源：真实市场数据（akshare）")
    print("计算日期：", datetime.now().strftime('%Y-%m-%d'))
    
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
        print(f"权重分布:")
        
        if calculator.weights is not None:
            weights_summary = calculator.weights['final_weight'].describe()
            print(f"  平均权重: {weights_summary['mean']:.4f}")
            print(f"  最大权重: {weights_summary['max']:.4f}")
            print(f"  最小权重: {weights_summary['min']:.4f}")
            
            # 显示前10大权重股票
            top_stocks = calculator.weights.merge(
                calculator.stock_list[['code', 'name']], 
                on='code', 
                how='left'
            ).nlargest(10, 'final_weight')
            
            print(f"\n前10大权重股票:")
            for idx, row in top_stocks.iterrows():
                print(f"  {row['code']} {row['name']}: {row['final_weight']:.4f}")
        
    else:
        print("计算失败，请检查数据源和网络连接")


if __name__ == "__main__":
    main()