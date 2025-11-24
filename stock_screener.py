"""
国证自由现金流指数股票筛选器
根据文档规则筛选股票并计算权重
"""

import pandas as pd
import numpy as np
import akshare as ak
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import time

warnings.filterwarnings('ignore')

class StockScreener:
    """股票筛选器类"""
    
    def __init__(self):
        self.stocks_data = None
        self.financial_data = None
        self.industry_data = None
        self.trading_data = None
        
    def get_stock_basic_info(self) -> pd.DataFrame:
        """获取股票基础信息"""
        print("正在获取股票基础信息...")
        try:
            # 获取A股基础信息
            stock_info = ak.stock_info_a_code_name()
            print(f"获取到 {len(stock_info)} 只股票的基础信息")
            return stock_info
        except Exception as e:
            print(f"获取股票基础信息失败: {e}")
            return pd.DataFrame()
    
    def get_financial_data(self, stock_codes: List[str]) -> Dict:
        """获取财务数据"""
        print("正在获取财务数据...")
        financial_dict = {}
        
        for i, code in enumerate(stock_codes[:50]):  # 限制前50只股票进行测试
            try:
                print(f"获取 {code} 财务数据 ({i+1}/{min(50, len(stock_codes))})")
                
                # 获取现金流量表数据
                cash_flow = ak.stock_cash_flow_sheet_by_yearly_em(symbol=code)
                if not cash_flow.empty:
                    financial_dict[code] = {
                        'cash_flow': cash_flow,
                        'code': code
                    }
                
                # 添加延时避免请求过频
                time.sleep(0.1)
                
            except Exception as e:
                print(f"获取 {code} 财务数据失败: {e}")
                continue
        
        print(f"成功获取 {len(financial_dict)} 只股票的财务数据")
        return financial_dict
    
    def get_trading_data(self, stock_codes: List[str]) -> Dict:
        """获取交易数据"""
        print("正在获取交易数据...")
        trading_dict = {}
        
        # 计算半年前的日期
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')
        
        for i, code in enumerate(stock_codes[:50]):  # 限制前50只股票
            try:
                print(f"获取 {code} 交易数据 ({i+1}/{min(50, len(stock_codes))})")
                
                # 获取历史交易数据
                hist_data = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                             start_date=start_date, end_date=end_date)
                
                if not hist_data.empty:
                    # 计算日均成交金额
                    hist_data['成交金额'] = hist_data['成交量'] * hist_data['收盘']
                    avg_amount = hist_data['成交金额'].mean()
                    
                    trading_dict[code] = {
                        'avg_trading_amount': avg_amount,
                        'latest_price': hist_data['收盘'].iloc[-1] if len(hist_data) > 0 else 0
                    }
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"获取 {code} 交易数据失败: {e}")
                continue
        
        print(f"成功获取 {len(trading_dict)} 只股票的交易数据")
        return trading_dict
    
    def get_industry_classification(self, stock_codes: List[str]) -> Dict:
        """获取行业分类数据"""
        print("正在获取行业分类数据...")
        industry_dict = {}
        
        try:
            # 获取行业分类数据
            industry_data = ak.stock_board_industry_name_em()
            
            for code in stock_codes[:50]:  # 限制前50只股票
                try:
                    # 获取个股行业信息
                    stock_industry = ak.stock_individual_info_em(symbol=code)
                    if not stock_industry.empty:
                        # 查找行业信息
                        industry_name = "未知"
                        for _, row in stock_industry.iterrows():
                            if "行业" in str(row.get('item', '')):
                                industry_name = str(row.get('value', '未知'))
                                break
                        
                        industry_dict[code] = industry_name
                    
                    time.sleep(0.05)
                    
                except Exception as e:
                    print(f"获取 {code} 行业信息失败: {e}")
                    industry_dict[code] = "未知"
                    continue
        
        except Exception as e:
            print(f"获取行业分类数据失败: {e}")
        
        print(f"成功获取 {len(industry_dict)} 只股票的行业分类")
        return industry_dict
    
    def filter_basic_conditions(self, stock_info: pd.DataFrame) -> pd.DataFrame:
        """基础条件筛选"""
        print("执行基础条件筛选...")
        
        # 剔除ST股票
        filtered = stock_info[~stock_info['name'].str.contains('ST|退', na=False)]
        print(f"剔除ST股票后剩余: {len(filtered)} 只")
        
        # 这里简化处理上市时间筛选，实际应该获取上市日期数据
        # 由于数据获取限制，我们保留所有非ST股票
        
        return filtered
    
    def filter_liquidity(self, stock_codes: List[str], trading_data: Dict) -> List[str]:
        """流动性筛选 - 剔除成交金额排名后20%"""
        print("执行流动性筛选...")
        
        # 计算成交金额排名
        amounts = [(code, data['avg_trading_amount']) for code, data in trading_data.items()]
        amounts.sort(key=lambda x: x[1], reverse=True)
        
        # 剔除后20%
        keep_count = int(len(amounts) * 0.8)
        filtered_codes = [code for code, _ in amounts[:keep_count]]
        
        print(f"流动性筛选后剩余: {len(filtered_codes)} 只")
        return filtered_codes
    
    def filter_industry(self, stock_codes: List[str], industry_data: Dict) -> List[str]:
        """行业筛选 - 剔除金融和房地产"""
        print("执行行业筛选...")
        
        filtered_codes = []
        for code in stock_codes:
            industry = industry_data.get(code, "未知")
            # 剔除金融和房地产行业
            if not any(keyword in industry for keyword in ['银行', '保险', '证券', '金融', '房地产', '地产']):
                filtered_codes.append(code)
        
        print(f"行业筛选后剩余: {len(filtered_codes)} 只")
        return filtered_codes
    
    def calculate_free_cash_flow_metrics(self, financial_data: Dict) -> Dict:
        """计算自由现金流相关指标"""
        print("计算自由现金流指标...")
        
        metrics = {}
        
        for code, data in financial_data.items():
            try:
                cash_flow_df = data['cash_flow']
                if cash_flow_df.empty:
                    continue
                
                # 获取最近一年的数据
                latest_data = cash_flow_df.iloc[0] if len(cash_flow_df) > 0 else None
                if latest_data is None:
                    continue
                
                # 提取关键指标（这里使用模拟数据，实际需要根据具体字段名调整）
                operating_cash_flow = self._extract_numeric_value(latest_data, ['经营活动产生的现金流量净额', '经营现金流'])
                capex = self._extract_numeric_value(latest_data, ['购建固定资产、无形资产和其他长期资产支付的现金', '资本支出'])
                
                # 计算自由现金流 = 经营现金流 - 资本支出
                free_cash_flow = operating_cash_flow - abs(capex) if operating_cash_flow and capex else None
                
                # 模拟企业价值（实际应该用市值+净债务）
                enterprise_value = abs(operating_cash_flow) * 10 if operating_cash_flow else None
                
                # 计算自由现金流率
                fcf_yield = free_cash_flow / enterprise_value if free_cash_flow and enterprise_value and enterprise_value != 0 else 0
                
                metrics[code] = {
                    'free_cash_flow': free_cash_flow or 0,
                    'operating_cash_flow': operating_cash_flow or 0,
                    'enterprise_value': enterprise_value or 0,
                    'fcf_yield': fcf_yield,
                    'valid': free_cash_flow and free_cash_flow > 0 and operating_cash_flow and operating_cash_flow > 0
                }
                
            except Exception as e:
                print(f"计算 {code} 现金流指标失败: {e}")
                continue
        
        print(f"成功计算 {len(metrics)} 只股票的现金流指标")
        return metrics
    
    def _extract_numeric_value(self, data_row, field_names: List[str]) -> Optional[float]:
        """从数据行中提取数值"""
        for field in field_names:
            for key, value in data_row.items():
                if field in str(key):
                    try:
                        # 清理数据并转换为数值
                        if pd.isna(value):
                            continue
                        value_str = str(value).replace(',', '').replace('--', '0')
                        return float(value_str)
                    except:
                        continue
        return None
    
    def filter_cash_flow_conditions(self, stock_codes: List[str], fcf_metrics: Dict) -> List[str]:
        """现金流条件筛选"""
        print("执行现金流条件筛选...")
        
        filtered_codes = []
        for code in stock_codes:
            metrics = fcf_metrics.get(code, {})
            if metrics.get('valid', False):
                filtered_codes.append(code)
        
        print(f"现金流筛选后剩余: {len(filtered_codes)} 只")
        return filtered_codes
    
    def select_top_stocks(self, stock_codes: List[str], fcf_metrics: Dict, top_n: int = 100) -> List[Tuple[str, float]]:
        """按自由现金流率排序选取前N只股票"""
        print(f"按自由现金流率排序选取前{top_n}只...")
        
        # 创建排序列表
        stock_yields = []
        for code in stock_codes:
            metrics = fcf_metrics.get(code, {})
            fcf_yield = metrics.get('fcf_yield', 0)
            if fcf_yield > 0:
                stock_yields.append((code, fcf_yield))
        
        # 按自由现金流率降序排序
        stock_yields.sort(key=lambda x: x[1], reverse=True)
        
        # 选取前N只
        selected = stock_yields[:min(top_n, len(stock_yields))]
        print(f"最终选取 {len(selected)} 只股票")
        
        return selected
    
    def calculate_weights(self, selected_stocks: List[Tuple[str, float]], fcf_metrics: Dict) -> Dict[str, float]:
        """计算股票权重"""
        print("计算股票权重...")
        
        weights = {}
        total_fcf = sum(fcf_metrics.get(code, {}).get('free_cash_flow', 0) for code, _ in selected_stocks)
        
        if total_fcf <= 0:
            # 如果总自由现金流为0或负数，使用等权重
            equal_weight = 1.0 / len(selected_stocks)
            for code, _ in selected_stocks:
                weights[code] = equal_weight
        else:
            # 按自由现金流计算初始权重
            for code, _ in selected_stocks:
                fcf = fcf_metrics.get(code, {}).get('free_cash_flow', 0)
                initial_weight = fcf / total_fcf if fcf > 0 else 0
                
                # 限制单只股票权重不超过10%
                final_weight = min(initial_weight, 0.10)
                weights[code] = final_weight
            
            # 重新标准化权重
            total_weight = sum(weights.values())
            if total_weight > 0:
                for code in weights:
                    weights[code] = weights[code] / total_weight
        
        print(f"权重计算完成，最大权重: {max(weights.values()):.4f}")
        return weights
    
    def run_screening(self) -> Tuple[List[str], Dict[str, float]]:
        """执行完整的股票筛选流程"""
        print("开始执行股票筛选流程...")
        
        # 1. 获取基础股票信息
        stock_info = self.get_stock_basic_info()
        if stock_info.empty:
            print("无法获取股票基础信息，筛选终止")
            return [], {}
        
        # 2. 基础条件筛选
        filtered_stocks = self.filter_basic_conditions(stock_info)
        stock_codes = filtered_stocks['code'].tolist()
        
        # 3. 获取各类数据
        trading_data = self.get_trading_data(stock_codes)
        industry_data = self.get_industry_classification(stock_codes)
        financial_data = self.get_financial_data(stock_codes)
        
        # 4. 执行各项筛选
        # 流动性筛选
        stock_codes = self.filter_liquidity(stock_codes, trading_data)
        
        # 行业筛选
        stock_codes = self.filter_industry(stock_codes, industry_data)
        
        # 计算现金流指标
        fcf_metrics = self.calculate_free_cash_flow_metrics(financial_data)
        
        # 现金流条件筛选
        stock_codes = self.filter_cash_flow_conditions(stock_codes, fcf_metrics)
        
        # 5. 选取前100只股票
        selected_stocks = self.select_top_stocks(stock_codes, fcf_metrics, 100)
        
        # 6. 计算权重
        final_codes = [code for code, _ in selected_stocks]
        weights = self.calculate_weights(selected_stocks, fcf_metrics)
        
        print("股票筛选流程完成！")
        return final_codes, weights

def main():
    """主函数"""
    print("=" * 60)
    print("国证自由现金流指数股票筛选器")
    print("=" * 60)
    
    # 创建筛选器实例
    screener = StockScreener()
    
    # 执行筛选
    selected_stocks, weights = screener.run_screening()
    
    # 输出结果
    print("\n" + "=" * 60)
    print("筛选结果")
    print("=" * 60)
    
    if selected_stocks and weights:
        print(f"\n成功筛选出 {len(selected_stocks)} 只股票:")
        print("-" * 40)
        
        # 创建结果DataFrame
        results = []
        for code in selected_stocks:
            weight = weights.get(code, 0)
            results.append({
                '股票代码': code,
                '权重': f"{weight:.4f}",
                '权重百分比': f"{weight*100:.2f}%"
            })
        
        results_df = pd.DataFrame(results)
        print(results_df.to_string(index=False))
        
        # 保存结果到文件
        results_df.to_csv('/workspace/stock_selection_results.csv', index=False, encoding='utf-8-sig')
        print(f"\n结果已保存到: /workspace/stock_selection_results.csv")
        
        # 统计信息
        print(f"\n统计信息:")
        print(f"- 总股票数: {len(selected_stocks)}")
        print(f"- 权重总和: {sum(weights.values()):.4f}")
        print(f"- 最大权重: {max(weights.values()):.4f} ({max(weights.values())*100:.2f}%)")
        print(f"- 最小权重: {min(weights.values()):.4f} ({min(weights.values())*100:.2f}%)")
        
    else:
        print("未能筛选出符合条件的股票")
    
    print("\n程序执行完成！")

if __name__ == "__main__":
    main()