// 샘플 데이터 생성 및 관리
class SampleDataGenerator {
    constructor() {
        this.stockData = [
            {
                code: '005930',
                name: '삼성전자',
                price: 71500,
                change: 1200,
                changePercent: 1.71,
                volume: 12500000,
                high: 72000,
                low: 70800,
                rsi: 64.5,
                macd: 850.2,
                signal: 720.8
            },
            {
                code: '000660',
                name: 'SK하이닉스',
                price: 128000,
                change: -2500,
                changePercent: -1.92,
                volume: 8200000,
                high: 131000,
                low: 127500,
                rsi: 42.1,
                macd: -1250.5,
                signal: -980.2
            },
            {
                code: '035420',
                name: 'NAVER',
                price: 185000,
                change: 3500,
                changePercent: 1.93,
                volume: 650000,
                high: 186500,
                low: 182000,
                rsi: 68.9,
                macd: 2100.3,
                signal: 1850.1
            },
            {
                code: '207940',
                name: '삼성바이오로직스',
                price: 795000,
                change: -15000,
                changePercent: -1.85,
                volume: 85000,
                high: 815000,
                low: 790000,
                rsi: 38.7,
                macd: -5200.8,
                signal: -4100.2
            },
            {
                code: '373220',
                name: 'LG에너지솔루션',
                price: 485000,
                change: 8000,
                changePercent: 1.68,
                volume: 420000,
                high: 490000,
                low: 481000,
                rsi: 61.2,
                macd: 3150.7,
                signal: 2800.5
            }
        ];

        this.portfolioData = {
            totalValue: 45650000,
            totalCost: 42800000,
            totalGain: 2850000,
            totalGainPercent: 6.66,
            dayGain: 125000,
            dayGainPercent: 0.27,
            buyingPower: 3200000
        };

        this.positions = [
            {
                code: '005930',
                name: '삼성전자',
                shares: 150,
                avgPrice: 69500,
                currentPrice: 71500,
                totalValue: 10725000,
                gain: 300000,
                gainPercent: 2.88
            },
            {
                code: '000660',
                name: 'SK하이닉스',
                shares: 80,
                avgPrice: 130000,
                currentPrice: 128000,
                totalValue: 10240000,
                gain: -160000,
                gainPercent: -1.54
            },
            {
                code: '035420',
                name: 'NAVER',
                shares: 60,
                avgPrice: 178000,
                currentPrice: 185000,
                totalValue: 11100000,
                gain: 420000,
                gainPercent: 3.93
            }
        ];

        this.initializeRealTimeUpdates();
    }

    // 실시간 데이터 업데이트 시뮬레이션
    initializeRealTimeUpdates() {
        setInterval(() => {
            this.updateStockPrices();
            this.updatePortfolio();
            this.notifyUpdate();
        }, 3000);
    }

    updateStockPrices() {
        this.stockData.forEach(stock => {
            // 가격 변동 (-1% ~ +1%)
            const changePercent = (Math.random() - 0.5) * 0.02;
            const priceChange = Math.round(stock.price * changePercent);

            stock.price += priceChange;
            stock.change += priceChange;
            stock.changePercent = ((stock.change / (stock.price - stock.change)) * 100);

            // RSI, MACD 업데이트
            stock.rsi += (Math.random() - 0.5) * 2;
            stock.rsi = Math.max(0, Math.min(100, stock.rsi));

            stock.macd += (Math.random() - 0.5) * 100;
            stock.signal += (Math.random() - 0.5) * 80;
        });
    }

    updatePortfolio() {
        // 포트폴리오 실시간 계산
        let totalValue = 0;
        let totalCost = 0;

        this.positions.forEach(position => {
            const currentStock = this.stockData.find(s => s.code === position.code);
            if (currentStock) {
                position.currentPrice = currentStock.price;
                position.totalValue = position.shares * position.currentPrice;
                position.gain = position.totalValue - (position.shares * position.avgPrice);
                position.gainPercent = (position.gain / (position.shares * position.avgPrice)) * 100;

                totalValue += position.totalValue;
                totalCost += position.shares * position.avgPrice;
            }
        });

        this.portfolioData.totalValue = totalValue + this.portfolioData.buyingPower;
        this.portfolioData.totalCost = totalCost;
        this.portfolioData.totalGain = totalValue - totalCost;
        this.portfolioData.totalGainPercent = (this.portfolioData.totalGain / totalCost) * 100;
    }

    notifyUpdate() {
        // 커스텀 이벤트 발송
        window.dispatchEvent(new CustomEvent('dataUpdate', {
            detail: {
                stocks: this.stockData,
                portfolio: this.portfolioData,
                positions: this.positions
            }
        }));
    }

    // 차트 데이터 생성
    generateChartData(days = 30) {
        const data = [];
        const today = new Date();

        for (let i = days; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);

            // 랜덤한 포트폴리오 가치 생성
            const baseValue = 42000000;
            const variation = Math.sin(i * 0.1) * 2000000 + (Math.random() - 0.5) * 1000000;

            data.push({
                date: date.toISOString().split('T')[0],
                value: baseValue + variation
            });
        }

        return data;
    }

    // 미니 차트 데이터 (주식별)
    generateMiniChartData(stockCode) {
        const stock = this.stockData.find(s => s.code === stockCode);
        if (!stock) return [];

        const data = [];
        const basePrice = stock.price;

        for (let i = 20; i >= 0; i--) {
            const variation = (Math.random() - 0.5) * 0.05; // ±5% 변동
            const price = Math.round(basePrice * (1 + variation));
            data.push(price);
        }

        return data;
    }

    // 공개 메서드들
    getStockData() {
        return this.stockData;
    }

    getPortfolioData() {
        return this.portfolioData;
    }

    getPositions() {
        return this.positions;
    }
}

// 전역 인스턴스 생성
window.sampleData = new SampleDataGenerator();