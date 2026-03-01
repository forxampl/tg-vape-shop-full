export interface OrderItem {
  product_id: number;
  quantity: number;
  flavor_id?: number;
}

export interface CreateOrderRequest {
  user_id: number;
  items: OrderItem[];
  delivery_address: string;
  phone_number?: string;
  comment?: string;
  total_amount: number;
}

export interface OrderResponse {
  id: number;
  user_id: number;
  status: string;
  total_amount: number;
  created_at: string;
  items: OrderItem[];
}