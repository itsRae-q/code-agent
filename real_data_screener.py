"""
国证自由现金流指数股票筛选器 - 真实数据版本
使用akshare获取真实A股数据进行筛选
"""

import pandas as pd
import numpy as np
import akshare as ak
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import time
import sys

warnings.filterwarnings('ignore')

class RealDataStockScreener:
    """使用真实数据的股票筛选器"""
    
    def __init__(self):
        self.stock_basic_info = None
        self.trading_data = {}
        self.financial_data = {}
        self.industry_data = {}
        
    def get_stock_basic_info(self) -> pd.DataFrame:
        """获取A股基础信息"""
        print("正在获取A股基础信息...")
        try:
            # 获取A股基础信息
            stock_info = ak.stock_info_a_code_name()
            print(f"成功获取 {len(stock_info)} 只A股基础信息")
            return stock_info
        except Exception as e:
            print(f"获取A股基础信息失败: {e}")
            return pd.DataFrame()
    
    def get_stock_trading_data(self, stock_codes: List[str], max_stocks: int = 100) -> Dict:
        """获取股票交易数据"""
        print(f"正在获取前{max_stocks}只股票的交易数据...")
        trading_data = {}
        
        # 计算半年前的日期
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')
        
        for i, code in enumerate(stock_codes[:max_stocks]):
            try:
                print(f"获取 {code} 交易数据 ({i+1}/{max_stocks})")
                
                # 获取历史交易数据
                hist_data = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                             start_date=start_date, end_date=end_date, adjust="")
                
                if not hist_data.empty and len(hist_data) > 0:
                    # 计算日均成交金额（万元）
                    hist_data['成交金额'] = hist_data['成交量'] * hist_data['收盘'] / 10000
                    avg_amount = hist_data['成交金额'].mean()
                    latest_price = hist_data['收盘'].iloc[-1]
                    
                    trading_data[code] = {
                        'avg_trading_amount': avg_amount,
                        'latest_price': latest_price,
                        'trading_days': len(hist_data)
                    }
                
                # 添加延时避免请求过频
                time.sleep(0.2)
                
            except Exception as e:
                print(f"获取 {code} 交易数据失败: {e}")
                continue
        
        print(f"成功获取 {len(trading_data)} 只股票的交易数据")
        return trading_data
    
    def get_stock_financial_data(self, stock_codes: List[str], max_stocks: int = 100) -> Dict:
        """获取股票财务数据"""
        print(f"正在获取前{max_stocks}只股票的财务数据...")
        financial_data = {}
        
        for i, code in enumerate(stock_codes[:max_stocks]):
            try:
                print(f"获取 {code} 财务数据 ({i+1}/{max_stocks})")
                
                # 获取现金流量表数据
                try:
                    cash_flow = ak.stock_cash_flow_sheet_by_yearly_em(symbol=code)
                    if not cash_flow.empty:
                        # 获取最新年度数据
                        latest_year_data = cash_flow.iloc[0]
                        
                        # 提取关键财务指标
                        operating_cf = self._safe_convert_to_float(latest_year_data.get('经营活动产生的现金流量净额', 0))
                        investment_cf = self._safe_convert_to_float(latest_year_data.get('投资活动产生的现金流量净额', 0))
                        
                        # 计算自由现金流 = 经营现金流 + 投资现金流（投资现金流通常为负）
                        free_cash_flow = operating_cf + investment_cf
                        
                        financial_data[code] = {
                            'operating_cash_flow': operating_cf,
                            'investment_cash_flow': investment_cf,
                            'free_cash_flow': free_cash_flow,
                            'report_date': latest_year_data.get('报告期', ''),
                            'code': code
                        }
                except Exception as e:
                    print(f"获取 {code} 现金流数据失败: {e}")
                
                # 获取利润表数据
                try:
                    profit_data = ak.stock_profit_sheet_by_yearly_em(symbol=code)
                    if not profit_data.empty and code in financial_data:
                        latest_profit_data = profit_data.iloc[0]
                        net_profit = self._safe_convert_to_float(latest_profit_data.get('净利润', 0))
                        revenue = self._safe_convert_to_float(latest_profit_data.get('营业总收入', 0))
                        
                        financial_data[code]['net_profit'] = net_profit
                        financial_data[code]['revenue'] = revenue
                        
                        # 计算经营现金流/净利润比例
                        if net_profit != 0:
                            financial_data[code]['cf_to_profit_ratio'] = operating_cf / net_profit
                        else:
                            financial_data[code]['cf_to_profit_ratio'] = 0
                            
                except Exception as e:
                    print(f"获取 {code} 利润数据失败: {e}")
                
                # 获取ROE数据（简化处理，使用最近几年的ROE）
                try:
                    balance_sheet = ak.stock_balance_sheet_by_yearly_em(symbol=code)
                    if not balance_sheet.empty and code in financial_data:
                        # 计算ROE稳定性（这里简化处理）
                        if len(balance_sheet) >= 3:
                            # 使用净利润/净资产的变化来估算ROE稳定性
                            roe_proxy = []
                            for j in range(min(3, len(balance_sheet))):
                                equity = self._safe_convert_to_float(balance_sheet.iloc[j].get('归属于母公司所有者权益合计', 1))
                                if equity > 0 and code in financial_data:
                                    roe_proxy.append(financial_data[code]['net_profit'] / equity)
                            
                            if len(roe_proxy) > 1:
                                financial_data[code]['roe_stability'] = np.std(roe_proxy)
                            else:
                                financial_data[code]['roe_stability'] = 0.5  # 默认值
                        else:
                            financial_data[code]['roe_stability'] = 0.5
                            
                except Exception as e:
                    print(f"获取 {code} ROE数据失败: {e}")
                    if code in financial_data:
                        financial_data[code]['roe_stability'] = 0.5
                
                time.sleep(0.3)  # 增加延时
                
            except Exception as e:
                print(f"获取 {code} 财务数据失败: {e}")
                continue
        
        print(f"成功获取 {len(financial_data)} 只股票的财务数据")
        return financial_data
    
    def get_stock_industry_data(self, stock_codes: List[str], max_stocks: int = 100) -> Dict:
        """获取股票行业数据"""
        print(f"正在获取前{max_stocks}只股票的行业数据...")
        industry_data = {}
        
        try:
            # 获取股票行业分类
            industry_info = ak.stock_board_industry_name_em()
            
            for i, code in enumerate(stock_codes[:max_stocks]):
                try:
                    # 获取个股详细信息
                    stock_info = ak.stock_individual_info_em(symbol=code)
                    
                    if not stock_info.empty:
                        # 查找行业信息
                        industry_name = "未知"
                        for _, row in stock_info.iterrows():
                            item = str(row.get('item', ''))
                            if '行业' in item:
                                industry_name = str(row.get('value', '未知'))
                                break
                        
                        industry_data[code] = industry_name
                        print(f"{code}: {industry_name}")
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"获取 {code} 行业信息失败: {e}")
                    industry_data[code] = "未知"
                    continue
        
        except Exception as e:
            print(f"获取行业数据失败: {e}")
        
        print(f"成功获取 {len(industry_data)} 只股票的行业数据")
        return industry_data
    
    def _safe_convert_to_float(self, value) -> float:
        """安全转换为浮点数"""
        if pd.isna(value):
            return 0.0
        try:
            # 移除千分位分隔符和其他字符
            if isinstance(value, str):
                value = value.replace(',', '').replace('--', '0').replace('-', '0')
            return float(value)
        except:
            return 0.0
    
    def filter_basic_conditions(self) -> List[str]:
        """基础条件筛选"""
        print("\n1. 执行基础条件筛选...")
        
        if self.stock_basic_info is None or self.stock_basic_info.empty:
            print("   没有基础股票信息")
            return []
        
        # 剔除ST、*ST股票
        filtered = self.stock_basic_info[~self.stock_basic_info['name'].str.contains('ST|退|暂停', na=False)]
        
        print(f"   原始A股数量: {len(self.stock_basic_info)}")
        print(f"   剔除ST等风险股票后: {len(filtered)}")
        
        return filtered['code'].tolist()
    
    def filter_liquidity(self, stock_codes: List[str]) -> List[str]:
        """流动性筛选"""
        print("\n2. 执行流动性筛选...")
        
        # 计算成交金额排名
        valid_codes = [code for code in stock_codes if code in self.trading_data]
        amounts = [(code, self.trading_data[code]['avg_trading_amount']) for code in valid_codes]
        amounts.sort(key=lambda x: x[1], reverse=True)
        
        # 保留前80%（剔除后20%）
        keep_count = int(len(amounts) * 0.8)
        filtered_codes = [code for code, _ in amounts[:keep_count]]
        
        print(f"   有交易数据的股票: {len(valid_codes)}")
        print(f"   流动性筛选后: {len(filtered_codes)}")
        
        return filtered_codes
    
    def filter_industry(self, stock_codes: List[str]) -> List[str]:
        """行业筛选"""
        print("\n3. 执行行业筛选...")
        
        filtered_codes = []
        financial_keywords = ['银行', '保险', '证券', '金融', '房地产', '地产']
        
        for code in stock_codes:
            industry = self.industry_data.get(code, '未知')
            # 剔除金融和房地产行业
            if not any(keyword in industry for keyword in financial_keywords):
                filtered_codes.append(code)
        
        print(f"   行业筛选前: {len(stock_codes)}")
        print(f"   剔除金融房地产后: {len(filtered_codes)}")
        
        return filtered_codes
    
    def filter_roe_stability(self, stock_codes: List[str]) -> List[str]:
        """ROE稳定性筛选"""
        print("\n4. 执行ROE稳定性筛选...")
        
        # 获取有ROE稳定性数据的股票
        valid_codes = [code for code in stock_codes if code in self.financial_data and 'roe_stability' in self.financial_data[code]]
        
        if not valid_codes:
            print("   没有ROE稳定性数据，跳过此筛选")
            return stock_codes
        
        # 按ROE稳定性排序（标准差越小越稳定）
        roe_stability = [(code, self.financial_data[code]['roe_stability']) for code in valid_codes]
        roe_stability.sort(key=lambda x: x[1])  # 升序排序
        
        # 保留前90%（剔除后10%）
        keep_count = int(len(roe_stability) * 0.9)
        filtered_codes = [code for code, _ in roe_stability[:keep_count]]
        
        print(f"   有ROE数据的股票: {len(valid_codes)}")
        print(f"   ROE稳定性筛选后: {len(filtered_codes)}")
        
        return filtered_codes
    
    def filter_cash_flow_conditions(self, stock_codes: List[str]) -> List[str]:
        """现金流条件筛选"""
        print("\n5. 执行现金流条件筛选...")
        
        filtered_codes = []
        
        for code in stock_codes:
            if code not in self.financial_data:
                continue
            
            fin_data = self.financial_data[code]
            
            # 检查现金流条件
            operating_cf = fin_data.get('operating_cash_flow', 0)
            free_cf = fin_data.get('free_cash_flow', 0)
            
            # 要求经营现金流为正，自由现金流为正
            if operating_cf > 0 and free_cf > 0:
                filtered_codes.append(code)
        
        print(f"   现金流筛选前: {len(stock_codes)}")
        print(f"   现金流条件筛选后: {len(filtered_codes)}")
        
        return filtered_codes
    
    def filter_operating_quality(self, stock_codes: List[str]) -> List[str]:
        """经营质量筛选"""
        print("\n6. 执行经营质量筛选...")
        
        # 计算经营现金流/净利润比例
        quality_ratios = []
        
        for code in stock_codes:
            if code not in self.financial_data:
                continue
            
            fin_data = self.financial_data[code]
            cf_to_profit_ratio = fin_data.get('cf_to_profit_ratio', 0)
            
            if cf_to_profit_ratio > 0:  # 只考虑比例为正的情况
                quality_ratios.append((code, cf_to_profit_ratio))
        
        if not quality_ratios:
            print("   没有有效的经营质量数据，跳过此筛选")
            return stock_codes
        
        # 按比例降序排序
        quality_ratios.sort(key=lambda x: x[1], reverse=True)
        
        # 保留前70%（剔除后30%）
        keep_count = int(len(quality_ratios) * 0.7)
        filtered_codes = [code for code, _ in quality_ratios[:keep_count]]
        
        print(f"   有经营质量数据的股票: {len(quality_ratios)}")
        print(f"   经营质量筛选后: {len(filtered_codes)}")
        
        return filtered_codes
    
    def calculate_fcf_yield_and_select_top(self, stock_codes: List[str], top_n: int = 100) -> List[Tuple[str, float]]:
        """计算自由现金流率并选取前N只"""
        print(f"\n7. 计算自由现金流率并选取前{top_n}只...")
        
        fcf_yields = []
        
        for code in stock_codes:
            if code not in self.financial_data or code not in self.trading_data:
                continue
            
            fin_data = self.financial_data[code]
            trading_data = self.trading_data[code]
            
            free_cash_flow = fin_data.get('free_cash_flow', 0)
            latest_price = trading_data.get('latest_price', 0)
            
            if free_cash_flow > 0 and latest_price > 0:
                # 简化计算：假设流通股本为1亿股
                market_cap = latest_price * 100000000  # 市值
                fcf_yield = free_cash_flow * 10000 / market_cap  # 自由现金流率
                
                fcf_yields.append((code, fcf_yield))
        
        # 按自由现金流率降序排序
        fcf_yields.sort(key=lambda x: x[1], reverse=True)
        
        # 选取前N只
        selected = fcf_yields[:min(top_n, len(fcf_yields))]
        
        print(f"   计算出FCF收益率的股票: {len(fcf_yields)}")
        print(f"   最终选取股票数: {len(selected)}")
        
        return selected
    
    def calculate_weights(self, selected_stocks: List[Tuple[str, float]]) -> Dict[str, float]:
        """计算股票权重"""
        print("\n8. 计算股票权重...")
        
        if not selected_stocks:
            return {}
        
        # 按自由现金流计算权重
        fcf_values = []
        for code, _ in selected_stocks:
            if code in self.financial_data:
                fcf = max(self.financial_data[code].get('free_cash_flow', 0), 0)
                fcf_values.append(fcf)
            else:
                fcf_values.append(0)
        
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
            # 等权重分配
            equal_weight = 1.0 / len(selected_stocks)
            for code, _ in selected_stocks:
                weights[code] = equal_weight
        
        max_weight = max(weights.values()) if weights else 0
        min_weight = min(weights.values()) if weights else 0
        
        print(f"   权重计算完成")
        print(f"   最大权重: {max_weight:.4f} ({max_weight*100:.2f}%)")
        print(f"   最小权重: {min_weight:.4f} ({min_weight*100:.2f}%)")
        
        return weights
    
    def run_screening(self, max_initial_stocks: int = 100) -> Tuple[List[str], Dict[str, float], List[Tuple[str, float]]]:
        """执行完整筛选流程"""
        print("=" * 60)
        print("国证自由现金流指数股票筛选 - 真实数据版本")
        print("=" * 60)
        
        # 1. 获取基础股票信息
        self.stock_basic_info = self.get_stock_basic_info()
        if self.stock_basic_info.empty:
            print("无法获取股票基础信息")
            return [], {}, []
        
        # 2. 基础条件筛选
        stock_codes = self.filter_basic_conditions()
        if not stock_codes:
            print("基础筛选后无股票")
            return [], {}, []
        
        # 限制处理的股票数量以避免API限制
        if len(stock_codes) > max_initial_stocks:
            print(f"限制处理前{max_initial_stocks}只股票以避免API限制")
            stock_codes = stock_codes[:max_initial_stocks]
        
        # 3. 获取各类数据
        self.trading_data = self.get_stock_trading_data(stock_codes, max_initial_stocks)
        self.industry_data = self.get_stock_industry_data(stock_codes, max_initial_stocks)
        self.financial_data = self.get_stock_financial_data(stock_codes, max_initial_stocks)
        
        # 4. 执行筛选流程
        stock_codes = self.filter_liquidity(stock_codes)
        stock_codes = self.filter_industry(stock_codes)
        stock_codes = self.filter_roe_stability(stock_codes)
        stock_codes = self.filter_cash_flow_conditions(stock_codes)
        stock_codes = self.filter_operating_quality(stock_codes)
        
        # 5. 计算FCF收益率并选取
        selected_stocks = self.calculate_fcf_yield_and_select_top(stock_codes, 100)
        
        # 6. 计算权重
        final_codes = [code for code, _ in selected_stocks]
        weights = self.calculate_weights(selected_stocks)
        
        return final_codes, weights, selected_stocks

def main():
    """主函数"""
    print("开始运行国证自由现金流指数股票筛选器...")
    
    # 创建筛选器
    screener = RealDataStockScreener()
    
    try:
        # 执行筛选（限制处理100只股票）
        selected_codes, weights, selected_stocks = screener.run_screening(max_initial_stocks=100)
        
        # 输出结果
        print("\n" + "=" * 60)
        print("筛选结果汇总")
        print("=" * 60)
        
        if selected_codes and weights:
            # 创建结果表格
            results = []
            
            for i, (code, fcf_yield) in enumerate(selected_stocks):
                weight = weights.get(code, 0)
                
                # 获取股票信息
                stock_name = "未知"
                if screener.stock_basic_info is not None:
                    name_row = screener.stock_basic_info[screener.stock_basic_info['code'] == code]
                    if not name_row.empty:
                        stock_name = name_row.iloc[0]['name']
                
                industry = screener.industry_data.get(code, '未知')
                
                fin_data = screener.financial_data.get(code, {})
                trading_data = screener.trading_data.get(code, {})
                
                results.append({
                    '排名': i + 1,
                    '股票代码': code,
                    '股票名称': stock_name,
                    '所属行业': industry,
                    '自由现金流率': f"{fcf_yield:.6f}",
                    '权重': f"{weight:.4f}",
                    '权重百分比': f"{weight*100:.2f}%",
                    '自由现金流(万元)': f"{fin_data.get('free_cash_flow', 0):,.0f}",
                    '经营现金流(万元)': f"{fin_data.get('operating_cash_flow', 0):,.0f}",
                    '最新股价(元)': f"{trading_data.get('latest_price', 0):.2f}"
                })
            
            results_df = pd.DataFrame(results)
            
            # 显示结果
            print(f"\n入选股票详情（共{len(results)}只）:")
            print("-" * 120)
            print(results_df.to_string(index=False))
            
            # 保存结果
            results_df.to_csv('/workspace/fcf_index_real_results.csv', index=False, encoding='utf-8-sig')
            print(f"\n结果已保存到: fcf_index_real_results.csv")
            
            # 统计信息
            print(f"\n统计信息:")
            print(f"- 入选股票总数: {len(selected_codes)}")
            print(f"- 权重总和: {sum(weights.values()):.6f}")
            print(f"- 最大权重: {max(weights.values()):.4f} ({max(weights.values())*100:.2f}%)")
            print(f"- 最小权重: {min(weights.values()):.4f} ({min(weights.values())*100:.2f}%)")
            print(f"- 平均权重: {np.mean(list(weights.values())):.4f} ({np.mean(list(weights.values()))*100:.2f}%)")
            
            # 行业分布
            industry_count = {}
            for code in selected_codes:
                industry = screener.industry_data.get(code, '未知')
                industry_count[industry] = industry_count.get(industry, 0) + 1
            
            print(f"\n行业分布:")
            for industry, count in sorted(industry_count.items(), key=lambda x: x[1], reverse=True):
                print(f"- {industry}: {count}只")
            
        else:
            print("未筛选出符合条件的股票")
    
    except Exception as e:
        print(f"筛选过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n程序执行完成！")

if __name__ == "__main__":
    main()