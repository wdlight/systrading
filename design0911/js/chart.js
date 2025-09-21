// 간단한 차트 라이브러리 (Canvas 기반)
class MiniChart {
    constructor(canvas, data, options = {}) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.data = data;
        this.options = {
            color: '#CCFF00',
            strokeWidth: 2,
            fillArea: true,
            fillOpacity: 0.1,
            ...options
        };

        this.setupCanvas();
        this.draw();
    }

    setupCanvas() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * window.devicePixelRatio;
        this.canvas.height = rect.height * window.devicePixelRatio;
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
    }

    draw() {
        if (!this.data || this.data.length < 2) return;

        const { width, height } = this.canvas.getBoundingClientRect();
        const ctx = this.ctx;

        ctx.clearRect(0, 0, width, height);

        // 데이터 정규화
        const min = Math.min(...this.data);
        const max = Math.max(...this.data);
        const range = max - min;

        if (range === 0) return;

        const points = this.data.map((value, index) => ({
            x: (index / (this.data.length - 1)) * width,
            y: height - ((value - min) / range) * height
        }));

        // 영역 채우기
        if (this.options.fillArea) {
            ctx.beginPath();
            ctx.moveTo(points[0].x, height);
            points.forEach(point => ctx.lineTo(point.x, point.y));
            ctx.lineTo(points[points.length - 1].x, height);
            ctx.closePath();

            const gradient = ctx.createLinearGradient(0, 0, 0, height);
            gradient.addColorStop(0, this.hexToRgba(this.options.color, this.options.fillOpacity));
            gradient.addColorStop(1, this.hexToRgba(this.options.color, 0));

            ctx.fillStyle = gradient;
            ctx.fill();
        }

        // 선 그리기
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        points.forEach(point => ctx.lineTo(point.x, point.y));

        ctx.strokeStyle = this.options.color;
        ctx.lineWidth = this.options.strokeWidth;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.stroke();
    }

    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    updateData(newData) {
        this.data = newData;
        this.draw();
    }
}

// 포트폴리오 대형 차트
class PortfolioChart {
    constructor(canvas, data, options = {}) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.data = data;
        this.options = {
            gridColor: '#2A2A2A',
            lineColor: '#CCFF00',
            fillColor: '#CCFF00',
            textColor: '#B0B0B0',
            strokeWidth: 3,
            ...options
        };

        this.setupCanvas();
        this.draw();
    }

    setupCanvas() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * window.devicePixelRatio;
        this.canvas.height = rect.height * window.devicePixelRatio;
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
    }

    draw() {
        if (!this.data || this.data.length < 2) return;

        const { width, height } = this.canvas.getBoundingClientRect();
        const ctx = this.ctx;

        ctx.clearRect(0, 0, width, height);

        const padding = 40;
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 2;

        // 데이터 정규화
        const values = this.data.map(d => d.value);
        const min = Math.min(...values);
        const max = Math.max(...values);
        const range = max - min;

        if (range === 0) return;

        // 그리드 그리기
        this.drawGrid(ctx, padding, chartWidth, chartHeight);

        // 데이터 포인트 계산
        const points = this.data.map((item, index) => ({
            x: padding + (index / (this.data.length - 1)) * chartWidth,
            y: padding + chartHeight - ((item.value - min) / range) * chartHeight,
            value: item.value,
            date: item.date
        }));

        // 영역 채우기
        ctx.beginPath();
        ctx.moveTo(points[0].x, padding + chartHeight);
        points.forEach(point => ctx.lineTo(point.x, point.y));
        ctx.lineTo(points[points.length - 1].x, padding + chartHeight);
        ctx.closePath();

        const gradient = ctx.createLinearGradient(0, padding, 0, padding + chartHeight);
        gradient.addColorStop(0, this.hexToRgba(this.options.fillColor, 0.2));
        gradient.addColorStop(1, this.hexToRgba(this.options.fillColor, 0));

        ctx.fillStyle = gradient;
        ctx.fill();

        // 선 그리기
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        points.forEach(point => ctx.lineTo(point.x, point.y));

        ctx.strokeStyle = this.options.lineColor;
        ctx.lineWidth = this.options.strokeWidth;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.stroke();

        // Y축 레이블
        this.drawYAxisLabels(ctx, min, max, padding, chartHeight);
    }

    drawGrid(ctx, padding, chartWidth, chartHeight) {
        ctx.strokeStyle = this.options.gridColor;
        ctx.lineWidth = 1;

        // 수평선
        for (let i = 0; i <= 4; i++) {
            const y = padding + (chartHeight / 4) * i;
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(padding + chartWidth, y);
            ctx.stroke();
        }

        // 수직선
        for (let i = 0; i <= 6; i++) {
            const x = padding + (chartWidth / 6) * i;
            ctx.beginPath();
            ctx.moveTo(x, padding);
            ctx.lineTo(x, padding + chartHeight);
            ctx.stroke();
        }
    }

    drawYAxisLabels(ctx, min, max, padding, chartHeight) {
        ctx.fillStyle = this.options.textColor;
        ctx.font = '12px -apple-system, BlinkMacSystemFont, sans-serif';
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';

        for (let i = 0; i <= 4; i++) {
            const value = min + ((max - min) / 4) * (4 - i);
            const y = padding + (chartHeight / 4) * i;
            const formattedValue = this.formatCurrency(value);

            ctx.fillText(formattedValue, padding - 10, y);
        }
    }

    formatCurrency(value) {
        if (value >= 1000000) {
            return `${(value / 1000000).toFixed(1)}M`;
        } else if (value >= 1000) {
            return `${(value / 1000).toFixed(0)}K`;
        }
        return value.toLocaleString();
    }

    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    updateData(newData) {
        this.data = newData;
        this.draw();
    }
}

// 차트 유틸리티 함수들
window.ChartUtils = {
    createMiniChart: function(canvas, data, isPositive = true) {
        const color = isPositive ? '#00C896' : '#FF4757';
        return new MiniChart(canvas, data, {
            color: color,
            strokeWidth: 2,
            fillArea: true,
            fillOpacity: 0.15
        });
    },

    createPortfolioChart: function(canvas, data) {
        return new PortfolioChart(canvas, data);
    },

    generateSparklineData: function(baseValue, days = 20, volatility = 0.05) {
        const data = [];
        let currentValue = baseValue;

        for (let i = 0; i < days; i++) {
            const change = (Math.random() - 0.5) * volatility;
            currentValue *= (1 + change);
            data.push(Math.round(currentValue));
        }

        return data;
    }
};