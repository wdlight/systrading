import yaml

from utils import KoreaInvestEnv, KoreaInvestAPI

def main():
  with open('config.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

  env_cls = KoreaInvestEnv(config)
  base_headers = env_cls.get_base_headers()
  cfg = env_cls.get_full_config()
  korea_invest_api = KoreaInvestAPI(cfg, base_headers=base_headers)

  print(korea_invest_api)
  print ( "------------------- Initialized -----------------\n\n")


  print ( "------------------- 삼성전자(005930) 현재가 -----------------")
  
  price_info_map = korea_invest_api.get_current_price("005930")
  print (price_info_map)

  print ( "\n\n------------------- 매도 호가 -----------------\n\n")
  price_info_map = korea_invest_api.get_hoga_info("005930")
  print (price_info_map)

  print ( "\n\n------------------- 종목별 잔고 -----------------\n\n")
  account_balance, details_df = korea_invest_api.get_acct_balance()
  print('$$$$$$$ 종목별 잔고 $$$$$$$$')
  print( details_df)


  print ( "\n\n------------------- 등락율 순위 -----------------\n\n")
  ranking_df = korea_invest_api.get_fluctuation_ranking()
  print(ranking_df)


  # 맥쿼리 : 088980
  # 모나미 : 005360
  print ( "\n\n------------------- 매수 test -----------------\n\n")
  res = korea_invest_api.buy_order("005360", order_qty=1, order_price=2465, order_type="00") # 삼성전자?
  order_num = res.get_body().output['ODNO']
  print(f"주문 접수 결과: {res.get_body()}")

  # print ( "\n\n------------------- 매도 test -----------------\n\n")
  # res = korea_invest_api.buy_order("005360", order_qty=1, order_price=60000, order_type="01") # 삼성전자?
  # print(f"주문 접수 결과: {res.get_body()}")
  
  
  print ( "---------------- 취소 주문 ----------------")
  res = korea_invest_api.cancel_order( order_no=order_num, order_qty = 1)

if __name__ == '__main__':
  main()