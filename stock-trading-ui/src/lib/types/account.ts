export interface Position {
  stock_code: string;
  stock_name: string;
  quantity: number;
  sellable_quantity: number;
  avg_price: number;
  current_price: number;
  unrealized_pnl: number;
  profit_rate: number;
  day_change: number;
  day_change_rate: number;
}

export interface AccountBalance {
  total_value: number;
  available_cash: number;
  total_purchase_amount: number;
  total_evaluation_amount: number;
  total_profit_loss: number;
  total_profit_loss_rate: number;
  positions: Position[];
}
