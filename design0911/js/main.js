// 메인 애플리케이션 JavaScript
class TradingApp {
    constructor() {
        this.charts = new Map();
        this.isLoaded = false;
        this.init();
    }

    async init() {
        // DOM 로드 대기
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        this.renderPortfolioSummary();
        this.renderStockList();
        this.setupEventListeners();
        this.startRealTimeUpdates();
        this.isLoaded = true;

        // 페이드인 애니메이션
        document.body.classList.add('fade-in');
    }

    renderPortfolioSummary() {
        const portfolioData = window.sampleData.getPortfolioData();
        const summaryElement = document.getElementById('portfolio-summary');

        if (!summaryElement) return;

        const isPositive = portfolioData.totalGain >= 0;
        const gainClass = isPositive ? 'portfolio-gain--positive' : 'portfolio-gain--negative';
        const gainIcon = isPositive ? '▲' : '▼';

        summaryElement.innerHTML = `
            <div class="portfolio-value">
                ${this.formatCurrency(portfolioData.totalValue)}
            </div>
            <div class="portfolio-gain ${gainClass}">
                <span class="portfolio-gain__icon">${gainIcon}</span>
                <span class="portfolio-gain__amount">
                    ${this.formatCurrency(Math.abs(portfolioData.totalGain))}
                    (${Math.abs(portfolioData.totalGainPercent).toFixed(2)}%)
                </span>
            </div>
            <div class="portfolio-stats">
                <div class="stat-item">
                    <div class="stat-item__label">일일 손익</div>
                    <div class="stat-item__value ${portfolioData.dayGain >= 0 ? 'portfolio-gain--positive' : 'portfolio-gain--negative'}">
                        ${this.formatCurrency(portfolioData.dayGain)}
                    </div>
                </div>
                <div class="stat-item">
                    <div class="stat-item__label">투자 원금</div>
                    <div class="stat-item__value">
                        ${this.formatCurrency(portfolioData.totalCost)}
                    </div>
                </div>
                <div class="stat-item">
                    <div class="stat-item__label">매수 가능 금액</div>
                    <div class="stat-item__value">
                        ${this.formatCurrency(portfolioData.buyingPower)}
                    </div>
                </div>
            </div>
        `;

        // 포트폴리오 차트 렌더링
        this.renderPortfolioChart();
    }

    renderPortfolioChart() {
        const chartContainer = document.getElementById('portfolio-chart');
        if (!chartContainer) return;

        const canvas = document.createElement('canvas');
        canvas.width = 800;
        canvas.height = 200;
        canvas.style.width = '100%';
        canvas.style.height = '200px';

        chartContainer.innerHTML = '';
        chartContainer.appendChild(canvas);

        const chartData = window.sampleData.generateChartData(30);
        const chart = window.ChartUtils.createPortfolioChart(canvas, chartData);
        this.charts.set('portfolio', chart);
    }

    renderStockList() {
        const stockData = window.sampleData.getStockData();
        const positions = window.sampleData.getPositions();
        const listElement = document.getElementById('stock-list');

        if (!listElement) return;

        listElement.innerHTML = stockData.map(stock => {
            const position = positions.find(p => p.code === stock.code);
            const isPositive = stock.change >= 0;
            const changeClass = isPositive ? 'stock-price__change--positive' : 'stock-price__change--negative';
            const itemClass = isPositive ? 'stock-item--positive' : 'stock-item--negative';
            const changeIcon = isPositive ? '▲' : '▼';

            return `
                <div class="stock-item ${itemClass}" data-symbol="${stock.code}">
                    <div class="stock-item__header">
                        <div class="stock-info">
                            <div class="stock-info__symbol">${stock.code}</div>
                            <div class="stock-info__name">${stock.name}</div>
                        </div>
                        <div class="stock-price">
                            <div class="stock-price__current">
                                ${this.formatPrice(stock.price)}
                            </div>
                            <div class="stock-price__change ${changeClass}">
                                <span>${changeIcon}</span>
                                <span>${this.formatPrice(Math.abs(stock.change))} (${Math.abs(stock.changePercent).toFixed(2)}%)</span>
                            </div>
                        </div>
                    </div>
                    <div class="stock-item__chart">
                        <canvas class="mini-chart" data-symbol="${stock.code}"></canvas>
                    </div>
                    <div class="stock-item__metrics">
                        <div class="metric">
                            <div class="metric__label">RSI</div>
                            <div class="metric__value">${stock.rsi.toFixed(1)}</div>
                        </div>
                        <div class="metric">
                            <div class="metric__label">MACD</div>
                            <div class="metric__value">${stock.macd.toFixed(1)}</div>
                        </div>
                        <div class="metric">
                            <div class="metric__label">거래량</div>
                            <div class="metric__value">${this.formatVolume(stock.volume)}</div>
                        </div>
                    </div>
                    ${position ? `
                        <div class="stock-item__position">
                            <div class="position-info">
                                <span>보유: ${position.shares}주</span>
                                <span class="${position.gain >= 0 ? 'portfolio-gain--positive' : 'portfolio-gain--negative'}">
                                    ${this.formatCurrency(position.gain)} (${position.gainPercent.toFixed(2)}%)
                                </span>
                            </div>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');

        // 미니 차트 렌더링
        this.renderMiniCharts();
    }

    renderMiniCharts() {
        const canvasElements = document.querySelectorAll('.mini-chart');

        canvasElements.forEach(canvas => {
            const symbol = canvas.dataset.symbol;
            const stockData = window.sampleData.getStockData().find(s => s.code === symbol);

            if (stockData) {
                const chartData = window.ChartUtils.generateSparklineData(stockData.price, 20, 0.02);
                const isPositive = stockData.change >= 0;
                const chart = window.ChartUtils.createMiniChart(canvas, chartData, isPositive);
                this.charts.set(`mini-${symbol}`, chart);
            }
        });
    }

    setupEventListeners() {
        // 실시간 데이터 업데이트 이벤트
        window.addEventListener('dataUpdate', (event) => {
            if (this.isLoaded) {
                this.updateDisplay(event.detail);
            }
        });

        // 주식 아이템 클릭 이벤트
        document.addEventListener('click', (event) => {
            const stockItem = event.target.closest('.stock-item');
            if (stockItem) {
                this.selectStock(stockItem.dataset.symbol);
            }
        });

        // 액션 버튼 이벤트
        const buyButton = document.getElementById('buy-button');
        const sellButton = document.getElementById('sell-button');

        if (buyButton) {
            buyButton.addEventListener('click', () => this.showBuyDialog());
        }

        if (sellButton) {
            sellButton.addEventListener('click', () => this.showSellDialog());
        }

        // 반응형 처리
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }

    startRealTimeUpdates() {
        // 실시간 업데이트는 sample-data.js에서 자동으로 시작됨
        console.log('✅ Real-time updates started');
    }

    updateDisplay(data) {
        // 포트폴리오 요약 업데이트
        this.updatePortfolioSummary(data.portfolio);

        // 주식 가격 업데이트
        this.updateStockPrices(data.stocks);

        // 차트 업데이트
        this.updateCharts(data);
    }

    updatePortfolioSummary(portfolioData) {
        const valueElement = document.querySelector('.portfolio-value');
        const gainElement = document.querySelector('.portfolio-gain__amount');

        if (valueElement) {
            valueElement.textContent = this.formatCurrency(portfolioData.totalValue);
            valueElement.classList.add('updated');
            setTimeout(() => valueElement.classList.remove('updated'), 1000);
        }

        if (gainElement) {
            const isPositive = portfolioData.totalGain >= 0;
            gainElement.textContent = `${this.formatCurrency(Math.abs(portfolioData.totalGain))} (${Math.abs(portfolioData.totalGainPercent).toFixed(2)}%)`;
            gainElement.className = isPositive ? 'portfolio-gain--positive' : 'portfolio-gain--negative';
        }
    }

    updateStockPrices(stocks) {
        stocks.forEach(stock => {
            const stockItem = document.querySelector(`[data-symbol="${stock.code}"]`);
            if (!stockItem) return;

            const priceElement = stockItem.querySelector('.stock-price__current');
            const changeElement = stockItem.querySelector('.stock-price__change');

            if (priceElement) {
                priceElement.textContent = this.formatPrice(stock.price);
                priceElement.classList.add('updated');
                setTimeout(() => priceElement.classList.remove('updated'), 1000);
            }

            if (changeElement) {
                const isPositive = stock.change >= 0;
                const changeIcon = isPositive ? '▲' : '▼';
                changeElement.innerHTML = `
                    <span>${changeIcon}</span>
                    <span>${this.formatPrice(Math.abs(stock.change))} (${Math.abs(stock.changePercent).toFixed(2)}%)</span>
                `;
                changeElement.className = `stock-price__change ${isPositive ? 'stock-price__change--positive' : 'stock-price__change--negative'}`;
            }

            // RSI, MACD 업데이트
            const rsiElement = stockItem.querySelector('.metric__value');
            if (rsiElement) {
                rsiElement.textContent = stock.rsi.toFixed(1);
            }
        });
    }

    updateCharts(data) {
        // 미니 차트 업데이트 (필요시)
        data.stocks.forEach(stock => {
            const chart = this.charts.get(`mini-${stock.code}`);
            if (chart) {
                const newData = window.ChartUtils.generateSparklineData(stock.price, 20, 0.02);
                chart.updateData(newData);
            }
        });
    }

    selectStock(symbol) {
        // 모든 주식 아이템에서 선택 해제
        document.querySelectorAll('.stock-item').forEach(item => {
            item.classList.remove('selected');
        });

        // 선택된 주식 아이템에 클래스 추가
        const selectedItem = document.querySelector(`[data-symbol="${symbol}"]`);
        if (selectedItem) {
            selectedItem.classList.add('selected');
        }

        console.log(`📈 Selected stock: ${symbol}`);
    }

    showBuyDialog() {
        alert('매수 주문 기능 (실제 구현 예정)');
    }

    showSellDialog() {
        alert('매도 주문 기능 (실제 구현 예정)');
    }

    handleResize() {
        // 차트 리사이즈 처리
        this.charts.forEach(chart => {
            if (chart.setupCanvas) {
                chart.setupCanvas();
                chart.draw();
            }
        });
    }

    // 유틸리티 메서드들
    formatCurrency(amount) {
        if (amount >= 100000000) { // 1억 이상
            return `${(amount / 100000000).toFixed(1)}억원`;
        } else if (amount >= 10000) { // 1만 이상
            return `${(amount / 10000).toFixed(0)}만원`;
        } else {
            return `${amount.toLocaleString()}원`;
        }
    }

    formatPrice(price) {
        return price.toLocaleString() + '원';
    }

    formatVolume(volume) {
        if (volume >= 1000000) {
            return `${(volume / 1000000).toFixed(1)}M`;
        } else if (volume >= 1000) {
            return `${(volume / 1000).toFixed(0)}K`;
        }
        return volume.toLocaleString();
    }
}

// 앱 초기화
window.addEventListener('load', () => {
    window.tradingApp = new TradingApp();
});

// PWA 지원을 위한 서비스 워커 등록
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}