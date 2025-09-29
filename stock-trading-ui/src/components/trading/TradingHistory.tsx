'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { cn, formatNumber, formatDateTime } from '@/lib/utils';
import { useOrders } from '@/stores/tradingStore';
import {
  History,
  Search,
  Filter,
  Download,
  MoreHorizontal,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  TrendingUp,
  TrendingDown
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface TradingHistoryProps {
  className?: string;
  maxRows?: number;
}

export function TradingHistory({ className, maxRows }: TradingHistoryProps) {
  const orders = useOrders();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'timestamp' | 'symbol' | 'quantity' | 'status'>('timestamp');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Filter and sort orders
  const filteredOrders = useMemo(() => {
    let filtered = orders.filter(order => {
      const matchesSearch = order.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           order.id.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || order.status === statusFilter;
      const matchesType = typeFilter === 'all' || order.type === typeFilter;

      return matchesSearch && matchesStatus && matchesType;
    });

    // Sort orders
    filtered.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortBy) {
        case 'timestamp':
          aValue = a.timestamp;
          bValue = b.timestamp;
          break;
        case 'symbol':
          aValue = a.symbol;
          bValue = b.symbol;
          break;
        case 'quantity':
          aValue = a.quantity;
          bValue = b.quantity;
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        default:
          return 0;
      }

      if (typeof aValue === 'string') {
        return sortOrder === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
    });

    return maxRows ? filtered.slice(0, maxRows) : filtered;
  }, [orders, searchTerm, statusFilter, typeFilter, sortBy, sortOrder, maxRows]);

  const handleSort = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'filled':
        return <CheckCircle className="h-3 w-3 text-green-400" />;
      case 'cancelled':
        return <XCircle className="h-3 w-3 text-red-400" />;
      case 'pending':
        return <Clock className="h-3 w-3 text-yellow-400" />;
      case 'partial':
        return <AlertCircle className="h-3 w-3 text-blue-400" />;
      default:
        return <Clock className="h-3 w-3 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClasses = "text-xs font-medium px-2 py-1 rounded-full";

    switch (status) {
      case 'filled':
        return <Badge className={cn(baseClasses, "bg-green-500/20 text-green-400 border-green-500/30")}>Filled</Badge>;
      case 'cancelled':
        return <Badge className={cn(baseClasses, "bg-red-500/20 text-red-400 border-red-500/30")}>Cancelled</Badge>;
      case 'pending':
        return <Badge className={cn(baseClasses, "bg-yellow-500/20 text-yellow-400 border-yellow-500/30")}>Pending</Badge>;
      case 'partial':
        return <Badge className={cn(baseClasses, "bg-blue-500/20 text-blue-400 border-blue-500/30")}>Partial</Badge>;
      default:
        return <Badge className={cn(baseClasses, "bg-gray-500/20 text-gray-400 border-gray-500/30")}>Unknown</Badge>;
    }
  };

  return (
    <Card className={cn("card-professional", className)}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-3 text-white">
            <div className="icon-bg-blue">
              <History className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-bold">Trading History</div>
              <div className="text-xs text-gray-400 font-normal">
                {filteredOrders.length} order{filteredOrders.length !== 1 ? 's' : ''}
              </div>
            </div>
          </CardTitle>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="ghost"
              className="h-8 px-2 text-xs text-gray-400 hover:text-white"
            >
              <Download className="h-3 w-3 mr-1" />
              Export
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0 text-gray-400 hover:text-white"
            >
              <MoreHorizontal className="h-3 w-3" />
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3 mt-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-3 w-3 text-gray-400" />
            <Input
              placeholder="Search by symbol or order ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-professional pl-9 h-8 text-xs"
            />
          </div>

          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-full sm:w-[120px] h-8 text-xs select-professional">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="filled">Filled</SelectItem>
              <SelectItem value="partial">Partial</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>

          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-full sm:w-[100px] h-8 text-xs select-professional">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="buy">Buy</SelectItem>
              <SelectItem value="sell">Sell</SelectItem>
            </SelectContent>
          </Select>

          <Button
            size="sm"
            variant="ghost"
            className="h-8 w-8 p-0 text-gray-400 hover:text-white"
          >
            <Filter className="h-3 w-3" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {filteredOrders.length === 0 ? (
          <div className="p-8 text-center">
            <div className="w-12 h-12 bg-gray-700/50 rounded-full flex items-center justify-center mx-auto mb-3">
              <History className="h-6 w-6 text-gray-500" />
            </div>
            <h4 className="text-sm font-medium text-gray-400 mb-2">
              {searchTerm ? 'No Orders Found' : 'No Trading History'}
            </h4>
            <p className="text-xs text-gray-500">
              {searchTerm
                ? 'Try adjusting your search filters'
                : 'Your trading orders will appear here'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-gray-700">
                  <TableHead
                    className="h-10 cursor-pointer hover:bg-gray-700 text-gray-300 text-xs"
                    onClick={() => handleSort('timestamp')}
                  >
                    Time
                    {sortBy === 'timestamp' && (
                      <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </TableHead>
                  <TableHead
                    className="h-10 cursor-pointer hover:bg-gray-700 text-gray-300 text-xs"
                    onClick={() => handleSort('symbol')}
                  >
                    Pair
                    {sortBy === 'symbol' && (
                      <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </TableHead>
                  <TableHead className="h-10 text-gray-300 text-xs">Type</TableHead>
                  <TableHead className="h-10 text-gray-300 text-xs">Order</TableHead>
                  <TableHead
                    className="h-10 cursor-pointer hover:bg-gray-700 text-gray-300 text-xs text-right"
                    onClick={() => handleSort('quantity')}
                  >
                    Amount
                    {sortBy === 'quantity' && (
                      <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </TableHead>
                  <TableHead className="h-10 text-gray-300 text-xs text-right">Price</TableHead>
                  <TableHead className="h-10 text-gray-300 text-xs text-right">Total</TableHead>
                  <TableHead
                    className="h-10 cursor-pointer hover:bg-gray-700 text-gray-300 text-xs"
                    onClick={() => handleSort('status')}
                  >
                    Status
                    {sortBy === 'status' && (
                      <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </TableHead>
                  <TableHead className="h-10 text-gray-300 text-xs">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <AnimatePresence>
                  {filteredOrders.map((order, index) => (
                    <motion.tr
                      key={order.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ duration: 0.2, delay: index * 0.05 }}
                      className="border-gray-700 hover:bg-gray-700/30"
                    >
                      <TableCell className="text-xs text-gray-300">
                        {formatDateTime(new Date(order.timestamp).toISOString())}
                      </TableCell>
                      <TableCell className="text-xs font-mono font-bold text-white">
                        {order.symbol}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          {order.type === 'buy' ? (
                            <TrendingUp className="h-3 w-3 text-green-400" />
                          ) : (
                            <TrendingDown className="h-3 w-3 text-red-400" />
                          )}
                          <span className={cn(
                            "text-xs font-medium",
                            order.type === 'buy' ? "text-green-400" : "text-red-400"
                          )}>
                            {order.type.toUpperCase()}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="text-xs text-gray-300 capitalize">
                          {order.orderType}
                        </span>
                      </TableCell>
                      <TableCell className="text-right text-xs font-mono text-white">
                        {formatNumber(order.quantity, { decimals: 6 })}
                      </TableCell>
                      <TableCell className="text-right text-xs font-mono text-white">
                        {order.price ? `$${formatNumber(order.price, { decimals: 2 })}` : 'Market'}
                      </TableCell>
                      <TableCell className="text-right text-xs font-mono text-white">
                        ${formatNumber((order.quantity * (order.price || 0)), { decimals: 2 })}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(order.status)}
                          {getStatusBadge(order.status)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 w-6 p-0 text-gray-400 hover:text-white"
                        >
                          <MoreHorizontal className="h-3 w-3" />
                        </Button>
                      </TableCell>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}